"""
Data models for Phantom Consensus Engine.
All models are pure dataclasses — no business logic here.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class Representative:
    id: str
    name: str
    faction: str
    influence: Optional[int]  # None if unparseable; imputed downstream


@dataclass
class Proposal:
    id: str
    title: str
    sponsor_id: str
    priority: float  # 0–10


@dataclass
class Objection:
    rep_id: str
    proposal_id: str
    severity: float  # 0–10, clamped


@dataclass
class Relationship:
    from_rep: str
    to_rep: str
    trust: float        # 0–100
    betrayal_prob: float  # 0–1


@dataclass
class RelationshipMatrix:
    rep_ids: list[str]
    scores: object  # np.ndarray shape (n, n) float64
    # index map for O(1) lookup
    index: dict[str, int] = field(default_factory=dict)

    def __post_init__(self) -> None:
        self.index = {rid: i for i, rid in enumerate(self.rep_ids)}

    def get_score(self, a: str, b: str) -> float:
        ia = self.index.get(a)
        ib = self.index.get(b)
        if ia is None or ib is None:
            return 0.0
        return float(self.scores[ia, ib])
