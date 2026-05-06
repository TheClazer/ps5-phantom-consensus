"""
Example: Using @trace_and_validate decorator in the consensus pipeline.

This demonstrates how to wrap key functions with the decorator to get:
  - Automatic input size logging
  - NaN value detection
  - ID normalization
  - Ghost Sponsor quarantine
"""
from __future__ import annotations
from pathlib import Path
import sys

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.sanitization import trace_and_validate
from src.sanitization.decorators import GhostSponsorError
from src.loader import load_all
from src.models import Proposal, Representative


# ── Example 1: Wrapping a data loader ────────────────────────────────────────

@trace_and_validate
def load_and_validate_proposals(data_dir: Path) -> list[Proposal]:
    """
    Load proposals with automatic validation.
    The decorator will:
      - Log input size
      - Normalize all IDs (sponsor_id, proposal_id)
      - Catch ghost sponsors and quarantine them
    """
    data = load_all(data_dir)
    proposals = data["proposals"]
    reps_by_id = {r.id: r for r in data["representatives"]}
    
    # Check for ghost sponsors
    valid_proposals = []
    for p in proposals:
        if p.sponsor_id not in reps_by_id:
            # Raise GhostSponsorError — decorator will catch and log
            raise GhostSponsorError(
                f"Proposal {p.id} references unknown sponsor {p.sponsor_id}"
            )
        valid_proposals.append(p)
    
    return valid_proposals


# ── Example 2: Wrapping a scoring function ───────────────────────────────────

@trace_and_validate
def compute_scores_with_validation(
    relationships: list,
    representatives: list[Representative]
) -> dict[str, float]:
    """
    Compute relationship scores with automatic validation.
    The decorator will:
      - Check for NaN values in trust/betrayal_prob
      - Normalize rep IDs in relationships
      - Log input size
    """
    scores = {}
    for rel in relationships:
        from_rep = rel.from_rep
        to_rep = rel.to_rep
        trust = rel.trust
        betrayal = rel.betrayal_prob
        
        # Compute score (decorator already checked for NaN)
        score = trust * (1.0 - betrayal) / 100.0
        scores[f"{from_rep}->{to_rep}"] = score
    
    return scores


# ── Example 3: Wrapping the main pipeline ────────────────────────────────────

@trace_and_validate
def run_consensus_pipeline(data_dir: Path) -> dict:
    """
    Full pipeline with validation at the entry point.
    The decorator provides a safety net for the entire execution.
    """
    # Load data (IDs will be normalized by decorator)
    data = load_all(data_dir)
    
    # ... rest of pipeline ...
    # (simplified for example)
    
    return {
        "final_agreement": {
            "proposals": ["prop_001", "prop_002"],
            "supporting_reps": ["rep_001", "rep_003"],
        },
        "alliances": [["rep_001", "rep_002"]],
    }


# ── Demo execution ────────────────────────────────────────────────────────────

if __name__ == "__main__":
    print("=" * 70)
    print("EXAMPLE: @trace_and_validate decorator usage")
    print("=" * 70)
    print()
    
    # Example 1: Load proposals with ghost sponsor handling
    print("Example 1: Loading proposals with ghost sponsor detection")
    print("-" * 70)
    try:
        proposals = load_and_validate_proposals(Path("data/raw"))
        print(f"✓ Loaded {len(proposals)} valid proposals")
    except Exception as e:
        print(f"✗ Error: {e}")
    print()
    
    # Example 2: Compute scores with NaN detection
    print("Example 2: Computing scores with NaN detection")
    print("-" * 70)
    from src.models import Relationship
    test_rels = [
        Relationship(from_rep="REP_001", to_rep="rep-2", trust=90.0, betrayal_prob=0.1),
        Relationship(from_rep=" Rep 3 ", to_rep="REP_004", trust=85.0, betrayal_prob=0.2),
    ]
    test_reps = []
    scores = compute_scores_with_validation(test_rels, test_reps)
    print(f"✓ Computed {len(scores)} relationship scores")
    for pair, score in scores.items():
        print(f"  {pair}: {score:.3f}")
    print()
    
    # Example 3: Full pipeline
    print("Example 3: Full consensus pipeline with validation")
    print("-" * 70)
    result = run_consensus_pipeline(Path("data/raw"))
    print(f"✓ Pipeline complete")
    print(f"  Selected proposals: {result['final_agreement']['proposals']}")
    print(f"  Supporting reps: {result['final_agreement']['supporting_reps']}")
    print(f"  Alliances: {result['alliances']}")
    print()
    
    print("=" * 70)
    print("All examples completed successfully!")
    print("=" * 70)
