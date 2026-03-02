# ─────────────────────────────────────────────────────────────────────────────
# hf_llm.py  —  HuggingFace Inference API Client
#
# PURPOSE : Send a prompt to a HuggingFace-hosted LLM and return the response.
#
# WHY HuggingFace INSTEAD OF OpenAI ?
#   • Free tier available with HF_API_TOKEN (no credit card needed for many models).
#   • Many open-weight models: Mistral, Zephyr, Falcon, Llama, etc.
#   • Same Python API for all of them.
#
# MODEL WE USE : "mistralai/Mistral-7B-Instruct-v0.2"
#   • Strong instruction-following capability.
#   • Free on HuggingFace Inference API (rate-limited but fine for a project).
#   • You can swap MODEL_ID for any HF-hosted chat model below.
#
# HOW TO GET A TOKEN :
#   1. Go to https://huggingface.co/settings/tokens
#   2. Create a "Read" token (free).
#   3. Put it in your .env file as:  HF_API_TOKEN=hf_xxxxx
# ─────────────────────────────────────────────────────────────────────────────

import os
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()   # Load environment variables from .env file

# The HuggingFace model to use for text generation
# Change this to any instruction-tuned model available on HuggingFace
MODEL_ID = "gemini-2.5-flash"


def call_llm(system_prompt: str, user_message: str, max_new_tokens: int = 1024) -> str:
    """
    Send a system prompt + user message to the HuggingFace Inference API
    and return the model's text response.

    Args:
        system_prompt   : the agent's persona and output format instructions
        user_message    : context + query built by build_user_message()
        max_new_tokens  : maximum tokens the model can generate in its reply

    Returns:
        The model's response as a plain string.
        Returns an error message string if the API call fails (never crashes).
    """
    token = os.getenv("GEMINI_API_KEY")

    if not token:
        raise EnvironmentError(
            "GEMINI_API_KEY not found. "
            "Create one at https://aistudio.google.com/app/apikey "
            "and add it to your .env file as: GEMINI_API_KEY=your_key"
        )

    genai.configure(api_key=token)
    model = genai.GenerativeModel(MODEL_ID)

    # ── Format the prompt in Mistral's [INST] chat template ───────────────────
    # Mistral-Instruct uses [INST] ... [/INST] to mark user turns.
    # We prepend the system prompt inside the first user turn.

    try:
        full_prompt = f"{system_prompt}\n\n{user_message}"
        response = model.generate_content(
            full_prompt,
            generation_config={
                "temperature": 0.3,
                "max_output_tokens": max_new_tokens,
            }
        )
        return response.text.strip()

    except Exception as e:
        return f"[LLM Error] {str(e)}"