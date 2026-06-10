from __future__ import annotations

from pathlib import Path

from ..agents.citation_guard_agent import CitationGuardAgent
from ..agents.draft_writer_agent import DraftWriterAgent, WritingPlanAgent
from ..agents.finalizer_agent import FinalizerAgent
from ..agents.refinement_agent import RefinementAgent
from ..agents.synthesis_agent import AppendixWriterAgent, BenchmarkWriterAgent, FigureWriterAgent
from ..config import RuntimeConfig
from ..llm.router import ModelRouter
from ..schemas import PaperExtraction, TaxonomyCandidate, WorkflowState
from ..utils import ensure_dir, read_json, write_json


class Stage2Workflow:
    def __init__(self, config: RuntimeConfig) -> None:
        self.config = config
        self.router = ModelRouter(
            cache_dir=config.cache_dir,
            routes=config.models.get("routes", {}),
            log_dir=config.output_dir / "logs" / "llm",
        )
        self.plan_agent = WritingPlanAgent()
        self.draft_agent = DraftWriterAgent(self.router)
        self.benchmark_agent = BenchmarkWriterAgent()
        self.figure_agent = FigureWriterAgent()
        self.appendix_agent = AppendixWriterAgent()
        self.citation_guard = CitationGuardAgent()
        self.refiner = RefinementAgent()
        self.finalizer = FinalizerAgent()

    def run(self, state: WorkflowState, *, candidate_id: str, target_word_count: int) -> WorkflowState:
        candidate = self._select_candidate(state.taxonomy_candidates, candidate_id)
        state.selected_taxonomy_id = candidate.candidate_id
        drafts_dir = ensure_dir(state.output_dir / "drafts")
        final_dir = ensure_dir(state.output_dir / "final")
        state.writing_plan = self.plan_agent.build(candidate=candidate, extractions=state.extractions, target_word_count=target_word_count)
        write_json(drafts_dir / "writing_plan.json", state.writing_plan.model_dump(mode="json"))
        draft_text = self.draft_agent.write(candidate=candidate, plan=state.writing_plan, extractions=state.extractions)
        benchmark_section, benchmark_tables = self.benchmark_agent.write(extractions=state.extractions)
        draft_text = draft_text.rstrip() + "\n\n" + benchmark_section + "\n"
        appendix_text = self.appendix_agent.write_grouping_appendix(candidate, state.extractions)
        notes_text = self._write_notes(candidate, state.extractions)
        draft_path = drafts_dir / "taxonomy_draft_v1.tex"
        notes_path = drafts_dir / "taxonomy_draft_v1_notes.md"
        tables_path = drafts_dir / "taxonomy_tables.tex"
        benchmark_path = drafts_dir / "benchmark_datasets.tex"
        figure_path = drafts_dir / "taxonomy_figure_mermaid.md"
        appendix_path = drafts_dir / "paper_grouping_appendix.tex"
        draft_path.write_text(draft_text, encoding="utf-8")
        notes_path.write_text(notes_text, encoding="utf-8")
        tables_path.write_text(benchmark_tables, encoding="utf-8")
        benchmark_path.write_text(benchmark_section + "\n\n" + benchmark_tables, encoding="utf-8")
        figure_path.write_text(self.figure_agent.write_mermaid(candidate), encoding="utf-8")
        appendix_path.write_text(appendix_text, encoding="utf-8")
        audit_text, diagnostics = self.citation_guard.audit_tex(tex_text=draft_text + "\n\n" + benchmark_tables, extractions=state.extractions)
        audit_path = final_dir / "citation_audit.md"
        audit_path.write_text(audit_text, encoding="utf-8")
        refined = self.refiner.refine(draft_text)
        refined_path = drafts_dir / "taxonomy_draft_v2_refined.tex"
        refined_path.write_text(refined, encoding="utf-8")
        final_text = refined + "\n" + benchmark_tables + "\n" + appendix_text
        final_path = final_dir / "taxonomy_final.tex"
        final_tables_path = final_dir / "taxonomy_tables.tex"
        final_benchmark_path = final_dir / "benchmark_datasets.tex"
        quality_path = final_dir / "quality_report.md"
        final_path.write_text(final_text, encoding="utf-8")
        final_tables_path.write_text(benchmark_tables, encoding="utf-8")
        final_benchmark_path.write_text(benchmark_section + "\n\n" + benchmark_tables, encoding="utf-8")
        quality_path.write_text(
            self.finalizer.write_quality_report(
                candidate=candidate,
                extractions=state.extractions,
                draft_text=final_text,
                citation_diagnostics=diagnostics,
            ),
            encoding="utf-8",
        )
        state.drafts.update(
            {
                "draft_v1": draft_path,
                "draft_v2_refined": refined_path,
                "taxonomy_tables": tables_path,
                "benchmark_datasets": benchmark_path,
                "appendix": appendix_path,
            }
        )
        state.audits.update({"citation_audit": audit_path, "quality_report": quality_path})
        return state

    def _select_candidate(self, candidates: list[TaxonomyCandidate], candidate_id: str) -> TaxonomyCandidate:
        for candidate in candidates:
            if candidate.candidate_id == candidate_id:
                return candidate
        raise ValueError(f"Selected candidate missing: {candidate_id}")

    def _write_notes(self, candidate: TaxonomyCandidate, extractions: dict[str, PaperExtraction]) -> str:
        lines = ["# Draft Notes", "", f"Selected taxonomy: {candidate.candidate_id} - {candidate.title}", "", "## Papers per branch"]
        for branch in candidate.branches:
            lines.append(f"- {branch.name}: {len(branch.all_assigned_primary)}")
        lines.extend(["", "## Weak evidence areas"])
        weak = [paper_id for paper_id, extraction in extractions.items() if extraction.extraction_confidence < 0.7]
        if weak:
            for paper_id in weak:
                lines.append(f"- {paper_id}: extraction confidence below 0.7")
        else:
            lines.append("- No low-confidence extraction flagged by the heuristic pipeline.")
        lines.extend(
            [
                "",
                "## Missing citation keys",
                "- Check generated fallback keys that equal `paper_id`.",
                "",
                "## Recommended manual checks",
                "- Inspect all boundary cases in outputs/taxonomy/taxonomy_conflicts.md.",
                "- Verify benchmark table values and scribble protocols.",
                "- Verify recent foundation-model claims manually.",
            ]
        )
        return "\n".join(lines).strip() + "\n"


def load_stage_state(*, output_dir: Path, literature_dir: Path) -> WorkflowState:
    state = WorkflowState(run_id="resume", literature_dir=literature_dir, output_dir=output_dir)
    papers_dir = output_dir / "papers"
    taxonomy_path = output_dir / "taxonomy" / "taxonomy_candidates.json"
    if not papers_dir.exists():
        raise FileNotFoundError("outputs/papers is missing; run stage1 first.")
    for path in sorted(papers_dir.glob("*.extraction.json")):
        extraction = PaperExtraction.model_validate(read_json(path))
        state.extractions[extraction.paper_id] = extraction
    if not taxonomy_path.exists():
        raise FileNotFoundError("outputs/taxonomy/taxonomy_candidates.json is missing; run stage1 first.")
    state.taxonomy_candidates = [TaxonomyCandidate.model_validate(item) for item in read_json(taxonomy_path)]
    return state
