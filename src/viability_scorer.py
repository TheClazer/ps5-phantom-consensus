"""
Proposal viability scoring.

controversy_threshold = 0.6 × max(obj_weights)
controversy(P) = min(1.0, obj_weight(P) / controversy_threshold)
viability(P) = (priority / 10) × (1 - controversy)

Poison Pill proposals: high priority + high objection → low viability.
"""
from __future__ import annotations
from src.models import Proposal


def compute_viability_scores(
    proposals: list[Proposal],
    obj_weights: dict[str, float],
) -> dict[str, float]:
    """
    Returns dict: proposal_id → viability score [0, 1].
    """
    if not obj_weights:
        # No objections → viability = priority / 10
        return {p.id: p.priority / 10.0 for p in proposals}

    max_weight = max(obj_weights.values())
    controversy_threshold = 0.6 * max_weight if max_weight > 0 else 1.0

    result: dict[str, float] = {}
    for p in proposals:
        w = obj_weights.get(p.id, 0.0)
        controversy = min(1.0, w / controversy_threshold) if controversy_threshold > 0 else 0.0
        viability = (p.priority / 10.0) * (1.0 - controversy)
        result[p.id] = max(0.0, min(1.0, viability))

    return result
