import os
import json
import re
from dotenv import load_dotenv
from anthropic import Anthropic

load_dotenv()

client = Anthropic()

def analyze_code(code: str, context: str = "") -> dict:
    prompt = f"""你是一个专业的代码审查专家。请分析以下代码，找出：
1. Bug和潜在错误
2. 安全漏洞
3. 性能问题
4. 代码风格问题

相关上下文：
{context}

待审查代码：
{code}

请用以下JSON格式返回结果：
{{
    "bugs": ["bug列表"],
    "security": ["安全问题列表"],
    "performance": ["性能问题列表"],
    "style": ["风格问题列表"],
    "score": 0-100的评分
}}

只返回JSON，不要其他内容。"""

    message = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=1000,
        messages=[{"role": "user", "content": prompt}]
    )

    text = message.content[0].text
    match = re.search(r'\{.*\}', text, re.DOTALL)
    if match:
        result = json.loads(match.group())
    else:
        raise ValueError(f"无法解析返回内容: {text}")
    return result