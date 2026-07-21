"""
The ONLY file in the whole app that knows which LLM provider we're using.
Every agent calls call_llm(prompt) and gets a string back — they never
import the Groq/OpenAI/Gemini SDK directly. This means switching providers
again later is a change in this one file, nothing else.

Currently using Groq (Llama 3.3 70B) — OpenAI-compatible API.
"""

import os
import json
from groq import Groq
from dotenv import load_dotenv

load_dotenv()

_client = Groq(api_key=os.getenv("GROQ_API_KEY"))

MODEL = "llama-3.3-70b-versatile"


def call_llm(prompt: str) -> str:
    """
    Sends a prompt to the LLM and returns the raw text response.
    Callers are responsible for telling the model to return JSON
    in their prompt, and for parsing/validating the result themselves.
    """
    response = _client.chat.completions.create(
        model=MODEL,
        messages=[{"role": "user", "content": prompt}],
    )
    return response.choices[0].message.content.strip()


def call_llm_json(prompt: str) -> dict:
    """
    Convenience wrapper for the common case: prompt asks for JSON,
    we strip markdown fences if the model adds them, and parse it.
    Raises json.JSONDecodeError if the model didn't return valid JSON —
    callers should catch this and decide how to handle a bad response.
    """
    text = call_llm(prompt)
    text = text.replace("```json", "").replace("```", "").strip()
    return json.loads(text)


if __name__ == "__main__":
    # Quick manual test — run this file directly: python -m services.llm_client
    test_prompt = 'Return ONLY this JSON object, nothing else: {"status": "ok", "provider": "groq"}'
    print(call_llm_json(test_prompt))