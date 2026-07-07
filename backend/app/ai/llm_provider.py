"""Centralized LLM provider with Gemini -> OpenRouter fallback.

If GEMINI_API_KEY is set, uses Google Gemini directly.
Otherwise falls back to OpenRouter (OpenAI-compatible API) using the same models.
"""

import base64
import os

from app.config import settings

OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"
OPENROUTER_TEXT_MODEL = "google/gemini-2.5-flash-preview-05-20"
OPENROUTER_VISION_MODEL = "google/gemini-2.0-flash-001"


def _has_gemini_key() -> bool:
    return bool(settings.gemini_api_key and len(settings.gemini_api_key) >= 10)


def _has_openrouter_key() -> bool:
    return bool(settings.openrouter_api_key and len(settings.openrouter_api_key) >= 10)


def get_llm(temperature: float = 0.3):
    """Return a LangChain chat model — Gemini if available, else OpenRouter."""
    if _has_gemini_key():
        from langchain_google_genai import ChatGoogleGenerativeAI

        return ChatGoogleGenerativeAI(
            model="gemini-2.5-flash",
            google_api_key=settings.gemini_api_key,
            temperature=temperature,
        )

    if _has_openrouter_key():
        from langchain_openai import ChatOpenAI

        return ChatOpenAI(
            model=OPENROUTER_TEXT_MODEL,
            openai_api_key=settings.openrouter_api_key,
            openai_api_base=OPENROUTER_BASE_URL,
            temperature=temperature,
            default_headers={
                "HTTP-Referer": "https://crimegpt.app",
                "X-Title": "CrimeGPT",
            },
        )

    raise RuntimeError(
        "No LLM API key configured. Set either GEMINI_API_KEY or OPENROUTER_API_KEY in .env"
    )


def generate_text(prompt: str, temperature: float = 0.3, max_tokens: int = 2048) -> str:
    """Generate text from a prompt string. Returns the response text."""
    if _has_gemini_key():
        import google.generativeai as genai

        genai.configure(api_key=settings.gemini_api_key)
        model = genai.GenerativeModel("gemini-2.0-flash")
        response = model.generate_content(
            prompt,
            generation_config=genai.types.GenerationConfig(
                temperature=temperature, max_output_tokens=max_tokens
            ),
        )
        return response.text

    if _has_openrouter_key():
        from openai import OpenAI

        client = OpenAI(
            api_key=settings.openrouter_api_key,
            base_url=OPENROUTER_BASE_URL,
        )
        response = client.chat.completions.create(
            model=OPENROUTER_TEXT_MODEL,
            messages=[{"role": "user", "content": prompt}],
            temperature=temperature,
            max_tokens=max_tokens,
            extra_headers={
                "HTTP-Referer": "https://crimegpt.app",
                "X-Title": "CrimeGPT",
            },
        )
        return response.choices[0].message.content

    raise RuntimeError(
        "No LLM API key configured. Set either GEMINI_API_KEY or OPENROUTER_API_KEY in .env"
    )


def generate_vision(image_path: str, prompt: str, temperature: float = 0.1, max_tokens: int = 500) -> str:
    """Analyze an image with a prompt. Returns the response text."""
    if _has_gemini_key():
        import google.generativeai as genai
        from PIL import Image

        genai.configure(api_key=settings.gemini_api_key)
        model = genai.GenerativeModel("gemini-2.0-flash")
        img = Image.open(image_path)
        response = model.generate_content(
            [img, prompt],
            generation_config=genai.types.GenerationConfig(
                temperature=temperature, max_output_tokens=max_tokens
            ),
        )
        img.close()
        return response.text

    if _has_openrouter_key():
        from openai import OpenAI

        ext = os.path.splitext(image_path)[1].lower()
        mime_map = {
            ".jpg": "image/jpeg", ".jpeg": "image/jpeg",
            ".png": "image/png", ".gif": "image/gif",
            ".webp": "image/webp", ".bmp": "image/bmp",
        }
        mime_type = mime_map.get(ext, "image/jpeg")

        with open(image_path, "rb") as f:
            image_b64 = base64.b64encode(f.read()).decode("utf-8")

        client = OpenAI(
            api_key=settings.openrouter_api_key,
            base_url=OPENROUTER_BASE_URL,
        )
        response = client.chat.completions.create(
            model=OPENROUTER_VISION_MODEL,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"type": "image_url", "image_url": {"url": f"data:{mime_type};base64,{image_b64}"}},
                        {"type": "text", "text": prompt},
                    ],
                }
            ],
            temperature=temperature,
            max_tokens=max_tokens,
            extra_headers={
                "HTTP-Referer": "https://crimegpt.app",
                "X-Title": "CrimeGPT",
            },
        )
        return response.choices[0].message.content

    raise RuntimeError(
        "No LLM API key configured. Set either GEMINI_API_KEY or OPENROUTER_API_KEY in .env"
    )


def generate_vision_base64(image_b64: str, mime_type: str, prompt: str, temperature: float = 0.1, max_tokens: int = 2048) -> str:
    """Analyze a base64-encoded image with a prompt. Returns the response text."""
    if _has_gemini_key():
        import google.generativeai as genai

        genai.configure(api_key=settings.gemini_api_key)
        model = genai.GenerativeModel("gemini-2.0-flash")
        response = model.generate_content(
            [
                {"mime_type": mime_type, "data": image_b64},
                prompt,
            ],
            generation_config=genai.types.GenerationConfig(
                temperature=temperature, max_output_tokens=max_tokens
            ),
        )
        return response.text

    if _has_openrouter_key():
        from openai import OpenAI

        client = OpenAI(
            api_key=settings.openrouter_api_key,
            base_url=OPENROUTER_BASE_URL,
        )
        response = client.chat.completions.create(
            model=OPENROUTER_VISION_MODEL,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"type": "image_url", "image_url": {"url": f"data:{mime_type};base64,{image_b64}"}},
                        {"type": "text", "text": prompt},
                    ],
                }
            ],
            temperature=temperature,
            max_tokens=max_tokens,
            extra_headers={
                "HTTP-Referer": "https://crimegpt.app",
                "X-Title": "CrimeGPT",
            },
        )
        return response.choices[0].message.content

    raise RuntimeError(
        "No LLM API key configured. Set either GEMINI_API_KEY or OPENROUTER_API_KEY in .env"
    )


def has_any_llm_key() -> bool:
    """Check if any LLM API key is configured."""
    return _has_gemini_key() or _has_openrouter_key()
