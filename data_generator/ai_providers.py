"""
Pluggable LLM backends for AI-assisted schema generation (text in → text out).

Each provider is responsible for API keys and SDK imports; callers parse and validate YAML/JSON.
"""

from __future__ import annotations

import os
from typing import Any, Protocol, runtime_checkable


class ProviderError(Exception):
    """Missing dependency, API key, or provider-specific failure."""


@runtime_checkable
class AIProvider(Protocol):
    """Minimal contract: return raw model text (YAML or JSON schema only)."""

    def generate_text(self, system_prompt: str, user_prompt: str) -> str:
        ...


def _import_genai() -> Any:
    try:
        import google.generativeai as genai  # type: ignore[import-untyped]
    except ImportError as exc:
        raise ProviderError(
            "Gemini provider requires google-generativeai. "
            "Install AI extras: pip install -r requirements-ai.txt"
        ) from exc
    return genai


def _import_openai_client() -> Any:
    try:
        from openai import OpenAI
    except ImportError as exc:
        raise ProviderError(
            "OpenAI provider requires the openai package. "
            "Install AI extras: pip install -r requirements-ai.txt"
        ) from exc
    return OpenAI


class GeminiProvider:
    """Google Gemini text generation; uses ``GEMINI_API_KEY``."""

    DEFAULT_MODEL = "gemini-2.0-flash"

    def __init__(self, model: str | None = None) -> None:
        genai = _import_genai()
        key = (os.environ.get("GEMINI_API_KEY") or "").strip()
        if not key:
            raise ProviderError(
                "GEMINI_API_KEY is not set. Add it to your .env or environment (see .env.example)."
            )
        genai.configure(api_key=key)
        self._genai = genai
        self._model_name = (model or os.environ.get("GEMINI_MODEL") or self.DEFAULT_MODEL).strip()

    def generate_text(self, system_prompt: str, user_prompt: str) -> str:
        up = user_prompt.strip()
        try:
            try:
                model = self._genai.GenerativeModel(
                    self._model_name,
                    system_instruction=system_prompt,
                )
                response = model.generate_content(up, generation_config={"temperature": 0.2})
            except TypeError:
                model = self._genai.GenerativeModel(self._model_name)
                combined = f"{system_prompt}\n\nUser request:\n{up}"
                response = model.generate_content(combined, generation_config={"temperature": 0.2})
        except Exception as exc:
            raise ProviderError(f"Gemini API request failed: {exc}") from exc
        text = _extract_gemini_text(response)
        if not text.strip():
            raise ProviderError("Gemini returned no usable text content.")
        return text


def _extract_gemini_text(response: Any) -> str:
    t = getattr(response, "text", None)
    if t and str(t).strip():
        return str(t)
    try:
        parts = response.candidates[0].content.parts
        return "".join(getattr(p, "text", "") for p in parts)
    except (AttributeError, IndexError, TypeError):
        return ""


class OpenAIProvider:
    """OpenAI Chat Completions; uses ``OPENAI_API_KEY``."""

    DEFAULT_MODEL = "gpt-4o-mini"

    def __init__(self, model: str | None = None) -> None:
        OpenAI = _import_openai_client()
        key = (os.environ.get("OPENAI_API_KEY") or "").strip()
        if not key:
            raise ProviderError(
                "OPENAI_API_KEY is not set. Add it to your .env or environment (see .env.example)."
            )
        self._client = OpenAI(api_key=key)
        self._model = (model or os.environ.get("OPENAI_MODEL") or self.DEFAULT_MODEL).strip()

    def generate_text(self, system_prompt: str, user_prompt: str) -> str:
        try:
            response = self._client.chat.completions.create(
                model=self._model,
                temperature=0.2,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt.strip()},
                ],
            )
        except Exception as exc:
            raise ProviderError(f"OpenAI API request failed: {exc}") from exc
        choice = response.choices[0] if response.choices else None
        content = getattr(getattr(choice, "message", None), "content", None)
        if content is None or not str(content).strip():
            raise ProviderError("OpenAI returned no usable text content.")
        return str(content)


def get_provider(name: str, model: str | None = None) -> AIProvider:
    """Return a configured provider instance. Raises ``ValueError`` for unknown ``name``."""
    key = (name or "").strip().lower()
    if key == "gemini":
        return GeminiProvider(model=model)
    if key == "openai":
        return OpenAIProvider(model=model)
    raise ValueError(f"Unsupported AI provider {name!r}. Use 'gemini' or 'openai'.")
