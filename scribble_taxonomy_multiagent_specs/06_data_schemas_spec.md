# Data Schema Spec

Use Pydantic models in `src/schemas/models.py` and JSON schema files in `src/schemas/`.

## PaperExtraction schema

```python
class EvidenceSpan(BaseModel):
    evidence_id: str
    paper_id: str
    section: str | None = None
    page: int | None = None
    text: str
    paraphrase: str
    supports_fields: list[str]

class TaxonomySignal(BaseModel):
    signal: str
    present: bool
    strength: Literal["primary", "secondary", "weak", "absent"]
    reason: str
    evidence_ids: list[str]

class DatasetUse(BaseModel):
    dataset_name: str
    role: Literal["main_benchmark", "auxiliary", "pretraining", "external_validation", "unknown"]
    modality: str | None = None
    target: str | None = None
    cases_or_images: str | None = None
    dimensionality: Literal["2D", "3D", "2.5D", "mixed", "unknown"] = "unknown"
    num_classes: str | None = None
    split_protocol: str | None = None
    scribble_protocol: str | None = None
    metrics: list[str] = []
    results_summary: str | None = None
    evidence_ids: list[str] = []

class MethodComponents(BaseModel):
    backbone: str | None = None
    architecture: list[str] = []
    modules: list[str] = []
    loss_terms: list[str] = []
    pseudo_label_generation: str | None = None
    consistency_target: str | None = None
    reliability_mechanism: str | None = None
    prior_type: str | None = None

class PaperExtraction(BaseModel):
    paper_id: str
    filename: str
    bibtex_key: str | None
    title: str
    authors: list[str]
    year: int | None
    venue: str | None
    method_name: str | None
    annotation_setting: str
    scribble_protocol: str
    task_domain: str
    modality: list[str]
    segmentation_target: list[str]
    core_problem: str
    key_contributions: list[str]
    method_summary: str
    algorithm_steps: list[str]
    method_components: MethodComponents
    taxonomy_signals: list[TaxonomySignal]
    datasets: list[DatasetUse]
    metrics: list[str]
    baselines: list[str]
    limitations: list[str]
    boundary_case_notes: list[str]
    evidence_spans: list[EvidenceSpan]
    extraction_confidence: float
```

## TaxonomyCandidate schema

```python
class TaxonomySubbranch(BaseModel):
    name: str
    definition: str
    inclusion_criteria: list[str]
    exclusion_criteria: list[str]
    representative_papers: list[str]
    boundary_cases: list[str]
    rationale: str

class TaxonomyBranch(BaseModel):
    branch_id: str
    name: str
    definition: str
    inclusion_criteria: list[str]
    exclusion_criteria: list[str]
    subbranches: list[TaxonomySubbranch]
    representative_papers: list[str]
    all_assigned_primary: list[str]
    all_assigned_secondary: list[str]
    limitations: list[str]
    transition_to_next: str | None

class TaxonomyCandidate(BaseModel):
    candidate_id: Literal["A", "B", "C"]
    title: str
    rationale: str
    branches: list[TaxonomyBranch]
    coverage_statistics: dict
    strengths: list[str]
    weaknesses: list[str]
    recommended_use: str
    reviewer_risks: list[str]
```

## WritingPlan schema

```python
class ParagraphPlan(BaseModel):
    paragraph_id: str
    latex_location: str
    paragraph_goal: str
    key_claims: list[str]
    papers_to_cite: list[str]
    evidence_ids: list[str]
    required_terms: list[str]
    avoid_terms: list[str]
    transition_role: Literal["definition", "mechanism", "evolution", "limitation", "benchmark", "transition", "discussion"]

class WritingPlan(BaseModel):
    selected_taxonomy_id: str
    target_word_count: int
    paragraph_plans: list[ParagraphPlan]
```

## Evidence matrix CSV columns

```csv
paper_id,filename,bibtex_key,title,year,venue,method_name,annotation_setting,manual_or_synthetic_scribble,modality,target,datasets,metrics,primary_signal,secondary_signals,architecture_tags,loss_tags,prior_tags,confidence,branch_candidate_A,branch_candidate_B,branch_candidate_C,boundary_case,notes
```

## JSON schema validation policy

- Validate every LLM output with Pydantic.
- On validation failure:
  1. send schema errors back to the same model for repair,
  2. retry once,
  3. fallback to a different model,
  4. mark failed if still invalid.
- Never parse free-form Markdown as the source of truth for extraction.
