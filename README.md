# Phantom Consensus

## Team Information
- **Team Name**: REDPANDAA
- **Year**: 2
- **All-Female Team**: No

## Architecture Overview

#### Describe your approach here. Keep it short and clear.

**Data Sanitization**: Regex-based ID normalization handles mixed case and whitespace variants. Type coercion with median imputation for null influence. Row-level CSV fault isolation prevents parser crashes. Ghost reference quarantine before scoring. Duplicate resolution via priority-based selection.

**Alliance Detection**: Relationship scoring via `trust × (1 - betrayal_prob) / 100`. Vectorized Floyd-Warshall propagates transitive risk through multi-hop betrayal chains (O(n³) = 125,000 ops at n=50, <1ms). Bidirectional trust requirement (`score(A→B) ≥ threshold AND score(B→A) ≥ threshold`) eliminates False Friend asymmetry. Percentile-based thresholds (75th/60th) adapt to skewed distributions without Gaussian assumptions. Edge pruning before graph construction reduces complexity.

**Proposal Prioritization**: Objection weight `Σ(severity × influence) / 10000` aggregates opposition. Adaptive controversy scoring relative to dataset maximum (`0.6 × max_weight`). Viability formula `(priority / 10) × (1 - controversy)` collapses Poison Pills to near-zero regardless of raw priority.

**Consensus Strategy**: Dual-condition Trojan detection (`max_betrayal > 75th percentile AND influence > 60`). Intra-faction infiltrator scanning. Bounded combinatorial optimization (k≤3) guarantees exact global optimum for p≤30 proposals. Objector exclusion from supporting representatives. Deterministic output (sorted IDs, fixed traversal order). Validated against 5 edge cases: empty input, all-trojan scenario, ghost sponsors, minimum viable (1 rep + 1 proposal), dense graph with alliances. Zero crashes guaranteed via exception handling and safe defaults.

**Note:** Please do not change the format or spelling of anything in this README. The fields are extracted using a script, so any changes to the structure or formatting may break the extraction process.
