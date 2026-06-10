from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class SignalRule:
    signal: str
    keywords: tuple[str, ...]
    default_strength: str


SIGNAL_RULES: tuple[SignalRule, ...] = (
    SignalRule("pseudo_label_generation", ("pseudo label", "pseudo-label", "pseudo mask", "pseudo-mask"), "primary"),
    SignalRule("label_propagation", ("random walk", "propagation", "graph cut", "label propagation"), "secondary"),
    SignalRule("self_training", ("self-training", "iterative refinement", "refinement"), "secondary"),
    SignalRule("co_training", ("co-training", "mutual", "dual branch", "triple branch"), "secondary"),
    SignalRule("image_consistency", ("consistency", "perturbation", "consistency regularization"), "secondary"),
    SignalRule("feature_consistency", ("feature consistency", "feature alignment", "feature perturbation"), "secondary"),
    SignalRule("teacher_student", ("teacher-student", "mean teacher", "ema teacher"), "secondary"),
    SignalRule("task_consistency", ("multi-task", "task consistency"), "weak"),
    SignalRule("uncertainty_estimation", ("uncertainty", "bayesian", "entropy"), "primary"),
    SignalRule("confidence_filtering", ("confidence", "reliable", "reliability"), "primary"),
    SignalRule("dynamic_reweighting", ("reweight", "curriculum", "dynamic weighting"), "secondary"),
    SignalRule("scribble_noise_modeling", ("noise", "noisy label", "error correction"), "secondary"),
    SignalRule("contrastive_learning", ("contrastive", "negative pair", "positive pair"), "primary"),
    SignalRule("prototype_learning", ("prototype", "prototypical", "centroid"), "primary"),
    SignalRule("feature_memory", ("memory bank", "feature memory"), "secondary"),
    SignalRule("boundary_prior", ("boundary", "edge", "signed distance", "distance map"), "primary"),
    SignalRule("shape_prior", ("shape prior", "shape", "size prior"), "primary"),
    SignalRule("topology_prior", ("topology", "topological"), "primary"),
    SignalRule("graph_crf_prior", ("crf", "graph", "geodesic"), "secondary"),
    SignalRule("adversarial_learning", ("adversarial", "discriminator", "gan"), "primary"),
    SignalRule("generative_modeling", ("generative", "diffusion", "augmentation"), "primary"),
    SignalRule("foundation_model", ("foundation model", "sam", "segment anything", "pretrained vision foundation"), "primary"),
)


DATASET_PATTERNS: dict[str, tuple[str, ...]] = {
    "ACDC": ("acdc",),
    "BraTS": ("brats", "brain tumor segmentation"),
    "CHAOS": ("chaos",),
    "LiTS": ("lits", "liver tumor segmentation"),
    "BTCV": ("btcv",),
    "FLARE": ("flare",),
    "ISIC": ("isic",),
    "GlaS": ("glas",),
    "CRAG": ("crag",),
    "DRIVE": ("drive",),
    "CHASE_DB1": ("chase_db1", "chase db1"),
    "STARE": ("stare",),
    "JSRT": ("jsrt",),
    "BUSI": ("busi",),
    "MM-WHS": ("mm-whs", "mmwhs"),
}


MODALITY_HINTS: dict[str, tuple[str, ...]] = {
    "MRI": ("mri", "magnetic resonance"),
    "CT": ("ct", "computed tomography"),
    "Ultrasound": ("ultrasound", "sonography"),
    "X-ray": ("x-ray", "xray", "radiograph"),
    "Dermoscopy": ("dermoscopy", "skin lesion"),
    "Histopathology": ("histology", "histopathology"),
    "Microscopy": ("microscopy", "microscopic"),
}


TARGET_HINTS: tuple[str, ...] = (
    "tumor",
    "brain",
    "cardiac",
    "myocardium",
    "atrium",
    "liver",
    "pancreas",
    "vessel",
    "lesion",
    "uterus",
    "organ",
    "ultrasound",
    "skin",
    "colon",
)


METRIC_HINTS: tuple[str, ...] = ("dice", "dsc", "iou", "jaccard", "hd95", "asd", "assd", "sensitivity", "specificity")


ARCHITECTURE_HINTS: tuple[str, ...] = (
    "unet",
    "u-net",
    "mamba",
    "transformer",
    "cnn",
    "vit",
    "gan",
    "sam",
)
