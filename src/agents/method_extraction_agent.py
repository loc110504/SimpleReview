from __future__ import annotations

from .common import (
    boundary_notes,
    build_algorithm_steps,
    build_evidence_spans,
    build_method_summary,
    default_limitations,
    detect_datasets,
    detect_metrics,
    detect_modalities,
    detect_scribble_protocol,
    detect_targets,
    detect_taxonomy_signals,
    summarize_components,
)
from ..llm.router import ModelRouter
from ..schemas import PaperExtraction
from ..schemas.json_schemas import PAPER_EXTRACTION_SCHEMA
from ..utils import stable_text_hash


class MethodExtractionAgent:
    def __init__(self, router: ModelRouter | None = None) -> None:
        self.router = router

    def extract(
        self,
        *,
        paper_id: str,
        filename: str,
        text: str,
        metadata: dict[str, object],
        bibtex_key: str | None = None,
    ) -> PaperExtraction:
        llm_extraction = self._extract_with_router(
            paper_id=paper_id,
            filename=filename,
            text=text,
            metadata=metadata,
            bibtex_key=bibtex_key,
        )
        if llm_extraction is not None:
            return llm_extraction
        evidence_spans = build_evidence_spans(paper_id, text)
        signals = detect_taxonomy_signals(text, evidence_spans)
        scribble_protocol = detect_scribble_protocol(text)
        modalities = detect_modalities(text)
        targets = detect_targets(text)
        metrics = detect_metrics(text)
        datasets = detect_datasets(text, paper_id, scribble_protocol, metrics)
        title = str(metadata.get("title") or filename)
        method_summary = build_method_summary(title, signals, modalities, targets)
        return PaperExtraction(
            paper_id=paper_id,
            filename=filename,
            bibtex_key=bibtex_key,
            title=title,
            authors=list(metadata.get("authors") or []),
            year=metadata.get("year"),
            venue=metadata.get("venue"),
            method_name=title.split(":")[0].strip(),
            annotation_setting="scribble_supervised" if "scribble" in text.lower() else "weakly_supervised_scribble_like",
            scribble_protocol=scribble_protocol,
            task_domain="medical_image_segmentation",
            modality=modalities,
            segmentation_target=targets,
            core_problem="Learn dense medical segmentation from sparse scribble annotations.",
            key_contributions=[
                "Adapts segmentation training to sparse scribble supervision.",
                "Introduces evidence-detected mechanism signals for taxonomy placement.",
            ],
            method_summary=method_summary,
            algorithm_steps=build_algorithm_steps(signals),
            method_components=summarize_components(text, signals),
            taxonomy_signals=signals,
            datasets=datasets,
            metrics=metrics,
            baselines=["fully supervised", "scribble-only partial CE"],
            limitations=default_limitations(signals),
            boundary_case_notes=boundary_notes(signals),
            evidence_spans=evidence_spans,
            extraction_confidence=0.78 if len(evidence_spans) >= 5 else 0.62,
        )

    def _extract_with_router(
        self,
        *,
        paper_id: str,
        filename: str,
        text: str,
        metadata: dict[str, object],
        bibtex_key: str | None,
    ) -> PaperExtraction | None:
        if self.router is None:
            return None
        provider_name, _ = self.router.resolve_route("method_extraction", "primary")
        if provider_name == "heuristic":
            return None
        prompt = (
            "Extract a structured PaperExtraction object for a scribble-supervised medical image segmentation paper.\n"
            "Use only supported evidence from the provided text.\n"
            f"paper_id: {paper_id}\n"
            f"filename: {filename}\n"
            f"seed_metadata: {metadata}\n"
            f"bibtex_key: {bibtex_key}\n"
            "Return valid JSON matching the schema.\n\n"
            "Paper text:\n"
            + text[:20000]
        )
        try:
            payload = self.router.generate_json(
                task_name="method_extraction",
                slot="primary",
                prompt=prompt,
                schema=PAPER_EXTRACTION_SCHEMA,
                schema_version="paper_extraction_v1",
                input_hash=f"{paper_id}:{stable_text_hash(text[:20000])}",
            )
            payload.setdefault("paper_id", paper_id)
            payload.setdefault("filename", filename)
            payload.setdefault("bibtex_key", bibtex_key)
            return PaperExtraction.model_validate(payload)
        except Exception:
            return None
