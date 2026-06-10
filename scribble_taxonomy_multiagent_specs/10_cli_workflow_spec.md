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
