import os
import sqlite3
from typing import TypedDict
from dotenv import load_dotenv
from anthropic import Anthropic
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.sqlite import SqliteSaver
from src.agents.analyzer import analyze_code
from src.rag.indexer import index_code_files

load_dotenv()

class ReviewState(TypedDict):
    code: str
    context: str
    analysis: dict
    fixed_code: str
    final_report: str

def retriever_node(state: ReviewState) -> ReviewState:
    print("🔍 Retriever: 正在检索相关上下文...")
    try:
        vectordb = index_code_files("./sample_code")
        results = vectordb.similarity_search(state["code"], k=2)
        context = "\n".join([doc.page_content for doc in results])
    except Exception:
        context = ""
    return {**state, "context": context}

def analyzer_node(state: ReviewState) -> ReviewState:
    print("🔬 Analyzer: 正在分析代码...")
    analysis = analyze_code(state["code"], state["context"])
    return {**state, "analysis": analysis}

def fixer_node(state: ReviewState) -> ReviewState:
    print("🔧 Fixer: 正在生成修复代码...")
    a = state["analysis"]
    issues = "\n".join([
        *[f"Bug: {b}" for b in a.get("bugs", [])],
        *[f"安全: {s}" for s in a.get("security", [])],
        *[f"性能: {p}" for p in a.get("performance", [])],
        *[f"风格: {s}" for s in a.get("style", [])],
    ])
    prompt = f"""你是一个专业的代码修复专家。请根据以下发现的问题，修复原始代码。

发现的问题：
{issues}

原始代码：
{state["code"]}

请直接返回修复后的完整代码，不要任何解释、注释说明或markdown代码块标记。"""

    client = Anthropic()
    message = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=4096,
        messages=[{"role": "user", "content": prompt}]
    )
    fixed_code = message.content[0].text.strip()
    return {**state, "fixed_code": fixed_code}

def reviewer_node(state: ReviewState) -> ReviewState:
    print("📝 Reviewer: 正在生成报告...")
    a = state["analysis"]
    report = f"""
=== 代码审查报告 ===

🐛 Bug ({len(a.get('bugs', []))}个):
{chr(10).join(f'  - {b}' for b in a.get('bugs', []))}

🔒 安全问题 ({len(a.get('security', []))}个):
{chr(10).join(f'  - {s}' for s in a.get('security', []))}

⚡ 性能问题 ({len(a.get('performance', []))}个):
{chr(10).join(f'  - {p}' for p in a.get('performance', []))}

✨ 风格问题 ({len(a.get('style', []))}个):
{chr(10).join(f'  - {s}' for s in a.get('style', []))}

📊 综合评分: {a.get('score', 0)}/100

🔧 修复后代码:
{state.get('fixed_code', '（无修复代码）')}
"""
    return {**state, "final_report": report}

def build_graph():
    conn = sqlite3.connect("checkpoints.db", check_same_thread=False)
    checkpointer = SqliteSaver(conn)

    graph = StateGraph(ReviewState)
    graph.add_node("retriever", retriever_node)
    graph.add_node("analyzer", analyzer_node)
    graph.add_node("fixer", fixer_node)
    graph.add_node("reviewer", reviewer_node)
    graph.set_entry_point("retriever")
    graph.add_edge("retriever", "analyzer")
    graph.add_edge("analyzer", "fixer")
    graph.add_edge("fixer", "reviewer")
    graph.add_edge("reviewer", END)
    return graph.compile(checkpointer=checkpointer)