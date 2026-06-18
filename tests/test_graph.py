from dotenv import load_dotenv
from src.agents.graph import build_graph

load_dotenv()

code = """
def divide(a, b):
    return a / b

password = "123456"
"""

graph = build_graph()
result = graph.invoke({
    "code": code,
    "context": "",
    "analysis": {},
    "final_report": ""
})

print(result["final_report"])