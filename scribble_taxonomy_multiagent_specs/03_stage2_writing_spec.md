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
