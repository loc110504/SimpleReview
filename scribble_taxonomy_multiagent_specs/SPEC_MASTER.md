<!-- FILE: README.md -->

# Scribble-Supervised Medical Image Segmentation Taxonomy Writer — Multi-Agent System Spec

## Goal
Build a Python-based multi-agent system that reads a local `literature/` folder containing ~55 key papers on **scribble-supervised medical image segmentation**, extracts method-level evidence, proposes 2–3 competing taxonomy designs, waits for the user to select one, then drafts, refines, and finalizes a LaTeX literature-review subsection on taxonomy, including benchmark/dataset summaries and BibTeX-backed citations.

The system must be designed for **research writing**, not only summarization. It should produce a taxonomy that is:

1. Mechanistically grounded: classes are based on how each method uses sparse scribble supervision.
2. Evidence-backed: every taxonomy claim links to extracted evidence from papers.
3. Hierarchical: about 5–6 top-level approaches, each with sub-approaches.
4. Developmental: writing should explain how each branch evolved, what limitation earlier methods had, and how later works addressed it.
5. LaTeX-ready: output is a complete `.tex` section with citations, tables, and optional taxonomy figure data.

## Required two-stage workflow

### Stage 1 — Full-paper extraction and taxonomy proposal
Run once over all files in `literature/`.

Outputs:
- `outputs/papers/*.json`: structured extraction for each paper.
- `outputs/evidence/evidence_matrix.csv`: one row per paper with method signals.
- `outputs/taxonomy/taxonomy_candidates.json`: 2–3 alternative taxonomy designs.
- `outputs/taxonomy/taxonomy_candidates.md`: readable report for user selection.
- `outputs/taxonomy/paper_to_candidate_mapping.md`: paper assignments under each candidate.

The program must stop after Stage 1 and ask the user to choose taxonomy candidate A/B/C or edit one.

### Stage 2 — Draft taxonomy, refine, final version
After user selects a taxonomy:

Outputs:
- `outputs/drafts/taxonomy_draft_v1.tex`
- `outputs/drafts/taxonomy_draft_v1_notes.md`
- `outputs/drafts/taxonomy_draft_v2_refined.tex`
- `outputs/final/taxonomy_final.tex`
- `outputs/final/taxonomy_tables.tex`
- `outputs/final/taxonomy_figure_mermaid.md`
- `outputs/final/benchmark_datasets.tex`
- `outputs/final/citation_audit.md`

## Recommended repository layout

```text
scribble_taxonomy_writer/
├── literature/                         # input PDFs, optional .bib, notes
├── src/
│   ├── main.py                          # CLI entrypoint
│   ├── config.py                        # env/config loading
│   ├── io/
│   │   ├── pdf_reader.py                 # PyMuPDF/GROBID extraction
│   │   ├── bibtex_reader.py              # bibtex parsing and key matching
│   │   └── cache.py                      # deterministic caching
│   ├── llm/
│   │   ├── base.py                       # provider interface
│   │   ├── openai_client.py              # GPT API wrapper
│   │   ├── gemini_client.py              # Gemini API wrapper
│   │   ├── router.py                     # model routing + retry
│   │   └── structured.py                 # JSON schema validation
│   ├── agents/
│   │   ├── ingestion_agent.py
│   │   ├── metadata_agent.py
│   │   ├── method_extraction_agent.py
│   │   ├── benchmark_agent.py
│   │   ├── taxonomy_proposer_agent.py
│   │   ├── taxonomy_critic_agent.py
│   │   ├── taxonomy_mapping_agent.py
│   │   ├── draft_writer_agent.py
│   │   ├── synthesis_agent.py
│   │   ├── refinement_agent.py
│   │   ├── citation_guard_agent.py
│   │   └── finalizer_agent.py
│   ├── workflows/
│   │   ├── stage1_extract_and_propose.py
│   │   └── stage2_write_and_refine.py
│   ├── schemas/
│   │   ├── paper_extraction.schema.json
│   │   ├── taxonomy_candidate.schema.json
│   │   ├── benchmark_dataset.schema.json
│   │   └── writing_plan.schema.json
│   └── prompts/
│       ├── extraction_prompts.py
│       ├── taxonomy_prompts.py
│       ├── writing_prompts.py
│       └── review_prompts.py
├── outputs/
├── configs/
│   ├── taxonomy_seed.yaml
│   ├── models.yaml
│   └── writing_style.yaml
├── .env
├── .env.example
├── requirements.txt
└── README.md
```

## CLI commands

```bash
# 0) install
pip install -r requirements.txt

# 1) run extraction and taxonomy proposals
python -m src.main stage1 --literature-dir literature --out outputs

# 2) inspect candidate taxonomies
cat outputs/taxonomy/taxonomy_candidates.md

# 3) select candidate B and optionally provide a YAML edit file
python -m src.main stage2 --candidate B --out outputs

# 4) refine only
python -m src.main refine --draft outputs/drafts/taxonomy_draft_v1.tex

# 5) final audit
python -m src.main audit --tex outputs/final/taxonomy_final.tex
```

## Non-negotiable engineering requirements

- Never draft taxonomy before all papers have valid extraction JSON or are explicitly marked `failed` with an error reason.
- Never cite a paper in LaTeX unless it has a BibTeX key and supporting extraction evidence.
- Every taxonomy branch must have:
  - definition,
  - inclusion criteria,
  - exclusion criteria,
  - representative papers,
  - boundary cases,
  - limitation/transition logic.
- Every generated paragraph must be traceable to paper-level evidence.
- Keep `hybrid` as a cross-tag unless the evidence shows a group is genuinely multi-paradigm and cannot be placed into a primary mechanism.
- Use deterministic caching of LLM calls by hashing `(model, prompt, input_text, schema_version)`.
- Use JSON schema validation and automatic repair loops for all extraction outputs.


