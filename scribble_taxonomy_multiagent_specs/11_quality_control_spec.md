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
