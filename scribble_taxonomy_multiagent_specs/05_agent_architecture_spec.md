# Multi-Agent Architecture Spec

## Orchestration principle
Use a deterministic workflow with specialized LLM agents. The system should behave like a multi-agent research assistant, but the execution path should be controlled, reproducible, and auditable.

Recommended orchestration approaches:
1. Simple custom Python workflow for maximum transparency.
2. LangGraph if stateful graph execution, checkpoints, and human-in-the-loop selection are desired.

## Core state object

```python
class WorkflowState(BaseModel):
    run_id: str
    literature_dir: Path
    output_dir: Path
    papers: list[PaperRecord]
    extractions: dict[str, PaperExtraction]
    evidence_matrix_path: Path | None
    taxonomy_candidates: list[TaxonomyCandidate]
    selected_taxonomy_id: str | None
    writing_plan: WritingPlan | None
    drafts: dict[str, Path]
    audits: dict[str, Path]
    errors: list[WorkflowError]
```

## Agents

### 1. IngestionAgent
Responsibility:
- List PDFs.
- Compute file hashes.
- Extract text, page map, tables, captions.
- Detect if file was already cached.

Tools:
- PyMuPDF.
- Optional GROBID.

Output:
- `PaperRecord`
- page-level JSON.

### 2. MetadataAgent
Responsibility:
- Identify title, authors, year, venue.
- Match BibTeX key.
- Detect duplicated papers.

Output:
- metadata JSON.

### 3. MethodExtractionAgent
Responsibility:
- Extract method contribution, modules, losses, workflow.
- Summarize in structured schema.
- Identify what makes it scribble-supervised.

Output:
- partial `PaperExtraction`.

### 4. BenchmarkExtractionAgent
Responsibility:
- Extract dataset, modality, split, metrics, benchmark protocol.
- Distinguish benchmark dataset from auxiliary/pretraining dataset.

Output:
- list of `BenchmarkDatasetUse`.

### 5. TaxonomySignalAgent
Responsibility:
- Multi-label mechanism tagging.
- Provide evidence-backed reasons.

Output:
- taxonomy signal list.

### 6. EvidenceVerifierAgent
Responsibility:
- Check that extraction claims are grounded.
- Ask alternate model to verify difficult papers.
- Flag hallucinated or unsupported tags.

Output:
- verified extraction JSON or issue report.

### 7. TaxonomyProposerAgent
Responsibility:
- Generate 2–3 candidate taxonomies.
- Use evidence matrix and signal clusters.
- Produce branch definitions and paper mappings.

Output:
- taxonomy candidates.

### 8. TaxonomyCriticAgent
Responsibility:
- Critique candidates.
- Detect overlapping branches and weak coverage.
- Recommend best candidate.

Output:
- candidate scorecard.

### 9. UserSelectionNode
Responsibility:
- Stop workflow after Stage 1.
- Ask user to select candidate or provide override.

Implementation:
- CLI prompt or config file.

### 10. WritingPlanAgent
Responsibility:
- Create paragraph-level plan.
- Assign citations and evidence IDs.

Output:
- `writing_plan.json`.

### 11. DraftWriterAgent
Responsibility:
- Write LaTeX paragraphs from plan.
- Preserve branch definitions and transition logic.

Output:
- `taxonomy_draft_v1.tex`.

### 12. BenchmarkWriterAgent
Responsibility:
- Write benchmark subsection and tables.

Output:
- `benchmark_datasets.tex`.

### 13. RefinementAgent
Responsibility:
- Improve academic writing.
- Reduce repetition.
- Strengthen limitations and transitions.

Output:
- `taxonomy_draft_v2_refined.tex`.

### 14. CitationGuardAgent
Responsibility:
- Verify citations and evidence grounding.

Output:
- `citation_audit.md`.

### 15. FinalizerAgent
Responsibility:
- Assemble final section, tables, appendix, figure data.
- Run LaTeX checks.

Output:
- final LaTeX files.

## Agent communication protocol

All agents communicate through typed JSON objects, not free-form text, except writing agents.

Example:

```python
class AgentResult(BaseModel):
    agent_name: str
    status: Literal["success", "failed", "needs_retry"]
    payload: dict
    warnings: list[str] = []
    evidence_ids: list[str] = []
    cost_estimate: float | None = None
```

## Model routing rules

- Extraction: use a strong structured-output model.
- Verification: use a different provider/model to reduce same-model blind spots.
- Taxonomy proposal: use strong reasoning model.
- Draft writing: use best writing model available.
- Refinement: use same or stronger model, but with citation guard constraints.

## Human-in-the-loop checkpoints

1. After Stage 1 candidate taxonomies.
2. After draft v1 if the user wants to edit branch names.
3. Before finalization if citation audit has unresolved warnings.

## Logging requirements

Each LLM call log:

```json
{
  "timestamp": "...",
  "run_id": "...",
  "agent": "MethodExtractionAgent",
  "model": "...",
  "input_hash": "...",
  "schema_version": "...",
  "cache_hit": false,
  "status": "success",
  "token_usage": {"input": 0, "output": 0},
  "cost_estimate": 0.0
}
```
