from __future__ import annotations

from typing import Any


class HeuristicLLMClient:
    name = "heuristic"

    def generate_text(self, prompt: str, *, model: str, temperature: float = 0.2) -> str:
        return prompt

    def generate_json(
        self,
        prompt: str,
        schema: dict[str, Any],
        *,
        model: str,
        temperature: float = 0.0,
    ) -> dict[str, Any]:
        return {"prompt": prompt, "schema_title": schema.get("title", "unknown")}
