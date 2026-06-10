from __future__ import annotations

import re
from pathlib import Path

from ..schemas import PaperExtraction


class CitationGuardAgent:
    def audit_tex(self, *, tex_text: str, extractions: dict[str, PaperExtraction]) -> tuple[str, dict[str, int]]:
        cite_keys = []
        for match in re.finditer(r"\\cite\{([^}]+)\}", tex_text):
            cite_keys.extend([key.strip() for key in match.group(1).split(",") if key.strip()])
        available_keys = {extraction.bibtex_key or extraction.paper_id for extraction in extractions.values()}
        missing = sorted(key for key in cite_keys if key not in available_keys)
        paragraphs = [paragraph.strip() for paragraph in tex_text.split("\n\n") if paragraph.strip()]
        uncited_paragraphs = sum(1 for paragraph in paragraphs if "\\cite{" not in paragraph and paragraph.startswith("\\paragraph") is False)
        lines = [
            "# Citation Audit",
            "",
            "## Summary",
            f"- Total citations: {len(cite_keys)}",
            f"- Missing keys: {len(missing)}",
            f"- Placeholder keys: {sum(1 for key in cite_keys if key.startswith('placeholder'))}",
            f"- Paragraphs without citation: {uncited_paragraphs}",
            "",
            "## Issues",
        ]
        if missing:
            for key in missing:
                lines.append(f"- Critical: missing BibTeX/evidence key `{key}`.")
        else:
            lines.append("- No missing citation keys detected against available extraction outputs.")
        diagnostics = {
            "total_citations": len(cite_keys),
            "missing_keys": len(missing),
            "uncited_paragraphs": uncited_paragraphs,
        }
        return "\n".join(lines).strip() + "\n", diagnostics
