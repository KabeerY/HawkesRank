# HawkesRank v1 Ablation Summary

Ablations reorder the already-retained top-2,000 pool; they do not retrain a model.

| Variant | Top-10 overlap | Top-50 overlap | Top-100 overlap |
|---|---:|---:|---:|
| `no_behavior_logistics` | 9/10 | 47/50 | 97/100 |
| `no_skill_corroboration` | 10/10 | 49/50 | 98/100 |
| `no_risk` | 10/10 | 50/50 | 100/100 |
| `no_near_miss` | 9/10 | 50/50 | 100/100 |

Interpretation: large top-k movement identifies a component that materially controls ranking; small movement indicates a tie-breaking or safety role.
