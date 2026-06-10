from __future__ import annotations

from ..schemas import DatasetUse, PaperExtraction


class BenchmarkExtractionAgent:
    def enrich(self, extraction: PaperExtraction) -> PaperExtraction:
        if extraction.datasets:
            return extraction
        extraction.datasets = [
            DatasetUse(
                dataset_name="unknown",
                role="unknown",
                modality=extraction.modality[0] if extraction.modality else None,
                target=", ".join(extraction.segmentation_target[:2]),
                dimensionality="unknown",
                scribble_protocol=extraction.scribble_protocol,
                metrics=extraction.metrics,
                evidence_ids=[span.evidence_id for span in extraction.evidence_spans[:1]],
            )
        ]
        return extraction
