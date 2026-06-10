from __future__ import annotations

from pathlib import Path

from ..io.pdf_reader import compute_file_hash, extract_pdf_text, list_pdfs, persist_text_artifacts
from ..schemas import PaperRecord
from ..utils import ensure_dir, read_json, slugify, write_json


class IngestionAgent:
    def run(self, *, literature_dir: Path, output_dir: Path) -> list[PaperRecord]:
        pdfs = list_pdfs(literature_dir)
        if not pdfs:
            raise FileNotFoundError(f"No PDFs found in {literature_dir}")
        text_dir = ensure_dir(output_dir / "text")
        manifest_path = text_dir / "manifest.json"
        manifest = read_json(manifest_path) if manifest_path.exists() else {}
        records: list[PaperRecord] = []
        updated_manifest: dict[str, dict[str, str]] = {}
        for path in pdfs:
            paper_id = slugify(path.stem)
            file_hash = compute_file_hash(path)
            text_path = text_dir / f"{paper_id}.txt"
            page_map_path = text_dir / f"{paper_id}.pages.json"
            cached = manifest.get(paper_id, {})
            if (
                cached.get("file_hash") == file_hash
                and text_path.exists()
                and page_map_path.exists()
            ):
                updated_manifest[paper_id] = {
                    "filename": path.name,
                    "file_hash": file_hash,
                    "text_path": str(text_path),
                    "page_map_path": str(page_map_path),
                }
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
                continue
            text, pages = extract_pdf_text(path)
            text_path, page_map_path = persist_text_artifacts(out_dir=output_dir, paper_id=paper_id, text=text, pages=pages)
            updated_manifest[paper_id] = {
                "filename": path.name,
                "file_hash": file_hash,
                "text_path": str(text_path),
                "page_map_path": str(page_map_path),
            }
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
        write_json(manifest_path, updated_manifest)
        return records
