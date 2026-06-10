# Stage 1 Spec — Full-Paper Extraction and Evidence Matrix

## Purpose
Stage 1 converts each paper in `literature/` into validated, structured evidence. It must not draft the final literature review. Its sole purpose is extraction, classification signals, and taxonomy candidate generation.

## Input

```text
literature/
├── paper_001.pdf
├── paper_002.pdf
├── ...
├── selected_paper.csv # To know when the paper was published and information about its venue. 
```

## Output

```text
outputs/
├── papers/
│   ├── paper_001.extraction.json
│   ├── paper_001.evidence.md
│   └── ...
├── evidence/
│   ├── evidence_matrix.csv
│   ├── evidence_matrix.jsonl
│   ├── failed_papers.csv
│   └── extraction_quality_report.md
└── logs/
    ├── llm_calls.jsonl
    └── stage1.log
```

## PDF parsing requirements

Implement `src/io/pdf_reader.py`.

### Required extraction fields per PDF page
- `page_number`
- `raw_text`
- `clean_text`
- `section_heading_guess`
- `tables_text`
- `figure_captions`
- `references_text`

### Recommended parsing stack
1. Primary: `pymupdf` (`fitz`) for robust text extraction.
2. Optional: GROBID for bibliographic metadata and section segmentation.
3. Optional fallback: OCR only for pages where extracted text length is below a threshold and page contains visible text.

### Section detection heuristics
Detect these sections using regex and LLM verification:
- Abstract
- Introduction
- Related Work
- Method / Proposed Method
- Experiments / Experimental Setup
- Results / Discussion
- Conclusion
- References

For survey writing, the most important sections are:
- Abstract
- Introduction
- Related Work
- Method / Proposed Method
- Experiments
- Dataset description
- Ablation / limitations if present

## Paper extraction schema
Every paper must be converted to `PaperExtraction` JSON. Use the schema in `schemas/paper_extraction.schema.json`.

### Required high-level fields
- `paper_id`
- `filename`
- `bibtex_key`
- `title`
- `authors`
- `year`
- `venue`
- `task_domain`
- `modality`
- `segmentation_target`
- `annotation_setting`
- `scribble_protocol`
- `core_problem`
- `key_contributions`
- `method_summary`
- `taxonomy_signals`
- `datasets`
- `benchmarks`
- `metrics`
- `baselines`
- `limitations`
- `evidence_spans`
- `confidence_scores`

## Detailed extraction tasks

### 1. MetadataAgent
Extract:
- title,
- authors,
- year,
- venue,
- DOI/arXiv if present,
- BibTeX key matched from `references.bib` or generated deterministically.

BibTeX key matching priority:
1. exact title match to `references.bib`,
2. normalized title match,
3. first author + year + first content word,
4. generated placeholder `MISSINGKEY_<firstauthor>_<year>`.

The system must flag missing/placeholder BibTeX keys in `citation_audit.md`.

### 2. AnnotationSettingAgent
Classify annotation regime:

Allowed primary regimes:
- `scribble_supervised`
- `weakly_supervised_scribble_like`
- `semi_supervised_full_mask`
- `mixed_scribble_and_full_mask`
- `not_relevant`

Allowed scribble protocols:
- `manual_scribbles`
- `synthetic_scribbles_from_full_masks`
- `skeletonized_masks`
- `random_walk_seed_lines`
- `centerline_or_click_lines`
- `unknown`

If the paper is not scribble-supervised but is useful as background, mark `secondary_relevance = true`.

### 3. MethodExtractionAgent
Extract the method into the following evidence fields:

```yaml
method_name:
problem_addressed:
main_idea:
supervision_signal:
  scribble_loss:
  dense_pseudo_label:
  consistency_loss:
  contrastive_loss:
  adversarial_loss:
  shape_or_boundary_prior:
architecture:
  backbone:
  teacher_student:
  dual_network:
  multi_decoder:
  graph_module:
  foundation_model:
algorithm_steps:
loss_functions:
key_modules:
novelty_claims:
claimed_advantages:
failure_modes_or_limitations:
```

### 4. TaxonomySignalAgent
The paper must be tagged using **multi-label signals**, not forced into a single taxonomy class yet.

Primary mechanism candidates:
- `pseudo_labeling`
- `label_propagation`
- `self_training`
- `co_training`
- `consistency_regularization`
- `image_consistency`
- `feature_consistency`
- `network_consistency`
- `task_level_consistency`
- `contrastive_learning`
- `prototype_learning`
- `adversarial_learning`
- `generative_modeling`
- `uncertainty_reliability`
- `noise_robust_learning`
- `boundary_shape_prior`
- `anatomical_prior`
- `foundation_model_assistance`
- `hybrid`

For each signal, store:
- `present`: boolean
- `strength`: `primary | secondary | weak`
- `evidence_quote`: short paraphrase, not long verbatim quote
- `section_or_page`: if available
- `reason`: why this signal applies

### 5. BenchmarkExtractionAgent
Extract benchmark info:

```yaml
dataset_name:
modality:
organ_or_target:
num_cases_or_images:
image_dimensionality:
num_classes:
train_val_test_split:
labeled_scribble_protocol:
manual_or_synthetic_scribbles:
percentage_or_amount_of_scribble_labels:
metrics:
reported_results:
baselines:
public_url_if_in_paper:
```

### 6. EvidenceVerifierAgent
This agent checks extraction reliability.

Rules:
- Reject extraction if method summary does not mention scribbles for a scribble paper.
- Reject taxonomy signal if no evidence span supports it.
- Flag methods with multiple plausible categories as `boundary_case`.
- Flag papers where dataset/protocol is not described.
- Flag papers with only abstract available.

## LLM call strategy

For each paper:
1. Chunk relevant sections into <= 12k tokens.
2. Run extraction with primary model.
3. Run verification with secondary model.
4. If disagreement occurs, run arbitration with a cheaper or stronger model depending on config.
5. Persist all intermediate JSON and logs.

Recommended routing:
- OpenAI/GPT: extraction requiring structured JSON and long-context synthesis.
- Gemini: cross-checking, candidate taxonomy criticism, and broad summarization.
- Local deterministic code: BibTeX matching, schema validation, CSV creation.

## Failure handling

A paper can be marked failed only after:
- text extraction attempted,
- metadata extraction attempted,
- one retry with alternate parser,
- one LLM retry with smaller chunks.

`failed_papers.csv` columns:

```csv
filename,stage,error_type,error_message,recoverable,next_action
```

## Acceptance criteria

Stage 1 is complete only when:
- At least 95% of relevant PDFs have valid extraction JSON.
- Every valid paper has at least one taxonomy signal.
- Every cited claim in candidate taxonomy reports points to at least one extracted paper.
- `evidence_matrix.csv` has no empty `method_name`, `title`, or `taxonomy_signals` cells for valid papers.
