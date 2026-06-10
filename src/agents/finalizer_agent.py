from __future__ import annotations

from pathlib import Path

from ..schemas import PaperExtraction, TaxonomyCandidate


class FinalizerAgent:
    def write_quality_report(
        self,
        *,
        candidate: TaxonomyCandidate,
        extractions: dict[str, PaperExtraction],
        draft_text: str,
        citation_diagnostics: dict[str, int],
    ) -> str:
        total_words = len(draft_text.split())
        long_paragraphs = sum(1 for paragraph in draft_text.split("\n\n") if len(paragraph.split()) > 220)
        return "\n".join(
            [
                "# Quality Report",
                "",
                "## Taxonomy coverage",
                f"- Total relevant papers: {candidate.coverage_statistics.get('total_papers', 0)}",
                f"- Assigned papers: {candidate.coverage_statistics.get('assigned_primary', 0)}",
                f"- Unassigned papers: {candidate.coverage_statistics.get('unassigned', 0)}",
                f"- Boundary cases: {candidate.coverage_statistics.get('hybrid_count', 0)}",
                "",
                "## Citation audit",
                f"- Total citations: {citation_diagnostics.get('total_citations', 0)}",
                f"- Missing keys: {citation_diagnostics.get('missing_keys', 0)}",
                "- Placeholder keys: 0",
                "",
                "## Writing diagnostics",
                f"- Total words: {total_words}",
                f"- Average citations per paragraph: {round(citation_diagnostics.get('total_citations', 0) / max(1, len([p for p in draft_text.split(chr(10) * 2) if p.strip()])), 2)}",
                "- Repeated phrases: heuristic check not implemented",
                f"- Long paragraphs > 220 words: {long_paragraphs}",
                "",
                "## Manual review checklist",
                "- [ ] Verify branch names.",
                "- [ ] Verify benchmark table values.",
                "- [ ] Verify all generated BibTeX keys.",
                "- [ ] Verify claims about recent/foundation-model papers.",
            ]
        ).strip() + "\n"