<!-- FILE: 00_survey_analysis.md -->

# Analysis of the Two Reference Survey Papers and Transferable Design Rules

This file summarizes what to imitate from the two semi-supervised segmentation surveys when designing a scribble-supervised taxonomy writer.

## 1. Survey 1: Deep learning-based semi-supervised semantic segmentation

### Taxonomy design
The generic semantic segmentation survey organizes the field into five top-level methodological families:

1. **Adversarial methods**
   - Definition: GAN-like or discriminator-based frameworks.
   - Subdivision:
     - Generative adversarial methods: generator synthesizes new images, segmentation model/discriminator uses real and synthetic data.
     - Non-generative adversarial methods: segmentation network plays generator-like role; discriminator judges predicted segmentation maps against ground-truth masks.
   - Writing pattern: starts from GAN concept, gives equation, then narrows to segmentation-specific adaptation, then lists representative variants.

2. **Consistency regularization**
   - Definition: enforce invariant/equivariant predictions across perturbations.
   - Subdivision is based on perturbation locus:
     - Input perturbations: CutMix, ClassMix, geometric/photometric augmentation.
     - Feature perturbations: perturb encoder features or auxiliary decoder outputs.
     - Network perturbations: independent networks or student-teacher variants.
     - Combined perturbations: mix multiple perturbation sources.
   - Writing pattern: formal objective first, then sub-branches by where perturbation acts.

3. **Pseudo-labeling**
   - Definition: generate labels for unlabeled data and train with them.
   - Subdivision:
     - Self-training: one model retrains on its own high-confidence predictions.
     - Mutual-training: multiple learners supervise each other; disagreement/reweighting mitigates error accumulation.
   - Writing pattern: explain simple loop, then discuss confirmation bias and reliability.

4. **Contrastive learning**
   - Definition: learn representation space where similar pixels/regions/classes are close and dissimilar ones are far.
   - Not heavily subdivided in the survey, but the writing distinguishes query/key sampling, memory bank, active sampling, pixel/region level.

5. **Hybrid methods**
   - Definition: combine several of the previous mechanisms.
   - The survey treats hybrid as a final top-level category, but for a scribble-specific taxonomy it may be better to treat hybrid as a secondary tag when a method still has a dominant mechanism.

### Methodology design
The survey constructs taxonomy through systematic search, inclusion/exclusion filtering, and manual classification of representative models. Classification criteria include:

- Core mechanism for using unlabeled data.
- Architectural components: discriminator, teacher-student, multi-branch, memory bank.
- Type of perturbation or supervisory signal: input, feature, network, pseudo-label.
- Whether method is generic or segmentation-specific.

### Benchmark writing
The survey writes benchmark sections in this order:

1. Explain why fair comparison is hard: different datasets, splits, base models, backbones, preprocessing.
2. Define selected datasets and why each is used.
3. Specify partition protocol.
4. Specify validation and repeated runs.
5. Specify metric.
6. Specify method selection criteria.
7. Specify base model/backbone and hardware.
8. Present quantitative tables.
9. Add qualitative visual discussion for failure modes.

This structure is directly transferable to scribble-supervised medical segmentation. Replace mean IoU emphasis with Dice, HD95/ASD, and boundary-sensitive metrics.

## 2. Survey 2: Deep semi-supervised learning for medical image segmentation

### Taxonomy design
The medical survey uses a medical-domain-oriented taxonomy:

1. **Pseudo labels**
   - Online pseudo-label generation with confidence, uncertainty, trust modules, ensembling, post-processing.
   - Label propagation using prototype learning, nearest-neighbor matching, semantic transfer.

2. **Unsupervised regularization**
   - Consistency learning.
   - Co-training.
   - Adversarial learning.
   - Entropy minimization.

3. **Knowledge priors**
   - Self-supervised tasks such as reconstruction, inpainting, jigsaw, contrastive learning.
   - Anatomical priors such as atlas, shape, size, relation, topology.

4. **Other real-world concerns**
   - Distribution misalignment.
   - Multi-level supervision.
   - Class imbalance.
   - Bayesian/generative formulations.

### Benchmark writing
The medical survey writes benchmark sections around medical datasets and clinical metrics:

- Metrics: DSC, IoU/Jaccard, HD, HD95.
- Benchmark datasets: LA MRI, NIH Pancreas CT, BraTS, ACDC.
- For each dataset, it reports:
  - modality,
  - number of cases,
  - resolution/preprocessing,
  - train/test split,
  - labeled/unlabeled protocol,
  - backbone convention,
  - lower-bound/upper-bound fully supervised setup,
  - representative method table.

### What to transfer to scribble-supervised segmentation
Scribble supervision is not identical to standard SSL. The key gap is **intra-image sparse supervision**: every training image may have only a small subset of labeled pixels, rather than a clean labeled set plus unlabeled set. Therefore, the taxonomy writer must reframe the SSL categories as follows:

- Pseudo-labeling becomes **scribble-to-dense label expansion**.
- Consistency regularization becomes **regularizing unlabeled pixels under sparse anchors**.
- Knowledge priors become more central because scribbles do not encode boundaries.
- Reliability/noise modeling deserves its own axis because pseudo masks propagated from scribbles can be noisy.
- Dataset benchmark sections must record whether scribbles are manual, simulated from full masks, skeletonized, random lines, bounding-line annotations, or generated by erosion/skeletonization.

## 3. Recommended scribble-supervised taxonomy seed

This seed is only a prior. Stage 1 must infer the final taxonomy from the 55 papers.

### Candidate top-level approaches
1. **Scribble-to-dense pseudo-label generation**
   - graph/random-walk/CRF propagation,
   - superpixel/region propagation,
   - confidence-filtered self-training,
   - co-training/mutual pseudo-labeling,
   - foundation-model-assisted pseudo-mask refinement.

