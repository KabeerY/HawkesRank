---
title: HawkesRank
emoji: 🦅
colorFrom: green
colorTo: yellow
sdk: docker
app_port: 7860
pinned: false
short_description: Evidence-first professional-state candidate ranking
---

# HawkesRank

**Find the proof behind the profile.**

HawkesRank is an evidence-first candidate ranking system built for Redrob's
Intelligent Candidate Discovery challenge. It separates candidates who merely
*look relevant* from candidates whose career history demonstrates relevant
ownership, production experience, and evaluation maturity.

![HawkesRank two-pass evidence-first candidate ranking architecture](assets/hawkesrank-architecture.png)

## Try the live sandbox

The Space opens with a bundled 50-profile sample. You can also upload a JSON or
JSONL file containing up to 100 candidate profiles.

The demo provides:

- a ranked shortlist with deterministic scores;
- a candidate-level evidence ledger;
- positive evidence, hard negatives, and risk flags;
- a transparent component score breakdown; and
- a downloadable ranked CSV.

The 100-profile limit applies only to this public interactive sandbox. The
official pipeline streams the complete 100,000-profile challenge dataset.

## What makes it different

Most retrieval systems begin with text similarity. HawkesRank begins with a
candidate's **professional state**:

1. Career evidence establishes the relevance band.
2. Direct search, ranking, retrieval, recommendation, and relevance ownership
   receive the strongest weight.
3. Production operation and evaluation maturity distinguish proven work from
   fashionable vocabulary.
4. Skills matter only when corroborated by career text or assessments.
5. Hard-negative suppression demotes convincing near-misses.
6. Behavior and logistics only reorder technically comparable candidates.

A skills list, side project, or keyword-dense summary cannot elevate a profile
into a high professional band by itself.

## Two-pass ranking pipeline

**Pass 1 — professional-state recall:** stream every profile, extract compact
career evidence, assign one of six bounded evidence bands, and retain the best
2,000 profiles in a fixed-size heap.

**Pass 2 — evidence-margin reranking:** build full evidence ledgers for the
retained pool, apply multi-signal scoring and narrow risk checks, then generate
grounded explanations for the final shortlist.

## Reproducibility

- Deterministic and CPU-only
- No GPU or model training
- No LLM in the ranking path
- No external APIs or network calls during ranking
- Standard-library-only full-dataset ranker
- Approximately 73 seconds and 72 MB peak RSS on the development machine

Runtime and memory are machine-dependent. The hosted Streamlit interface is
kept separate from the official ranking implementation.

## Inspect the work

- [GitHub repository](https://github.com/KabeerY/HawkesRank)
- [Full methodology](https://github.com/KabeerY/HawkesRank/blob/main/docs/methodology.md)
- [Dataset-discovered candidate archetypes](https://github.com/KabeerY/HawkesRank/blob/main/candidate_archetypes.md)
- [Verification report](https://github.com/KabeerY/HawkesRank/blob/main/outputs/verification_report.md)
- [Ablation summary](https://github.com/KabeerY/HawkesRank/blob/main/outputs/ablation_summary.md)

HawkesRank is a challenge proof of concept, not an automated hiring decision
system. Its explanations expose the evidence used so that a recruiter can
review—not outsource—the final judgment.
