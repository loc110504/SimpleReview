from __future__ import annotations

from collections import defaultdict

import json

from ..llm.router import ModelRouter
from ..schemas import PaperExtraction, ParagraphPlan, TaxonomyBranch, TaxonomyCandidate, WritingPlan
from ..utils import wrap_latex_text


class WritingPlanAgent:
    def build(self, *, candidate: TaxonomyCandidate, extractions: dict[str, PaperExtraction], target_word_count: int) -> WritingPlan:
        plans: list[ParagraphPlan] = [
            ParagraphPlan(
                paragraph_id="design_definition",
                latex_location="sec:taxonomy_design",
                paragraph_goal="Define the scribble-supervised problem setting and explain taxonomy principles.",
                key_claims=[
                    "Scribble supervision labels only a sparse subset of pixels.",
                    "The taxonomy is mechanism-first and evidence-grounded.",
                ],
                papers_to_cite=self._select_papers(extractions, limit=3),
                evidence_ids=self._select_evidence(extractions, limit=6),
                required_terms=["\\mathcal{D}", "\\Omega_i^s", "\\Omega_i^u"],
                avoid_terms=["state-of-the-art"],
                transition_role="definition",
            )
        ]
        for branch in candidate.branches:
            plans.append(
                ParagraphPlan(
                    paragraph_id=f"{branch.branch_id}_definition",
                    latex_location=f"sec:{branch.branch_id}",
                    paragraph_goal=f"Define {branch.name}.",
                    key_claims=[
                        branch.definition,
                        "This family should be distinguished from adjacent branches using scribble-specific supervision logic.",
                    ],
                    papers_to_cite=branch.representative_papers[:4],
                    evidence_ids=self._select_evidence({paper_id: extractions[paper_id] for paper_id in branch.representative_papers if paper_id in extractions}, limit=8),
                    required_terms=["Definition"],
                    avoid_terms=["novel", "best"],
                    transition_role="definition",
                )
            )
            plans.append(
                ParagraphPlan(
                    paragraph_id=f"{branch.branch_id}_evolution",
                    latex_location=f"sec:{branch.branch_id}",
                    paragraph_goal=f"Explain the developmental evolution inside {branch.name}.",
                    key_claims=[
                        "Methods within this branch share a common supervision mechanism.",
                        "Later works respond to specific limitations of earlier variants.",
                    ],
                    papers_to_cite=branch.all_assigned_primary[:5],
                    evidence_ids=self._select_evidence({paper_id: extractions[paper_id] for paper_id in branch.all_assigned_primary if paper_id in extractions}, limit=10),
                    required_terms=["limitation", "transition"],
                    avoid_terms=["breakthrough"],
                    transition_role="evolution",
                )
            )
        plans.append(
            ParagraphPlan(
                paragraph_id="discussion",
                latex_location="sec:taxonomy_discussion",
                paragraph_goal="Discuss open problems and future directions.",
                key_claims=[
                    "Benchmark protocols remain heterogeneous.",
                    "Recent foundation-model papers increase both opportunity and comparability risk.",
                ],
                papers_to_cite=self._select_papers(extractions, limit=4),
                evidence_ids=self._select_evidence(extractions, limit=8),
                required_terms=["benchmark", "manual scribbles", "synthetic scribbles"],
                avoid_terms=["solved"],
                transition_role="discussion",
            )
        )
        return WritingPlan(
            selected_taxonomy_id=candidate.candidate_id,
            target_word_count=target_word_count,
            paragraph_plans=plans,
        )

    def _select_papers(self, extractions: dict[str, PaperExtraction], *, limit: int) -> list[str]:
        return list(extractions.keys())[:limit]

    def _select_evidence(self, extractions: dict[str, PaperExtraction], *, limit: int) -> list[str]:
        evidence_ids: list[str] = []
        for extraction in extractions.values():
            evidence_ids.extend(span.evidence_id for span in extraction.evidence_spans[:2])
            if len(evidence_ids) >= limit:
                break
        return evidence_ids[:limit]


