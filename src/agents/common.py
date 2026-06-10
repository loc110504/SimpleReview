from __future__ import annotations

import re
from collections import Counter
from pathlib import Path
from typing import Iterable

from ..knowledge import ARCHITECTURE_HINTS, DATASET_PATTERNS, METRIC_HINTS, MODALITY_HINTS, SIGNAL_RULES, TARGET_HINTS
from ..schemas import DatasetUse, EvidenceSpan, MethodComponents, PaperExtraction, TaxonomySignal
from ..utils import slugify


def sentence_split(text: str) -> list[str]:
    normalized = re.sub(r"\s+", " ", text)
    parts = re.split(r"(?<=[.!?])\s+", normalized)
    return [part.strip() for part in parts if len(part.strip()) > 20]


def parse_year_and_venue(filename: str) -> tuple[int | None, str | None]:
    match = re.match(r"\[([A-Za-z]+)(\d{4})\]", filename)
    if not match:
        return None, None
    return int(match.group(2)), match.group(1)


def detect_title(text: str, filename: str) -> str:
    for line in text.splitlines():
        line = line.strip()
        if 12 <= len(line) <= 220 and not line.lower().startswith("abstract"):
            return re.sub(r"\s+", " ", line)
    return Path(filename).stem


def detect_scribble_protocol(text: str) -> str:
    lowered = text.lower()
    if "manual scribble" in lowered or "manually annotated" in lowered:
        return "manual_scribbles"
    if "centerline" in lowered or "skeleton" in lowered:
        return "skeleton_or_centerline"
    if "random line" in lowered:
        return "sparse_random_lines"
    if "generated from full mask" in lowered or "simulated scribble" in lowered or "synthetic scribble" in lowered:
        return "synthetic_scribbles_from_full_masks"
    return "unknown"


def detect_modalities(text: str) -> list[str]:
    lowered = text.lower()
    found = [name for name, hints in MODALITY_HINTS.items() if any(hint in lowered for hint in hints)]
    return found or ["unknown"]


def detect_targets(text: str) -> list[str]:
    lowered = text.lower()
    found = [target for target in TARGET_HINTS if target in lowered]
    return list(dict.fromkeys(found)) or ["unknown"]


def detect_metrics(text: str) -> list[str]:
    lowered = text.lower()
    found = [metric.upper() if metric in {"dsc", "iou"} else metric for metric in METRIC_HINTS if metric in lowered]
    return list(dict.fromkeys(found))


def detect_architecture_terms(text: str) -> list[str]:
    lowered = text.lower()
    found = [term for term in ARCHITECTURE_HINTS if term in lowered]
    return list(dict.fromkeys(found))


def detect_datasets(text: str, paper_id: str, scribble_protocol: str, metrics: list[str]) -> list[DatasetUse]:
    lowered = text.lower()
    datasets: list[DatasetUse] = []
    for name, patterns in DATASET_PATTERNS.items():
        if any(pattern in lowered for pattern in patterns):
            datasets.append(
                DatasetUse(
                    dataset_name=name,
                    role="main_benchmark",
                    modality=detect_modalities(text)[0],
                    target=", ".join(detect_targets(text)[:2]),
                    dimensionality="3D" if "3d" in lowered else ("2.5D" if "2.5d" in lowered else ("2D" if "2d" in lowered else "unknown")),
                    scribble_protocol=scribble_protocol,
                    metrics=metrics,
                    evidence_ids=[f"{paper_id}_dataset_{slugify(name)}"],
                )
            )
    return datasets


def build_evidence_spans(paper_id: str, text: str) -> list[EvidenceSpan]:
    sentences = sentence_split(text)
    selected: list[str] = []
    seen = set()
    keywords = ("scribble", "pseudo", "consistency", "uncert", "contrastive", "boundary", "shape", "dataset", "dice")
    for sentence in sentences:
        lowered = sentence.lower()
        if any(keyword in lowered for keyword in keywords):
            key = lowered[:120]
            if key not in seen:
                seen.add(key)
                selected.append(sentence)
        if len(selected) >= 8:
            break
    if len(selected) < 5:
        for sentence in sentences[:8]:
            key = sentence.lower()[:120]
            if key not in seen:
                seen.add(key)
                selected.append(sentence)
            if len(selected) >= 5:
                break
    spans: list[EvidenceSpan] = []
    for idx, sentence in enumerate(selected[:8], start=1):
        spans.append(
            EvidenceSpan(
                evidence_id=f"{paper_id}_ev_{idx}",
                paper_id=paper_id,
                section=None,
                page=None,
                text=sentence[:400],
                paraphrase=sentence[:220],
                supports_fields=[],
            )
        )
    return spans


def detect_taxonomy_signals(text: str, evidence_spans: list[EvidenceSpan]) -> list[TaxonomySignal]:
    lowered = text.lower()
    signals: list[TaxonomySignal] = []
    evidence_lookup = {span.evidence_id: span for span in evidence_spans}
    for rule in SIGNAL_RULES:
        matched = [keyword for keyword in rule.keywords if keyword in lowered]
        present = bool(matched)
        evidence_ids = [
            evidence_id
            for evidence_id, span in evidence_lookup.items()
            if any(keyword in span.text.lower() for keyword in matched)
        ]
        signals.append(
            TaxonomySignal(
                signal=rule.signal,
                present=present,
                strength=rule.default_strength if present else "absent",
                reason=f"Matched keywords: {', '.join(matched[:3])}" if present else "No direct keyword evidence found.",
                evidence_ids=evidence_ids[:4],
            )
        )
    return signals


