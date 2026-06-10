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
