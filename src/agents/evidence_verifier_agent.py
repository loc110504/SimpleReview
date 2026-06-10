from __future__ import annotations

from ..schemas import AgentResult, PaperExtraction


class EvidenceVerifierAgent:
    def verify(self, extraction: PaperExtraction) -> AgentResult:
        warnings: list[str] = []
        status = "success"
        if len(extraction.evidence_spans) < 5:
            warnings.append("Fewer than 5 evidence spans; manual review recommended.")
        if not any(signal.present for signal in extraction.taxonomy_signals):
            status = "needs_retry"
            warnings.append("No taxonomy signal detected.")
        if extraction.extraction_confidence < 0.65:
            warnings.append("Low extraction confidence.")
        return AgentResult(
            agent_name="EvidenceVerifierAgent",
            status=status,
            payload=extraction.model_dump(mode="json"),
            warnings=warnings,
            evidence_ids=[span.evidence_id for span in extraction.evidence_spans],
        )
