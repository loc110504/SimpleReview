from __future__ import annotations

import argparse
import sys
from pathlib import Path


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Scribble-supervised taxonomy literature review writer")
    subparsers = parser.add_subparsers(dest="command", required=True)

    stage1 = subparsers.add_parser("stage1")
    stage1.add_argument("--literature-dir", default="literature")
    stage1.add_argument("--out", default="outputs")
    stage1.add_argument("--bib", default="literature/references.bib")
    stage1.add_argument("--config", default="configs/models.yaml")

    stage2 = subparsers.add_parser("stage2")
    stage2.add_argument("--candidate", required=True, choices=["A", "B", "C"])
    stage2.add_argument("--out", default="outputs")
    stage2.add_argument("--literature-dir", default="literature")
    stage2.add_argument("--target-words", type=int, default=6000)

    refine = subparsers.add_parser("refine")
    refine.add_argument("--draft", required=True)
    refine.add_argument("--out", default="outputs")
    refine.add_argument("--literature-dir", default="literature")

    audit = subparsers.add_parser("audit")
    audit.add_argument("--tex", required=True)
    audit.add_argument("--out", default="outputs")
    audit.add_argument("--literature-dir", default="literature")
    audit.add_argument("--bib", default="literature/references.bib")

    return parser


def command_stage1(args: argparse.Namespace) -> int:
    from .config import load_runtime_config
    from .io.bibtex_reader import build_bib_lookup, load_bibtex_entries
    from .state import create_workflow_state
    from .workflows.stage1_extract_and_propose import Stage1Workflow

    root_dir = Path.cwd()
    literature_dir = root_dir / args.literature_dir
    if not literature_dir.exists():
        print(f"[Stage 1] Missing literature directory: {literature_dir}", file=sys.stderr)
        return 1
    config = load_runtime_config(root_dir=root_dir, output_dir=root_dir / args.out, models_path=root_dir / args.config)
    state = create_workflow_state(literature_dir=literature_dir, output_dir=config.output_dir)
    bib_lookup = build_bib_lookup(load_bibtex_entries(root_dir / args.bib))
    workflow = Stage1Workflow(config)
    state = workflow.run(state, bib_lookup=bib_lookup)
    failed_count = 0
    failed_csv = config.output_dir / "evidence" / "failed_papers.csv"
    if failed_csv.exists():
        failed_count = max(sum(1 for _ in failed_csv.open("r", encoding="utf-8")) - 1, 0)
    print(f"[Stage 1] Found {len(state.papers)} PDFs")
    print(f"[Stage 1] Extracted text: {len(state.papers)}/{len(state.papers)}")
    print(f"[Stage 1] Valid extraction JSON: {len(state.extractions)}/{len(state.papers)}")
    print(f"[Stage 1] Failed: {failed_count} (see outputs/evidence/failed_papers.csv)")
    print(f"[Stage 1] Generated {len(state.taxonomy_candidates)} candidate taxonomies")
    print("[Stage 1] Please review outputs/taxonomy/taxonomy_candidates.md and select A/B/C.")
    return 0 if state.taxonomy_candidates else 1


def command_stage2(args: argparse.Namespace) -> int:
    from .config import load_runtime_config
    from .workflows.stage2_write_and_refine import Stage2Workflow, load_stage_state

    root_dir = Path.cwd()
    config = load_runtime_config(root_dir=root_dir, output_dir=root_dir / args.out)
    state = load_stage_state(output_dir=config.output_dir, literature_dir=root_dir / args.literature_dir)
    workflow = Stage2Workflow(config)
    state = workflow.run(state, candidate_id=args.candidate, target_word_count=args.target_words)
    print(f"[Stage 2] Selected taxonomy: {state.selected_taxonomy_id}")
    print(f"[Stage 2] Writing plan: {len(state.writing_plan.paragraph_plans) if state.writing_plan else 0} paragraphs")
    print(f"[Stage 2] Draft created: {state.drafts['draft_v1']}")
    audit_path = state.audits.get("citation_audit")
    warning_count = 0
    if audit_path and audit_path.exists():
        warning_count = sum(1 for line in audit_path.read_text(encoding="utf-8").splitlines() if line.startswith("- Critical"))
    print(f"[Stage 2] Citation warnings: {warning_count} (see {audit_path.name if audit_path else 'citation_audit.md'})")
    return 0


def command_refine(args: argparse.Namespace) -> int:
    from .config import load_runtime_config

    root_dir = Path.cwd()
    config = load_runtime_config(root_dir=root_dir, output_dir=root_dir / args.out)
    draft_path = root_dir / args.draft
    if not draft_path.exists():
        print(f"[Refine] Missing draft file: {draft_path}", file=sys.stderr)
        return 1
    from .agents.refinement_agent import RefinementAgent

    refined_text = RefinementAgent().refine(draft_path.read_text(encoding="utf-8"))
    refined_path = config.output_dir / "drafts" / "taxonomy_draft_v2_refined.tex"
    refined_path.parent.mkdir(parents=True, exist_ok=True)
    refined_path.write_text(refined_text, encoding="utf-8")
    final_path = config.output_dir / "final" / "taxonomy_final.tex"
    final_path.parent.mkdir(parents=True, exist_ok=True)
    final_path.write_text(refined_text, encoding="utf-8")
    print(f"[Refine] Refined draft created: {refined_path}")
    print(f"[Refine] Final section created: {final_path}")
    return 0


def command_audit(args: argparse.Namespace) -> int:
    from .workflows.audit import run_audit

    root_dir = Path.cwd()
    output_dir = root_dir / args.out
    tex_path = root_dir / args.tex
    if not tex_path.exists():
        print(f"[Audit] Missing tex file: {tex_path}", file=sys.stderr)
        return 1
    audit_text, diagnostics = run_audit(tex_path=tex_path, papers_dir=output_dir / "papers")
    audit_path = output_dir / "final" / "citation_audit.md"
    audit_path.parent.mkdir(parents=True, exist_ok=True)
    audit_path.write_text(audit_text, encoding="utf-8")
    print(f"[Audit] Citation audit written: {audit_path}")
    print(f"[Audit] Missing keys: {diagnostics.get('missing_keys', 0)}")
    return 0 if diagnostics.get("missing_keys", 0) == 0 else 1


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    try:
        if args.command == "stage1":
            return command_stage1(args)
        if args.command == "stage2":
            return command_stage2(args)
        if args.command == "refine":
            return command_refine(args)
        if args.command == "audit":
            return command_audit(args)
        parser.error(f"Unsupported command: {args.command}")
        return 1
    except Exception as exc:
        print(str(exc), file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
