from __future__ import annotations

import os
from pathlib import Path
from typing import Any

from ..io.cache import CacheStore
from ..utils import write_json
from .gemini_client import GeminiClient
from .mock_client import HeuristicLLMClient
from .ollama_client import OllamaClient
from .openai_client import OpenAIClient


class ModelRouter:
    def __init__(self, *, cache_dir: Path, routes: dict[str, Any], log_dir: Path) -> None:
        self.cache = CacheStore(cache_dir / "llm")
        self.routes = routes
        self.log_dir = log_dir
        self.log_dir.mkdir(parents=True, exist_ok=True)
        self._providers: dict[str, Any] = {"heuristic": HeuristicLLMClient()}

    def _provider(self, name: str) -> Any:
        if name in self._providers:
            return self._providers[name]
        if name == "openai":
            self._providers[name] = OpenAIClient()
            return self._providers[name]
        if name == "gemini":
            self._providers[name] = GeminiClient()
            return self._providers[name]
        if name == "ollama":
            self._providers[name] = OllamaClient()
            return self._providers[name]
        raise KeyError(f"Unsupported provider route: {name}")

    def resolve_route(self, task_name: str, slot: str = "primary") -> tuple[str, str]:
        route_value = self.routes.get(task_name, {}).get(slot, "heuristic")
        if route_value == "heuristic":
            return "heuristic", "heuristic"
        if "." not in route_value:
            return route_value, route_value
        provider_name, model_kind = route_value.split(".", 1)
        env_var = {
            ("openai", "extract"): "OPENAI_MODEL_EXTRACT",
            ("openai", "write"): "OPENAI_MODEL_WRITE",
            ("openai", "fast"): "OPENAI_MODEL_FAST",
            ("gemini", "extract"): "GEMINI_MODEL_EXTRACT",
            ("gemini", "fast"): "GEMINI_MODEL_FAST",
            ("ollama", "extract"): "OLLAMA_MODEL_EXTRACT",
            ("ollama", "write"): "OLLAMA_MODEL_WRITE",
            ("ollama", "fast"): "OLLAMA_MODEL_FAST",
        }.get((provider_name, model_kind))
        return provider_name, os.getenv(env_var or "", route_value)

    def generate_json(
        self,
        *,
        task_name: str,
        slot: str,
        prompt: str,
        schema: dict[str, Any],
        schema_version: str,
        input_hash: str,
    ) -> dict[str, Any]:
        provider_name, model = self.resolve_route(task_name, slot)
        cache_key = self.cache.key_for(
            {
                "provider": provider_name,
                "model": model,
                "schema_version": schema_version,
                "prompt": prompt,
                "input_hash": input_hash,
            }
        )
        cached = self.cache.load(cache_key)
        if cached is not None:
            return cached
        provider = self._provider(provider_name)
        payload = provider.generate_json(prompt, schema, model=model)
        self.cache.save(cache_key, payload)
        write_json(
            self.log_dir / f"{cache_key}.json",
            {
                "provider": provider_name,
                "model": model,
                "cache_hit": False,
                "task_name": task_name,
                "schema_version": schema_version,
            },
        )
        return payload

    def generate_text(
        self,
        *,
        task_name: str,
        slot: str,
        prompt: str,
        schema_version: str,
        input_hash: str,
    ) -> str:
        provider_name, model = self.resolve_route(task_name, slot)
        cache_key = self.cache.key_for(
            {
                "provider": provider_name,
                "model": model,
                "schema_version": schema_version,
                "prompt": prompt,
                "input_hash": input_hash,
            }
        )
        cached = self.cache.load(cache_key)
        if cached is not None:
            return str(cached.get("text", ""))
        provider = self._provider(provider_name)
        text = provider.generate_text(prompt, model=model)
        self.cache.save(cache_key, {"text": text})
        return text
