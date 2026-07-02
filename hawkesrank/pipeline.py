from __future__ import annotations

import csv
import heapq
import json
import resource
import time
from collections import Counter
from pathlib import Path
from typing import Any

from .config import FINAL_SIZE, INSPECTION_SIZE, TOP_POOL_SIZE
from .evidence import EvidenceLedger, Pass1State, extract_ledger, extract_pass1_state
from .reasoning import generate_reasoning
from .scoring import ablation_score, score_pass2
from .validation import sha256_file, strict_validate


COMPONENT_COLUMNS = [
    "professional_band_score",
    "current_work_subtype_score",
    "retrieval_search_ranking_score",
    "vector_embedding_hybrid_score",
    "production_ml_system_score",
    "evaluation_maturity_score",
    "python_backend_platform_score",
    "product_shipper_score",
    "experience_fit_score",
    "skill_corroboration_score",
    "behavior_fit_score",
    "logistics_fit_score",
    "near_miss_penalty",
    "coherence_risk_penalty",
]


def _join(values: list[str]) -> str:
    return " | ".join(value for value in values if value)


def _pool_row(rank: int, ledger: EvidenceLedger) -> dict[str, Any]:
    return {
        "pass1_rank": rank,
        "candidate_id": ledger.candidate_id,
        "pass1_score": f"{ledger.pass1_score:.6f}",
        "professional_band": ledger.band_name,
        "band_id": ledger.band,
        "subtype": ledger.subtype,
        "current_title": ledger.title,
        "years_experience": f"{ledger.years_experience:.1f}",
        "current_company": ledger.company,
        "location": ledger.location,
        "open_to_work": ledger.behavior["open_to_work"],
        "days_since_active": ledger.behavior["days_since_active"],
        "response_rate": f"{ledger.behavior['recruiter_response_rate']:.3f}",
        "notice_period_days": ledger.logistics["notice_period_days"],
        "willing_to_relocate": ledger.logistics["willing_to_relocate"],
        "retrieval_raw": f"{ledger.raw['retrieval']:.4f}",
        "ranking_raw": f"{ledger.raw['ranking']:.4f}",
        "evaluation_raw": f"{ledger.raw['evaluation']:.4f}",
        "production_raw": f"{ledger.raw['production']:.4f}",
        "ownership_raw": f"{ledger.raw['ownership']:.4f}",
        "skill_corroboration": f"{ledger.skill_corroboration:.4f}",
        "positive_evidence": _join(ledger.positive_evidence),
        "negative_evidence": _join(ledger.negative_evidence),
        "risk_flags": _join(ledger.risk_flags),
    }


def _inspection_row(rank: int, ledger: EvidenceLedger) -> dict[str, Any]:
    row = {
        "rank": rank,
        "candidate_id": ledger.candidate_id,
        "final_score": f"{ledger.final_score:.6f}",
        "professional_band": ledger.band_name,
        "band_id": ledger.band,
        "subtype": ledger.subtype,
        "current_title": ledger.title,
        "headline": ledger.headline,
        "years_experience": f"{ledger.years_experience:.1f}",
        "current_company": ledger.company,
        "industry": ledger.industry,
        "location": ledger.location,
        "career_titles": _join(ledger.career_titles),
        "current_work_evidence": _join(ledger.positive_evidence),
        "negative_evidence": _join(ledger.negative_evidence),
        "risk_flags": _join(ledger.risk_flags),
        "open_to_work": ledger.behavior["open_to_work"],
        "last_active_date": ledger.behavior["last_active_date"],
        "response_rate": f"{ledger.behavior['recruiter_response_rate']:.3f}",
        "response_hours": f"{ledger.behavior['avg_response_time_hours']:.1f}",
        "notice_period_days": ledger.logistics["notice_period_days"],
        "willing_to_relocate": ledger.logistics["willing_to_relocate"],
        "target_location": ledger.logistics["target_location"],
        "reasoning": ledger.reasoning,
    }
    row.update({key: f"{ledger.components[key]:.6f}" for key in COMPONENT_COLUMNS})
    return row


def _write_csv(path: Path, rows: list[dict[str, Any]], fieldnames: list[str] | None = None) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        raise ValueError(f"Cannot write empty CSV: {path}")
    fieldnames = fieldnames or list(rows[0].keys())
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def _run_ablation(ledgers: list[EvidenceLedger], final_ids: list[str]) -> str:
    variants = [
        "no_behavior_logistics",
        "no_skill_corroboration",
        "no_risk",
        "no_near_miss",
    ]
    baseline_top10 = set(final_ids[:10])
    baseline_top50 = set(final_ids[:50])
    baseline_top100 = set(final_ids[:100])
    lines = [
        "# HawkesRank v1 Ablation Summary",
        "",
        "Ablations reorder the already-retained top-2,000 pool; they do not retrain a model.",
        "",
        "| Variant | Top-10 overlap | Top-50 overlap | Top-100 overlap |",
        "|---|---:|---:|---:|",
    ]
    for variant in variants:
        ordered = sorted(
            ledgers,
            key=lambda ledger: (-ablation_score(ledger, variant), ledger.candidate_id),
        )
        ids = [ledger.candidate_id for ledger in ordered]
        lines.append(
            f"| `{variant}` | {len(baseline_top10 & set(ids[:10]))}/10 "
            f"| {len(baseline_top50 & set(ids[:50]))}/50 "
            f"| {len(baseline_top100 & set(ids[:100]))}/100 |"
        )
    lines.extend(
        [
            "",
            "Interpretation: large top-k movement identifies a component that materially controls ranking; "
            "small movement indicates a tie-breaking or safety role.",
        ]
    )
    return "\n".join(lines) + "\n"


