"""
Phantom Consensus Engine — Main Pipeline
=========================================
14-stage pipeline:
  1.  Load & sanitize data
  2.  Build relationship score matrix
  3.  Compute transitive risk (Floyd-Warshall)
  4.  Calibrate thresholds (percentile-based)
  5.  Compute objection weights
  6.  Compute viability scores
  7.  Calibrate viability_min from score distribution
  8.  Filter Trojan Horse representatives
  9.  Scan faction infiltrators
  10. Remove infiltrators from safe reps
  11. Detect alliances
  12. Build consensus
  13. Assemble final output
  14. Write output/final_agreement.json
"""
from __future__ import annotations
import json
import sys
from pathlib import Path

from src.loader import load_all
from src.relationship_scorer import build_score_matrix, compute_transitive_risk
from src.threshold_calibrator import calibrate_thresholds, calibrate_viability_min
from src.objection_scorer import compute_objection_weights
from src.viability_scorer import compute_viability_scores
from src.trojan_filter import filter_trojans
from src.infiltrator_scan import scan_infiltrators
from src.alliance_detector import detect_alliances
from src.consensus_builder import build_consensus


def run_pipeline(data_dir: Path = Path("data/raw"), output_dir: Path = Path("output")) -> dict:
    output_dir.mkdir(parents=True, exist_ok=True)

    # ── Stage 1: Load & sanitize ──────────────────────────────────────────────
    data = load_all(data_dir)
    reps = data["representatives"]
    proposals = data["proposals"]
    objections = data["objections"]
    relationships = data["relationships"]

    if not reps:
        result = {"selected_proposals": [], "supporting_representatives": [], "alliances": []}
        _write_output(result, output_dir)
        return result

    # ── Stage 2: Build score matrix ───────────────────────────────────────────
    rep_ids = [r.id for r in reps]
    matrix = build_score_matrix(relationships, rep_ids)

    # ── Stage 3: Transitive risk (Floyd-Warshall) ─────────────────────────────
    matrix = compute_transitive_risk(matrix)

    # ── Stage 4: Calibrate thresholds ────────────────────────────────────────
    thresholds = calibrate_thresholds(relationships, matrix)

    # ── Stage 5: Objection weights ────────────────────────────────────────────
    reps_by_id = {r.id: r for r in reps}
    obj_weights = compute_objection_weights(objections, reps_by_id)

    # ── Stage 6: Viability scores ─────────────────────────────────────────────
    viability_scores = compute_viability_scores(proposals, obj_weights)

    # ── Stage 7: Calibrate viability_min ─────────────────────────────────────
    viability_min = calibrate_viability_min(list(viability_scores.values()))

    # ── Stage 8: Filter Trojan Horse reps ────────────────────────────────────
    safe_reps, trojan_ids = filter_trojans(
        reps,
        relationships,
        thresholds["trojan_betrayal"],
        thresholds["trojan_influence"],
    )

    # ── Stage 9: Scan faction infiltrators ───────────────────────────────────
    infiltrator_ids = scan_infiltrators(safe_reps, matrix, thresholds["infiltrator"])

    # ── Stage 10: Remove infiltrators ────────────────────────────────────────
    safe_reps = [r for r in safe_reps if r.id not in infiltrator_ids]

    # ── Stage 11: Detect alliances ────────────────────────────────────────────
    safe_rep_ids = [r.id for r in safe_reps]
    alliances = detect_alliances(matrix, safe_rep_ids, thresholds["alliance_min"])

    # ── Stage 12: Build consensus ─────────────────────────────────────────────
    consensus = build_consensus(
        proposals,
        safe_reps,
        viability_scores,
        objections,
        viability_min,
    )

    # ── Stage 13: Assemble final output ──────────────────────────────────────
    result = {
        "final_agreement": {
            "proposals": consensus["selected_proposals"],
            "supporting_reps": consensus["supporting_representatives"],
        },
        "alliances": alliances,
    }

    # ── Stage 14: Write output ────────────────────────────────────────────────
    _write_output(result, output_dir)

    return result


def _write_output(result: dict, output_dir: Path) -> None:
    out_path = output_dir / "final_agreement.json"
    out_path.write_text(json.dumps(result, indent=2), encoding="utf-8")


if __name__ == "__main__":
    data_dir = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("data/raw")
    result = run_pipeline(data_dir)
    print(json.dumps(result, indent=2))
