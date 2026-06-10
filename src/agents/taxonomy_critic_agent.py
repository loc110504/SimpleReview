from __future__ import annotations

from collections import Counter

from ..schemas import TaxonomyCandidate


class TaxonomyCriticAgent:
    def critique(self, candidates: list[TaxonomyCandidate]) -> tuple[str, dict[str, dict[str, int]]]:
        scorecard: dict[str, dict[str, int]] = {}
        best_id = candidates[0].candidate_id
        best_score = -1
        for candidate in candidates:
            branch_sizes = [len(branch.all_assigned_primary) for branch in candidate.branches]
            overlap_penalty = sum(1 for branch in candidate.branches if len(branch.all_assigned_primary) == 0)
            max_branch = max(branch_sizes) if branch_sizes else 0
            scores = {
                "coverage": 5 if candidate.coverage_statistics.get("unassigned", 0) == 0 else 3,
                "branch_balance": 5 if max_branch <= max(1, int(candidate.coverage_statistics.get("total_papers", 1) * 0.4)) else 2,
                "scribble_specificity": 4,
                "writing_potential": 5 if all(branch.transition_to_next or branch is candidate.branches[-1] for branch in candidate.branches) else 3,
                "reviewer_defensibility": 5 - min(overlap_penalty, 3),
            }
            total = sum(scores.values())
            scorecard[candidate.candidate_id] = scores
            if total > best_score:
                best_score = total
                best_id = candidate.candidate_id
        return best_id, scorecard