def run_pipeline(
    candidates_path: str | Path,
    output_root: str | Path = ".",
    pool_size: int = TOP_POOL_SIZE,
    inspection_size: int = INSPECTION_SIZE,
    final_size: int = FINAL_SIZE,
) -> dict[str, Any]:
    started = time.perf_counter()
    candidates_path = Path(candidates_path)
    root = Path(output_root)
    outputs_dir = root / "outputs"
    final_dir = root / "final"
    outputs_dir.mkdir(parents=True, exist_ok=True)
    final_dir.mkdir(parents=True, exist_ok=True)

    heap: list[tuple[float, str, Pass1State]] = []
    total = 0
    all_band_counts: Counter[str] = Counter()
    with candidates_path.open("r", encoding="utf-8") as handle:
        for line in handle:
            if not line.strip():
                continue
            record = json.loads(line)
            total += 1
            state = extract_pass1_state(record)
            all_band_counts[state.band_name] += 1
            item = (state.pass1_score, state.candidate_id, state)
            if len(heap) < pool_size:
                heapq.heappush(heap, item)
            elif item[:2] > heap[0][:2]:
                heapq.heapreplace(heap, item)

    selected_states = {item[2].candidate_id: item[2] for item in heap}
    retained: list[EvidenceLedger] = []
    with candidates_path.open("r", encoding="utf-8") as handle:
        for line in handle:
            if not line.strip():
                continue
            record = json.loads(line)
            state = selected_states.get(record["candidate_id"])
            if state is None:
                continue
            ledger = extract_ledger(record)
            ledger.pass1_score = state.pass1_score
            retained.append(ledger)
    retained.sort(key=lambda ledger: (-ledger.pass1_score, ledger.candidate_id))
    pool_rows = [_pool_row(rank, ledger) for rank, ledger in enumerate(retained, 1)]
    _write_csv(outputs_dir / "top_2000_candidates.csv", pool_rows)

    for ledger in retained:
        score_pass2(ledger)
    retained.sort(key=lambda ledger: (-ledger.final_score, ledger.candidate_id))
    for rank, ledger in enumerate(retained, 1):
        ledger.reasoning = generate_reasoning(ledger, rank)

    inspected = retained[:inspection_size]
    inspection_rows = [_inspection_row(rank, ledger) for rank, ledger in enumerate(inspected, 1)]
    _write_csv(outputs_dir / "top_300_inspection.csv", inspection_rows)

    breakdown_fields = [
        "rank", "candidate_id", "final_score", "professional_band", "subtype",
        "current_title", "years_experience", *COMPONENT_COLUMNS, "risk_flags",
    ]
    _write_csv(
        outputs_dir / "score_breakdown_top_300.csv",
        inspection_rows,
        fieldnames=breakdown_fields,
    )

    finalists = retained[:final_size]
    previous_score = float("inf")
    submission_rows: list[dict[str, Any]] = []
    for rank, ledger in enumerate(finalists, 1):
        display_score = round(ledger.final_score, 6)
        if display_score >= previous_score:
            display_score = round(previous_score - 0.000001, 6)
        previous_score = display_score
        submission_rows.append(
            {
                "candidate_id": ledger.candidate_id,
                "rank": rank,
                "score": f"{display_score:.6f}",
                "reasoning": ledger.reasoning,
            }
        )
    submission_path = final_dir / "submission.csv"
    _write_csv(submission_path, submission_rows, fieldnames=["candidate_id", "rank", "score", "reasoning"])

    risky_rows = [
        _inspection_row(rank, ledger)
        for rank, ledger in enumerate(finalists, 1)
        if any(not flag.startswith("weak:") for flag in ledger.risk_flags)
        or ledger.components["behavior_fit_score"] < -1.5
    ]
    if risky_rows:
        _write_csv(outputs_dir / "risky_top_100.csv", risky_rows)

    ablation_text = _run_ablation(retained, [ledger.candidate_id for ledger in finalists])
    (outputs_dir / "ablation_summary.md").write_text(ablation_text, encoding="utf-8")

    strict_errors = strict_validate(submission_path, candidates_path, expected_rows=final_size)
    elapsed = time.perf_counter() - started
    max_rss_raw = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    # macOS reports bytes; Linux reports KiB.
    max_rss_mb = max_rss_raw / (1024 * 1024) if max_rss_raw > 10_000_000 else max_rss_raw / 1024

    top20 = finalists[:20]
    summary = {
        "candidate_records_scanned": total,
        "pool_size": len(retained),
        "inspection_size": len(inspected),
        "final_size": len(finalists),
        "runtime_seconds": round(elapsed, 4),
        "max_rss_mb": round(max_rss_mb, 2),
        "submission_sha256": sha256_file(submission_path),
        "strict_validation_errors": strict_errors,
        "all_candidate_band_distribution": dict(all_band_counts),
        "top_2000_band_distribution": dict(band_distribution(retained)),
        "top_100_band_distribution": dict(band_distribution(finalists)),
        "top_20_archetypes": [
            {
                "rank": rank,
                "candidate_id": ledger.candidate_id,
                "band": ledger.band_name,
                "subtype": ledger.subtype,
                "title": ledger.title,
                "score": ledger.final_score,
            }
            for rank, ledger in enumerate(top20, 1)
        ],
        "risky_top_100_count": len(risky_rows),
    }
    (outputs_dir / "run_summary.json").write_text(
        json.dumps(summary, indent=2), encoding="utf-8"
    )
    if strict_errors:
        raise ValueError("Strict validation failed: " + "; ".join(strict_errors))
    return summary
