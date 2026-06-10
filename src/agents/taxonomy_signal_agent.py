from __future__ import annotations

from ..schemas import PaperExtraction


class TaxonomySignalAgent:
    def normalize(self, extraction: PaperExtraction) -> PaperExtraction:
        present = [signal for signal in extraction.taxonomy_signals if signal.present]
        if not present and extraction.taxonomy_signals:
            extraction.taxonomy_signals[0].present = True
            extraction.taxonomy_signals[0].strength = "weak"
            extraction.taxonomy_signals[0].reason = "Fallback weak signal assigned to avoid unclassified paper."
        return extraction
