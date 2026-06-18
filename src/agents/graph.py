import os
from typing import TypedDict, Annotated
from dotenv import load_dotenv
from langgraph.graph import StateGraph, END
from src.agents.analyzer import analyze_code
from src.rag.indexer import index_code_files

load_dotenv()

class ReviewState(TypedDict):
    code: str
    context: str
    analysis: dict
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
"""
    return {**state, "final_report": report}

def build_graph():
    graph = StateGraph(ReviewState)
    graph.add_node("retriever", retriever_node)
    graph.add_node("analyzer", analyzer_node)
    graph.add_node("reviewer", reviewer_node)
    graph.set_entry_point("retriever")
    graph.add_edge("retriever", "analyzer")
    graph.add_edge("analyzer", "reviewer")
    graph.add_edge("reviewer", END)
    return graph.compile()