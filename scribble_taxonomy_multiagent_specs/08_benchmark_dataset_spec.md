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
