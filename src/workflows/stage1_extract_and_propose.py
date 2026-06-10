from __future__ import annotations

import csv
from pathlib import Path

from ..agents.benchmark_agent import BenchmarkExtractionAgent
from ..agents.evidence_verifier_agent import EvidenceVerifierAgent
from ..agents.ingestion_agent import IngestionAgent
from ..agents.metadata_agent import MetadataAgent
from ..agents.method_extraction_agent import MethodExtractionAgent
from ..agents.taxonomy_critic_agent import TaxonomyCriticAgent
from ..agents.taxonomy_mapping_agent import TaxonomyMappingAgent
from ..agents.taxonomy_proposer_agent import TaxonomyProposerAgent
from ..agents.taxonomy_signal_agent import TaxonomySignalAgent
from ..config import RuntimeConfig
from ..llm.router import ModelRouter
from ..schemas import PaperExtraction, WorkflowState
from ..utils import ensure_dir, read_json, write_json


class Stage1Workflow:
    def __init__(self, config: RuntimeConfig) -> None:
        self.config = config
        self.router = ModelRouter(
            cache_dir=config.cache_dir,
            routes=config.models.get("routes", {}),
            log_dir=config.output_dir / "logs" / "llm",
        )
        self.ingestion = IngestionAgent()
        self.metadata_agent = MetadataAgent(config.root_dir / "literature")
        self.method_agent = MethodExtractionAgent(self.router)
        self.benchmark_agent = BenchmarkExtractionAgent()
        self.signal_agent = TaxonomySignalAgent()
        self.verifier = EvidenceVerifierAgent()
        self.proposer = TaxonomyProposerAgent(config.taxonomy_seed)
        self.critic = TaxonomyCriticAgent()
        self.mapper = TaxonomyMappingAgent()

    def run(self, state: WorkflowState, *, bib_lookup: dict[str, dict] | None = None) -> WorkflowState:
        bib_lookup = bib_lookup or {}
        outputs = state.output_dir
        paper_dir = ensure_dir(outputs / "papers")
        evidence_dir = ensure_dir(outputs / "evidence")
        taxonomy_dir = ensure_dir(outputs / "taxonomy")
        state.papers = self.ingestion.run(literature_dir=state.literature_dir, output_dir=outputs)
        failed_rows: list[dict[str, str]] = []
        for record in state.papers:
            text = record.text_path.read_text(encoding="utf-8") if record.text_path else ""
            metadata = self.metadata_agent.extract(filename=record.filename, text=text)
            bibtex_key = self._match_bibtex_key(metadata, bib_lookup) or record.paper_id
            extraction = self.method_agent.extract(
                paper_id=record.paper_id,
                filename=record.filename,
                text=text,
                metadata=metadata,
                bibtex_key=bibtex_key,
            )
            extraction = self.benchmark_agent.enrich(extraction)
            extraction = self.signal_agent.normalize(extraction)
            verification = self.verifier.verify(extraction)
            if verification.status == "needs_retry":
                failed_rows.append({"paper_id": record.paper_id, "filename": record.filename, "reason": "; ".join(verification.warnings)})
                continue
            state.extractions[record.paper_id] = extraction
            write_json(paper_dir / f"{record.paper_id}.extraction.json", extraction.model_dump(mode="json"))
        self._write_failed_csv(failed_rows, evidence_dir / "failed_papers.csv")
        evidence_matrix_path = evidence_dir / "evidence_matrix.csv"
        self._write_evidence_matrix(state.extractions, evidence_matrix_path)
        state.evidence_matrix_path = evidence_matrix_path
        candidates = self.proposer.propose(state.extractions)
        state.taxonomy_candidates = candidates
        best_id, scorecard = self.critic.critique(candidates)
        write_json(taxonomy_dir / "taxonomy_candidates.json", [candidate.model_dump(mode="json") for candidate in candidates])
        (taxonomy_dir / "taxonomy_candidates.md").write_text(self._render_candidate_report(candidates, best_id, scorecard), encoding="utf-8")
        self.mapper.write_mapping_report(candidates=candidates, extractions=state.extractions, out_dir=taxonomy_dir)
        return state

    def _match_bibtex_key(self, metadata: dict[str, object], bib_lookup: dict[str, dict]) -> str | None:
        title = str(metadata.get("title") or "").lower()
        for key, entry in bib_lookup.items():
            entry_title = str(entry.get("title") or "").lower()
            if title and title in entry_title:
                return key
        return None

    def _write_failed_csv(self, rows: list[dict[str, str]], path: Path) -> None:
        with path.open("w", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=["paper_id", "filename", "reason"])
            writer.writeheader()
            writer.writerows(rows)

    def _write_evidence_matrix(self, extractions: dict[str, PaperExtraction], path: Path) -> None:
        rows = []
        for extraction in extractions.values():
            primary = next((signal.signal for signal in extraction.taxonomy_signals if signal.present and signal.strength == "primary"), "")
            secondary = [signal.signal for signal in extraction.taxonomy_signals if signal.present and signal.strength in {"secondary", "weak"}]
            rows.append(
                {
                    "paper_id": extraction.paper_id,
                    "filename": extraction.filename,
                    "bibtex_key": extraction.bibtex_key or "",
                    "title": extraction.title,
                    "year": extraction.year or "",
                    "venue": extraction.venue or "",
                    "method_name": extraction.method_name or "",
                    "annotation_setting": extraction.annotation_setting,
                    "manual_or_synthetic_scribble": extraction.scribble_protocol,
                    "modality": "|".join(extraction.modality),
                    "target": "|".join(extraction.segmentation_target),
                    "datasets": "|".join(dataset.dataset_name for dataset in extraction.datasets),
                    "metrics": "|".join(extraction.metrics),
                    "primary_signal": primary,
                    "secondary_signals": "|".join(secondary),
                    "architecture_tags": "|".join(extraction.method_components.architecture),
                    "loss_tags": "|".join(extraction.method_components.loss_terms),
                    "prior_tags": "|".join(signal.signal for signal in extraction.taxonomy_signals if signal.present and "prior" in signal.signal),
                    "confidence": extraction.extraction_confidence,
                    "branch_candidate_A": "",
                    "branch_candidate_B": "",
                    "branch_candidate_C": "",
                    "boundary_case": "yes" if extraction.boundary_case_notes else "no",
                    "notes": " | ".join(extraction.boundary_case_notes),
                }
            )
        fieldnames = [
            "paper_id",
            "filename",
            "bibtex_key",
            "title",
            "year",
            "venue",
            "method_name",
            "annotation_setting",
            "manual_or_synthetic_scribble",
            "modality",
            "target",
            "datasets",
            "metrics",
            "primary_signal",
            "secondary_signals",
            "architecture_tags",
            "loss_tags",
            "prior_tags",
            "confidence",
            "branch_candidate_A",
            "branch_candidate_B",
            "branch_candidate_C",
            "boundary_case",
            "notes",
        ]
        with path.open("w", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(rows)

    def _render_candidate_report(self, candidates, best_id: str, scorecard: dict[str, dict[str, int]]) -> str:
        lines = ["# Taxonomy Candidate Report", ""]
        for candidate in candidates:
            lines.append(f"## Candidate {candidate.candidate_id}: {candidate.title}")
            lines.append("")
            lines.append(candidate.rationale)
            lines.append("")
            lines.append("### Branches")
            for branch in candidate.branches:
                lines.append(f"- **{branch.name}**: {branch.definition}")
                lines.append(f"  Representative papers: {', '.join(branch.representative_papers) or 'none'}")
                lines.append(f"  Inclusion: {'; '.join(branch.inclusion_criteria)}")
                lines.append(f"  Exclusion: {'; '.join(branch.exclusion_criteria)}")
            lines.append("")
            lines.append("### Coverage")
            for key, value in candidate.coverage_statistics.items():
                lines.append(f"- {key}: {value}")
            lines.append("")
            lines.append("### Strengths")
            for item in candidate.strengths:
                lines.append(f"- {item}")
            lines.append("")
            lines.append("### Weaknesses")
            for item in candidate.weaknesses or ["No major weakness flagged by the heuristic critic."]:
                lines.append(f"- {item}")
            lines.append("")
            lines.append("### Scorecard")
            for metric, value in scorecard.get(candidate.candidate_id, {}).items():
                lines.append(f"- {metric}: {value}/5")
            lines.append("")
        lines.extend(
            [
                f"Recommended candidate by critic: **{best_id}**",
                "",
                "Please choose one option:",
                "[A] Mechanism-first taxonomy",
                "[B] Supervision-signal-first taxonomy",
                "[C] Chronological-evolution taxonomy",
                "[custom] Provide edits in configs/user_taxonomy_override.yaml",
            ]
        )
        return "\n".join(lines).strip() + "\n"
