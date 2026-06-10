from __future__ import annotations

import csv
from pathlib import Path

from .common import detect_title, parse_year_and_venue


class MetadataAgent:
    def __init__(self, literature_dir: Path) -> None:
        self._csv_lookup = self._load_selected_papers(literature_dir / "selected_paper.csv")

    def _load_selected_papers(self, path: Path) -> dict[int, dict[str, str]]:
        if not path.exists():
            return {}
        lookup: dict[int, dict[str, str]] = {}
        with path.open("r", encoding="utf-8-sig", newline="") as handle:
            reader = csv.reader(handle)
            for row in reader:
                if not row or not row[0].isdigit():
                    continue
                lookup[int(row[0])] = {
                    "year": row[1] if len(row) > 1 else "",
                    "title": row[2] if len(row) > 2 else "",
                    "venue": row[3] if len(row) > 3 else "",
                }
        return lookup

    def extract(self, *, filename: str, text: str) -> dict[str, object]:
        year, venue = parse_year_and_venue(filename)
        title = detect_title(text, filename)
        if venue is None and year is None:
            for entry in self._csv_lookup.values():
                candidate_title = (entry.get("title") or "").strip()
                if candidate_title and candidate_title.lower() in text[:5000].lower():
                    title = candidate_title
                    venue = entry.get("venue") or None
                    year = int(entry["year"]) if entry.get("year", "").isdigit() else None
                    break
        return {
            "title": title,
            "year": year,
            "venue": venue,
            "authors": [],
        }
