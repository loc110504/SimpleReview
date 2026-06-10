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
