from __future__ import annotations

from collections import Counter, defaultdict
from typing import Callable

from ..schemas import PaperExtraction, TaxonomyBranch, TaxonomyCandidate, TaxonomySubbranch


def _signal_strength_rank(value: str) -> int:
    return {"primary": 3, "secondary": 2, "weak": 1, "absent": 0}[value]


class TaxonomyProposerAgent:
    def __init__(self, taxonomy_seed: dict) -> None:
        self.taxonomy_seed = taxonomy_seed

    def propose(self, extractions: dict[str, PaperExtraction]) -> list[TaxonomyCandidate]:
        relevant = {paper_id: extraction for paper_id, extraction in extractions.items() if extraction.annotation_setting != "background_only"}
        return [
            self._build_candidate(
                candidate_id="A",
                title="Mechanism-first taxonomy",
                rationale="Organizes methods by the main learning mechanism that converts sparse scribbles into denser supervision or additional regularization.",
                branch_mapper=self._map_candidate_a,
                extractions=relevant,
            ),
            self._build_candidate(
                candidate_id="B",
                title="Supervision-signal-first taxonomy",
                rationale="Organizes methods by the type of training signal derived from sparse scribbles.",
                branch_mapper=self._map_candidate_b,
                extractions=relevant,
            ),
            self._build_candidate(
                candidate_id="C",
                title="Chronological-evolution taxonomy",
                rationale="Organizes methods by the evolution of scribble-supervised segmentation from propagation-heavy methods to newer reliability, representation, and foundation-assisted methods.",
                branch_mapper=self._map_candidate_c,
                extractions=relevant,
            ),
        ]

    def _build_candidate(
        self,
        *,
        candidate_id: str,
        title: str,
        rationale: str,
        branch_mapper: Callable[[PaperExtraction], str],
        extractions: dict[str, PaperExtraction],
    ) -> TaxonomyCandidate:
        branch_defs = self._branch_catalog(candidate_id)
        branch_to_papers: dict[str, list[str]] = defaultdict(list)
        branch_to_secondary: dict[str, list[str]] = defaultdict(list)
        for paper_id, extraction in extractions.items():
            branch_id = branch_mapper(extraction)
            branch_to_papers[branch_id].append(paper_id)
            for signal in extraction.taxonomy_signals:
                if signal.present and signal.strength in {"secondary", "weak"}:
                    branch_to_secondary[branch_id].append(f"{paper_id}:{signal.signal}")
        branches: list[TaxonomyBranch] = []
        for branch_id, descriptor in branch_defs.items():
            papers = branch_to_papers.get(branch_id, [])
            subbranches = [
                TaxonomySubbranch(
                    name=sub["name"],
                    definition=sub["definition"],
                    inclusion_criteria=sub["inclusion_criteria"],
                    exclusion_criteria=sub["exclusion_criteria"],
                    representative_papers=papers[:3],
                    boundary_cases=[
                        paper_id
                        for paper_id in papers
                        if extractions[paper_id].boundary_case_notes
                    ][:3],
                    rationale=sub["rationale"],
                )
                for sub in descriptor["subbranches"]
            ]
            branches.append(
                TaxonomyBranch(
                    branch_id=branch_id,
                    name=descriptor["name"],
                    definition=descriptor["definition"],
                    inclusion_criteria=descriptor["inclusion_criteria"],
                    exclusion_criteria=descriptor["exclusion_criteria"],
                    subbranches=subbranches,
                    representative_papers=papers[:5],
                    all_assigned_primary=papers,
                    all_assigned_secondary=branch_to_secondary.get(branch_id, []),
                    limitations=descriptor["limitations"],
                    transition_to_next=descriptor["transition_to_next"],
                )
            )
        assigned_primary = sum(len(branch.all_assigned_primary) for branch in branches)
        total = len(extractions)
        hybrid_count = sum(1 for extraction in extractions.values() if len([s for s in extraction.taxonomy_signals if s.present and s.strength == "primary"]) > 1)
        coverage = {
            "total_papers": total,
            "assigned_primary": assigned_primary,
            "assigned_secondary": sum(len(branch.all_assigned_secondary) for branch in branches),
            "unassigned": max(total - assigned_primary, 0),
            "hybrid_count": hybrid_count,
        }
        branch_sizes = [len(branch.all_assigned_primary) for branch in branches if branch.all_assigned_primary]
        strengths = [
            "Preserves scribble-specific mechanism distinctions.",
            "Provides inclusion/exclusion rules for reviewer-defensible grouping.",
        ]
        weaknesses = []
        if branch_sizes and max(branch_sizes) > max(1, total * 0.4):
            weaknesses.append("One branch exceeds the preferred 40% balance threshold and needs manual review.")
        if coverage["unassigned"] > 0:
            weaknesses.append("Some papers remain weakly assigned and should be checked in taxonomy_conflicts.md.")
        recommended_use = "Recommended when the literature review needs clear mechanistic argumentation and developmental transitions."
        return TaxonomyCandidate(
            candidate_id=candidate_id,  # type: ignore[arg-type]
            title=title,
            rationale=rationale,
            branches=branches,
            coverage_statistics=coverage,
            strengths=strengths,
            weaknesses=weaknesses,
            recommended_use=recommended_use,
            reviewer_risks=[
                "Boundary papers with mixed pseudo-labeling and consistency components may need explicit primary/secondary explanation.",
                "Recent foundation-assisted papers should be checked manually for over-generalization.",
            ],
        )

    def _top_signal(self, extraction: PaperExtraction) -> str:
        signals = sorted(
            [signal for signal in extraction.taxonomy_signals if signal.present],
            key=lambda item: (_signal_strength_rank(item.strength), item.signal),
            reverse=True,
        )
        return signals[0].signal if signals else "pseudo_label_generation"

    def _map_candidate_a(self, extraction: PaperExtraction) -> str:
        top = self._top_signal(extraction)
        mapping = {
            "pseudo_label_generation": "pseudo_labeling",
            "label_propagation": "pseudo_labeling",
            "self_training": "pseudo_labeling",
            "co_training": "pseudo_labeling",
            "image_consistency": "consistency",
            "feature_consistency": "consistency",
            "teacher_student": "consistency",
            "task_consistency": "consistency",
            "uncertainty_estimation": "reliability",
            "confidence_filtering": "reliability",
            "dynamic_reweighting": "reliability",
            "scribble_noise_modeling": "reliability",
            "contrastive_learning": "representation",
            "prototype_learning": "representation",
            "feature_memory": "representation",
            "boundary_prior": "structure",
            "shape_prior": "structure",
            "topology_prior": "structure",
            "graph_crf_prior": "structure",
            "adversarial_learning": "generative",
            "generative_modeling": "generative",
            "foundation_model": "generative",
        }
        return mapping.get(top, "pseudo_labeling")

    def _map_candidate_b(self, extraction: PaperExtraction) -> str:
        present = {signal.signal for signal in extraction.taxonomy_signals if signal.present}
        if {"foundation_model", "generative_modeling", "adversarial_learning"} & present:
            return "external_prior"
        if {"boundary_prior", "shape_prior", "topology_prior", "graph_crf_prior"} & present:
            return "structural_signal"
        if {"contrastive_learning", "prototype_learning", "feature_memory"} & present:
            return "feature_signal"
        if {"image_consistency", "feature_consistency", "teacher_student", "task_consistency"} & present:
            return "unlabeled_regularization"
        if {"uncertainty_estimation", "confidence_filtering", "dynamic_reweighting", "scribble_noise_modeling"} & present:
            return "multi_model_or_reliability"
        return "propagated_labels"

    def _map_candidate_c(self, extraction: PaperExtraction) -> str:
        year = extraction.year or 9999
        present = {signal.signal for signal in extraction.taxonomy_signals if signal.present}
        if year <= 2020 and {"label_propagation", "graph_crf_prior"} & present:
            return "classical_propagation"
        if year <= 2021:
            return "scribble_losses"
        if {"pseudo_label_generation", "self_training", "co_training"} & present:
            return "pseudo_mask_refinement"
        if {"image_consistency", "feature_consistency", "teacher_student", "task_consistency"} & present:
            return "consistency_cotraining"
        if {"contrastive_learning", "prototype_learning", "feature_memory"} & present:
            return "representation_learning"
        return "structure_foundation"

    def _branch_catalog(self, candidate_id: str) -> dict[str, dict]:
        catalogs: dict[str, dict[str, dict]] = {
            "A": {
                "pseudo_labeling": {
                    "name": "Scribble-to-dense pseudo-label generation",
                    "definition": "Methods whose main mechanism densifies sparse scribbles into fuller supervisory masks.",
                    "inclusion_criteria": ["Dense pseudo masks or propagated labels drive the main unlabeled-pixel supervision."],
                    "exclusion_criteria": ["Consistency is only auxiliary and does not dominate the learning signal."],
                    "subbranches": [
                        {
                            "name": "Graph-, CRF-, and region-based label propagation",
                            "definition": "Propagation relies on graph affinity, region similarity, or CRF-like smoothing.",
                            "inclusion_criteria": ["Classical propagation signals are explicit."],
                            "exclusion_criteria": ["Propagation is not the dominant mechanism."],
                            "rationale": "Captures the earliest scribble densification lineage.",
                        },
                        {
                            "name": "Self-training and iterative pseudo-mask refinement",
                            "definition": "A network generates and iteratively cleans pseudo masks.",
                            "inclusion_criteria": ["Pseudo-mask updates are repeated across training."],
                            "exclusion_criteria": ["Pseudo labels are static or trivial."],
                            "rationale": "Represents the modern pseudo-mask refinement stream.",
                        },
                    ],
                    "limitations": ["Pseudo masks can introduce confirmation bias when scribble anchors are sparse."],
                    "transition_to_next": "These limits motivate regularizers that stabilize predictions beyond direct pseudo-mask expansion.",
                },
                "consistency": {
                    "name": "Consistency regularization under sparse scribble anchors",
                    "definition": "Methods that constrain predictions, features, or tasks to stay stable while scribbles anchor only a small pixel subset.",
                    "inclusion_criteria": ["Consistency is a primary learning signal on unlabeled pixels or views."],
                    "exclusion_criteria": ["Consistency is only a minor loss around pseudo labels."],
                    "subbranches": [
                        {
                            "name": "Image- and feature-level consistency",
                            "definition": "Perturbed images or feature spaces are aligned.",
                            "inclusion_criteria": ["Image or feature perturbations are explicit."],
                            "exclusion_criteria": ["Only teacher-student EMA is discussed."],
                            "rationale": "Shows how sparse labels are complemented by invariance assumptions.",
                        },
                        {
                            "name": "Network-level and teacher--student consistency",
                            "definition": "Multiple networks or an EMA teacher cross-regularize sparse supervision.",
                            "inclusion_criteria": ["Teacher/student or multi-network consistency exists."],
                            "exclusion_criteria": ["Networks only provide pseudo masks without consistency objectives."],
                            "rationale": "Highlights cross-view reliability under sparse supervision.",
                        },
                    ],
                    "limitations": ["Consistency assumptions can oversmooth errors in structurally ambiguous regions."],
                    "transition_to_next": "This pushes later works to explicitly estimate which pseudo labels are trustworthy.",
                },
                "reliability": {
                    "name": "Reliability-, uncertainty-, and noise-aware learning",
                    "definition": "Methods centered on selecting, weighting, correcting, or denoising unreliable supervision induced by sparse scribbles.",
                    "inclusion_criteria": ["Confidence, entropy, uncertainty, or dynamic trust is the core novelty."],
                    "exclusion_criteria": ["Reliability is only mentioned as a minor heuristic."],
                    "subbranches": [
                        {
                            "name": "Confidence and entropy-based pixel selection",
                            "definition": "Only reliable pixels contribute strongly to supervision.",
                            "inclusion_criteria": ["Confidence filtering or entropy guidance is explicit."],
                            "exclusion_criteria": ["Selection is static and not reliability-aware."],
                            "rationale": "Separates trust modeling from generic pseudo-labeling.",
                        }
                    ],
                    "limitations": ["Reliability estimators can be miscalibrated across datasets or organs."],
                    "transition_to_next": "To go beyond filtering, later works improve feature geometry itself.",
                },
                "representation": {
                    "name": "Representation learning: contrastive and prototype-based approaches",
                    "definition": "Methods that leverage sparse scribbles to shape feature space rather than only densify labels.",
                    "inclusion_criteria": ["Contrastive or prototype objectives define the main contribution."],
                    "exclusion_criteria": ["Representation loss is only a small auxiliary regularizer."],
                    "subbranches": [
                        {
                            "name": "Pixel-level contrastive learning",
                            "definition": "Sparse scribble anchors define positive and negative pixel relations.",
                            "inclusion_criteria": ["Pixel-level contrastive pairs are explicit."],
                            "exclusion_criteria": ["Only prototype averaging is used."],
                            "rationale": "Explains how sparse labels supervise representation geometry.",
                        },
                        {
                            "name": "Region-level and prototype-based representation learning",
                            "definition": "Class prototypes or memory summarize sparse supervision.",
                            "inclusion_criteria": ["Prototypes, centroids, or memory banks appear centrally."],
                            "exclusion_criteria": ["Representation learning is absent."],
                            "rationale": "Captures methods that abstract scribbles into higher-level region cues.",
                        },
                    ],
                    "limitations": ["Representation methods often depend on careful sampling design."],
                    "transition_to_next": "Feature quality alone does not guarantee anatomical plausibility, motivating structural priors.",
                },
                "structure": {
                    "name": "Structure-, boundary-, and anatomy-prior methods",
                    "definition": "Methods that restore information missing from scribbles by injecting boundary, shape, topology, graph, or anatomy priors.",
                    "inclusion_criteria": ["Structural prior information is necessary to the method claim."],
                    "exclusion_criteria": ["Boundary cues are incidental and not central."],
                    "subbranches": [
                        {
                            "name": "Boundary and signed-distance supervision",
                            "definition": "Boundary-aware losses or distance maps compensate for sparse contour coverage.",
                            "inclusion_criteria": ["Boundary or distance supervision is explicit."],
                            "exclusion_criteria": ["Only pseudo-label smoothing is present."],
                            "rationale": "Matches the scribble-specific lack of boundary annotation.",
                        }
                    ],
                    "limitations": ["Strong priors may underperform on atypical anatomy or pathology."],
                    "transition_to_next": "The newest works instead import stronger external priors from generative or foundation models.",
                },
                "generative": {
                    "name": "Generative, adversarial, and foundation-model-assisted methods",
                    "definition": "Methods that recruit adversarial realism, generative augmentation, or foundation-model priors to enrich sparse supervision.",
                    "inclusion_criteria": ["External priors or generative models are central to supervision expansion."],
                    "exclusion_criteria": ["A pretrained encoder is used but does not shape supervision logic."],
                    "subbranches": [
                        {
                            "name": "Adversarial or generative supervision",
                            "definition": "A generative or adversarial objective refines segmentation realism.",
                            "inclusion_criteria": ["GAN-like or generative training is explicit."],
                            "exclusion_criteria": ["No external prior beyond standard augmentation."],
                            "rationale": "Separates newer external-prior methods from in-model regularization.",
                        },
                        {
                            "name": "Foundation-model-assisted pseudo-mask construction",
                            "definition": "Foundation models provide masks, priors, or initialization for sparse supervision.",
                            "inclusion_criteria": ["SAM or similar models are used materially."],
                            "exclusion_criteria": ["Generic pretrained backbones only."],
                            "rationale": "Captures the recent shift toward stronger pretrained priors.",
                        },
                    ],
                    "limitations": ["These methods raise comparability and reproducibility questions across corpora."],
                    "transition_to_next": None,
                },
            },
            "B": {
                "propagated_labels": {
                    "name": "Propagated labels and pseudo masks",
                    "definition": "Sparse scribbles are converted into denser labels that directly supervise unlabeled pixels.",
                    "inclusion_criteria": ["Pseudo masks or propagated regions dominate supervision."],
                    "exclusion_criteria": ["No densification occurs."],
                    "subbranches": [{"name": "Static propagation", "definition": "One-shot or low-iteration densification.", "inclusion_criteria": ["Single-stage propagation is explicit."], "exclusion_criteria": ["Iterative refinement dominates."], "rationale": "Captures direct label spreading."}],
                    "limitations": ["Label expansion errors can accumulate."],
                    "transition_to_next": "When pseudo labels are insufficient, later methods regularize unlabeled pixels more softly.",
                },
                "unlabeled_regularization": {
                    "name": "Regularization over unlabeled pixels",
                    "definition": "Unlabeled regions are constrained through consistency or invariant prediction targets.",
                    "inclusion_criteria": ["Consistency or unlabeled regularization is primary."],
                    "exclusion_criteria": ["Regularization is incidental."],
                    "subbranches": [{"name": "Teacher-student regularization", "definition": "A teacher stabilizes sparse supervision.", "inclusion_criteria": ["EMA or multi-network training exists."], "exclusion_criteria": ["Teacher only generates pseudo masks."], "rationale": "Shows model-to-model signal transfer."}],
                    "limitations": ["Regularization may blur hard boundaries."],
                    "transition_to_next": "This creates demand for stronger feature-space guidance.",
                },
                "feature_signal": {
                    "name": "Feature-space supervision",
                    "definition": "Sparse scribbles supervise embeddings, prototypes, or memory structures instead of only masks.",
                    "inclusion_criteria": ["Contrastive or prototype learning is central."],
                    "exclusion_criteria": ["No representation objective exists."],
                    "subbranches": [{"name": "Contrastive feature learning", "definition": "Sparse labels define positive and negative relations.", "inclusion_criteria": ["Contrastive pairs are explicit."], "exclusion_criteria": ["Prototype-only methods."], "rationale": "Feature geometry is the main signal."}],
                    "limitations": ["Representation quality depends on sampling and augmentation."],
                    "transition_to_next": "Feature discrimination alone does not recover missing anatomical structure.",
                },
                "structural_signal": {
                    "name": "Structural and boundary supervision",
                    "definition": "Sparse scribbles are complemented by boundary, distance, shape, or topology constraints.",
                    "inclusion_criteria": ["Structural prior is explicit."],
                    "exclusion_criteria": ["Only generic smoothness exists."],
                    "subbranches": [{"name": "Boundary-aware signals", "definition": "Boundary cues compensate for missing contour detail.", "inclusion_criteria": ["Boundary maps or edges are learned."], "exclusion_criteria": ["No boundary-targeted loss."], "rationale": "Scribbles underspecify contour location."}],
                    "limitations": ["Fixed priors may not fit abnormal cases."],
                    "transition_to_next": "Newer works borrow signals from multiple models or external priors.",
                },
                "multi_model_or_reliability": {
                    "name": "Multi-model supervision and reliability control",
                    "definition": "Sparse supervision is filtered, cross-checked, or reweighted using multiple predictions or uncertainty cues.",
                    "inclusion_criteria": ["Reliability or ensemble agreement is central."],
                    "exclusion_criteria": ["Only one model with plain pseudo masks."],
                    "subbranches": [{"name": "Confidence-controlled supervision", "definition": "Only high-trust predictions are reinforced.", "inclusion_criteria": ["Confidence or uncertainty filtering exists."], "exclusion_criteria": ["No explicit trust estimation."], "rationale": "Reliability becomes a supervision signal itself."}],
                    "limitations": ["Calibration quality can vary across datasets."],
                    "transition_to_next": "External priors provide an alternative to internal trust heuristics.",
                },
                "external_prior": {
                    "name": "External prior and foundation-model supervision",
                    "definition": "External generative or foundation priors provide additional structure beyond the sparse scribbles.",
                    "inclusion_criteria": ["SAM, generative, or adversarial prior shapes the supervision pathway."],
                    "exclusion_criteria": ["Only standard pretrained encoder transfer."],
                    "subbranches": [{"name": "Foundation-guided supervision", "definition": "Foundation models bootstrap pseudo masks or priors.", "inclusion_criteria": ["Foundation model role is explicit."], "exclusion_criteria": ["Foundation model mention is incidental."], "rationale": "Represents the newest supervision source in the corpus."}],
                    "limitations": ["External priors complicate fairness and reproducibility."],
                    "transition_to_next": None,
                },
            },
            "C": {
                "classical_propagation": {
                    "name": "Classical graph/CRF/random-walk propagation",
                    "definition": "Early methods expand scribbles with classical affinity or probabilistic propagation.",
                    "inclusion_criteria": ["Graph, CRF, or random-walk propagation is explicit."],
                    "exclusion_criteria": ["Deep pseudo-mask pipelines dominate."],
                    "subbranches": [{"name": "Affinity-based propagation", "definition": "Low-level similarity guides label spread.", "inclusion_criteria": ["Classical propagation terms are present."], "exclusion_criteria": ["Propagation is learned end-to-end."], "rationale": "Represents the pre-deep baseline family."}],
                    "limitations": ["Low-level affinity is brittle near weak boundaries."],
                    "transition_to_next": "Deep networks replaced hand-crafted propagation with learned scribble losses and dense predictors.",
                },
                "scribble_losses": {
                    "name": "CNN scribble losses and partial cross entropy",
                    "definition": "Methods train CNNs directly on sparse scribble pixels with partial losses and weak regularizers.",
                    "inclusion_criteria": ["Scribble-only loss design is central."],
                    "exclusion_criteria": ["Iterative pseudo-mask refinement dominates."],
                    "subbranches": [{"name": "Partial-label training", "definition": "Sparse pixels drive a direct segmentation loss.", "inclusion_criteria": ["Partial CE or equivalent exists."], "exclusion_criteria": ["Pseudo-mask training dominates."], "rationale": "Captures the direct deep-learning baseline."}],
                    "limitations": ["Sparse direct supervision leaves most pixels weakly constrained."],
                    "transition_to_next": "This gap encouraged pseudo-mask refinement and self-training.",
                },
                "pseudo_mask_refinement": {
                    "name": "Pseudo-mask refinement and self-training",
                    "definition": "Methods iteratively expand and clean pseudo masks derived from sparse scribbles.",
                    "inclusion_criteria": ["Pseudo-mask updates are iterative or self-training based."],
                    "exclusion_criteria": ["Consistency dominates instead of densification."],
                    "subbranches": [{"name": "Iterative self-training", "definition": "Pseudo masks are regenerated and refined across training.", "inclusion_criteria": ["Iterative refinement exists."], "exclusion_criteria": ["One-shot propagation only."], "rationale": "Captures the central densification trend."}],
                    "limitations": ["Confirmation bias becomes a major failure mode."],
                    "transition_to_next": "Consistency and co-training emerged to stabilize these noisy masks.",
                },
                "consistency_cotraining": {
                    "name": "Consistency, teacher-student, and co-training",
                    "definition": "Multiple views or models cross-regularize sparse supervision.",
                    "inclusion_criteria": ["Consistency or co-training is explicit."],
                    "exclusion_criteria": ["Only densification exists."],
                    "subbranches": [{"name": "Cross-view stabilization", "definition": "Different views or networks align predictions.", "inclusion_criteria": ["View or model consistency exists."], "exclusion_criteria": ["No cross-view constraint."], "rationale": "Addresses instability from sparse supervision."}],
                    "limitations": ["Cross-view agreement can reinforce shared errors."],
                    "transition_to_next": "Later works target richer representations and explicit reliability control.",
                },
                "representation_learning": {
                    "name": "Representation, contrastive, and prototype learning",
                    "definition": "Feature-space learning becomes a primary route for handling sparse supervision.",
                    "inclusion_criteria": ["Contrastive or prototype logic is central."],
                    "exclusion_criteria": ["No feature-space contribution."],
                    "subbranches": [{"name": "Prototype-centered learning", "definition": "Sparse labels define class prototypes or feature memories.", "inclusion_criteria": ["Prototype or memory terms exist."], "exclusion_criteria": ["Only direct pseudo masks."], "rationale": "Feature geometry becomes the main lever."}],
                    "limitations": ["Feature objectives may be harder to interpret clinically."],
                    "transition_to_next": "Recent methods reintroduce structural priors or import powerful pretrained priors.",
                },
                "structure_foundation": {
                    "name": "Structure-aware and foundation-model-enhanced methods",
                    "definition": "Recent works combine boundary/shape priors with stronger external pretrained priors.",
                    "inclusion_criteria": ["Structural or foundation priors dominate the novelty."],
                    "exclusion_criteria": ["Older propagation-only logic."],
                    "subbranches": [{"name": "Boundary/foundation hybrids", "definition": "Boundary-aware learning is strengthened with newer priors.", "inclusion_criteria": ["Boundary or foundation terms are explicit."], "exclusion_criteria": ["No structural or external prior exists."], "rationale": "Captures the recent convergence of stronger priors."}],
                    "limitations": ["These papers can overlap with earlier families and need careful explanation."],
                    "transition_to_next": None,
                },
            },
        }
        return catalogs[candidate_id]
