"""
Data ingestion + sanitization layer.
Handles: dirty IDs, type coercion, deduplication, ghost reference removal.
"""
from __future__ import annotations
import json
import re
import csv
from pathlib import Path
from typing import Optional
from src.models import Representative, Proposal, Objection, Relationship


# ── ID normalisation ──────────────────────────────────────────────────────────

_REP_RE = re.compile(r'^(?:rep|REP|Rep)[_\-]?(\d+)$')
_PROP_RE = re.compile(r'^(?:prop|PROP|Prop)[_\-]?(\d+)$')


def normalize_rep_id(raw: object) -> Optional[str]:
    if not isinstance(raw, str):
        return None
    s = raw.strip().lower().replace('-', '_')
    m = _REP_RE.match(raw.strip())
    if m:
        return f"rep_{m.group(1).zfill(3)}"
    return s or None


def normalize_prop_id(raw: object) -> Optional[str]:
    if not isinstance(raw, str):
        return None
    s = raw.strip().lower().replace('-', '_')
    m = _PROP_RE.match(raw.strip())
    if m:
        return f"prop_{m.group(1).zfill(3)}"
    return s or None


# ── Type coercion helpers ─────────────────────────────────────────────────────

def _coerce_influence(v: object) -> Optional[int]:
    if v is None:
        return None
    try:
        parsed = int(float(str(v).strip()))
        return max(0, min(100, parsed))
    except (ValueError, TypeError):
        return None


def _coerce_float(v: object, lo: float = 0.0, hi: float = 100.0) -> Optional[float]:
    try:
        f = float(str(v).strip())
        return max(lo, min(hi, f))
    except (ValueError, TypeError):
        return None


def _coerce_severity(v: object) -> Optional[float]:
    """Severity 0-10; reject negatives and non-numeric."""
    f = _coerce_float(v, 0.0, 10.0)
    return f


# ── Loaders ───────────────────────────────────────────────────────────────────

def load_representatives(path: Path) -> list[Representative]:
    raw: list[dict] = json.loads(path.read_text(encoding="utf-8"))
    seen: dict[str, Representative] = {}
    influences: list[int] = []

    for rec in raw:
        rid = normalize_rep_id(rec.get("id"))
        if rid is None:
            continue
        inf = _coerce_influence(rec.get("influence"))
        if inf is not None:
            influences.append(inf)
        rep = Representative(
            id=rid,
            name=str(rec.get("name", "")),
            faction=str(rec.get("faction", "Unknown")),
            influence=inf,
        )
        # dedup: keep first occurrence
        if rid not in seen:
            seen[rid] = rep

    # impute None influence with median of valid values
    median_inf: int = int(sorted(influences)[len(influences) // 2]) if influences else 50
    for rep in seen.values():
        if rep.influence is None:
            rep.influence = median_inf

    return list(seen.values())


def load_proposals(path: Path) -> list[Proposal]:
    raw: list[dict] = json.loads(path.read_text(encoding="utf-8"))
    seen: dict[str, Proposal] = {}

    for rec in raw:
        pid = normalize_prop_id(rec.get("id"))
        if pid is None:
            continue
        priority = _coerce_float(rec.get("priority", 5), 0.0, 10.0) or 5.0
        sponsor = normalize_rep_id(rec.get("sponsor") or rec.get("sponsor_id"))
        if sponsor is None:
            continue
        prop = Proposal(
            id=pid,
            title=str(rec.get("title", "")),
            sponsor_id=sponsor,
            priority=priority,
        )
        # dedup: keep highest priority
        if pid not in seen or prop.priority > seen[pid].priority:
            seen[pid] = prop

    return list(seen.values())


def load_objections(path: Path) -> list[Objection]:
    raw: list[dict] = json.loads(path.read_text(encoding="utf-8"))
    seen: set[tuple[str, str]] = set()
    result: list[Objection] = []

    for rec in raw:
        rid = normalize_rep_id(rec.get("rep_id"))
        pid = normalize_prop_id(rec.get("proposal_id"))
        if rid is None or pid is None:
            continue
        sev = _coerce_severity(rec.get("severity"))
        if sev is None:
            continue
        key = (rid, pid)
        if key in seen:
            continue
        seen.add(key)
        result.append(Objection(rep_id=rid, proposal_id=pid, severity=sev))

    return result


def load_relationships(path: Path) -> list[Relationship]:
    result: list[Relationship] = []
    seen: set[tuple[str, str]] = set()

    with path.open(encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        for i, row in enumerate(reader):
            try:
                fr = normalize_rep_id(row.get("from") or row.get("from_rep"))
                to = normalize_rep_id(row.get("to") or row.get("to_rep"))
                if fr is None or to is None or fr == to:
                    continue
                trust = _coerce_float(row.get("trust", "0"), 0.0, 100.0)
                bp = _coerce_float(row.get("betrayal_prob", "0"), 0.0, 1.0)
                if trust is None or bp is None:
                    continue
                key = (fr, to)
                if key in seen:
                    continue
                seen.add(key)
                result.append(Relationship(
                    from_rep=fr, to_rep=to,
                    trust=trust, betrayal_prob=bp,
                ))
            except Exception:
                continue  # quarantine bad row

    return result


# ── Reference validation ──────────────────────────────────────────────────────

def validate_references(
    reps: list[Representative],
    proposals: list[Proposal],
    objections: list[Objection],
) -> tuple[list[Proposal], list[Objection]]:
    rep_ids = {r.id for r in reps}
    prop_ids = {p.id for p in proposals}

    valid_proposals = [p for p in proposals if p.sponsor_id in rep_ids]
    valid_objections = [
        o for o in objections
        if o.rep_id in rep_ids and o.proposal_id in prop_ids
    ]
    return valid_proposals, valid_objections


# ── Master loader ─────────────────────────────────────────────────────────────

def load_all(data_dir: Path) -> dict:
    reps = load_representatives(data_dir / "representatives.json")
    proposals = load_proposals(data_dir / "proposals.json")
    objections = load_objections(data_dir / "objections.json")
    relationships = load_relationships(data_dir / "relations.csv")

    proposals, objections = validate_references(reps, proposals, objections)

    return {
        "representatives": reps,
        "proposals": proposals,
        "objections": objections,
        "relationships": relationships,
    }
