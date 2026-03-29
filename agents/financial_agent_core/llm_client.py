import os
from dotenv import load_dotenv
from google import genai
from google.genai import types

from .constants import MODEL_ID

load_dotenv()


def call_gemini(prompt: str, max_tokens: int = 8192) -> str:
    token = os.getenv("GEMINI_API_KEY")
    client = genai.Client(api_key=token)
    response = client.models.generate_content(
        model=MODEL_ID,
        contents=prompt,
        config=types.GenerateContentConfig(
            temperature=0.3,
            max_output_tokens=max_tokens,
        ),
    )
    return response.text.strip()
