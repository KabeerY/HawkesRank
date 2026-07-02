# HawkesRank v1 methodology

## 1. Problem interpretation

The released JD is not a bag-of-skills query. Redrob needs a hands-on senior engineer who has owned ranking, retrieval, search, matching, or recommendation in production; understands evaluation; can ship product; and is realistically reachable. The documents explicitly warn that keyword-stuffed profiles, plain-language strong candidates, behavioral twins, and honeypots are present.

Therefore HawkesRank estimates a candidate's **professional state** before measuring detailed fit. It asks: what kind of work has this person proved in career records, how direct is that proof, what corroborates it, what contradicts it, and are they hireable now?

## 2. Dataset-grounded discovery

A streaming audit of all 100,000 records found a highly stratified synthetic pool: large nontechnical and generic-software populations, smaller data and applied-ML populations, and a very small direct search/ranking tail. Exact counts, archetype examples, template diversity, and anomaly prevalence are recorded in [`../candidate_archetypes.md`](../candidate_archetypes.md).

This discovery shaped the concept vocabulary and test cases, but the ranker never uses candidate IDs, exact family sizes, template frequency, or full-description lookup tables. Rules operate on arbitrary field text and relationships.

The audit also showed that several apparent anomalies are common background noise: repeated career descriptions, inverted salary ranges, skill durations modestly exceeding total experience, and activity dates before signup. Penalizing those broadly would punish thousands of otherwise coherent profiles. They remain weak diagnostics unless combined with unsupported AI claims.

## 3. Pass 1: professional-state recall

The first pass streams one JSON object at a time and stores only a `Pass1State` for the best 2,000 candidates. It reads title, current work, career history, summary, and a small subset of behavioral fields.

Each profile enters one of six ordered bands:

| Band | Meaning | Ceiling logic |
|---|---|---|
| 0 | Low relevance | nontechnical or unsupported AI vocabulary |
| 1 | Software-adjacent | general engineering or side-project AI |
| 2 | Data/backend-adjacent | data platform and analytics foundations |
| 3 | Applied ML | career-proven ML without direct retrieval/ranking ownership |
| 4 | Direct search/ranking | owned, production, evaluated retrieval/ranking work |
| 5 | Senior relevance owner | senior scope plus direct ownership, scale, production, and evaluation |

High bands require relationships among evidence types. For example, band 4 requires direct retrieval/ranking or RAG-plus-vector evidence, current ownership, production proof, and evaluation or sufficiently strong vector/search proof. A matching skill list cannot satisfy those conditions.

Pass-1 evidence then orders candidates inside bands. Direct current work, evaluation, vector systems, production, ownership, career ML, and an ML/search title contribute. Availability is only a small tie-break. A fixed-size min-heap bounds memory.

## 4. Pass 2: evidence-margin reranking

The second scan loads the retained 2,000 records and creates a full `EvidenceLedger`. Evidence is collected separately from current career, prior career, title/headline, summary, and skills with these principles:

- Current career has the largest weight.
- Prior career is meaningful but discounted.
- Title and summary provide context, not proof by themselves.
- Skills have a deliberately small weight.
- Repeated terms have diminishing returns.
- A listed skill earns corroboration only when career text or an assessment supports it.

The final score is the sum of positive evidence minus near-miss and coherence penalties, then clipped by the professional-band ceiling.

| Component | Role |
|---|---|
| `professional_band_score` | dominant professional-state prior |
| `current_work_subtype_score` | directness of search, ranking, hybrid retrieval, relevance ownership, recommendation, RAG, or adjacent work |
| `retrieval_search_ranking_score` | career-weighted IR/ranking evidence |
| `vector_embedding_hybrid_score` | dense/sparse/vector infrastructure evidence |
| `production_ml_system_score` | shipped, served, scaled, monitored, or operated systems |
| `evaluation_maturity_score` | NDCG/MRR/MAP, labels, benchmarks, A/B tests, feedback loops, or offline-online reasoning |
| `python_backend_platform_score` | implementation and systems foundations |
| `product_shipper_score` | product/user/outcome language and delivery |
| `experience_fit_score` | graded fit around the flexible 5–9 year target |
| `skill_corroboration_score` | career- or assessment-supported skills only |
| `behavior_fit_score` | bounded reachability and engagement modifier |
| `logistics_fit_score` | bounded notice/location/relocation modifier |
| `near_miss_penalty` | explicit suppression of lookalikes missing ownership, production, evaluation, or availability |
| `coherence_risk_penalty` | narrow impossible or reinforcing contradictions |

