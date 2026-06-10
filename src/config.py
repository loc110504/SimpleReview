from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

try:
    from dotenv import load_dotenv
except ImportError:  # pragma: no cover - fallback for environments without python-dotenv
    def load_dotenv(_path: Path) -> bool:
        return False


@dataclass(slots=True)
class RuntimeConfig:
    root_dir: Path
    cache_dir: Path
    output_dir: Path
    max_paper_chunk_tokens: int
    max_repair_retries: int
    enable_web_search: bool
    enable_grobid: bool
    models: dict[str, Any]
    taxonomy_seed: dict[str, Any]
    writing_style: dict[str, Any]


def _load_yaml(path: Path) -> dict[str, Any]:
    if not path.exists():
        raise FileNotFoundError(f"Missing config file: {path}")
    with path.open("r", encoding="utf-8") as handle:
        return yaml.safe_load(handle) or {}


def _as_bool(value: str | None, default: bool = False) -> bool:
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def load_runtime_config(
    *,
    root_dir: Path,
    output_dir: Path | None = None,
    models_path: Path | None = None,
    taxonomy_seed_path: Path | None = None,
    writing_style_path: Path | None = None,
) -> RuntimeConfig:
    load_dotenv(root_dir / ".env")
    models_path = models_path or root_dir / "configs" / "models.yaml"
    taxonomy_seed_path = taxonomy_seed_path or root_dir / "configs" / "taxonomy_seed.yaml"
    writing_style_path = writing_style_path or root_dir / "configs" / "writing_style.yaml"
    models = _load_yaml(models_path)
    taxonomy_seed = _load_yaml(taxonomy_seed_path)
    writing_style = _load_yaml(writing_style_path)
    cache_dir = root_dir / os.getenv("CACHE_DIR", ".cache")
    resolved_output_dir = output_dir or root_dir / os.getenv("OUTPUT_DIR", "outputs")
    return RuntimeConfig(
        root_dir=root_dir,
        cache_dir=cache_dir,
        output_dir=resolved_output_dir,
        max_paper_chunk_tokens=int(os.getenv("MAX_PAPER_CHUNK_TOKENS", "12000")),
        max_repair_retries=int(os.getenv("MAX_REPAIR_RETRIES", "2")),
        enable_web_search=_as_bool(os.getenv("ENABLE_WEB_SEARCH"), default=False),
        enable_grobid=_as_bool(os.getenv("ENABLE_GROBID"), default=False),
        models=models,
        taxonomy_seed=taxonomy_seed,
        writing_style=writing_style,
    )
