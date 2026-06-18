import os
from dotenv import load_dotenv
from src.agents.graph import build_graph

load_dotenv()

graph = build_graph()

# 第一次运行，用thread_id标识会话
config = {"configurable": {"thread_id": "session_001"}}

code = """
def divide(a, b):
    return a / b

password = "123456"
"""

print("=== 第一次运行 ===")
result = graph.invoke({
    "code": code,
    "context": "",
    "analysis": {},
    "final_report": ""
}, config=config)

print(result["final_report"])

# 模拟重启后恢复会话
print("=== 从Redis恢复会话状态 ===")
state = graph.get_state(config)
print(f"会话已保存，评分：{state.values['analysis'].get('score')}/100")