from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path
from typing import Any


def compute_file_hash(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def list_pdfs(literature_dir: Path) -> list[Path]:
    return sorted(path for path in literature_dir.glob("*.pdf") if path.is_file())


def normalize_text(text: str) -> str:
    text = text.replace("\x00", " ")
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def extract_pdf_text(path: Path) -> tuple[str, list[dict[str, Any]]]:
    try:
        import fitz
    except ImportError as exc:
        raise RuntimeError("PyMuPDF is required to extract PDF text.") from exc

    doc = fitz.open(path)
    pages: list[dict[str, Any]] = []
    page_texts: list[str] = []
    for index, page in enumerate(doc):
        text = normalize_text(page.get_text("text"))
        page_texts.append(text)
        pages.append({"page": index + 1, "text": text})
    return "\n\n".join(page_texts), pages


def persist_text_artifacts(*, out_dir: Path, paper_id: str, text: str, pages: list[dict[str, Any]]) -> tuple[Path, Path]:
    text_dir = out_dir / "text"
    text_dir.mkdir(parents=True, exist_ok=True)
    text_path = text_dir / f"{paper_id}.txt"
    page_map_path = text_dir / f"{paper_id}.pages.json"
    text_path.write_text(text, encoding="utf-8")
    page_map_path.write_text(json.dumps(pages, indent=2, ensure_ascii=False), encoding="utf-8")
    return text_path, page_map_path
