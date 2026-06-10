from __future__ import annotations

from dataclasses import MISSING, asdict, dataclass, field, fields
from pathlib import Path
from typing import Any, Literal, Union, get_args, get_origin, get_type_hints


def Field(*, default: Any = MISSING, default_factory: Any = MISSING) -> Any:
    kwargs: dict[str, Any] = {}
    if default is not MISSING:
        kwargs["default"] = default
    if default_factory is not MISSING:
        kwargs["default_factory"] = default_factory
    return field(**kwargs)


class ModelMixin:
    @classmethod
    def model_validate(cls, payload: Any):
        if isinstance(payload, cls):
            return payload
        if not isinstance(payload, dict):
            raise TypeError(f"{cls.__name__}.model_validate expected dict, got {type(payload)!r}")
        hints = get_type_hints(cls)
        kwargs = {}
        for info in fields(cls):
            value = payload.get(info.name, MISSING)
            if value is MISSING:
                continue
            kwargs[info.name] = _convert_value(value, hints.get(info.name, Any))
        return cls(**kwargs)

    def model_dump(self, mode: str | None = None) -> dict[str, Any]:
        return _dump_value(self)


def _convert_value(value: Any, annotation: Any) -> Any:
    origin = get_origin(annotation)
    args = get_args(annotation)
    if annotation is Any:
        return value
    if origin is Union:
        non_none = [arg for arg in args if arg is not type(None)]
        if value is None:
            return None
        for arg in non_none:
            try:
                return _convert_value(value, arg)
            except Exception:
                continue
        return value
    if origin in {list, list[Any]}:
        item_type = args[0] if args else Any
        return [_convert_value(item, item_type) for item in value or []]
    if origin in {dict, dict[Any, Any]}:
        key_type = args[0] if args else Any
        value_type = args[1] if len(args) > 1 else Any
        return {_convert_value(key, key_type): _convert_value(item, value_type) for key, item in (value or {}).items()}
    if origin is Literal:
        return value
    if annotation is Path:
        return Path(value)
    if isinstance(annotation, type) and issubclass(annotation, ModelMixin):
        return annotation.model_validate(value)
    return value


def _dump_value(value: Any) -> Any:
    if isinstance(value, ModelMixin):
        output = {}
        for info in fields(value):
            output[info.name] = _dump_value(getattr(value, info.name))
        return output
    if isinstance(value, Path):
        return str(value)
    if isinstance(value, list):
        return [_dump_value(item) for item in value]
    if isinstance(value, dict):
        return {key: _dump_value(item) for key, item in value.items()}
    return value


@dataclass
class EvidenceSpan(ModelMixin):
    evidence_id: str
    paper_id: str
    section: str | None = None
    page: int | None = None
    text: str = ""
    paraphrase: str = ""
    supports_fields: list[str] = Field(default_factory=list)


@dataclass
class TaxonomySignal(ModelMixin):
    signal: str
    present: bool
    strength: Literal["primary", "secondary", "weak", "absent"]
    reason: str
    evidence_ids: list[str] = Field(default_factory=list)


@dataclass
class DatasetUse(ModelMixin):
    dataset_name: str
    role: Literal["main_benchmark", "auxiliary", "pretraining", "external_validation", "unknown"]
    modality: str | None = None
    target: str | None = None
    cases_or_images: str | None = None
    dimensionality: Literal["2D", "3D", "2.5D", "mixed", "unknown"] = "unknown"
    num_classes: str | None = None
    split_protocol: str | None = None
    scribble_protocol: str | None = None
    metrics: list[str] = Field(default_factory=list)
    results_summary: str | None = None
    evidence_ids: list[str] = Field(default_factory=list)


@dataclass
class MethodComponents(ModelMixin):
    backbone: str | None = None
    architecture: list[str] = Field(default_factory=list)
    modules: list[str] = Field(default_factory=list)
    loss_terms: list[str] = Field(default_factory=list)
    pseudo_label_generation: str | None = None
    consistency_target: str | None = None
    reliability_mechanism: str | None = None
    prior_type: str | None = None


