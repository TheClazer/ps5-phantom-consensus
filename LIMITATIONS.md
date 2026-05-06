# Limitations — Phantom Consensus Engine

## Known Limitations

### 1. Trojan Threshold Sensitivity
The trojan detection uses `max_betrayal > threshold AND influence > threshold`.
At the boundary (betrayal_prob exactly at the 75th percentile), a representative
may be incorrectly classified. The percentile-based calibration mitigates this
but does not eliminate it.

**Impact**: Edge cases where a borderline rep is included/excluded.
**Mitigation**: Clamped bounds [0.60, 0.95] prevent degenerate thresholds.

---

### 2. Alliance Detection at Low Density
When the relationship graph is sparse (few edges), the 60th percentile threshold
may be calibrated too high, resulting in no alliances detected even when weak
alliances exist.

**Impact**: May under-report alliances in sparse datasets.
**Mitigation**: Clamped lower bound of 0.30 ensures threshold never becomes
unreasonably high.

---

### 3. Combination Enumeration Limit
The consensus builder enumerates combinations up to k=3. If the optimal
consensus requires 4+ proposals, the greedy fallback is used for p>30.

**Impact**: Suboptimal selection for large proposal sets requiring k>3.
**Mitigation**: At hackathon scale (p≤30), k=3 covers the vast majority of
realistic scenarios.

---

### 4. Infiltrator Detection with Single-Member Factions
Representatives in single-member factions cannot be evaluated for infiltration
(no intra-faction peers to compare against). They pass the infiltrator check
by default.

**Impact**: A lone representative in a faction cannot be flagged as an
infiltrator regardless of their betrayal probability.
**Mitigation**: Trojan detection still catches high-betrayal single-faction
members via the dual-condition check.

---

### 5. No Temporal Weighting
The relationship data includes `last_interaction` timestamps, but we do not
weight recent interactions more heavily than older ones.

**Impact**: Stale relationships carry the same weight as recent ones.
**Mitigation**: The betrayal_prob field implicitly captures current risk state.

---

### 6. Objection Weight Normalization
Normalization by 10,000 (max: severity=10 × influence=100) means that a
single high-severity, high-influence objector can dominate the weight.
Multiple low-influence objectors may be underweighted relative to one
powerful objector.

**Impact**: Concentrated opposition is penalized more than distributed
opposition of equal total weight — this is intentional (Poison Pill detection)
but may not reflect all political realities.

---

### 7. No Proposal Dependency Modeling
The engine treats proposals as independent. In reality, some proposals may
conflict with or depend on others (e.g., a budget proposal enabling an
infrastructure proposal).

**Impact**: The combination enumeration may select conflicting proposals.
**Mitigation**: Out of scope for this problem definition.

---

### 8. Scale Beyond n=50
Floyd-Warshall is O(n³). At n=500, this is 125,000,000 operations (~100ms).
At n=5000, it becomes impractical.

**Impact**: Not suitable for large-scale political networks.
**Mitigation**: For this problem (n≤50), performance is well within bounds.
Future work: sparse Dijkstra-based propagation for larger graphs.
