from __future__ import annotations

from collections import Counter

from .config import BAND_BASE, BAND_CEILING, REFERENCE_DATE
from .evidence import EvidenceLedger


def _clamp(value: float, low: float, high: float) -> float:
    return max(low, min(high, value))


SUBTYPE_SCORE = {
    "search_ranking": 10.0,
    "hybrid_retrieval": 10.0,
    "semantic_search": 9.0,
    # Plain-language owners of evaluated matching/search systems should not
    # lose to profiles that repeat fashionable retrieval vocabulary.
    "relevance_ownership": 12.0,
    "recommendation": 7.5,
    "rag_system": 6.5,
    "historical_search_evidence": 5.5,
    "ml_platform": 4.5,
    "applied_ml": 4.0,
    "backend_platform": 3.0,
    "data_platform": 2.5,
    "cv_speech_ml": 1.0,
    "software_engineering": 0.5,
    "nontechnical_or_other": 0.0,
}


def score_pass1(ledger: EvidenceLedger) -> float:
    raw = ledger.raw
    evidence = (
        4.5 * (raw["retrieval"] + raw["ranking"])
        + 2.0 * raw["evaluation"]
        + 1.5 * raw["production"]
        + 1.0 * raw["ownership"]
        + 0.7 * raw["applied_ml"]
        + 0.3 * raw["python_platform"]
    )
    behavior_tiebreak = (
        0.8 * int(ledger.behavior["open_to_work"])
        + 0.8 * int(ledger.behavior["days_since_active"] <= 90)
        + 0.8 * ledger.behavior["recruiter_response_rate"]
    )
    ledger.pass1_score = round(ledger.band * 100.0 + evidence + behavior_tiebreak, 6)
    return ledger.pass1_score


def _experience_fit(years: float) -> float:
    if 5.0 <= years <= 9.0:
        return 8.0
    if 4.0 <= years < 5.0 or 9.0 < years <= 11.0:
        return 5.5
    if 3.0 <= years < 4.0 or 11.0 < years <= 13.0:
        return 2.5
    return 0.0


def _behavior_score(ledger: EvidenceLedger) -> float:
    b = ledger.behavior
    score = 0.0
    score += 1.8 if b["open_to_work"] else -1.2
    days = b["days_since_active"]
    if days <= 30:
        score += 1.5
    elif days <= 75:
        score += 1.0
    elif days <= 120:
        score += 0.2
    elif days <= 180:
        score -= 0.8
    else:
        score -= 1.8
    score += 2.0 * (b["recruiter_response_rate"] - 0.5)
    if b["avg_response_time_hours"] <= 24:
        score += 0.8
    elif b["avg_response_time_hours"] > 120:
        score -= 0.8
    score += 0.8 * (b["interview_completion_rate"] - 0.5)
    score += 0.35 if b["verified_email"] and b["verified_phone"] else 0.0
    score += 0.25 if b["linkedin_connected"] else 0.0
    score += 0.45 if b["github_activity_score"] >= 35 else 0.0
    score += min(0.5, b["saved_by_recruiters_30d"] / 100.0)
    return _clamp(score, -4.0, 4.0)


def _logistics_score(ledger: EvidenceLedger) -> float:
    logistics = ledger.logistics
    score = 0.0
    notice = logistics["notice_period_days"]
    if notice <= 30:
        score += 1.6
    elif notice <= 60:
        score += 0.8
    elif notice <= 90:
        score -= 0.5
    else:
        score -= 1.5
    if logistics["target_location"]:
        score += 1.2
    elif logistics["willing_to_relocate"]:
        score += 0.8
    elif logistics["country"].lower() != "india":
        score -= 1.4
    else:
        score -= 0.4
    if logistics["preferred_work_mode"] in {"hybrid", "flexible", "onsite"}:
        score += 0.25
    return _clamp(score, -3.0, 3.0)


