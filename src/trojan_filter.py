"""
Trojan Horse detection.

A rep is a Trojan if:
  max(betrayal_prob outgoing) > trojan_betrayal_threshold
  AND influence > trojan_influence_threshold

Uses raw betrayal_prob (not derived score) for detection signal.
"""
from __future__ import annotations
from src.models import Representative, Relationship


def _max_betrayal(rep_id: str, relationships: list[Relationship]) -> float:
    probs = [r.betrayal_prob for r in relationships if r.from_rep == rep_id]
    return max(probs) if probs else 0.0


def is_trojan(
    rep: Representative,
    relationships: list[Relationship],
    trojan_betrayal_threshold: float,
    trojan_influence_threshold: float,
) -> bool:
    if rep.influence is None:
        return False
    mb = _max_betrayal(rep.id, relationships)
    return mb > trojan_betrayal_threshold and rep.influence > trojan_influence_threshold


def filter_trojans(
    reps: list[Representative],
    relationships: list[Relationship],
    trojan_betrayal_threshold: float,
    trojan_influence_threshold: float,
) -> tuple[list[Representative], list[str]]:
    """
    Returns (safe_reps, trojan_ids).
    """
    safe: list[Representative] = []
    trojans: list[str] = []

    for rep in reps:
        if is_trojan(rep, relationships, trojan_betrayal_threshold, trojan_influence_threshold):
            trojans.append(rep.id)
        else:
            safe.append(rep)

    return safe, trojans