def determine_primary_secondary(signals: list[TaxonomySignal]) -> tuple[str | None, list[str]]:
    ranking = {"primary": 3, "secondary": 2, "weak": 1, "absent": 0}
    present = [signal for signal in signals if signal.present]
    if not present:
        return None, []
    ordered = sorted(present, key=lambda item: (ranking[item.strength], item.signal), reverse=True)
    return ordered[0].signal, [signal.signal for signal in ordered[1:4]]


def summarize_components(text: str, signals: list[TaxonomySignal]) -> MethodComponents:
    lowered = text.lower()
    architectures = detect_architecture_terms(text)
    losses: list[str] = []
    if "cross entropy" in lowered or "partial ce" in lowered:
        losses.append("partial_cross_entropy")
    if "dice loss" in lowered:
        losses.append("dice_loss")
    if "contrastive loss" in lowered:
        losses.append("contrastive_loss")
    if "consistency loss" in lowered:
        losses.append("consistency_loss")
    present_signals = {signal.signal for signal in signals if signal.present}
    return MethodComponents(
        backbone=architectures[0] if architectures else None,
        architecture=architectures,
        modules=[signal.signal for signal in signals if signal.present][:6],
        loss_terms=losses,
        pseudo_label_generation="yes" if "pseudo_label_generation" in present_signals else None,
        consistency_target="feature/prediction" if {"image_consistency", "feature_consistency", "teacher_student"} & present_signals else None,
        reliability_mechanism="uncertainty or reliability filtering" if {"uncertainty_estimation", "confidence_filtering"} & present_signals else None,
        prior_type="structural prior" if {"boundary_prior", "shape_prior", "topology_prior", "graph_crf_prior"} & present_signals else None,
    )


def build_method_summary(title: str, signals: list[TaxonomySignal], modalities: list[str], targets: list[str]) -> str:
    present = [signal.signal.replace("_", " ") for signal in signals if signal.present][:4]
    summary = f"{title} studies scribble-supervised segmentation"
    if modalities and modalities[0] != "unknown":
        summary += f" for {'/'.join(modalities)} data"
    if targets and targets[0] != "unknown":
        summary += f" targeting {', '.join(targets[:2])}"
    if present:
        summary += f", emphasizing {', '.join(present)}."
    else:
        summary += "."
    return summary


def build_algorithm_steps(signals: list[TaxonomySignal]) -> list[str]:
    steps = ["Use sparse scribble pixels as the supervised anchor set."]
    present = {signal.signal for signal in signals if signal.present}
    if "pseudo_label_generation" in present or "label_propagation" in present:
        steps.append("Expand sparse supervision into denser pseudo masks or propagated labels.")
    if {"image_consistency", "feature_consistency", "teacher_student", "task_consistency"} & present:
        steps.append("Regularize unlabeled pixels or views through consistency constraints.")
    if {"uncertainty_estimation", "confidence_filtering", "dynamic_reweighting"} & present:
        steps.append("Suppress unreliable pseudo labels using confidence-aware filtering or weighting.")
    if {"contrastive_learning", "prototype_learning"} & present:
        steps.append("Improve feature discrimination with contrastive or prototype supervision.")
    if {"boundary_prior", "shape_prior", "topology_prior", "graph_crf_prior"} & present:
        steps.append("Inject structural priors to recover boundaries or anatomical plausibility.")
    if {"adversarial_learning", "generative_modeling", "foundation_model"} & present:
        steps.append("Leverage external generative or foundation-model priors to strengthen sparse supervision.")
    return steps


def default_limitations(signals: list[TaxonomySignal]) -> list[str]:
    present = {signal.signal for signal in signals if signal.present}
    limitations: list[str] = []
    if "pseudo_label_generation" in present:
        limitations.append("Pseudo-mask expansion may amplify early prediction errors.")
    if {"image_consistency", "feature_consistency", "teacher_student"} & present:
        limitations.append("Consistency assumptions may fail when perturbations cross anatomical boundaries.")
    if {"uncertainty_estimation", "confidence_filtering"} & present:
        limitations.append("Reliability estimation can be calibration-sensitive.")
    if {"contrastive_learning", "prototype_learning"} & present:
        limitations.append("Representation objectives may be data-hungry relative to scribble-only supervision.")
    if {"boundary_prior", "shape_prior", "topology_prior"} & present:
        limitations.append("Strong priors can hurt unusual anatomies or lesions.")
    if {"foundation_model", "generative_modeling"} & present:
        limitations.append("External priors may reduce reviewer confidence if adaptation details are unclear.")
    return limitations or ["The paper leaves some supervision details under-specified in the extracted text."]


def boundary_notes(signals: list[TaxonomySignal]) -> list[str]:
    counts = Counter(signal.strength for signal in signals if signal.present)
    if counts.get("primary", 0) > 1:
        return ["Multiple primary-strength signals suggest a taxonomy boundary case."]
    return []


def choose_representative_papers(paper_ids: Iterable[str], *, limit: int = 5) -> list[str]:
    return list(dict.fromkeys(paper_ids))[:limit]

