from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Protocol


class LLMProvider(Protocol):
    def generate_text(self, prompt: str, *, model: str, temperature: float = 0.2) -> str: ...

    def generate_json(
        self,
        prompt: str,
        schema: dict[str, Any],
        *,
        model: str,
        temperature: float = 0.0,
    ) -> dict[str, Any]: ...


@dataclass(slots=True)
class LoggedResponse:
    payload: dict[str, Any]
    provider: str
    model: str
    cache_hit: bool = False
