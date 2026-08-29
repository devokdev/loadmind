import os
import json
import re
import requests
from config import GROQ_API_KEY, GROQ_MODEL

class LLMClient:
    def __init__(self):
        self.api_key = GROQ_API_KEY or os.getenv("GROQ_API_KEY")
        self.model = GROQ_MODEL or "qwen/qwen3.6-27b"
        self.api_url = "https://api.groq.com/openai/v1/chat/completions"

    def generate_json(self, prompt: str, system_instruction: str = None) -> str:
        if not self.api_key:
            raise ValueError("Groq API key is not configured.")

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

        sys_msg = system_instruction or "You are the LoadMind Autonomous AI Diagnostician. Respond in raw JSON format only matching the requested schema. Do not enclose in markdown blocks."

        messages = [
            {"role": "system", "content": sys_msg},
            {"role": "user", "content": prompt}
        ]

        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": 0.1,
            "max_tokens": 1024
        }

        try:
            res = requests.post(self.api_url, headers=headers, json=payload, timeout=12)
            if res.status_code == 200:
                data = res.json()
                content = data["choices"][0]["message"]["content"]
                # Strip think tags if model outputs them
                content = re.sub(r'<think>.*?</think>', '', content, flags=re.DOTALL).strip()
                # Strip markdown fences if present
                if content.startswith("```json"):
                    content = content[7:]
                if content.startswith("```"):
                    content = content[3:]
                if content.endswith("```"):
                    content = content[:-3]
                content = content.strip()
                return content
            else:
                print(f"Groq API call returned status {res.status_code}: {res.text}")
                raise Exception(f"Groq API error: {res.status_code}")
        except Exception as e:
            print(f"Groq generation error: {e}")
            raise e

llm_client = LLMClient()


