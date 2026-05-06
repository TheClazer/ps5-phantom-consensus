"""
Objection weight computation.

raw_weight(P) = Σ severity_i × influence_i   (skip None influence)
normalized_weight(P) = raw_weight / 10000     (max: sev=10 × inf=100 × many reps)
"""
from __future__ import annotations
from src.models import Objection, Representative


def compute_objection_weights(
    objections: list[Objection],
    reps_by_id: dict[str, Representative],
) -> dict[str, float]:
    """
    Returns dict: proposal_id → normalized objection weight [0, 1].
    Proposals with no objections → 0.0.
    """
    raw: dict[str, float] = {}

    for obj in objections:
        rep = reps_by_id.get(obj.rep_id)
        if rep is None or rep.influence is None:
            continue
        weight = obj.severity * rep.influence
        raw[obj.proposal_id] = raw.get(obj.proposal_id, 0.0) + weight

    # Normalize by theoretical max (severity=10, influence=100 → 1000 per objector)
    # We normalize by 10000 to keep values in [0,1] for typical cases
    return {pid: min(1.0, w / 10000.0) for pid, w in raw.items()}
