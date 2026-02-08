import os
from typing import List, Dict, Optional
import requests
import json
from dotenv import load_dotenv

load_dotenv(override=True)

class LLMEngine:
    def __init__(self):
        self.api_key = os.getenv("OPENROUTER_API_KEY") or os.getenv("OPENAI_API_KEY")
        self.base_url = "https://openrouter.ai/api/v1/chat/completions"
        if not self.api_key or self.api_key in ["your_openrouter_key_here", "your_key_here"]:
            self.api_key = None
            print("WARNING: Valid API_KEY not found. Running in mock mode.")

    async def generate_response(self, messages: List[Dict[str, any]], model: str = "openai/gpt-oss-20b:free"):
        if not self.api_key:
            user_msg = messages[-1]["content"] if messages else ""
            return {"role": "assistant", "content": f"Mock response to: {user_msg}"}

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "http://localhost:3000", # Optional for OpenRouter
            "X-Title": "Aura AI",
        }

        payload = {
            "model": model,
            "messages": messages,
            "reasoning": {"enabled": True}
        }

        try:
            response = requests.post(self.base_url, headers=headers, data=json.dumps(payload))
            response.raise_for_status()
            data = response.json()
            return data['choices'][0]['message']
        except Exception as e:
            return {"role": "assistant", "content": f"Error connecting to OpenRouter: {str(e)}"}

    def moderate_content(self, text: str) -> bool:
        prohibited_terms = ["script kiddy", "illegal action"]
        for term in prohibited_terms:
            if term in text.lower():
                return False
        return True

engine = LLMEngine()
