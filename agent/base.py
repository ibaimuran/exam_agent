"""Agent 基类 — 共享 AI 调用能力"""
import os
import openai


class BaseAgent:
    """所有 Agent 的基类，封装 DeepSeek API 调用"""

    def __init__(self, api_key: str = None, base_url: str = None):
        self.api_key = api_key or os.getenv("DEEPSEEK_API_KEY", "")
        self.base_url = base_url or "https://api.deepseek.com"
        self.model = "deepseek-chat"

    def _call_ai(self, system: str, user: str, temp: float = 0.1, max_tok: int = 4000) -> str:
        client = openai.OpenAI(api_key=self.api_key, base_url=self.base_url)
        resp = client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            temperature=temp,
            max_tokens=max_tok,
        )
        return resp.choices[0].message.content
