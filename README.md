# Phantom Consensus

## Team Information
- **Team Name**: REDPANDAA
- **Year**: 2
- **All-Female Team**: No

## Architecture Overview

#### Describe your approach here. Keep it short and clear.

- How did you approach cleaning the raw data, including handling missing values, inconsistent formats, and outliers?

We normalize all IDs via regex (handling mixed case, whitespace, delimiter variants) before any cross-referencing. Influence values are cast from string/null with clamping to [0,100]; null influence is imputed with the median of valid values. Duplicate proposals are resolved by keeping the highest-priority entry. Ghost references (proposals with unknown sponsors, objections from unknown reps) are quarantined before scoring. CSV rows with unparseable fields are isolated per-row without crashing the parser.

- What logic did you use to detect underlying alliances and evaluate the impact of asymmetric trust and betrayal probabilities?

Relationship scores are computed as `trust × (1 - betrayal_prob) / 100`, normalized to [0,1]. Transitive risk is propagated via vectorized Floyd-Warshall on the risk domain (`risk = 1 - score`), catching multi-hop betrayal chains. Alliance detection requires bidirectional trust: an edge is added only when `score(A→B) ≥ threshold AND score(B→A) ≥ threshold`. This eliminates False Friend relationships where one side's trust is not reciprocated. Thresholds are percentile-based (60th percentile of non-zero scores) to adapt to the input distribution without Gaussian assumptions.

- How did you prioritize proposals given varying objection severities and differing levels of influence among objectors?

Objection weight per proposal is `Σ(severity × influence) / 10000`, aggregating all objectors. A controversy score is derived relative to the dataset's maximum objection weight (`controversy = obj_weight / (0.6 × max_weight)`), making detection adaptive. Viability is `(priority / 10) × (1 - controversy)` — a Poison Pill proposal with maximum priority but heavy influential opposition collapses toward zero viability regardless of its raw priority.

- Describe the strategy used by your consensus engine to maintain a stable agreement while avoiding "Trojan Horse" candidates and "Poison Pill" proposals.

Trojan Horse detection flags representatives where `max_betrayal_prob > 75th percentile threshold AND influence > 60`. These are excluded before alliance detection and consensus building. Faction infiltrators (members whose average intra-faction score falls below the infiltrator threshold) are also excluded. For proposal selection, we enumerate all combinations up to k=3 for p≤30 proposals, selecting the combination with maximum total viability — guaranteeing the globally optimal set rather than a greedy approximation. Objectors to selected proposals are excluded from the supporting representatives list.

**Note:** Please do not change the format or spelling of anything in this README. The fields are extracted using a script, so any changes to the structure or formatting may break the extraction process.