@dataclass
class PaperExtraction(ModelMixin):
    paper_id: str
    filename: str
    bibtex_key: str | None
    title: str
    authors: list[str] = Field(default_factory=list)
    year: int | None = None
    venue: str | None = None
    method_name: str | None = None
    annotation_setting: str = ""
    scribble_protocol: str = ""
    task_domain: str = ""
    modality: list[str] = Field(default_factory=list)
    segmentation_target: list[str] = Field(default_factory=list)
    core_problem: str = ""
    key_contributions: list[str] = Field(default_factory=list)
    method_summary: str = ""
    algorithm_steps: list[str] = Field(default_factory=list)
    method_components: MethodComponents = Field(default_factory=MethodComponents)
    taxonomy_signals: list[TaxonomySignal] = Field(default_factory=list)
    datasets: list[DatasetUse] = Field(default_factory=list)
    metrics: list[str] = Field(default_factory=list)
    baselines: list[str] = Field(default_factory=list)
    limitations: list[str] = Field(default_factory=list)
    boundary_case_notes: list[str] = Field(default_factory=list)
    evidence_spans: list[EvidenceSpan] = Field(default_factory=list)
    extraction_confidence: float = 0.0


@dataclass
class TaxonomySubbranch(ModelMixin):
    name: str
    definition: str
    inclusion_criteria: list[str] = Field(default_factory=list)
    exclusion_criteria: list[str] = Field(default_factory=list)
    representative_papers: list[str] = Field(default_factory=list)
    boundary_cases: list[str] = Field(default_factory=list)
    rationale: str = ""


@dataclass
class TaxonomyBranch(ModelMixin):
    branch_id: str
    name: str
    definition: str
    inclusion_criteria: list[str] = Field(default_factory=list)
    exclusion_criteria: list[str] = Field(default_factory=list)
    subbranches: list[TaxonomySubbranch] = Field(default_factory=list)
    representative_papers: list[str] = Field(default_factory=list)
    all_assigned_primary: list[str] = Field(default_factory=list)
    all_assigned_secondary: list[str] = Field(default_factory=list)
    limitations: list[str] = Field(default_factory=list)
    transition_to_next: str | None = None


@dataclass
class TaxonomyCandidate(ModelMixin):
    candidate_id: Literal["A", "B", "C"]
    title: str
    rationale: str
    branches: list[TaxonomyBranch] = Field(default_factory=list)
    coverage_statistics: dict[str, Any] = Field(default_factory=dict)
    strengths: list[str] = Field(default_factory=list)
    weaknesses: list[str] = Field(default_factory=list)
    recommended_use: str = ""
    reviewer_risks: list[str] = Field(default_factory=list)


@dataclass
class ParagraphPlan(ModelMixin):
    paragraph_id: str
    latex_location: str
    paragraph_goal: str
    key_claims: list[str] = Field(default_factory=list)
    papers_to_cite: list[str] = Field(default_factory=list)
    evidence_ids: list[str] = Field(default_factory=list)
    required_terms: list[str] = Field(default_factory=list)
    avoid_terms: list[str] = Field(default_factory=list)
    transition_role: Literal[
        "definition",
        "mechanism",
        "evolution",
        "limitation",
        "benchmark",
        "transition",
        "discussion",
    ] = "definition"


@dataclass
class WritingPlan(ModelMixin):
    selected_taxonomy_id: str
    target_word_count: int
    paragraph_plans: list[ParagraphPlan] = Field(default_factory=list)


@dataclass
class PaperRecord(ModelMixin):
    paper_id: str
    filename: str
    path: Path
    file_hash: str
    text_path: Path | None = None
    page_map_path: Path | None = None
    status: Literal["pending", "processed", "failed"] = "pending"


@dataclass
class WorkflowError(ModelMixin):
    paper_id: str | None = None
    stage: str = ""
    message: str = ""
    severity: Literal["warning", "critical"] = "warning"


@dataclass
class AgentResult(ModelMixin):
    agent_name: str
    status: Literal["success", "failed", "needs_retry"]
    payload: dict[str, Any] = Field(default_factory=dict)
    warnings: list[str] = Field(default_factory=list)
    evidence_ids: list[str] = Field(default_factory=list)
    cost_estimate: float | None = None


@dataclass
class WorkflowState(ModelMixin):
    run_id: str
    literature_dir: Path
    output_dir: Path
    papers: list[PaperRecord] = Field(default_factory=list)
    extractions: dict[str, PaperExtraction] = Field(default_factory=dict)
    evidence_matrix_path: Path | None = None
    taxonomy_candidates: list[TaxonomyCandidate] = Field(default_factory=list)
    selected_taxonomy_id: str | None = None
    writing_plan: WritingPlan | None = None
    drafts: dict[str, Path] = Field(default_factory=dict)
    audits: dict[str, Path] = Field(default_factory=dict)
    errors: list[WorkflowError] = Field(default_factory=list)
