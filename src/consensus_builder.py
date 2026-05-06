"""
Consensus builder.

Bounded combinatorial optimization: for p ≤ 30, we enumerate all combinations
up to k=3, selecting the combination with maximum total viability. This
guarantees exact global optimum while keeping runtime tractable (O(p³)
worst-case, ~4,000 combinations at p=30).

For p > 30: greedy fallback (top-3 by viability).

Objectors to selected proposals are EXCLUDED from supporting_reps.

Determinism: combination enumeration order is fixed by proposal ordering.
Identical inputs always produce identical consensus.
"""
from __future__ import annotations
from itertools import combinations
from src.models import Proposal, Representative, Objection


def build_consensus(
    proposals: list[Proposal],
    safe_reps: list[Representative],
    viability_scores: dict[str, float],
    objections: list[Objection],
    viability_min: float,
) -> dict:
    """
    Returns:
      {
        "selected_proposals": [prop_id, ...],
        "supporting_representatives": [rep_id, ...],
      }
    """
    # Filter to viable proposals only
    viable = [p for p in proposals if viability_scores.get(p.id, 0.0) >= viability_min]

    if not viable:
        # Fallback: take the single highest-viability proposal regardless of threshold
        if proposals:
            best = max(proposals, key=lambda p: viability_scores.get(p.id, 0.0))
            viable = [best]
        else:
            return {"selected_proposals": [], "supporting_representatives": []}

    # Select best combination
    selected: list[Proposal] = _select_proposals(viable, viability_scores)

    # Build objector set for selected proposals
    selected_ids = {p.id for p in selected}
    objectors: set[str] = {
        o.rep_id for o in objections if o.proposal_id in selected_ids
    }

    # Supporting reps: safe reps who are NOT objectors, sorted by influence desc
    supporters = [
        r for r in safe_reps if r.id not in objectors
    ]
    supporters.sort(key=lambda r: r.influence or 0, reverse=True)

    return {
        "selected_proposals": sorted(selected_ids),
        "supporting_representatives": [r.id for r in supporters],
    }


def _select_proposals(
    viable: list[Proposal],
    viability_scores: dict[str, float],
) -> list[Proposal]:
    """Exact enumeration for p<=30, greedy fallback otherwise."""
    if not viable:
        return []

    if len(viable) <= 30:
        best_combo: tuple[Proposal, ...] = (viable[0],)
        best_score: float = viability_scores.get(viable[0].id, 0.0)

        max_k = min(3, len(viable))
        for k in range(1, max_k + 1):
            for combo in combinations(viable, k):
                score = sum(viability_scores.get(p.id, 0.0) for p in combo)
                if score > best_score:
                    best_score = score
                    best_combo = combo

        return list(best_combo)
    else:
        # Greedy fallback
        sorted_viable = sorted(
            viable,
            key=lambda p: viability_scores.get(p.id, 0.0),
            reverse=True,
        )
        return sorted_viable[:3]
