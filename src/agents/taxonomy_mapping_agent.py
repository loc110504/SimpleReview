from __future__ import annotations

from collections import defaultdict
from pathlib import Path

from ..schemas import PaperExtraction, TaxonomyCandidate


class TaxonomyMappingAgent:
    def write_mapping_report(
        self,
        *,
        candidates: list[TaxonomyCandidate],
        extractions: dict[str, PaperExtraction],
        out_dir: Path,
    ) -> tuple[Path, Path]:
        out_dir.mkdir(parents=True, exist_ok=True)
        mapping_path = out_dir / "paper_to_candidate_mapping.md"
        conflicts_path = out_dir / "taxonomy_conflicts.md"
        mapping_lines = ["# Paper-to-candidate mapping", ""]
        conflict_lines = ["# Taxonomy conflicts", ""]
        boundary_cases = defaultdict(list)
        for candidate in candidates:
            mapping_lines.append(f"## Candidate {candidate.candidate_id}: {candidate.title}")
            mapping_lines.append("")
            for branch in candidate.branches:
                mapping_lines.append(f"### {branch.name}")
                for paper_id in branch.all_assigned_primary:
                    extraction = extractions[paper_id]
                    mapping_lines.append(f"- `{paper_id}`: {extraction.title}")
                    if extraction.boundary_case_notes:
                        boundary_cases[candidate.candidate_id].append((paper_id, extraction.boundary_case_notes))
                mapping_lines.append("")
        for candidate_id, items in boundary_cases.items():
            conflict_lines.append(f"## Candidate {candidate_id}")
            for paper_id, notes in items:
                conflict_lines.append(f"- `{paper_id}`: {' '.join(notes)}")
            conflict_lines.append("")
        if len(conflict_lines) == 2:
            conflict_lines.append("No boundary cases were detected by the heuristic verifier.")
        mapping_path.write_text("\n".join(mapping_lines).strip() + "\n", encoding="utf-8")
        conflicts_path.write_text("\n".join(conflict_lines).strip() + "\n", encoding="utf-8")
        return mapping_path, conflicts_path
