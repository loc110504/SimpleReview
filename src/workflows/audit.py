from __future__ import annotations

from pathlib import Path

from ..agents.citation_guard_agent import CitationGuardAgent
from ..schemas import PaperExtraction
from ..utils import read_json


def run_audit(*, tex_path: Path, papers_dir: Path) -> tuple[str, dict[str, int]]:
    extractions: dict[str, PaperExtraction] = {}
    for path in sorted(papers_dir.glob("*.extraction.json")):
        extraction = PaperExtraction.model_validate(read_json(path))
        extractions[extraction.paper_id] = extraction
    tex_text = tex_path.read_text(encoding="utf-8")
    return CitationGuardAgent().audit_tex(tex_text=tex_text, extractions=extractions)
