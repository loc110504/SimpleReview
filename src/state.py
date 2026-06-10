from __future__ import annotations

from pathlib import Path
from uuid import uuid4

from .schemas import WorkflowState


def create_workflow_state(*, literature_dir: Path, output_dir: Path) -> WorkflowState:
    return WorkflowState(
        run_id=uuid4().hex[:12],
        literature_dir=literature_dir,
        output_dir=output_dir,
    )
