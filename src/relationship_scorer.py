"""
Relationship scoring + Floyd-Warshall transitive risk propagation.

score(A→B) = trust × (1 - betrayal_prob) / 100
Transitive risk via vectorized Floyd-Warshall.
"""
from __future__ import annotations
import numpy as np
from src.models import Relationship, RelationshipMatrix


def build_score_matrix(
    relationships: list[Relationship],
    rep_ids: list[str],
) -> RelationshipMatrix:
    """Build n×n score matrix. Missing pairs default to 0.0."""
    n = len(rep_ids)
    index = {rid: i for i, rid in enumerate(rep_ids)}
    scores = np.zeros((n, n), dtype=np.float64)

    for rel in relationships:
        i = index.get(rel.from_rep)
        j = index.get(rel.to_rep)
        if i is None or j is None:
            continue
        raw = rel.trust * (1.0 - rel.betrayal_prob) / 100.0
        scores[i, j] = float(np.clip(raw, 0.0, 1.0))

    return RelationshipMatrix(rep_ids=rep_ids, scores=scores)


def compute_transitive_risk(matrix: RelationshipMatrix) -> RelationshipMatrix:
    """
    Floyd-Warshall on risk domain.
    risk[i][j] = 1 - score[i][j]
    Relaxation: risk[i][j] = min(risk[i][j], risk[i][k] + risk[k][j])
    Vectorized inner loop: O(n³) with NumPy broadcasting → <1ms at n=50.
    """
    n = len(matrix.rep_ids)
    risk = 1.0 - matrix.scores.copy()

    for k in range(n):
        # broadcast: risk[:, k:k+1] is column k, risk[k:k+1, :] is row k
        risk = np.minimum(risk, risk[:, k : k + 1] + risk[k : k + 1, :])

    risk = np.clip(risk, 0.0, 1.0)
    transitive_scores = np.clip(1.0 - risk, 0.0, 1.0)

    return RelationshipMatrix(rep_ids=matrix.rep_ids, scores=transitive_scores)
