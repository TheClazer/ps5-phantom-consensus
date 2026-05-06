"""
Percentile-based threshold calibration.
Handles skewed distributions without Gaussian assumptions.
Falls back to config defaults when data is insufficient.
"""
from __future__ import annotations
import numpy as np
from src.models import Relationship, RelationshipMatrix

# ── Config defaults (fallbacks when < 3 data points) ─────────────────────────
DEFAULT_TROJAN_BETRAYAL: float = 0.70
DEFAULT_TROJAN_INFLUENCE: float = 60.0
DEFAULT_ALLIANCE_MIN: float = 0.45
DEFAULT_VIABILITY_MIN: float = 0.10
DEFAULT_INFILTRATOR: float = 0.50


def calibrate_thresholds(
    relationships: list[Relationship],
    matrix: RelationshipMatrix,
) -> dict[str, float]:
    """
    Returns calibrated thresholds:
      trojan_betrayal   — 75th percentile of betrayal_probs, clamped [0.60, 0.95]
      trojan_influence  — fixed at 60 (influence is already 0-100 scale)
      alliance_min      — 60th percentile of non-zero scores, clamped [0.30, 0.80]
      viability_min     — 25th percentile of viability scores (computed later),
                          here we return a placeholder; viability_scorer updates it
      infiltrator       — 50th percentile of intra-faction scores
    """
    result: dict[str, float] = {
        "trojan_betrayal": DEFAULT_TROJAN_BETRAYAL,
        "trojan_influence": DEFAULT_TROJAN_INFLUENCE,
        "alliance_min": DEFAULT_ALLIANCE_MIN,
        "viability_min": DEFAULT_VIABILITY_MIN,
        "infiltrator": DEFAULT_INFILTRATOR,
    }

    # Trojan betrayal threshold
    betrayal_probs = [r.betrayal_prob for r in relationships]
    if len(betrayal_probs) >= 3:
        t = float(np.percentile(betrayal_probs, 75))
        result["trojan_betrayal"] = float(np.clip(t, 0.60, 0.95))

    # Alliance min threshold
    nonzero = matrix.scores[matrix.scores > 0.0].flatten()
    if len(nonzero) >= 3:
        t = float(np.percentile(nonzero, 60))
        result["alliance_min"] = float(np.clip(t, 0.30, 0.80))

    return result


def calibrate_viability_min(viability_scores: list[float]) -> float:
    """Called after viability scores are computed."""
    if len(viability_scores) >= 3:
        t = float(np.percentile(viability_scores, 25))
        return max(0.05, t)
    return DEFAULT_VIABILITY_MIN
