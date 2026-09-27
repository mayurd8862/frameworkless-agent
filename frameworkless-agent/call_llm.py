
import json
from typing import Any, Callable, Dict, Optional
import os
from dotenv import load_dotenv
from google import genai
from google.genai import types
load_dotenv()

from prompt import SYSTEM_PROMPT


# ============================================================
# 1. LLM CLIENT
# ============================================================


GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
client = genai.Client()
# client = genai.Client(api_key="GEMINI_API_KEY")



# ============================================================
# 7. GEMINI LLM CALL
# ============================================================

MODEL = "gemini-3.1-flash-lite"

def call_llm(
    messages: list[types.Content]
) -> Dict[str, Any]:

    """
    Sends the conversation to Gemini and parses its JSON response.
    """

    response = client.models.generate_content(
        model=MODEL,
        contents=messages,
        config=types.GenerateContentConfig(
            system_instruction=SYSTEM_PROMPT,
            temperature=0,
            response_mime_type="application/json"
        )
    )

    content = response.text

    if not content:
        raise ValueError(
            "Gemini returned an empty response."
        )

    try:
        result = json.loads(content)

    except json.JSONDecodeError as error:

        raise ValueError(
            f"Gemini returned invalid JSON:\n{content}"
        ) from error

    return result