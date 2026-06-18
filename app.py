import streamlit as st
from dotenv import load_dotenv
from src.agents.graph import build_graph

load_dotenv()

st.set_page_config(page_title="Code Review Agent", page_icon="🔍", layout="wide")
st.title("🔍 Code Review Agent")
st.caption("基于 Claude + LangGraph 的智能代码审查系统")

col1, col2 = st.columns(2)

with col1:
    st.subheader("输入代码")
    code = st.text_area("粘贴你的代码", height=400, placeholder="把代码粘贴到这里...")
    run = st.button("开始审查", type="primary", use_container_width=True)

with col2:
    st.subheader("审查报告")
    if run and code.strip():
        with st.spinner("Agent正在分析中..."):
            graph = build_graph()
            result = graph.invoke({
                "code": code,
                "context": "",
                "analysis": {},
                "final_report": ""
            })
            a = result["analysis"]

            score = a.get("score", 0)
            color = "green" if score >= 70 else "orange" if score >= 40 else "red"
            st.metric("综合评分", f"{score}/100")

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

    elif run:
        st.warning("请先输入代码")
    else:
        st.info("在左边输入代码，点击「开始审查」")