import os
from dotenv import load_dotenv
import anthropic

load_dotenv()

client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

message = client.messages.create(
    model="claude-sonnet-4-6",
    max_tokens=100,
    messages=[{"role": "user", "content": "say hi"}]
)

print(message.content[0].text)