def _near_miss_penalty(ledger: EvidenceLedger) -> float:
    raw = ledger.raw
    penalty = 0.0
    joined_negatives = " ".join(ledger.negative_evidence).lower()
    if "side projects" in joined_negatives or "courses" in joined_negatives:
        penalty += 8.0
    if "limited ownership" in joined_negatives:
        penalty += 5.0
    if ledger.all_services:
        penalty += 5.0
    if ledger.subtype == "cv_speech_ml" and raw["retrieval"] + raw["ranking"] < 1.0:
        penalty += 6.0
    if ledger.band >= 3 and raw["retrieval"] + raw["ranking"] < 0.8:
        penalty += 3.0
    if ledger.subtype == "recommendation" and raw["production"] < 0.8:
        penalty += 3.0
    if ledger.band >= 4 and raw["evaluation"] < 0.55:
        penalty += 4.0
    if ledger.band >= 4 and raw["ownership"] < 0.7:
        penalty += 3.0
    if ledger.years_experience > 13.0:
        penalty += 3.0
    elif ledger.years_experience < 3.0:
        penalty += 2.0
    # This is a hard-negative gate inside a professional band, not a generic
    # behavior boost: an unavailable, unresponsive expert is a weaker shortlist
    # choice than a comparably proven and reachable one.
    if (
        ledger.band >= 4
        and not ledger.behavior["open_to_work"]
        and ledger.behavior["recruiter_response_rate"] < 0.20
    ):
        penalty += 7.0
    if (
        ledger.band >= 4
        and ledger.behavior["days_since_active"] > 120
        and ledger.behavior["recruiter_response_rate"] < 0.20
    ):
        penalty += 3.0
    if ledger.band >= 4 and ledger.behavior["days_since_active"] > 180:
        penalty += 2.0
    return _clamp(penalty, 0.0, 18.0)


def _risk_penalty(ledger: EvidenceLedger) -> float:
    flags = ledger.risk_flags
    hard = sum(
        flag.startswith("expert_zero_duration")
        or flag == "multiple_contradictions_with_ai_claims"
        for flag in flags
    )
    medium = sum(
        flag in {"unsupported_ai_skill_stuffing", "title_career_ai_mismatch"}
        for flag in flags
    )
    weak = sum(flag.startswith("weak:") for flag in flags)
    penalty = hard * 9.0 + medium * 3.5 + max(0, weak - 1) * 0.45
    return _clamp(penalty, 0.0, 20.0)


def score_pass2(ledger: EvidenceLedger) -> float:
    raw = ledger.raw
    components = {
        "professional_band_score": BAND_BASE[ledger.band],
        "current_work_subtype_score": SUBTYPE_SCORE.get(ledger.subtype, 0.0),
        "retrieval_search_ranking_score": _clamp(
            4.8 * (raw["retrieval"] + raw["ranking"]), 0.0, 20.0
        ),
        "vector_embedding_hybrid_score": _clamp(3.2 * raw["vector_embedding"], 0.0, 8.0),
        "production_ml_system_score": _clamp(4.0 * raw["production"], 0.0, 12.0),
        "evaluation_maturity_score": _clamp(5.0 * raw["evaluation"], 0.0, 12.0),
        "python_backend_platform_score": _clamp(2.0 * raw["python_platform"], 0.0, 5.0),
        "product_shipper_score": _clamp(2.0 * raw["product_shipper"], 0.0, 5.0),
        "experience_fit_score": _experience_fit(ledger.years_experience),
        "skill_corroboration_score": ledger.skill_corroboration,
        "behavior_fit_score": _behavior_score(ledger),
        "logistics_fit_score": _logistics_score(ledger),
        "near_miss_penalty": _near_miss_penalty(ledger),
        "coherence_risk_penalty": _risk_penalty(ledger),
    }
    positive_keys = [key for key in components if not key.endswith("penalty")]
    total = sum(components[key] for key in positive_keys)
    total -= components["near_miss_penalty"] + components["coherence_risk_penalty"]
    total = min(total, BAND_CEILING[ledger.band])
    ledger.components = {key: round(value, 6) for key, value in components.items()}
    ledger.final_score = round(total, 6)
    return ledger.final_score


def ablation_score(ledger: EvidenceLedger, variant: str) -> float:
    if not ledger.components:
        score_pass2(ledger)
    components = ledger.components
    score = ledger.final_score
    if variant == "no_behavior_logistics":
        score -= components["behavior_fit_score"] + components["logistics_fit_score"]
    elif variant == "no_skill_corroboration":
        score -= components["skill_corroboration_score"]
    elif variant == "no_risk":
        score += components["coherence_risk_penalty"]
    elif variant == "no_near_miss":
        score += components["near_miss_penalty"]
    else:
        raise ValueError(f"Unknown ablation variant: {variant}")
    return round(score, 6)


def band_distribution(ledgers: list[EvidenceLedger]) -> Counter[str]:
    return Counter(ledger.band_name for ledger in ledgers)
