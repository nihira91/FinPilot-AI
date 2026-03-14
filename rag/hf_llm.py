#Genai Inference API Client


import os
from google import genai
from google.genai import types
from dotenv import load_dotenv

load_dotenv()

MODEL_ID = "gemini-2.5-flash"


def call_llm(system_prompt: str, user_message: str, max_new_tokens: int = 1024) -> str:
    token = os.getenv("GEMINI_API_KEY")

    if not token:
        raise EnvironmentError(
            "GEMINI_API_KEY not found. "
        )

    try:
        client = genai.Client(api_key=token)
        full_prompt = f"{system_prompt}\n\n{user_message}"
        
        response = client.models.generate_content(
            model=MODEL_ID,
            contents=full_prompt,
            config=types.GenerateContentConfig(
                temperature=0.3,
                max_output_tokens=max_new_tokens,
            )
        )
        return response.text.strip()

    except Exception as e:
        return f"[LLM Error] {str(e)}"