2. **Consistency and perturbation regularization under sparse labels**
   - image-level consistency,
   - feature-level consistency,
   - network-level consistency / mean teacher / dual network,
   - task-level consistency such as mask/contour/signed-distance prediction,
   - mixed perturbation strategies.

3. **Reliability-, uncertainty-, and noise-aware learning**
   - uncertainty estimation,
   - confidence thresholding,
   - error correction/refinement networks,
   - curriculum and dynamic reweighting,
   - scribble noise modeling.

4. **Representation learning and contrastive/prototype methods**
   - pixel-level contrastive learning,
   - region/prototype learning,
   - class memory bank,
   - cross-view feature alignment.

5. **Structure-, boundary-, and anatomy-prior methods**
   - shape/size/topology priors,
   - boundary-aware losses,
   - contour/signed-distance transforms,
   - graph/geodesic priors,
   - anatomical relation constraints.

6. **Generative, adversarial, and foundation-model-assisted methods**
   - adversarial mask realism,
   - generative augmentation,
   - SAM/foundation-model refinement,
   - diffusion/large model priors if present in corpus.

### Cross-tags
- Hybrid/multi-paradigm.
- Transformer/foundation architecture.
- 2D vs 3D.
- Dataset-specific vs generalizable.
- Manual scribble vs simulated scribble.
- Boundary-focused vs region-focused.

## 4. Writing style rules to emulate

Each taxonomy branch should be written in the following pattern:

1. Definition of the approach.
2. Why scribble supervision makes the approach necessary.
3. Core mechanism and objective/loss, if available.
4. Representative papers, grouped by sub-approach rather than one-by-one.
5. Development narrative: earlier limitation → later solution.
6. Boundary cases and relation to adjacent branches.
7. Critical analysis: failure modes, assumptions, computational cost, dataset sensitivity.
8. Transition paragraph to the next branch.


<!-- FILE: 01_stage1_extraction_spec.md -->

# Stage 1 Spec — Full-Paper Extraction and Evidence Matrix

## Purpose
Stage 1 converts each paper in `literature/` into validated, structured evidence. It must not draft the final literature review. Its sole purpose is extraction, classification signals, and taxonomy candidate generation.

## Input

```text
literature/
├── paper_001.pdf
├── paper_002.pdf
├── ...
├── references.bib        # optional but strongly recommended
└── manual_metadata.csv   # optional override file
```

Optional `manual_metadata.csv` columns:

