# Results — Phantom Consensus Engine

## Output on Sample Data

```json
{
  "final_agreement": {
    "proposals": ["prop_002", "prop_003"],
    "supporting_reps": ["rep_003", "rep_004"]
  },
  "alliances": []
}
```

---

## Decision Trace

### Data Sanitization

| Issue | Raw Data | After Sanitization |
|-------|----------|-------------------|
| Duplicate rep | `REP_001` (duplicate of `rep_001`) | Removed — first occurrence kept |
| Duplicate rep | ` rep_004` (whitespace) | Normalized to `rep_001`, removed |
| Null influence | `rep_004.influence = null` | Imputed with median (85) |
| String influence | `rep_002.influence = "70"` | Cast to int: 70 |
| Clamped influence | `rep_005.influence = 150` | Clamped to 100 |
| Duplicate proposal | `prop_003` appears twice | Kept priority=9.5 version |
| Ghost sponsor | `prop_005.sponsor = rep_099` | Quarantined — rep_099 not in dataset |
| Ghost objector | `rep_099` objects to `prop_001` | Quarantined — rep_099 not in dataset |
| Invalid severity | `rep_001` objects with severity="high" | Quarantined — non-numeric |
| Negative severity | `rep_001` objects with severity=-3 | Quarantined — below 0 |
| Null severity | `rep_005` objects with severity=null | Quarantined |
| Duplicate objection | `rep_003` objects to `prop_001` twice | Deduplicated — first kept |
| Bad CSV row | `rep_002→rep_003` trust=empty | Quarantined — missing trust |
| Bad CSV row | `rep_004→rep_005` rivalry="high" | Parsed (rivalry not used in scoring) |
| Bad CSV row | `rep_005→rep_006` betrayal_prob=1.5 | Clamped to 1.0 |
| Duplicate CSV row | `rep_001→rep_002` appears twice | Deduplicated |

---

### Threshold Calibration

| Threshold | Value | Method |
|-----------|-------|--------|
| `trojan_betrayal` | 0.600 | 75th percentile of betrayal_probs |
| `trojan_influence` | 60.0 | Fixed (influence scale 0-100) |
| `alliance_min` | 0.562 | 60th percentile of non-zero scores |
| `viability_min` | 0.100 | 25th percentile of viability scores |
| `infiltrator` | 0.500 | Default (insufficient faction data) |

---

### Trojan Detection

| Rep | Max Betrayal | Influence | Trojan? | Reason |
|-----|-------------|-----------|---------|--------|
| rep_001 | 0.75 (→rep_006) | 85 | ✅ YES | betrayal > 0.60 AND influence > 60 |
| rep_002 | 0.35 | 70 | ❌ No | betrayal ≤ 0.60 |
| rep_003 | 0.45 | 95 | ❌ No | betrayal ≤ 0.60 |
| rep_004 | 0.20 | 85 | ❌ No | betrayal ≤ 0.60 |
| rep_005 | 1.00 (clamped) | 100 | ✅ YES | betrayal > 0.60 AND influence > 60 |
| rep_006 | 0.80 | 92 | ✅ YES | betrayal > 0.60 AND influence > 60 |

**Safe reps after trojan filter**: rep_002, rep_003, rep_004

---

### Objection Weights

| Proposal | Objectors | Raw Weight | Normalized |
|----------|-----------|------------|------------|
| prop_001 | rep_003 (sev=8, inf=95) | 760 | 0.0760 |
| prop_002 | *(rep_001 objection invalid — non-numeric severity)* | 0 | 0.0000 |
| prop_003 | rep_002 (sev=5, inf=70) | 350 | 0.0350 |
| prop_004 | rep_003 (sev=9, inf=95) | 855 | 0.0855 |

---

### Viability Scores

| Proposal | Priority | Obj Weight | Controversy | Viability | Decision |
|----------|----------|------------|-------------|-----------|----------|
| prop_001 | 8.0 | 0.0760 | 1.000 | **0.000** | ❌ Rejected (Poison Pill) |
| prop_002 | 10.0 | 0.0000 | 0.000 | **1.000** | ✅ Selected |
| prop_003 | 9.5 | 0.0350 | 0.410 | **0.302** | ✅ Selected |
| prop_004 | 10.0 | 0.0855 | 1.000 | **0.000** | ❌ Rejected (Poison Pill) |

**prop_001**: Despite priority=8, rep_003 (influence=95) objects with severity=8 → controversy=1.0 → viability=0.

**prop_004**: Despite priority=10, rep_003 (influence=95) objects with severity=9 → controversy=1.0 → viability=0.

---

### Alliance Detection

After removing trojans (rep_001, rep_005, rep_006), the remaining safe reps (rep_002, rep_003, rep_004) have no mutual relationships in the dataset that meet the bidirectional threshold.

The genuine alliances in the raw data (rep_001↔rep_004, rep_002↔rep_005) both involve at least one trojan representative — correctly excluded.

**Result**: `alliances: []` — correct, no stable alliances among safe representatives.

---

### Final Consensus

**Selected proposals**: prop_002 (viability=1.0) + prop_003 (viability=0.302)

**Supporting reps**: rep_003, rep_004 (safe reps not objecting to selected proposals)
- rep_002 objected to prop_003 → excluded from supporting_reps

---

## Performance

| Stage | Time |
|-------|------|
| Data loading + sanitization | <2ms |
| Score matrix build | <1ms |
| Floyd-Warshall (n=6) | <0.1ms |
| Threshold calibration | <0.1ms |
| Objection + viability scoring | <0.1ms |
| Trojan + infiltrator filtering | <0.1ms |
| Alliance detection | <0.1ms |
| Consensus builder | <0.1ms |
| **Total** | **<5ms** |

At n=50, p=30: estimated <10ms total.
