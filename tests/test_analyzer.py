import os
from dotenv import load_dotenv
from src.agents.analyzer import analyze_code

load_dotenv()

code = """
def divide(a, b):
    return a / b

password = "123456"
"""

result = analyze_code(code)

print("Bug:", result["bugs"])
print("安全问题:", result["security"])
print("性能问题:", result["performance"])
print("风格问题:", result["style"])
print("评分:", result["score"])