```csv
filename,bibtex_key,title,year,venue,notes
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


<!-- FILE: 02_taxonomy_proposal_spec.md -->

# Stage 1B Spec — Taxonomy Candidate Proposal

## Purpose
After structured extraction, propose 2–3 candidate taxonomies for the user's selection. The system must not assume the seed taxonomy is correct. It must infer clusters from the corpus and then use the seed only as a prior.

## Inputs
- `outputs/papers/*.extraction.json`
- `outputs/evidence/evidence_matrix.csv`
- `configs/taxonomy_seed.yaml`

## Outputs
- `outputs/taxonomy/taxonomy_candidates.json`
- `outputs/taxonomy/taxonomy_candidates.md`
- `outputs/taxonomy/paper_to_candidate_mapping.md`
- `outputs/taxonomy/taxonomy_conflicts.md`

## Candidate taxonomy design
Generate three styles if evidence supports them:

### Candidate A — Mechanism-first taxonomy
Organize by learning mechanism:
1. Scribble-to-dense pseudo-labeling / label propagation.
2. Consistency regularization.
3. Reliability/uncertainty/noise-aware learning.
4. Contrastive/prototype representation learning.
5. Boundary/shape/anatomical prior learning.
6. Generative/adversarial/foundation-model-assisted methods.

### Candidate B — Supervision-signal-first taxonomy
Organize by how sparse scribbles are converted into learning signals:
1. Propagated labels and pseudo masks.
2. Regularization over unlabeled pixels.
3. Feature-space supervision.
4. Structural/boundary supervision.
5. Multi-model supervision.
6. External prior/foundation-model supervision.

### Candidate C — Chronological-evolution taxonomy
Organize by research evolution:
1. Classical graph/CRF/random-walk propagation.
2. CNN scribble losses and partial cross entropy.
3. Pseudo-mask refinement/self-training.
4. Consistency/teacher-student and co-training.
5. Representation, contrastive and prototype methods.
6. Structure-aware and foundation-model-enhanced methods.

The agent may generate different candidates if the extracted evidence suggests better structures.

## Required content for each candidate

```yaml
candidate_id:
title:
rationale:
top_level_branches:
  - branch_id:
    branch_name:
    definition:
    inclusion_criteria:
    exclusion_criteria:
    subbranches:
      - subbranch_name:
        definition:
        representative_papers:
        boundary_cases:
    representative_papers:
    core_limitations:
    writing_angle:
coverage_statistics:
  total_papers:
  assigned_primary:
  assigned_secondary:
  unassigned:
  hybrid_count:
advantages:
risks:
recommended_for_user:
```

## Clustering and classification procedure

### Step 1. Create method-signal matrix
Rows are papers. Columns are taxonomy signals.
Values:
- 0 = absent
- 1 = weak
- 2 = secondary
- 3 = primary

Also encode:
- year,
- architecture tags,
- dataset tags,
- modality,
- scribble protocol,
- benchmark family.

### Step 2. Infer clusters
Use both deterministic and LLM-assisted clustering:

- Deterministic: hierarchical clustering over signal matrix.
- LLM: ask taxonomy proposer to inspect groupings and name branches.
- Reconciliation: EvidenceVerifierAgent checks every proposed branch has enough papers and distinct criteria.

### Step 3. Assign primary and secondary labels
Rules:
- A method with pseudo masks plus consistency should be primary by the mechanism that produces the main unsupervised/sparse-region signal.
- If consistency only regularizes pseudo labels, primary may still be pseudo-labeling and secondary consistency.
- If the novelty is uncertainty/reliability rather than pseudo-label generation itself, primary may be reliability/noise-aware.
- `hybrid` is not primary unless no single mechanism dominates or the paper explicitly proposes a balanced multi-paradigm framework.

### Step 4. Detect boundary cases
A boundary case is a paper where:
- top two primary scores are close,
- evidence suggests multiple mechanisms,
- taxonomy agents disagree,
- the paper contribution is a general architecture rather than a learning principle.

Output boundary cases to `taxonomy_conflicts.md`.

## Scoring criteria for choosing best taxonomy

Each candidate should be scored 1–5 on:

1. Coverage of all 55 papers.
2. Branch balance: no branch should contain >40% of papers unless justified.
3. Conceptual separation: definitions do not overlap heavily.
4. Scribble specificity: categories reflect sparse scribble supervision, not generic SSL only.
5. Writing potential: allows narrative of evolution/limitations.
6. Benchmark integration: connects methods to dataset patterns.
7. Reviewer defensibility: categories are easy to justify in a thesis/paper.

## User selection format

The final candidate report should end with:

```text
Please choose one option:
[A] Mechanism-first taxonomy
[B] Supervision-signal-first taxonomy
[C] Chronological-evolution taxonomy
[custom] Provide edits in configs/user_taxonomy_override.yaml
```

## Acceptance criteria

- At least 2 and at most 3 candidate taxonomies.
- Every candidate maps at least 90% of relevant papers.
- Every branch has at least 3 representative papers unless explicitly marked as emerging trend.
- Every branch includes inclusion/exclusion rules.
- The report explains trade-offs, not just labels.


<!-- FILE: 03_stage2_writing_spec.md -->

# Stage 2 Spec — Draft Taxonomy Writing in LaTeX

## Purpose
After the user selects a taxonomy, generate a high-quality LaTeX literature-review section on scribble-supervised medical image segmentation taxonomy.

## Inputs
- `outputs/taxonomy/taxonomy_candidates.json`
- selected candidate ID or user-edited YAML override
- `outputs/papers/*.extraction.json`
- `outputs/evidence/evidence_matrix.csv`
- `references.bib` or generated BibTeX file
- `configs/writing_style.yaml`

## Outputs
```text
outputs/drafts/taxonomy_draft_v1.tex
outputs/drafts/taxonomy_draft_v1_notes.md
outputs/drafts/taxonomy_tables.tex
outputs/drafts/benchmark_datasets.tex
outputs/drafts/taxonomy_figure_mermaid.md
outputs/drafts/paper_grouping_appendix.tex
```

## LaTeX structure

Recommended section structure:

```latex
\section{Taxonomy of Scribble-supervised Medical Image Segmentation}
\label{sec:taxonomy_scribble}

\subsection{Problem Setting and Taxonomy Design Principles}
\label{sec:taxonomy_design}

\subsection{Scribble-to-dense Pseudo-label Generation}
\label{sec:pseudo_labeling}

\subsubsection{Graph-, CRF-, and Region-based Label Propagation}
\subsubsection{Self-training and Iterative Pseudo-mask Refinement}
\subsubsection{Co-training and Mutual Pseudo-labeling}

\subsection{Consistency Regularization under Sparse Scribble Anchors}
\subsubsection{Image-level Consistency}
\subsubsection{Feature-level Consistency}
\subsubsection{Network-level and Teacher--Student Consistency}
\subsubsection{Task-level and Combined Consistency}

\subsection{Reliability-, Uncertainty-, and Noise-aware Learning}
\subsubsection{Confidence and Entropy-based Pixel Selection}
\subsubsection{Error Correction and Pseudo-label Refinement}
\subsubsection{Curriculum and Dynamic Reweighting}

\subsection{Representation Learning: Contrastive and Prototype-based Approaches}
\subsubsection{Pixel-level Contrastive Learning}
\subsubsection{Region-level and Prototype-based Representation Learning}

\subsection{Structure-, Boundary-, and Anatomy-prior Methods}
\subsubsection{Boundary and Signed-distance Supervision}
\subsubsection{Shape, Size, Topology, and Anatomical Relation Priors}

\subsection{Generative, Adversarial, and Foundation-model-assisted Methods}
\subsubsection{Adversarial Mask Realism and Generative Augmentation}
\subsubsection{Foundation-model-assisted Pseudo-mask Construction}

\subsection{Benchmark Datasets and Evaluation Protocols}
\label{sec:scribble_benchmarks}

\subsection{Discussion: Open Problems and Future Directions}
\label{sec:taxonomy_discussion}
```

The actual structure must follow the selected taxonomy, not blindly use this template.

## Writing principles

### 1. Definition-first paragraphs
Every top-level branch starts with:

```latex
\paragraph{Definition.}
...
```

The definition must state:
- what the family does,
- what kind of supervision it creates from scribbles,
- what part of the image/model it regularizes,
- how it differs from adjacent families.

### 2. Developmental synthesis, not paper-by-paper listing
Bad:

> Paper A did X. Paper B did Y. Paper C did Z.

Good:

> Early graph-based propagation methods attempted to densify scribbles using low-level similarity, but their reliance on local appearance made them fragile near weak boundaries. Later CNN-based self-training methods replaced hand-crafted propagation with model-driven pseudo masks, but introduced confirmation bias. To reduce this bias, subsequent co-training frameworks used multiple learners or views to cross-check pseudo labels.

### 3. Evidence grouping
Each paragraph should group 2–5 papers if they share a mechanism. Use individual discussion only for seminal or boundary-case papers.

### 4. Limitation-transition logic
Each subsection should end with a transition:
- limitation of current family,
- why next family emerged,
- what new assumption or signal the next family uses.

### 5. Citation density
- Every paragraph making method claims must cite at least one paper.
- Avoid citation dumping: do not put 10 papers after one generic sentence.
- Prefer citations after precise claims.

### 6. Mathematical notation
Define scribble setting early:

```latex
Let \mathcal{D}=\{(x_i, s_i)\}_{i=1}^{N} denote the training set, where x_i is an image and s_i \in \{0,1,\dots,C,\varnothing\}^{H\times W} is a sparse scribble map. The set of labeled scribble pixels is \Omega_i^s=\{p \mid s_i(p) \neq \varnothing\}, while \Omega_i^u denotes unlabeled pixels.
```

Use optional generalized objective:

```latex
\mathcal{L}=\mathcal{L}_{scr}(\Omega^s)+\lambda_p\mathcal{L}_{pl}(\Omega^u)+\lambda_c\mathcal{L}_{cons}+\lambda_r\mathcal{L}_{reg}.
```

### 7. Benchmark writing
Dataset benchmark subsection must include:
- dataset name,
- modality,
- target anatomy/pathology,
- number of cases/images,
- 2D/3D,
- classes,
- scribble annotation protocol,
- split protocol,
- evaluation metrics,
- whether scribbles are manual or simulated,
- common baselines.

Use a LaTeX table:

```latex
\begin{table}[t]
\centering
\caption{Common benchmarks for scribble-supervised medical image segmentation.}
\label{tab:scribble_benchmarks}
\resizebox{\linewidth}{!}{%
\begin{tabular}{lllllll}
\toprule
Dataset & Modality & Target & Cases/images & Scribble protocol & Split & Metrics \\
\midrule
...
\bottomrule
\end{tabular}}
\end{table}
```

## Drafting agent workflow

### 1. WritingPlanAgent
Creates paragraph-level plan:

```yaml
section:
subsection:
paragraph_id:
claim:
papers_to_cite:
evidence_ids:
transition_role:
```

### 2. LiteratureSynthesisAgent
Writes each paragraph from evidence. It must not cite papers not listed in the plan.

### 3. BenchmarkWriterAgent
Writes benchmark subsection and table using `BenchmarkExtractionAgent` outputs.

### 4. LaTeXFormatterAgent
Converts all text to valid LaTeX:
- escapes special characters,
- uses `\cite{}` keys,
- labels sections and tables,
- ensures packages needed: `booktabs`, `multirow`, `graphicx`, `adjustbox` or `resizebox`.

### 5. NoteWriterAgent
Creates `taxonomy_draft_v1_notes.md` containing:
- papers per branch,
- weak evidence areas,
- missing citation keys,
- recommended manual checks,
- possible taxonomy objections from reviewers.

## Acceptance criteria

- All citations are valid BibTeX keys.
- No subsection has only one paper unless marked as emerging trend.
- Benchmark table contains only datasets actually found in the corpus unless user allows external supplementation.
- Draft includes a critical discussion, not only taxonomy description.
- Draft compiles as standalone section when inserted into an `article` or thesis template.


<!-- FILE: 04_refinement_and_finalization_spec.md -->

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


<!-- FILE: 05_agent_architecture_spec.md -->

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


<!-- FILE: 06_data_schemas_spec.md -->

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


<!-- FILE: 07_prompts_spec.md -->

# Prompt Spec for All Agents

This file contains prompt templates. The implementation should store them in `src/prompts/` as Python strings or Jinja templates.

## Global system prompt for extraction agents

```text
You are a meticulous research extraction agent for scribble-supervised medical image segmentation papers.
Your task is to extract only information supported by the provided paper text.
Do not invent datasets, losses, modules, or citations.
When uncertain, write "unknown" and lower the confidence score.
Return valid JSON that matches the provided schema.
Use concise paraphrases for evidence; do not copy long passages.
```

## MethodExtractionAgent prompt

```text
Input:
- Paper metadata if available
- Extracted sections: Abstract, Introduction, Method, Experiments, Conclusion
- JSON schema: PaperExtraction

Task:
Extract the paper's method and evidence for taxonomy construction.
Focus on the following questions:
1. Is this paper genuinely scribble-supervised medical image segmentation?
2. What supervision signal is available: sparse scribbles, simulated scribbles, full masks, unlabeled data, mixed labels?
3. How does the method convert scribbles into learning signal?
4. Does it generate dense pseudo labels? If yes, how?
5. Does it use consistency regularization? At image, feature, network, task, or mixed level?
6. Does it use uncertainty, confidence, entropy, dynamic weighting, or error correction?
7. Does it use contrastive learning, prototypes, feature memory, or clustering?
8. Does it use boundary, shape, topology, anatomical, graph, CRF, or geodesic priors?
9. Does it use adversarial learning, generative modeling, foundation models, or SAM-like models?
10. What datasets, splits, scribble protocols, metrics, and baselines are reported?

Rules:
- Provide at least 5 evidence spans for relevant papers.
- Evidence spans should be short paraphrases with page/section if known.
- Set extraction_confidence between 0 and 1.
- If information is absent, use null or "unknown".
- Do not classify into one final taxonomy branch yet; only provide taxonomy signals.
```

## EvidenceVerifierAgent prompt

```text
You are checking another agent's extraction.
Compare the structured extraction against the paper text.
Mark unsupported claims, missing key mechanisms, and incorrect taxonomy signals.
For each issue, return severity: critical, major, minor.
If the extraction is acceptable, return status "pass".
If not, return corrected fields only.
```

## TaxonomyProposerAgent prompt

```text
You are designing a taxonomy for a literature review on scribble-supervised medical image segmentation.
You receive a matrix of 55 papers with multi-label method signals and evidence summaries.
Propose 2–3 alternative hierarchical taxonomies.

Requirements:
- 5–6 top-level branches unless the evidence strongly suggests otherwise.
- Each branch must have definition, inclusion criteria, exclusion criteria, subbranches, representative papers, limitations, and boundary cases.
- Do not blindly copy semi-supervised taxonomies; adapt them to scribble supervision.
- Explain how each taxonomy would support a strong literature-review narrative.
- Provide coverage statistics and risks.
```

## TaxonomyCriticAgent prompt

```text
You are a strict survey-paper reviewer.
Evaluate the proposed taxonomy candidates.
Focus on:
1. overlap between branches,
2. missing method families,
3. weakly justified categories,
4. whether hybrid is overused,
5. whether the taxonomy is specific to scribble supervision,
6. whether it can support benchmark discussion,
7. whether reviewers could challenge it.

Return a scorecard and recommended candidate.
```

## WritingPlanAgent prompt

```text
Create a paragraph-level writing plan for the selected taxonomy.
For each paragraph, specify claim, papers, evidence IDs, transition role, and target length.
The plan must support a developmental narrative, not a paper-by-paper list.
```

## DraftWriterAgent prompt

```text
Write LaTeX for the planned paragraph.
Use only the supplied evidence IDs and BibTeX keys.
Write in clear academic English suitable for a Q1 journal or thesis.
Avoid unsupported state-of-the-art claims.
Group papers by shared mechanisms.
End major subsections with limitations or transition logic.
Return LaTeX only.
```

## RefinementAgent prompt

```text
Improve the LaTeX draft without changing the citation meaning.
Improve flow, reduce repetition, and strengthen critical analysis.
Do not add new papers unless they are supplied in the evidence context.
Flag any claim that needs manual verification.
```

## CitationGuardAgent prompt

```text
Audit the LaTeX section.
For each paragraph, list:
- main claim,
- cited keys,
- evidence IDs,
- whether the evidence supports the claim.
Return critical issues first.
Do not rewrite unless explicitly asked.
```


<!-- FILE: 08_benchmark_dataset_spec.md -->

# Benchmark and Dataset Extraction/Writing Spec

## Purpose
Create a benchmark subsection analogous to medical SSL surveys, but adapted to scribble-supervised medical image segmentation.

## Required benchmark dimensions
For each dataset used by the 55 papers, extract:

1. Dataset name.
2. Modality: MRI, CT, ultrasound, X-ray, dermoscopy, histopathology, microscopy, etc.
3. Target: organ/pathology/anatomical structure.
4. 2D/3D setting.
5. Number of cases/images/slices.
6. Number of classes.
7. Scribble protocol:
   - manual scribbles,
   - synthetic scribbles generated from full masks,
   - skeleton/centerline scribbles,
   - sparse random line scribbles,
   - unknown.
8. Split protocol:
   - train/val/test,
   - cross-validation,
   - official challenge split,
   - paper-specific split.
9. Metrics:
   - Dice/DSC,
   - IoU/Jaccard,
   - HD/HD95,
   - ASD/ASSD,
   - sensitivity/specificity,
   - boundary F-score if used.
10. Baselines:
   - fully supervised upper bound,
   - scribble-only partial CE baseline,
   - weakly supervised baselines,
   - semi-supervised baselines if included.
11. Preprocessing:
   - resizing,
   - cropping,
   - normalization,
   - resampling,
   - patch size.
12. Public availability and URL if stated.

## Benchmark table types

### Table 1 — Dataset overview
Columns:

```latex
Dataset & Modality & Target & 2D/3D & Cases/images & Scribble protocol & Metrics
```

### Table 2 — Evaluation protocol overview
Columns:

```latex
Dataset & Common split & Labeled pixels / scribble setting & Baseline & Upper bound & Notes
```

### Table 3 — Method-to-benchmark mapping
Columns:

```latex
Method family & Representative papers & Datasets & Metrics & Main evaluation pattern
```

## Benchmark writing structure

```latex
\subsection{Benchmark Datasets and Evaluation Protocols}
Medical scribble-supervised segmentation is evaluated under heterogeneous protocols because many works synthesize scribbles from dense masks rather than collecting manual scribbles. This makes direct comparison difficult. We therefore summarize benchmarks along three axes: imaging modality, scribble-generation protocol, and evaluation metric.

\paragraph{Cardiac MRI benchmarks.} ...
\paragraph{Abdominal organ benchmarks.} ...
\paragraph{Lesion and tumor benchmarks.} ...
\paragraph{Histopathology and microscopy benchmarks.} ...
\paragraph{Evaluation metrics.} ...
\paragraph{Protocol limitations.} ...
```

## Dataset grouping rules

Group by modality/clinical target, not by method, for readability:

1. Cardiac MRI: ACDC, MSCMRseg/MM-WHS if present.
2. Abdominal CT/MRI: Pancreas, LiTS, CHAOS, BTCV, FLARE if present.
3. Brain/tumor MRI: BraTS and related.
4. X-ray/ultrasound: JSRT, chest, fetal, vessel, etc.
5. Dermoscopy/histology/microscopy: ISIC, GlaS, CRAG, nuclei.

Do not invent datasets. If common datasets are not found in the corpus, omit them or put them in a “not observed in this corpus” note only if the user allows external references.

## Quality checks

- Every dataset table cell must cite the paper where it was extracted.
- If two papers report conflicting splits for the same dataset, keep both and mark as protocol variation.
- Distinguish dataset properties from paper-specific experimental protocol.
- Flag synthetic scribble protocols because they can inflate comparability relative to manual scribbles.


<!-- FILE: 09_config_env_api_spec.md -->

# Configuration, API, and Environment Spec

## .env.example

```bash
# OpenAI
OPENAI_API_KEY=your_openai_key_here
OPENAI_MODEL_EXTRACT=gpt-5.5
OPENAI_MODEL_WRITE=gpt-5.5
OPENAI_MODEL_FAST=gpt-5.4-mini

# Gemini
GEMINI_API_KEY=your_gemini_key_here
GEMINI_MODEL_EXTRACT=gemini-3-pro
GEMINI_MODEL_FAST=gemini-3-flash

# Optional external services
SEMANTIC_SCHOLAR_API_KEY=
CROSSREF_MAILTO=
GROBID_URL=http://localhost:8070

# Runtime
CACHE_DIR=.cache
OUTPUT_DIR=outputs
MAX_PAPER_CHUNK_TOKENS=12000
MAX_REPAIR_RETRIES=2
ENABLE_WEB_SEARCH=false
ENABLE_GROBID=false
```

## requirements.txt

```text
pydantic>=2.7
python-dotenv>=1.0
pymupdf>=1.24
pandas>=2.2
numpy>=1.26
pyyaml>=6.0
bibtexparser>=1.4
rich>=13.7
tenacity>=8.2
orjson>=3.10
openai>=2.0.0
google-genai>=1.0.0
langgraph>=0.2.0
scikit-learn>=1.4
rapidfuzz>=3.6
latexcodec>=2.0
```

Make `langgraph` optional if implementing a simple custom workflow.

## Model provider interface

```python
class LLMProvider(Protocol):
    def generate_text(self, prompt: str, *, model: str, temperature: float = 0.2) -> str: ...
    def generate_json(self, prompt: str, schema: dict, *, model: str, temperature: float = 0.0) -> dict: ...
```

## OpenAI client requirements

- Load `OPENAI_API_KEY` from environment.
- Support structured JSON outputs.
- Log model name, token usage, and cost estimate if available.
- Retry transient API errors with exponential backoff.

Pseudo-code:

```python
from openai import OpenAI
client = OpenAI()

response = client.responses.create(
    model=model,
    input=prompt,
    text={
        "format": {
            "type": "json_schema",
            "name": "paper_extraction",
            "schema": schema,
            "strict": True,
        }
    },
)
```

## Gemini client requirements

- Load `GEMINI_API_KEY` from environment.
- Support JSON schema / structured output.
- Use Gemini as verifier/critic or writing alternative.

Pseudo-code:

```python
from google import genai
from google.genai import types
client = genai.Client()

response = client.models.generate_content(
    model=model,
    contents=prompt,
    config=types.GenerateContentConfig(
        response_mime_type="application/json",
        response_schema=schema,
        temperature=0.0,
    ),
)
```

## Routing policy

`configs/models.yaml` should define:

```yaml
routes:
  metadata:
    primary: openai.extract
    verifier: gemini.fast
  method_extraction:
    primary: openai.extract
    verifier: gemini.extract
  benchmark_extraction:
    primary: openai.extract
    verifier: gemini.fast
  taxonomy_proposal:
    primary: openai.write
    critic: gemini.extract
  drafting:
    primary: openai.write
    critic: gemini.extract
  refinement:
    primary: openai.write
    critic: gemini.fast
```

## Caching

Cache key:

```python
sha256(json.dumps({
    "provider": provider,
    "model": model,
    "schema_version": schema_version,
    "prompt": prompt,
    "input_hash": input_hash,
}, sort_keys=True).encode()).hexdigest()
```

Cache files:

```text
.cache/llm/<cache_key>.json
```

## Security

- Never commit `.env`.
- Provide `.env.example` only.
- Do not log API keys.
- Redact keys from exceptions.
- Store paper text locally only.


<!-- FILE: 10_cli_workflow_spec.md -->

# CLI Workflow Spec

## CLI structure

Use `argparse` or `typer`.

```bash
python -m src.main stage1 \
  --literature-dir literature \
  --out outputs \
  --bib literature/references.bib \
  --config configs/models.yaml

python -m src.main stage2 \
  --candidate A \
  --out outputs \
  --target-words 6000

python -m src.main refine \
  --draft outputs/drafts/taxonomy_draft_v1.tex \
  --out outputs

python -m src.main audit \
  --tex outputs/final/taxonomy_final.tex \
  --bib literature/references.bib
```

## Command: `stage1`

### Pipeline
1. Validate input directory.
2. Parse optional BibTeX.
3. Extract text from PDFs.
4. Run metadata extraction.
5. Run method extraction.
6. Run benchmark extraction.
7. Run taxonomy signal tagging.
8. Run verification/repair.
9. Build evidence matrix.
10. Generate taxonomy candidates.
11. Write user-facing candidate report.
12. Stop.

### Required console output

```text
[Stage 1] Found 55 PDFs
[Stage 1] Extracted text: 55/55
[Stage 1] Valid extraction JSON: 53/55
[Stage 1] Failed: 2 (see outputs/evidence/failed_papers.csv)
[Stage 1] Generated 3 candidate taxonomies
[Stage 1] Please review outputs/taxonomy/taxonomy_candidates.md and select A/B/C.
```

## Command: `stage2`

### Pipeline
1. Load selected taxonomy.
2. Apply optional user override.
3. Build writing plan.
4. Write taxonomy sections.
5. Write benchmark section.
6. Generate LaTeX tables.
7. Run citation audit.
8. Write draft notes.

### Required console output

```text
[Stage 2] Selected taxonomy: A
[Stage 2] Writing plan: 42 paragraphs
[Stage 2] Draft created: outputs/drafts/taxonomy_draft_v1.tex
[Stage 2] Citation warnings: 3 (see citation_audit.md)
```

## Command: `refine`

### Pipeline
1. Load draft and evidence.
2. Run taxonomy coherence reviewer.
3. Run evidence grounding reviewer.
4. Run academic style reviewer.
5. Apply safe rewrites.
6. Write refined draft.

## Command: `audit`

### Pipeline
1. Parse all `\cite{}` keys.
2. Check against `.bib`.
3. Map citations to paper extraction evidence.
4. Check table citations.
5. Compile if possible.
6. Write final quality report.

## Error handling

All commands must return non-zero exit code if critical errors occur.

Critical errors:
- input directory missing,
- no PDFs found,
- no valid taxonomy candidates,
- selected candidate missing,
- missing BibTeX for >20% of cited papers,
- LaTeX cannot compile after auto-fix.

Warnings:
- missing dataset split,
- unknown scribble protocol,
- boundary taxonomy case,
- extraction confidence <0.65.


<!-- FILE: 11_quality_control_spec.md -->

# Quality Control and Evaluation Spec

## Why this is needed
A literature-review generation system can easily produce plausible but unsupported taxonomy claims. This project must prioritize traceability and reviewer-defensible synthesis.

## Quality metrics

### Extraction quality
- `metadata_complete_rate`
- `valid_json_rate`
- `evidence_span_count_per_paper`
- `taxonomy_signal_coverage_rate`
- `dataset_extraction_complete_rate`

### Taxonomy quality
- `assigned_primary_rate`
- `unassigned_rate`
- `branch_balance_entropy`
- `boundary_case_rate`
- `avg_papers_per_branch`
- `overlap_score_between_branch_definitions`

### Writing quality
- `citations_per_paragraph`
- `unsupported_claim_count`
- `paragraphs_over_220_words`
- `repetition_score`
- `latex_compile_success`

## Evidence grounding audit

For each paragraph:

```yaml
paragraph_id:
text:
claims:
  - claim:
    cited_papers:
    evidence_ids:
    support: supported|partially_supported|unsupported
    action: keep|weaken|remove|needs_manual_check
```

## Taxonomy overlap audit

For each pair of branches:

```yaml
branch_pair:
shared_papers:
shared_signals:
overlap_reason:
resolution:
```

Possible resolutions:
- Keep as primary/secondary tags.
- Merge branches.
- Rename one branch to clarify scope.
- Move subbranch.
- Mark as hybrid.

## Reviewer simulation checklist

Before finalization, answer:

1. Why is this taxonomy specific to scribble supervision rather than generic SSL?
2. Why are the top-level branches mutually coherent?
3. Why is hybrid not overused?
4. Are graph/CRF/classical propagation methods fairly represented?
5. Are deep learning methods and foundation-model methods separated properly?
6. Are benchmark protocols comparable?
7. Does the writing explain limitations and not only advantages?
8. Does each branch have enough papers to justify being top-level?
9. Are recent papers handled accurately?
10. Are dataset and metric claims grounded?

## Manual review requirements
The user should manually inspect:
- taxonomy candidate choice,
- all boundary cases,
- final benchmark table,
- claims about best-performing methods,
- any papers with extraction confidence below 0.7,
- generated BibTeX keys.

## Red flags

The system should warn if it sees:
- many papers assigned to `hybrid` as primary,
- branch names copied exactly from semi-supervised surveys without scribble-specific adaptation,
- benchmark table mixing full-mask SSL and scribble-supervised protocols,
- a paper cited in a branch but no method evidence supports it,
- a dataset's scribble protocol marked unknown in many papers.


<!-- FILE: tasks/implementation_checklist.md -->

# Implementation Checklist for Coding Agent

## Phase 0 — Setup
- [ ] Create repository layout.
- [ ] Add `.env.example`, `requirements.txt`, configs.
- [ ] Implement config loader.
- [ ] Implement logging and cache utilities.

## Phase 1 — Data ingestion
- [ ] PDF listing and hashing.
- [ ] PyMuPDF extraction.
- [ ] Section segmentation.
- [ ] Figure caption/table text extraction.
- [ ] BibTeX parsing and title matching.

## Phase 2 — LLM clients
- [ ] OpenAI client.
- [ ] Gemini client.
- [ ] Provider router.
- [ ] JSON schema call wrapper.
- [ ] Retry and repair loop.
- [ ] LLM cache.

## Phase 3 — Extraction agents
- [ ] MetadataAgent.
- [ ] MethodExtractionAgent.
- [ ] BenchmarkExtractionAgent.
- [ ] TaxonomySignalAgent.
- [ ] EvidenceVerifierAgent.
- [ ] Evidence matrix writer.

## Phase 4 — Taxonomy proposal
- [ ] Deterministic signal clustering.
- [ ] TaxonomyProposerAgent.
- [ ] TaxonomyCriticAgent.
- [ ] Candidate report writer.
- [ ] Stop-and-select checkpoint.

## Phase 5 — Drafting
- [ ] WritingPlanAgent.
- [ ] DraftWriterAgent.
- [ ] BenchmarkWriterAgent.
- [ ] LaTeXFormatterAgent.
- [ ] Draft notes writer.

## Phase 6 — Refinement and finalization
- [ ] TaxonomyCoherenceReviewer.
- [ ] EvidenceGroundingReviewer.
- [ ] AcademicStyleReviewer.
- [ ] ReviewerSimulationAgent.
- [ ] CitationGuardAgent.
- [ ] LaTeX compile check.
- [ ] Final quality report.

## Phase 7 — Tests
- [ ] Unit test: PDF extraction on 2 papers.
- [ ] Unit test: BibTeX matching.
- [ ] Unit test: schema validation repair.
- [ ] Integration test: Stage 1 on 3 papers.
- [ ] Integration test: Stage 2 on sample candidate.
- [ ] Audit test: missing citation key detection.
