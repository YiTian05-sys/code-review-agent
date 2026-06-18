import uuid
import sqlite3
import streamlit as st
from dotenv import load_dotenv
from src.agents.graph import build_graph

load_dotenv()

st.set_page_config(
    page_title="Code Review Agent 🔍 | Multi-Agent 智能代码审查系统",
    page_icon="🔍",
    layout="wide"
)

if "thread_id" not in st.session_state:
    st.session_state.thread_id = str(uuid.uuid4())



def render_report(result: dict):
    a = result.get("analysis", {})
    lang_map = {
        "Python": "python", "JavaScript": "javascript",
        "Java": "java", "TypeScript": "typescript",
    }

    c1, c2, c3 = st.columns(3)
    c1.metric("检测语言", result.get("language") or "未知")
    c2.metric("综合评分", f"{a.get('score', 0)}/100")
    c3.metric("审查质量", f"{result.get('quality_score', 0):.0f}/100")

    if a.get("bugs"):
        st.error(f"🐛 Bug（{len(a['bugs'])}个）")
        for b in a["bugs"]:
            st.write(f"- {b}")

    if a.get("security"):
        st.warning(f"🔒 安全问题（{len(a['security'])}个）")
        for s in a["security"]:
            st.write(f"- {s}")

    if a.get("performance"):
        st.info(f"⚡ 性能问题（{len(a['performance'])}个）")
        for p in a["performance"]:
            st.write(f"- {p}")

    if a.get("style"):
        st.info(f"✨ 风格问题（{len(a['style'])}个）")
        for s in a["style"]:
            st.write(f"- {s}")

    if result.get("fixed_code"):
        st.subheader("🔧 修复后代码")
        lang_key = lang_map.get(result.get("language", ""), "python")
        st.code(result["fixed_code"], language=lang_key)


# --- Page header ---
st.title("Code Review Agent 🔍 | Multi-Agent 智能代码审查系统")
st.caption("基于 Claude + LangGraph 的智能代码审查系统")

# --- Sidebar: history ---
with st.sidebar:
    st.header("📋 历史审查记录")
    try:
        conn = sqlite3.connect("checkpoints.db", check_same_thread=False)
        rows = conn.execute(
            "SELECT DISTINCT thread_id, MAX(checkpoint_id) as last_id "
            "FROM checkpoints GROUP BY thread_id ORDER BY last_id DESC LIMIT 20"
        ).fetchall()
        conn.close()
        if rows:
            for row in rows:
                tid = row[0]
                if st.button(f"🕐 {tid[:8]}...", key=f"hist_{tid}"):
                    st.session_state.selected_thread = tid
        else:
            st.info("暂无历史记录")
    except Exception:
        st.info("暂无历史记录")

# --- File uploader ---
uploaded_file = st.file_uploader(
    "上传代码文件（支持 .py .js .java .ts）",
    type=["py", "js", "java", "ts"]
)

# --- Main layout ---
col1, col2 = st.columns(2)

with col1:
    st.subheader("输入代码")
    default_code = ""
    if uploaded_file is not None:
        default_code = uploaded_file.read().decode("utf-8")
    code = st.text_area(
        "粘贴你的代码",
        height=400,
        placeholder="把代码粘贴到这里...",
        value=default_code,
    )
    run = st.button("开始审查", type="primary", use_container_width=True)

with col2:
    st.subheader("审查报告")

    selected = st.session_state.get("selected_thread")
    if selected and not run:
        graph = build_graph()
        hist_config = {"configurable": {"thread_id": selected}}
        try:
            snapshot = graph.get_state(hist_config)
            if snapshot and snapshot.values:
                st.caption(f"历史记录：{selected[:8]}...")
                render_report(snapshot.values)
            else:
                st.warning("该历史记录为空")
        except Exception as e:
            st.warning(f"无法恢复历史记录：{e}")
    elif run and code.strip():
        st.session_state.pop("selected_thread", None)
        st.session_state.thread_id = str(uuid.uuid4())
        with st.spinner("Agent正在分析中..."):
            graph = build_graph()
            config = {"configurable": {"thread_id": st.session_state.thread_id}}
            result = graph.invoke(
                {
                    "code": code,
                    "context": "",
                    "analysis": {},
                    "fixed_code": "",
                    "final_report": "",
                    "language": "",
                    "quality_score": 0.0,
                },
                config=config,
            )
            render_report(result)
    elif run:
        st.warning("请先输入代码")
    else:
        st.info("在左边输入代码，点击「开始审查」")
