from __future__ import annotations

import json
import os
from typing import Any


class GeminiClient:
    name = "gemini"

    def __init__(self) -> None:
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise RuntimeError("GEMINI_API_KEY is not configured.")
        try:
            from google import genai
            from google.genai import types
        except ImportError as exc:
            raise RuntimeError("google-genai package is not installed.") from exc
        self._client = genai.Client(api_key=api_key)
        self._types = types

    def generate_text(self, prompt: str, *, model: str, temperature: float = 0.2) -> str:
        response = self._client.models.generate_content(
            model=model,
            contents=prompt,
            config=self._types.GenerateContentConfig(temperature=temperature),
        )
        return response.text or ""

    def generate_json(
        self,
        prompt: str,
        schema: dict[str, Any],
        *,
        model: str,
        temperature: float = 0.0,
    ) -> dict[str, Any]:
        response = self._client.models.generate_content(
            model=model,
            contents=prompt,
            config=self._types.GenerateContentConfig(
                response_mime_type="application/json",
                response_schema=schema,
                temperature=temperature,
            ),
        )
        return json.loads(response.text or "{}")
