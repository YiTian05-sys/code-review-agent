import re
import json
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
    language: str
    quality_score: float


def supervisor_node(state: ReviewState) -> ReviewState:
    print("🎯 Supervisor: 正在检测代码语言...")
    client = Anthropic()
    prompt = f"""分析以下代码是什么编程语言，并给出针对该语言的审查重点。

代码：
{state["code"][:500]}

请严格按照以下JSON格式返回，language字段只填语言名称本身（如 Python、JavaScript、Java、TypeScript 等）：
{{
    "language": "Python",
    "hints": "重点检查异常处理和类型安全"
}}

只返回JSON对象，不要任何解释或代码块标记。"""

    message = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=300,
        messages=[{"role": "user", "content": prompt}]
    )
    text = message.content[0].text
    print(f"[supervisor] Claude raw: {text!r}")
    language = "未知"
    hints = ""
    try:
        match = re.search(r'\{.*\}', text, re.DOTALL)
        if match:
            parsed = json.loads(match.group())
            language = parsed.get("language", "未知") or "未知"
            hints = parsed.get("hints", "")
    except (json.JSONDecodeError, ValueError):
        pass

    context_hint = f"[语言: {language}] {hints}"
    return {**state, "language": language, "context": context_hint}


def retriever_node(state: ReviewState) -> ReviewState:
    print("🔍 Retriever: 正在检索相关上下文...")
    try:
        vectordb = index_code_files("./sample_code")
        results = vectordb.similarity_search(state["code"], k=2)
        retrieved = "\n".join([doc.page_content for doc in results])
        existing = state.get("context", "")
        context = f"{existing}\n{retrieved}".strip() if retrieved else existing
    except Exception:
        context = state.get("context", "")
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


def evaluator_node(state: ReviewState) -> ReviewState:
    print("⭐ Evaluator: 正在评估报告质量...")
    client = Anthropic()
    prompt = f"""你是一个代码审查质量评估专家。请评估以下审查报告的质量，评分标准：

1. 问题描述是否具体（30分）：问题定位准确、描述清晰
2. 修复建议是否可行（40分）：修复代码完整、逻辑正确、能实际解决问题
3. 有无误报（30分）：没有把正常代码当作问题报告

审查报告：
{state["final_report"]}

原始代码：
{state["code"]}

请严格按照以下JSON格式返回，score字段填写0到100之间的整数：
{{"score": 85}}

只返回JSON对象，不要任何解释或代码块标记。"""

    message = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=30,
        messages=[{"role": "user", "content": prompt}]
    )
    text = message.content[0].text.strip()
    print(f"[evaluator] Claude raw: {text!r}")
    quality_score = 0.0
    try:
        match = re.search(r'\{.*\}', text, re.DOTALL)
        if match:
            parsed = json.loads(match.group())
            quality_score = float(parsed.get("score", 0))
    except (json.JSONDecodeError, ValueError):
        num_match = re.search(r'\d+(?:\.\d+)?', text)
        if num_match:
            quality_score = float(num_match.group())
    quality_score = min(100.0, max(0.0, quality_score))
    return {**state, "quality_score": quality_score}


def build_graph():
    conn = sqlite3.connect("checkpoints.db", check_same_thread=False)
    checkpointer = SqliteSaver(conn)

    graph = StateGraph(ReviewState)
    graph.add_node("supervisor", supervisor_node)
    graph.add_node("retriever", retriever_node)
    graph.add_node("analyzer", analyzer_node)
    graph.add_node("fixer", fixer_node)
    graph.add_node("reviewer", reviewer_node)
    graph.add_node("evaluator", evaluator_node)
    graph.set_entry_point("supervisor")
    graph.add_edge("supervisor", "retriever")
    graph.add_edge("retriever", "analyzer")
    graph.add_edge("analyzer", "fixer")
    graph.add_edge("fixer", "reviewer")
    graph.add_edge("reviewer", "evaluator")
    graph.add_edge("evaluator", END)
    return graph.compile(checkpointer=checkpointer)