class DraftWriterAgent:
    def __init__(self, router: ModelRouter | None = None) -> None:
        self.router = router

    def write(self, *, candidate: TaxonomyCandidate, plan: WritingPlan, extractions: dict[str, PaperExtraction]) -> str:
        llm_text = self._write_with_router(candidate=candidate, plan=plan, extractions=extractions)
        if llm_text:
            return llm_text.strip() + "\n"
        sections: list[str] = [
            r"\section{Taxonomy of Scribble-supervised Medical Image Segmentation}",
            r"\label{sec:taxonomy_scribble}",
            "",
            r"\subsection{Problem Setting and Taxonomy Design Principles}",
            r"\label{sec:taxonomy_design}",
            self._write_problem_setting(plan, extractions),
        ]
        for branch in candidate.branches:
            sections.extend(self._write_branch(branch, extractions))
        sections.extend(
            [
                r"\subsection{Discussion: Open Problems and Future Directions}",
                r"\label{sec:taxonomy_discussion}",
                self._write_discussion(candidate, extractions),
            ]
        )
        return "\n".join(sections).strip() + "\n"

    def _write_with_router(self, *, candidate: TaxonomyCandidate, plan: WritingPlan, extractions: dict[str, PaperExtraction]) -> str | None:
        if self.router is None:
            return None
        provider_name, _ = self.router.resolve_route("drafting", "primary")
        if provider_name == "heuristic":
            return None
        prompt = (
            "Write a LaTeX literature-review taxonomy section for scribble-supervised medical image segmentation.\n"
            "Requirements:\n"
            "- Definition-first paragraphs.\n"
            "- Developmental synthesis, not paper-by-paper listing.\n"
            "- End major subsections with limitation-transition logic.\n"
            "- Use only supplied BibTeX keys.\n"
            "- Return LaTeX only.\n\n"
            f"Selected taxonomy:\n{json.dumps(candidate.model_dump(mode='json'), ensure_ascii=False)}\n\n"
            f"Writing plan:\n{json.dumps(plan.model_dump(mode='json'), ensure_ascii=False)}\n\n"
            f"Paper evidence subset:\n{json.dumps({paper_id: extraction.model_dump(mode='json') for paper_id, extraction in list(extractions.items())[:12]}, ensure_ascii=False)}"
        )
        try:
            return self.router.generate_text(
                task_name="drafting",
                slot="primary",
                prompt=prompt,
                schema_version="drafting_v1",
                input_hash=f"{candidate.candidate_id}:{len(plan.paragraph_plans)}:{len(extractions)}",
            )
        except Exception:
            return None

    def _write_problem_setting(self, plan: WritingPlan, extractions: dict[str, PaperExtraction]) -> str:
        cite_keys = self._citation_block([extractions[paper_id].bibtex_key or paper_id for paper_id in list(extractions)[:3]])
        return "\n".join(
            [
                r"\paragraph{Definition.}",
                "Let $\\mathcal{D}=\\{(x_i, s_i)\\}_{i=1}^{N}$ denote the training set, where $x_i$ is a medical image and $s_i \\in \\{0,1,\\dots,C,\\varnothing\\}^{H\\times W}$ is a sparse scribble map. The labeled scribble pixels are $\\Omega_i^s=\\{p \\mid s_i(p) \\neq \\varnothing\\}$, while $\\Omega_i^u$ denotes unlabeled pixels. In this setting, each method must transform sparse supervision into denser or more reliable learning signals rather than assuming fully labeled masks.",
                f"This review therefore organizes the corpus by the mechanism that converts scribbles into supervision, keeps hybrid behavior as a secondary tag when possible, and links each family to evidence-backed limitations and transitions {cite_keys}.",
                r"The generic objective can be summarized as $\mathcal{L}=\mathcal{L}_{scr}(\Omega^s)+\lambda_p\mathcal{L}_{pl}(\Omega^u)+\lambda_c\mathcal{L}_{cons}+\lambda_r\mathcal{L}_{reg}$, where the relative importance of pseudo-labeling, consistency, and structural regularization depends on the selected branch.",
            ]
        )

    def _write_branch(self, branch: TaxonomyBranch, extractions: dict[str, PaperExtraction]) -> list[str]:
        lines = [
            rf"\subsection{{{wrap_latex_text(branch.name)}}}",
            rf"\label{{sec:{branch.branch_id}}}",
            r"\paragraph{Definition.}",
        ]
        rep_keys = self._citation_block(self._paper_keys(branch.representative_papers, extractions))
        lines.append(f"{wrap_latex_text(branch.definition)} {rep_keys}")
        if branch.subbranches:
            for subbranch in branch.subbranches:
                lines.append(rf"\subsubsection{{{wrap_latex_text(subbranch.name)}}}")
                sub_keys = self._citation_block(self._paper_keys(subbranch.representative_papers or branch.representative_papers, extractions))
                lines.append(
                    f"{wrap_latex_text(subbranch.definition)} Early and later papers in this subbranch are grouped because they share the same scribble-specific supervision logic rather than only reporting the same dataset. {sub_keys}"
                )
        lines.append(self._write_evolution(branch, extractions))
        return lines + [""]

    def _write_evolution(self, branch, extractions: dict[str, PaperExtraction]) -> str:
        papers = [extractions[paper_id] for paper_id in branch.all_assigned_primary if paper_id in extractions][:5]
        if not papers:
            return "This branch is currently under-populated in the extracted corpus and should be treated as an emerging trend."
        summaries = [paper.method_summary for paper in papers[:3]]
        cite_keys = self._citation_block(self._paper_keys([paper.paper_id for paper in papers], extractions))
        limitations = "; ".join(branch.limitations[:2])
        transition = branch.transition_to_next or "No further transition is defined because this branch closes the selected taxonomy."
        return (
            "Within this family, the literature develops from earlier attempts that establish the core mechanism toward later variants that stabilize or specialize it. "
            + " ".join(wrap_latex_text(summary) for summary in summaries)
            + f" {cite_keys} "
            + f"The main limitation is that {wrap_latex_text(limitations.lower())}, which explains why the next family emerges around a different supervision assumption. "
            + wrap_latex_text(transition)
        )

    def _write_discussion(self, candidate: TaxonomyCandidate, extractions: dict[str, PaperExtraction]) -> str:
        all_datasets = sorted({dataset.dataset_name for extraction in extractions.values() for dataset in extraction.datasets if dataset.dataset_name != "unknown"})
        cite_keys = self._citation_block(self._paper_keys(list(extractions.keys())[:4], extractions))
        dataset_phrase = ", ".join(all_datasets[:6]) if all_datasets else "dataset protocols reported in the corpus"
        return (
            "Two corpus-level issues remain unresolved. First, many papers still rely on synthetic scribbles or paper-specific splits, so benchmark comparison across "
            + wrap_latex_text(dataset_phrase)
            + f" must be interpreted with caution {cite_keys}. "
            "Second, newer reliability-aware and foundation-assisted methods improve supervision quality, but they also increase overlap between pseudo-labeling, structural priors, and external priors. "
            "A defensible literature review should therefore explain not only where each paper is placed, but also why nearby alternatives were excluded or retained as secondary tags."
        )

    def _paper_keys(self, paper_ids: list[str], extractions: dict[str, PaperExtraction]) -> list[str]:
        return [extractions[paper_id].bibtex_key or paper_id for paper_id in paper_ids if paper_id in extractions]

    def _citation_block(self, keys: list[str]) -> str:
        unique = [key for key in dict.fromkeys(keys) if key]
        return rf"\cite{{{','.join(unique)}}}" if unique else ""
