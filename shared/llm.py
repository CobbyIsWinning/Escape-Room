"""Simple optional Google Gemini adapter using the free-tier-capable API.

Requires GEMINI_API_KEY in environment or Streamlit secrets. Internet access
and a Gemini account with available free quota are required for live calls.
"""
import os


def api_key():
    key = os.getenv('GEMINI_API_KEY', '').strip()
    if key:
        return key
    try:
        import streamlit as st
        return str(st.secrets.get('GEMINI_API_KEY', '')).strip()
    except Exception:
        return ''


def generate(system_instruction: str, messages: list[dict], *, temperature: float = 0.5,
             response_schema=None):
    key = api_key()
    if not key:
        return None
    from google import genai
    from google.genai import types

    client = genai.Client(api_key=key, http_options=types.HttpOptions(
        timeout=20000, retry_options=types.HttpRetryOptions(attempts=1),
    ))
    contents = [types.Content(role=('model' if m['role'] == 'assistant' else 'user'),
                              parts=[types.Part.from_text(text=m['content'])])
                for m in messages]
    model = os.getenv('GEMINI_MODEL', 'gemini-3.8-flash')
    # Short wizard dialogue needs room for both reasoning and the spoken reply.
    thinking = types.ThinkingConfig(thinking_level=types.ThinkingLevel.LOW) if model.startswith('gemini-3') else None
    response = client.models.generate_content(
        model=model,
        contents=contents,
        config=types.GenerateContentConfig(
            system_instruction=system_instruction,
            temperature=temperature,
            max_output_tokens=1024,
            thinking_config=thinking,
            response_mime_type='application/json' if response_schema else None,
            response_json_schema=response_schema,
        ),
    )
    return (response.text or '').strip() or None
