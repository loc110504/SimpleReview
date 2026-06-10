from __future__ import annotations

from pathlib import Path
from typing import Any


def load_bibtex_entries(path: Path | None) -> list[dict[str, Any]]:
    if path is None or not path.exists():
        return []
    try:
        import bibtexparser
    except ImportError:
        return []

    with path.open("r", encoding="utf-8") as handle:
        bib_db = bibtexparser.load(handle)
    return list(bib_db.entries)


def build_bib_lookup(entries: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    lookup: dict[str, dict[str, Any]] = {}
    for entry in entries:
        key = entry.get("ID")
        if key:
            lookup[key] = entry
    return lookup
