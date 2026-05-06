"""
Faction infiltrator detection.

A rep is an infiltrator if their average relationship score
against own faction members is below (1 - infiltrator_threshold).

Shared faction label ≠ safety.
"""
from __future__ import annotations
from collections import defaultdict
from src.models import Representative, RelationshipMatrix


def scan_infiltrators(
    reps: list[Representative],
    matrix: RelationshipMatrix,
    infiltrator_threshold: float = 0.50,
) -> set[str]:
    """
    Returns set of rep_ids flagged as infiltrators.
    """
    # Group by faction
    factions: dict[str, list[str]] = defaultdict(list)
    for rep in reps:
        factions[rep.faction].append(rep.id)

    flagged: set[str] = set()

    for faction, members in factions.items():
        if len(members) < 2:
            # Single-member faction: no intra-faction comparison possible
            continue

        for rep_id in members:
            others = [m for m in members if m != rep_id]
            scores = [matrix.get_score(rep_id, other) for other in others]
            avg_score = sum(scores) / len(scores) if scores else 1.0

            # Flag if avg score against own faction is suspiciously low
            if avg_score < (1.0 - infiltrator_threshold):
                flagged.add(rep_id)

    return flagged
