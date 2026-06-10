from __future__ import annotations

from pathlib import Path

from ..schemas import PaperExtraction, TaxonomyCandidate
from ..utils import wrap_latex_text


class BenchmarkWriterAgent:
    def write(self, *, extractions: dict[str, PaperExtraction]) -> tuple[str, str]:
        datasets = []
        for extraction in extractions.values():
            for dataset in extraction.datasets:
                if dataset.dataset_name != "unknown":
                    datasets.append((dataset, extraction))
        overview_rows: list[str] = []
        protocol_rows: list[str] = []
        method_rows: list[str] = []
        seen_dataset_rows = set()
        for dataset, extraction in datasets:
            cite_key = extraction.bibtex_key or extraction.paper_id
            overview_key = (dataset.dataset_name, extraction.paper_id)
            if overview_key not in seen_dataset_rows:
                overview_rows.append(
                    " & ".join(
                        [
                            wrap_latex_text(dataset.dataset_name),
                            wrap_latex_text(dataset.modality or "unknown"),
                            wrap_latex_text(dataset.target or "unknown"),
                            wrap_latex_text(dataset.dimensionality),
                            wrap_latex_text(dataset.cases_or_images or "unknown"),
                            wrap_latex_text(dataset.scribble_protocol or "unknown"),
                            wrap_latex_text(", ".join(dataset.metrics) or "unknown"),
                        ]
                    )
                    + rf" \\ \cite{{{cite_key}}}"
                )
                protocol_rows.append(
                    " & ".join(
                        [
                            wrap_latex_text(dataset.dataset_name),
                            wrap_latex_text(dataset.split_protocol or "paper-specific split"),
                            wrap_latex_text(dataset.scribble_protocol or "unknown"),
                            "scribble-only partial CE",
                            "fully supervised",
                            wrap_latex_text("protocol variation may exist"),
                        ]
                    )
                    + rf" \\ \cite{{{cite_key}}}"
                )
                seen_dataset_rows.add(overview_key)
        family_to_datasets: dict[str, set[str]] = {}
        family_to_papers: dict[str, list[str]] = {}
        for extraction in extractions.values():
            signal = next((signal.signal for signal in extraction.taxonomy_signals if signal.present), "unknown")
            family_to_datasets.setdefault(signal, set()).update(dataset.dataset_name for dataset in extraction.datasets)
            family_to_papers.setdefault(signal, []).append(extraction.bibtex_key or extraction.paper_id)
        for family, paper_keys in family_to_papers.items():
            method_rows.append(
                " & ".join(
                    [
                        wrap_latex_text(family.replace("_", " ")),
                        wrap_latex_text(", ".join(dict.fromkeys(paper_keys[:3]))),
                        wrap_latex_text(", ".join(sorted(family_to_datasets.get(family, set()) - {"unknown"})) or "unknown"),
                        wrap_latex_text(" / ".join(sorted({metric for extraction in extractions.values() for metric in extraction.metrics[:2]})) or "Dice"),
                        wrap_latex_text("family-specific evaluation protocol"),
                    ]
                )
                + r" \\"
            )
        section = "\n".join(
            [
                r"\subsection{Benchmark Datasets and Evaluation Protocols}",
                r"\label{sec:scribble_benchmarks}",
                "Medical scribble-supervised segmentation is evaluated under heterogeneous protocols because many works synthesize scribbles from dense masks rather than collecting manual scribbles. This makes direct comparison difficult. We therefore summarize benchmarks along three axes: imaging modality, scribble-generation protocol, and evaluation metric.",
                r"\paragraph{Protocol limitations.} Synthetic scribbles and paper-specific splits remain common, so any taxonomy discussion should separate method advances from protocol advantages.",
            ]
        )
        tables = "\n\n".join(
            [
                self._table(
                    caption="Common benchmarks for scribble-supervised medical image segmentation.",
                    label="tab:scribble_benchmarks",
                    columns="lllllll",
                    header="Dataset & Modality & Target & 2D/3D & Cases/images & Scribble protocol & Metrics",
                    rows=overview_rows or ["unknown & unknown & unknown & unknown & unknown & unknown & unknown \\\\"],
                ),
                self._table(
                    caption="Evaluation protocol overview for scribble-supervised benchmarks.",
                    label="tab:scribble_protocols",
                    columns="llllll",
                    header="Dataset & Common split & Labeled pixels / scribble setting & Baseline & Upper bound & Notes",
                    rows=protocol_rows or ["unknown & unknown & unknown & unknown & unknown & unknown \\\\"],
                ),
                self._table(
                    caption="Method-family to benchmark mapping.",
                    label="tab:scribble_mapping",
                    columns="lllll",
                    header="Method family & Representative papers & Datasets & Metrics & Main evaluation pattern",
                    rows=method_rows or ["unknown & unknown & unknown & unknown & unknown \\\\"],
                ),
            ]
        )
        return section, tables

    def _table(self, *, caption: str, label: str, columns: str, header: str, rows: list[str]) -> str:
        body = "\n".join(rows)
        return "\n".join(
            [
                r"\begin{table}[t]",
                r"\centering",
                rf"\caption{{{caption}}}",
                rf"\label{{{label}}}",
                r"\resizebox{\linewidth}{!}{%",
                rf"\begin{{tabular}}{{{columns}}}",
                r"\toprule",
                header + r" \\",
                r"\midrule",
                body,
                r"\bottomrule",
                r"\end{tabular}}",
                r"\end{table}",
            ]
        )


class FigureWriterAgent:
    def write_mermaid(self, candidate: TaxonomyCandidate) -> str:
        lines = ["```mermaid", "flowchart TD", f"  ROOT[{candidate.title}]"]
        for branch in candidate.branches:
            branch_node = branch.branch_id.upper()
            lines.append(f"  ROOT --> {branch_node}[{branch.name}]")
            for index, subbranch in enumerate(branch.subbranches, start=1):
                sub_id = f"{branch_node}_{index}"
                lines.append(f"  {branch_node} --> {sub_id}[{subbranch.name}]")
        lines.append("```")
        return "\n".join(lines) + "\n"


class AppendixWriterAgent:
    def write_grouping_appendix(self, candidate: TaxonomyCandidate, extractions: dict[str, PaperExtraction]) -> str:
        lines = [r"\subsection*{Appendix: Paper Grouping by Selected Taxonomy}"]
        for branch in candidate.branches:
            lines.append(rf"\paragraph{{{wrap_latex_text(branch.name)}}}")
            entries = [wrap_latex_text(extractions[paper_id].title) for paper_id in branch.all_assigned_primary if paper_id in extractions]
            if entries:
                lines.append("; ".join(entries) + ".")
            else:
                lines.append("No paper was assigned by the heuristic pipeline.")
        return "\n".join(lines) + "\n"
