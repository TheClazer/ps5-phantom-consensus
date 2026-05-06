"""
Edge case tests for the Phantom Consensus Engine.
Tests 1-5 from the final checklist.
"""
from __future__ import annotations
import json
import tempfile
import shutil
from pathlib import Path
import pytest

from main import run_pipeline

# ── Helpers ───────────────────────────────────────────────────────────────────

def _make_data_dir(
    reps: list[dict],
    proposals: list[dict],
    objections: list[dict],
    relations: str,
) -> Path:
    """Create a temp directory with the 4 input files."""
    d = Path(tempfile.mkdtemp())
    (d / "representatives.json").write_text(json.dumps(reps))
    (d / "proposals.json").write_text(json.dumps(proposals))
    (d / "objections.json").write_text(json.dumps(objections))
    (d / "relations.csv").write_text(relations)
    return d


def _run(data_dir: Path) -> dict:
    out_dir = Path(tempfile.mkdtemp())
    result = run_pipeline(data_dir, out_dir)
    shutil.rmtree(str(data_dir))
    shutil.rmtree(str(out_dir))
    return result


def _assert_schema(result: dict) -> None:
    """Assert exact output schema."""
    assert set(result.keys()) == {"final_agreement", "alliances"}, \
        f"Wrong top-level keys: {result.keys()}"
    fa = result["final_agreement"]
    assert set(fa.keys()) == {"proposals", "supporting_reps"}, \
        f"Wrong final_agreement keys: {fa.keys()}"
    assert isinstance(fa["proposals"], list)
    assert isinstance(fa["supporting_reps"], list)
    assert isinstance(result["alliances"], list)
    # All IDs must be strings
    for pid in fa["proposals"]:
        assert isinstance(pid, str), f"proposal ID not string: {pid}"
    for rid in fa["supporting_reps"]:
        assert isinstance(rid, str), f"rep ID not string: {rid}"
    # Sorted
    assert fa["proposals"] == sorted(fa["proposals"]), "proposals not sorted"
    assert fa["supporting_reps"] == sorted(fa["supporting_reps"]), "reps not sorted"
    for alliance in result["alliances"]:
        assert alliance == sorted(alliance), f"alliance not sorted: {alliance}"
    assert result["alliances"] == sorted(result["alliances"]), "alliances not sorted"


# ── Test 1: Completely empty input ────────────────────────────────────────────

def test_empty_input():
    d = _make_data_dir([], [], [], "from,to,trust,rivalry,betrayal_prob\n")
    result = _run(d)
    _assert_schema(result)
    assert result["final_agreement"]["proposals"] == []
    assert result["final_agreement"]["supporting_reps"] == []
    assert result["alliances"] == []


# ── Test 2: All reps are trojans ──────────────────────────────────────────────

def test_all_trojans():
    reps = [
        {"id": "rep_001", "name": "A", "faction": "X", "influence": 95},
        {"id": "rep_002", "name": "B", "faction": "X", "influence": 90},
    ]
    proposals = [
        {"id": "prop_001", "title": "T", "sponsor": "rep_001", "priority": 8},
    ]
    relations = (
        "from,to,trust,rivalry,betrayal_prob\n"
        "rep_001,rep_002,90,5,0.99\n"
        "rep_002,rep_001,90,5,0.99\n"
    )
    d = _make_data_dir(reps, proposals, [], relations)
    result = _run(d)
    _assert_schema(result)
    # No safe reps → no supporters (proposals may still be selected)
    assert result["final_agreement"]["supporting_reps"] == []
    assert result["alliances"] == []


# ── Test 3: All proposals invalid (ghost sponsors) ───────────────────────────

def test_all_proposals_invalid():
    reps = [
        {"id": "rep_001", "name": "A", "faction": "X", "influence": 70},
    ]
    proposals = [
        {"id": "prop_001", "title": "Ghost", "sponsor": "rep_999", "priority": 9},
        {"id": "prop_002", "title": "Ghost2", "sponsor": "rep_998", "priority": 8},
    ]
    d = _make_data_dir(reps, proposals, [], "from,to,trust,rivalry,betrayal_prob\n")
    result = _run(d)
    _assert_schema(result)
    assert result["final_agreement"]["proposals"] == []
    assert result["final_agreement"]["supporting_reps"] == []


# ── Test 4: Single rep + single proposal (minimum viable) ────────────────────

def test_minimum_viable():
    reps = [
        {"id": "rep_001", "name": "Solo", "faction": "X", "influence": 70},
    ]
    proposals = [
        {"id": "prop_001", "title": "Solo Bill", "sponsor": "rep_001", "priority": 7},
    ]
    d = _make_data_dir(reps, proposals, [], "from,to,trust,rivalry,betrayal_prob\n")
    result = _run(d)
    _assert_schema(result)
    assert "prop_001" in result["final_agreement"]["proposals"]
    assert "rep_001" in result["final_agreement"]["supporting_reps"]
    assert result["alliances"] == []


# ── Test 5: Dense relationship graph (scale + alliance detection) ─────────────

def test_dense_graph_with_alliances():
    reps = [
        {"id": "rep_001", "name": "A", "faction": "Alpha", "influence": 80},
        {"id": "rep_002", "name": "B", "faction": "Alpha", "influence": 75},
        {"id": "rep_003", "name": "C", "faction": "Beta",  "influence": 70},
        {"id": "rep_004", "name": "D", "faction": "Beta",  "influence": 65},
    ]
    proposals = [
        {"id": "prop_001", "title": "P1", "sponsor": "rep_001", "priority": 8},
        {"id": "prop_002", "title": "P2", "sponsor": "rep_003", "priority": 6},
    ]
    # Strong mutual trust, low betrayal → should form alliances
    relations = (
        "from,to,trust,rivalry,betrayal_prob\n"
        "rep_001,rep_002,90,5,0.05\n"
        "rep_002,rep_001,88,5,0.05\n"
        "rep_003,rep_004,85,8,0.08\n"
        "rep_004,rep_003,87,8,0.06\n"
        "rep_001,rep_003,30,60,0.50\n"
        "rep_003,rep_001,25,65,0.55\n"
    )
    d = _make_data_dir(reps, proposals, [], relations)
    result = _run(d)
    _assert_schema(result)
    # Must detect at least one alliance
    assert len(result["alliances"]) >= 1, \
        f"Expected alliances in dense graph, got: {result['alliances']}"
    # All alliance members must be valid rep IDs
    valid_ids = {"rep_001", "rep_002", "rep_003", "rep_004"}
    for alliance in result["alliances"]:
        for rid in alliance:
            assert rid in valid_ids, f"Unknown rep in alliance: {rid}"
    # Output must be valid JSON (no float instability)
    serialised = json.dumps(result)
    reparsed = json.loads(serialised)
    assert reparsed == result
