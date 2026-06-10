# Implementation Checklist for Coding Agent

## Phase 0 — Setup
- [ ] Create repository layout.
- [ ] Add `.env.example`, `requirements.txt`, configs.
- [ ] Implement config loader.
- [ ] Implement logging and cache utilities.

## Phase 1 — Data ingestion
- [ ] PDF listing and hashing.
- [ ] PyMuPDF extraction.
- [ ] Section segmentation.
- [ ] Figure caption/table text extraction.
- [ ] BibTeX parsing and title matching.

## Phase 2 — LLM clients
- [ ] OpenAI client.
- [ ] Gemini client.
- [ ] Provider router.
- [ ] JSON schema call wrapper.
- [ ] Retry and repair loop.
- [ ] LLM cache.

## Phase 3 — Extraction agents
- [ ] MetadataAgent.
- [ ] MethodExtractionAgent.
- [ ] BenchmarkExtractionAgent.
- [ ] TaxonomySignalAgent.
- [ ] EvidenceVerifierAgent.
- [ ] Evidence matrix writer.

## Phase 4 — Taxonomy proposal
- [ ] Deterministic signal clustering.
- [ ] TaxonomyProposerAgent.
- [ ] TaxonomyCriticAgent.
- [ ] Candidate report writer.
- [ ] Stop-and-select checkpoint.

## Phase 5 — Drafting
- [ ] WritingPlanAgent.
- [ ] DraftWriterAgent.
- [ ] BenchmarkWriterAgent.
- [ ] LaTeXFormatterAgent.
- [ ] Draft notes writer.

## Phase 6 — Refinement and finalization
- [ ] TaxonomyCoherenceReviewer.
- [ ] EvidenceGroundingReviewer.
- [ ] AcademicStyleReviewer.
- [ ] ReviewerSimulationAgent.
- [ ] CitationGuardAgent.
- [ ] LaTeX compile check.
- [ ] Final quality report.

## Phase 7 — Tests
- [ ] Unit test: PDF extraction on 2 papers.
- [ ] Unit test: BibTeX matching.
- [ ] Unit test: schema validation repair.
- [ ] Integration test: Stage 1 on 3 papers.
- [ ] Integration test: Stage 2 on sample candidate.
- [ ] Audit test: missing citation key detection.
