from __future__ import annotations

import json
import os
from typing import Any
from urllib import error, request


class OllamaClient:
    name = "ollama"

    def __init__(self, *, base_url: str | None = None) -> None:
        self.base_url = (base_url or os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")).rstrip("/")

    def generate_text(self, prompt: str, *, model: str, temperature: float = 0.2) -> str:
        payload = {
            "model": model,
            "messages": [{"role": "user", "content": prompt}],
            "stream": False,
            "options": {"temperature": temperature},
        }
        response = self._post_json("/api/chat", payload)
        return str(response.get("message", {}).get("content", ""))

    def generate_json(
        self,
        prompt: str,
        schema: dict[str, Any],
        *,
        model: str,
        temperature: float = 0.0,
    ) -> dict[str, Any]:
        payload = {
            "model": model,
            "messages": [
                {
                    "role": "user",
                    "content": prompt + "\n\nReturn the answer as JSON that matches the provided schema.",
                }
            ],
            "stream": False,
            "format": schema,
            "options": {"temperature": temperature},
        }
        response = self._post_json("/api/chat", payload)
        content = str(response.get("message", {}).get("content", "")).strip()
        if not content:
            return {}
        return json.loads(content)

    def _post_json(self, path: str, payload: dict[str, Any]) -> dict[str, Any]:
        raw = json.dumps(payload).encode("utf-8")
        req = request.Request(
            url=f"{self.base_url}{path}",
            data=raw,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        try:
            with request.urlopen(req, timeout=120) as response:
                return json.loads(response.read().decode("utf-8"))
        except error.URLError as exc:
            raise RuntimeError(f"Failed to reach Ollama at {self.base_url}: {exc}") from exc