## 5. Hard negatives and risk

Near-miss penalties cover side-project-only AI, explicitly limited ownership, services-only careers, CV/speech profiles without IR, direct-search candidates without evaluation or ownership, recommendation without production, severe experience mismatch, and technically strong profiles that are simultaneously unavailable, inactive, and unresponsive.

Risk handling is intentionally asymmetric:

- Expert proficiency with zero months is a strong honeypot-like flag.
- Unsupported AI stuffing plus a nontechnical title/career mismatch is material.
- Multiple contradictions become strong only when paired with unsupported AI claims.
- Repeated descriptions, salary inversion, activity-before-signup, and modest duration overruns are weak and contribute little unless they accumulate.

This follows the bundle's instruction to avoid broad synthetic-noise penalties while naturally suppressing unmistakably impossible profiles.

## 6. Behavior and logistics

Behavior is bounded to `[-4, +4]`; logistics is bounded to `[-3, +3]`. Open-to-work, recency relative to a fixed 2026-06-01 snapshot date, recruiter response rate and speed, interview completion, verification, GitHub activity, saves, notice period, target location, and relocation contribute.

These values can reorder candidates in the same evidence neighborhood. They cannot change the professional band. A separate hard-negative applies only when a high-band candidate combines several severe availability failures; this prevents a perfect-on-paper but unreachable profile from consuming the most valuable top-10 slot.

## 7. Grounded reasoning

Each finalist receives a 1–2 sentence explanation assembled from ledger fields only. It includes title and experience, a specific current-work fact connected to Redrob's intelligence-layer mandate, and up to two material concerns such as experience mismatch, inactive status, response rate, notice, or relocation. Four syntactic variants prevent identical boilerplate while keeping claims deterministic.

The implementation avoids claims about a named technology unless the current work description contains it. For plain-language candidates, it describes the proven system relationship—such as query understanding, ranking calibration, evaluation ownership, or production operations—without requiring fashionable vocabulary.

## 8. Verification and ablation

The pipeline produces:

- a complete pass-1 pool for recall inspection;
- a top-300 evidence report;
- a top-300 score-component matrix;
- a top-100 risk review;
- component-removal overlap ablations;
- a run summary with runtime, memory, band counts, hash, and validator errors.

Unit tests enforce the highest-risk invariants: keyword skills cannot elevate a project manager, direct career proof beats copied skills, behavior cannot change professional identity, plain-language relevance ownership is recognized, and reasoning contains candidate facts.

The organizer validator and a stricter local validator check format. The stricter validator additionally verifies candidate existence against the JSONL, finite and strictly decreasing scores, unique nonempty explanations, and a minimum explanation length.

## 9. Rejected v1 approaches

BM25/TF-IDF, MiniLM, FAISS, JobBERT, local LLM inference, hosted APIs, and pseudo-training were intentionally excluded. They are common competitor baselines, add operational or compute risk, and can reward the very vocabulary traps described in the bundle. A semantic feature would only be considered after this deterministic system, with a controlled ablation and a low weight that cannot override career proof.

## 10. Limitations

There are no public relevance labels or live leaderboard feedback, so weights cannot be empirically tuned against NDCG. The system instead uses the released JD, explicit organizer warnings, full-dataset structure, adversarial invariants, manual top-rank inspection, and ablations. Pattern-based concept extraction can miss unusual phrasing; its mitigation is a broad plain-language ownership path and traceable reports rather than an opaque model.
