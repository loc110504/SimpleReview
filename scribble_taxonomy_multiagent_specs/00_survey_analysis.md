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
