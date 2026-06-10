# Stage 3–4 Spec — Refinement, Quality Control, and Final LaTeX

## Purpose
Improve writing quality, remove unsupported claims, fix taxonomy inconsistencies, and produce the final LaTeX version.

## Inputs
- `outputs/drafts/taxonomy_draft_v1.tex`
- `outputs/drafts/taxonomy_draft_v1_notes.md`
- `outputs/papers/*.extraction.json`
- `outputs/evidence/evidence_matrix.csv`
- user comments if provided

## Outputs
```text
outputs/drafts/taxonomy_draft_v2_refined.tex
outputs/final/taxonomy_final.tex
outputs/final/taxonomy_tables.tex
outputs/final/benchmark_datasets.tex
outputs/final/citation_audit.md
outputs/final/quality_report.md
```

## Refinement agents

### 1. TaxonomyCoherenceReviewer
Checks:
- Are top-level branches mutually distinguishable?
- Are subbranches placed under the correct parent?
- Are hybrid methods explained as hybrid rather than forced artificially?
- Are there missing branches suggested by evidence?
- Are definitions consistent across the whole section?

Output:

```yaml
issues:
  - severity: critical|major|minor
    location:
    problem:
    suggested_fix:
```

### 2. EvidenceGroundingReviewer
Checks every paragraph:
- Does each claim have citations?
- Do citations actually support the claim?
- Are there over-generalized claims from one paper?
- Are limitations attributed correctly?

If a claim is unsupported, the agent must either:
- add evidence-supported citation,
- weaken the claim,
- move it to a hypothesis/future direction,
- remove it.

### 3. AcademicStyleReviewer
Improves:
- flow,
- clarity,
- academic tone,
- paragraph transitions,
- concise grouping,
- reduction of repetition.

Style target:
- Simple academic English, IELTS 7.5–8.0.
- Direct and precise.
- Suitable for Q1 journal/thesis literature review.

### 4. ReviewerSimulationAgent
Simulates likely reviewer objections:
- taxonomy overlap,
- missing benchmark standardization,
- insufficient distinction between scribble-supervised and semi-supervised learning,
- too much paper listing,
- unsupported claims about state-of-the-art,
- missing recent foundation model discussion.

### 5. CitationGuardAgent
Checks:
- every `\cite{}` key exists,
- no placeholder key remains,
- no paper appears in wrong branch without secondary-label explanation,
- no citation is used in final text if extraction failed.

### 6. LaTeXCompileAgent
Runs:

```bash
latexmk -pdf -interaction=nonstopmode main.tex
```

If no `main.tex` exists, create a temporary wrapper:

```latex
\documentclass{article}
\usepackage{booktabs}
\usepackage{multirow}
\usepackage{graphicx}
\usepackage{amsmath}
\usepackage{amssymb}
\usepackage{adjustbox}
\usepackage[numbers]{natbib}
\begin{document}
\input{taxonomy_final.tex}
\bibliographystyle{unsrt}
\bibliography{references}
\end{document}
```

## Quality gates

Finalization fails if:
- Missing BibTeX keys remain.
- Any top-level branch has no definition.
- More than 10% of paragraphs have no citation.
- Any dataset in benchmark table has no source paper.
- LaTeX has compile-breaking syntax errors.
- `citation_audit.md` contains critical unresolved issues.

## Final quality report

`quality_report.md` must include:

```markdown
# Quality Report

## Taxonomy coverage
- Total relevant papers:
- Assigned papers:
- Unassigned papers:
- Boundary cases:

## Citation audit
- Total citations:
- Missing keys:
- Placeholder keys:

## Writing diagnostics
- Total words:
- Average citations per paragraph:
- Repeated phrases:
- Long paragraphs > 220 words:

## Manual review checklist
- [ ] Verify branch names.
- [ ] Verify benchmark table values.
- [ ] Verify all generated BibTeX keys.
- [ ] Verify claims about recent/foundation-model papers.
```
