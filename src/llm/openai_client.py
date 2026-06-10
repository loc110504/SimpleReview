from __future__ import annotations

import os
from typing import Any


class OpenAIClient:
    name = "openai"

    def __init__(self) -> None:
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise RuntimeError("OPENAI_API_KEY is not configured.")
        try:
            from openai import OpenAI
        except ImportError as exc:
            raise RuntimeError("openai package is not installed.") from exc
        self._client = OpenAI(api_key=api_key)

    def generate_text(self, prompt: str, *, model: str, temperature: float = 0.2) -> str:
        response = self._client.responses.create(model=model, input=prompt, temperature=temperature)
        return getattr(response, "output_text", "")

    def generate_json(
        self,
        prompt: str,
        schema: dict[str, Any],
        *,
        model: str,
        temperature: float = 0.0,
    ) -> dict[str, Any]:
        response = self._client.responses.create(
            model=model,
            input=prompt,
            temperature=temperature,
            text={
                "format": {
                    "type": "json_schema",
                    "name": schema.get("title", "structured_output"),
                    "schema": schema,
                    "strict": True,
                }
            },
        )
        text = getattr(response, "output_text", "{}")
        import json

        return json.loads(text)
