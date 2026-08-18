import os
import google.generativeai as genai
from config import GEMINI_API_KEY

class LLMClient:
    def __init__(self):
        self.api_key = GEMINI_API_KEY or os.getenv("GEMINI_API_KEY")
        if self.api_key:
            genai.configure(api_key=self.api_key)
            # Use gemini-1.5-flash or gemini-pro
            self.model = genai.GenerativeModel('gemini-1.5-flash')
        else:
            self.model = None

    def generate_json(self, prompt: str, system_instruction: str = None) -> str:
        if not self.model:
            raise ValueError("Gemini API key is not configured.")
        
        # Configure JSON output if possible
        generation_config = {
            "response_mime_type": "application/json"
        }
        
        # We can pass system instruction if supported
        response = self.model.generate_content(
            prompt,
            generation_config=generation_config
        )
        return response.text

llm_client = LLMClient()
