from __future__ import annotations

from pathlib import Path

from ..io.pdf_reader import compute_file_hash, extract_pdf_text, list_pdfs, persist_text_artifacts
from ..schemas import PaperRecord
from ..utils import ensure_dir, slugify


class IngestionAgent:
    def run(self, *, literature_dir: Path, output_dir: Path) -> list[PaperRecord]:
        pdfs = list_pdfs(literature_dir)
        if not pdfs:
            raise FileNotFoundError(f"No PDFs found in {literature_dir}")
        ensure_dir(output_dir / "text")
        records: list[PaperRecord] = []
        for path in pdfs:
            paper_id = slugify(path.stem)
            file_hash = compute_file_hash(path)
            text, pages = extract_pdf_text(path)
            text_path, page_map_path = persist_text_artifacts(out_dir=output_dir, paper_id=paper_id, text=text, pages=pages)
            records.append(
                PaperRecord(
                    paper_id=paper_id,
                    filename=path.name,
                    path=path,
                    file_hash=file_hash,
                    text_path=text_path,
                    page_map_path=page_map_path,
                    status="processed",
                )
            )
        return records
