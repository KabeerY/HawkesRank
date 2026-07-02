from __future__ import annotations

import math
import re
from dataclasses import asdict, dataclass, field
from datetime import date
from typing import Any, Iterable

from .config import (
    BAND_NAMES,
    DATA_TITLE_TERMS,
    ML_TITLE_TERMS,
    NONTECH_TITLE_TERMS,
    REFERENCE_DATE,
    SENIOR_TITLE_TERMS,
    SERVICE_COMPANIES,
    SOFTWARE_TITLE_TERMS,
    TARGET_LOCATION_TERMS,
)


def _rx(*phrases: str) -> re.Pattern[str]:
    return re.compile("|".join(f"(?:{p})" for p in phrases), re.IGNORECASE)


PATTERNS: dict[str, re.Pattern[str]] = {
    "retrieval": _rx(
        r"information retrieval", r"semantic search", r"hybrid (?:search|retrieval)",
        r"dense retrieval", r"sparse (?:retrieval|search)", r"search (?:system|product|engine|infrastructure)",
        r"search and discovery", r"search & discovery", r"query understanding", r"query expansion",
        r"document retrieval", r"candidate sourcing", r"matching layer", r"content matching",
    ),
    "ranking": _rx(
        r"ranking (?:layer|pipeline|model|system|algorithm)", r"ranker", r"re-ranking", r"reranking",
        r"learning[- ]to[- ]rank", r"learning to rank", r"relevance", r"personalization",
        r"recommendation system", r"recommendation-style", r"recommendations-heavy",
        r"collaborative filtering", r"matrix factorization", r"discovery feed",
    ),
    "vector_embedding": _rx(
        r"embedding", r"sentence[- ]transform", r"dense vector", r"vector (?:search|database|index|retrieval)",
        r"faiss", r"pinecone", r"qdrant", r"weaviate", r"milvus", r"pgvector", r"hnsw",
        r"bge(?:[- ](?:base|large))?", r"mpnet", r"bm25", r"opensearch", r"elasticsearch",
    ),
    "evaluation": _rx(
        r"ndcg(?:@\d+)?", r"mrr", r"mean average precision", r"map@\d+", r"recall@\w+",
        r"precision@\w+", r"a/b test", r"ab test", r"offline[- /]online", r"online[- /]offline",
        r"human (?:relevance )?judg", r"relevance label", r"evaluation framework", r"eval framework",
        r"held-out eval", r"offline benchmark", r"engagement metric", r"click-through", r"dwell time",
        r"optimization target", r"metric correlation", r"quality regression", r"feedback loop",
    ),
    "production": _rx(
        r"production", r"shipped", r"deployed", r"serving", r"operated", r"live a/b",
        r"real users", r"\d+[mkb]?\+? (?:users|queries|items|documents)", r"at scale",
        r"latency", r"p95", r"qps", r"on-call", r"monitoring", r"rollback", r"index refresh",
        r"versioning", r"retraining cadence", r"drift", r"inference service", r"launch improved",
    ),
    "ownership": _rx(
        r"\bowned\b", r"\bled\b", r"\bdesigned\b", r"\bbuilt\b", r"\bimplemented\b",
        r"\barchitected\b", r"\bdrove\b", r"\bmigrated\b", r"from scratch", r"end[- ]to[- ]end",
        r"complete overhaul", r"rollout", r"mentored", r"grew (?:the )?team",
    ),
    "applied_ml": _rx(
        r"machine learning", r"\bml\b", r"model training", r"predictive model", r"feature engineering",
        r"xgboost", r"lightgbm", r"scikit[- ]learn", r"pytorch", r"tensorflow", r"nlp",
        r"transformer", r"classification", r"forecasting", r"fraud detection", r"churn prediction",
        r"model deployment", r"model serving", r"feature store", r"mlflow", r"kubeflow",
    ),
    "python_platform": _rx(
        r"python", r"fastapi", r"flask", r"backend", r"microservices?", r"api layer",
        r"data pipeline", r"feature pipeline", r"spark", r"airflow", r"kafka", r"sql",
        r"postgres", r"redis", r"docker", r"kubernetes", r"infrastructure", r"distributed system",
    ),
    "product_shipper": _rx(
        r"product", r"pm", r"user", r"recruiter", r"launch", r"shipped", r"conversion",
        r"retention", r"revenue", r"engagement", r"time-to-shortlist", r"working v1",
        r"customer-facing", r"business outcome", r"production load",
    ),
    "rag_llm": _rx(
        r"\brag\b", r"llm", r"langchain", r"llamaindex", r"prompt engineering",
        r"fine[- ]tun", r"lora", r"qlora", r"openai (?:api|embedding)", r"generative ai", r"genai",
    ),
    "cv_speech": _rx(
        r"computer vision", r"image classification", r"object detection", r"opencv", r"resnet",
        r"\bcnn\b", r"speech recognition", r"\btts\b", r"robotics", r"\byolo\b", r"\bgan",
    ),
    "research": _rx(
        r"research-only", r"pure research", r"academic lab", r"publication", r"published paper",
        r"\bphd\b", r"research scientist", r"research environment",
    ),
    "side_project": _rx(
        r"side project", r"self[- ]directed", r"online course", r"self[- ]learn", r"ai enthusiast",
        r"experimenting with", r"played with", r"curious about", r"transitioning toward",
        r"grow (?:my|into)", r"learning modern", r"haven't done it in a professional capacity",
        r"professional experience .* limited", r"recent \(under 12 months\)",
    ),
    "limited_ownership": _rx(
        r"deployment was handled by", r"built by another team", r"my own modeling work was secondary",
        r"my role was more on the modeling side than the production", r"still building depth",
        r"wouldn't call myself an ml specialist", r"limited .* exposure", r"not the model itself",
    ),
    "hands_off": _rx(
        r"architecture-only", r"moved into architecture", r"haven't written production code",
        r"people management only", r"no longer hands-on",
    ),
}


FIELD_WEIGHTS = {
    "current_career": 1.0,
    "prior_career": 0.58,
    "headline_title": 0.42,
    "summary": 0.34,
    "skills": 0.10,
}


@dataclass
class EvidenceLedger:
    candidate_id: str
    title: str
    headline: str
    company: str
    industry: str
    location: str
    country: str
    years_experience: float
    current_description: str
    current_start_date: str
    career_titles: list[str]
    skill_names: list[str]
    assessments: dict[str, float]
    matched: dict[str, dict[str, list[str]]]
    raw: dict[str, float]
    band: int
    band_name: str
    subtype: str
    positive_evidence: list[str]
    negative_evidence: list[str]
    risk_flags: list[str]
    behavior: dict[str, Any]
    logistics: dict[str, Any]
    all_services: bool
    skill_corroboration: float
    pass1_score: float = 0.0
    components: dict[str, float] = field(default_factory=dict)
    final_score: float = 0.0
    reasoning: str = ""

    def flat_dict(self) -> dict[str, Any]:
        result = asdict(self)
        result["positive_evidence"] = " | ".join(self.positive_evidence)
        result["negative_evidence"] = " | ".join(self.negative_evidence)
        result["risk_flags"] = " | ".join(self.risk_flags)
        result["career_titles"] = " | ".join(self.career_titles)
        result["skill_names"] = " | ".join(self.skill_names)
        return result


@dataclass
class Pass1State:
    candidate_id: str
    band: int
    band_name: str
    pass1_score: float
    title: str
    years_experience: float
    current_company: str
    location: str


def _contains_any(text: str, terms: Iterable[str]) -> bool:
    value = text.lower()
    return any(term in value for term in terms)


def _terms(text: str, pattern: re.Pattern[str], limit: int = 12) -> list[str]:
    found: list[str] = []
    seen: set[str] = set()
    for match in pattern.finditer(text):
        term = re.sub(r"\s+", " ", match.group(0).strip().lower())
        if term and term not in seen:
            found.append(term)
            seen.add(term)
        if len(found) >= limit:
            break
    return found


def _parse_date(value: str) -> date:
    try:
        return date.fromisoformat(value)
    except (TypeError, ValueError):
        return REFERENCE_DATE


def _clamp(value: float, low: float, high: float) -> float:
    return max(low, min(high, value))


def _relevant_sentence(text: str) -> str:
    sentences = re.split(r"(?<=[.!?])\s+", text.strip())
    priority = re.compile(
        r"ranking|retrieval|search|recommend|relevance|embedding|a/b|ndcg|mrr|production|shipped|deployed",
        re.IGNORECASE,
    )
    for sentence in sentences:
        if priority.search(sentence):
            return sentence.strip()
    return sentences[0].strip() if sentences else ""


def _classify_subtype(current_text: str, combined_career: str) -> str:
    current = current_text.lower()
    if re.search(r"learning[- ]to[- ]rank|ranking layer|ranking pipeline|ranking models", current):
        return "search_ranking"
    if re.search(r"hybrid (?:search|retrieval)|sparse and dense|bm25 .* dense", current):
        return "hybrid_retrieval"
    if re.search(r"semantic search|sentence-transform|query expansion", current):
        return "semantic_search"
    if re.search(r"embedding-based search|keyword-based .*search|matching layer|search and discovery", current):
        return "relevance_ownership"
    if re.search(r"recommendation system|recommendation-style|collaborative filtering|personalization", current):
        return "recommendation"
    if (
        (PATTERNS["retrieval"].search(current) or PATTERNS["ranking"].search(current))
        and PATTERNS["ownership"].search(current)
    ):
        # Deliberately recognize plain-language professional ownership. Strong
        # evidence should not require fashionable IR library names.
        return "relevance_ownership"
    if re.search(r"\brag\b|retrieval.augmented", current):
        return "rag_system"
    if re.search(r"mlflow|kubeflow|feature store|model monitoring", current):
        return "ml_platform"
    if PATTERNS["applied_ml"].search(current):
        if PATTERNS["cv_speech"].search(current):
            return "cv_speech_ml"
        return "applied_ml"
    if PATTERNS["python_platform"].search(current):
        if re.search(r"spark|airflow|warehouse|data pipeline|dbt|kafka", current):
            return "data_platform"
        return "backend_platform"
    if re.search(r"frontend|mobile|devops|qa|full-stack|java backend", current):
        return "software_engineering"
    if PATTERNS["ranking"].search(combined_career) or PATTERNS["retrieval"].search(combined_career):
        return "historical_search_evidence"
    return "nontechnical_or_other"


def _strong_senior_scope(text: str) -> bool:
    return bool(
        re.search(
            r"large-scale|\b(?:30|35|50)m\+?\b|billions?|millions of (?:users|items|queries|documents)"
            r"|team of \d|led (?:the )?migration|owned the end-to-end|flagship product"
            r"|personalization infrastructure|complete overhaul|grew from .* engineers",
            text,
            re.IGNORECASE,
        )
    )


def extract_pass1_state(record: dict[str, Any]) -> Pass1State:
    """Cheap first-pass state: searches only broad evidence, without building a full ledger."""
    profile = record["profile"]
    signals = record["redrob_signals"]
    careers = record["career_history"]
    current = next((job for job in careers if job.get("is_current")), careers[0])
    current_text = f"{current.get('title', '')} {current.get('description', '')}"
    career_text = " ".join(
        f"{job.get('title', '')} {job.get('description', '')}" for job in careers
    )
    summary = profile.get("summary", "")
    title = profile.get("current_title", "")
    title_lower = title.lower()

    direct_current = bool(
        PATTERNS["retrieval"].search(current_text) or PATTERNS["ranking"].search(current_text)
    )
    rag_direct = bool(PATTERNS["rag_llm"].search(current_text))
    evaluation = bool(PATTERNS["evaluation"].search(career_text))
    vector = bool(PATTERNS["vector_embedding"].search(career_text))
    production = bool(PATTERNS["production"].search(career_text))
    ownership = bool(PATTERNS["ownership"].search(current_text))
    ml_career = bool(PATTERNS["applied_ml"].search(career_text))
    limited = bool(PATTERNS["limited_ownership"].search(current_text + " " + summary))
    side_only = bool(PATTERNS["side_project"].search(summary)) and not (direct_current or ml_career)
    senior_title = _contains_any(title_lower, SENIOR_TITLE_TERMS)
    ml_title = _contains_any(title_lower, ML_TITLE_TERMS)
    data_title = _contains_any(title_lower, DATA_TITLE_TERMS)
    software_title = _contains_any(title_lower, SOFTWARE_TITLE_TERMS)
    nontech_title = _contains_any(title_lower, NONTECH_TITLE_TERMS)
    data_current = bool(
        re.search(r"spark|airflow|warehouse|data pipeline|dbt|kafka|analytics", current_text, re.I)
    )

    strong_ml_current = bool(
        re.search(
            r"model training|predictive model|recommendation-style|computer vision models"
            r"|nlp pipelines|fraud-detection|time-series forecasting|churn prediction",
            current_text,
            re.IGNORECASE,
        )
    )
    if (
        senior_title
        and direct_current
        and ownership
        and production
        and evaluation
        and _strong_senior_scope(current_text + " " + summary)
    ):
        band = 5
    elif (
        (direct_current or (rag_direct and vector))
        and ownership
        and production
        and (evaluation or vector)
        and not limited
    ):
        band = 4
    elif (ml_title and ml_career) or strong_ml_current:
        band = 3
    elif data_current or data_title:
        band = 2
    elif software_title or PATTERNS["python_platform"].search(current_text):
        band = 1
    else:
        band = 0
    if side_only and band >= 3:
        band = 1
    if nontech_title and not direct_current:
        band = 0
    if limited and band >= 4:
        band = 3

    evidence = (
        8.0 * int(direct_current)
        + 5.0 * int(evaluation)
        + 4.0 * int(vector)
        + 3.0 * int(production)
        + 2.0 * int(ownership)
        + 1.5 * int(ml_career)
        # Preserve recall for the small, high-value ML/search strata when the
        # 2,000-profile heap is crowded by generic data/backend profiles.
        + 5.0 * int(ml_title)
    )
    behavior = (
        0.8 * int(signals.get("open_to_work_flag", False))
        + 0.8 * float(signals.get("recruiter_response_rate", 0.0))
    )
    score = round(band * 100.0 + evidence + behavior, 6)
    return Pass1State(
        candidate_id=record["candidate_id"],
        band=band,
        band_name=BAND_NAMES[band],
        pass1_score=score,
        title=title,
        years_experience=float(profile.get("years_of_experience", 0.0)),
        current_company=profile.get("current_company", ""),
        location=profile.get("location", ""),
    )


def extract_ledger(record: dict[str, Any]) -> EvidenceLedger:
    profile = record["profile"]
    signals = record["redrob_signals"]
    careers = record["career_history"]
    current = next((job for job in careers if job.get("is_current")), careers[0])
    prior = [job for job in careers if job is not current]

    texts = {
        "current_career": " ".join([current.get("title", ""), current.get("description", "")]),
        "prior_career": " ".join(
            f"{job.get('title', '')} {job.get('description', '')}" for job in prior
        ),
        "headline_title": " ".join(
            [profile.get("current_title", ""), profile.get("headline", "")]
        ),
        "summary": profile.get("summary", ""),
        "skills": " ".join(skill.get("name", "") for skill in record.get("skills", [])),
    }

    matched: dict[str, dict[str, list[str]]] = {}
    raw: dict[str, float] = {}
    for group, pattern in PATTERNS.items():
        matched[group] = {}
        score = 0.0
        for field_name, text in texts.items():
            terms = _terms(text, pattern)
            matched[group][field_name] = terms
            # Diminishing returns keep keyword repetition from manufacturing evidence.
            score += FIELD_WEIGHTS[field_name] * min(3.0, math.sqrt(len(terms)) if terms else 0.0)
        raw[group] = round(score, 4)

    title = profile.get("current_title", "")
    title_lower = title.lower()
    combined_career = f"{texts['current_career']} {texts['prior_career']}"
    current_text = texts["current_career"]
    subtype = _classify_subtype(current_text, combined_career)

    direct_current = bool(
        PATTERNS["retrieval"].search(current_text) or PATTERNS["ranking"].search(current_text)
    )
    direct_career_strength = raw["retrieval"] + raw["ranking"]
    evaluation_career = bool(
        matched["evaluation"]["current_career"] or matched["evaluation"]["prior_career"]
    )
    vector_career = bool(
        matched["vector_embedding"]["current_career"] or matched["vector_embedding"]["prior_career"]
    )
    production_career = bool(
        matched["production"]["current_career"] or matched["production"]["prior_career"]
    )
    ownership_current = bool(matched["ownership"]["current_career"])
    ml_career = bool(
        matched["applied_ml"]["current_career"] or matched["applied_ml"]["prior_career"]
    )
    data_current = bool(
        re.search(r"spark|airflow|warehouse|data pipeline|dbt|kafka|analytics", current_text, re.I)
    )

    senior_title = _contains_any(title_lower, SENIOR_TITLE_TERMS)
    ml_title = _contains_any(title_lower, ML_TITLE_TERMS)
    data_title = _contains_any(title_lower, DATA_TITLE_TERMS)
    software_title = _contains_any(title_lower, SOFTWARE_TITLE_TERMS)
    nontech_title = _contains_any(title_lower, NONTECH_TITLE_TERMS)

    limited = bool(PATTERNS["limited_ownership"].search(current_text + " " + texts["summary"]))
    side_only = bool(PATTERNS["side_project"].search(texts["summary"])) and not (
        direct_current or ml_career
    )

    rag_direct = bool(PATTERNS["rag_llm"].search(current_text))
    strong_ml_current = bool(
        re.search(
            r"model training|predictive model|recommendation-style|computer vision models"
            r"|nlp pipelines|fraud-detection|time-series forecasting|churn prediction",
            current_text,
            re.IGNORECASE,
        )
    )
    if (
        senior_title
        and direct_career_strength >= 1.8
        and ownership_current
        and production_career
        and evaluation_career
        and _strong_senior_scope(current_text + " " + texts["summary"])
    ):
        band = 5
    elif (
        (direct_current or (rag_direct and vector_career))
        and ownership_current
        and production_career
        and (evaluation_career or (vector_career and direct_career_strength >= 2.0))
        and not limited
    ):
        band = 4
    elif (ml_title and ml_career) or strong_ml_current:
        band = 3
    elif data_current or data_title:
        band = 2
    elif software_title or PATTERNS["python_platform"].search(current_text):
        band = 1
    else:
        band = 0

    # Evidence ceilings: vocabulary and side projects cannot create a higher professional state.
    if side_only and band >= 3:
        band = 1
    if nontech_title and not direct_current:
        band = 0
    if limited and band >= 4:
        band = 3

    skill_names = [skill.get("name", "") for skill in record.get("skills", [])]
    career_lower = combined_career.lower()
    corroborated: list[str] = []
    for skill in record.get("skills", []):
        name = skill.get("name", "")
        if name and name.lower() in career_lower:
            corroborated.append(name)
    relevant_assessments = {
        name: float(value)
        for name, value in signals.get("skill_assessment_scores", {}).items()
        if PATTERNS["retrieval"].search(name)
        or PATTERNS["ranking"].search(name)
        or PATTERNS["vector_embedding"].search(name)
        or PATTERNS["applied_ml"].search(name)
        or PATTERNS["python_platform"].search(name)
    }
    skill_corroboration = _clamp(
        len(corroborated) * 0.45
        + sum(1 for score in relevant_assessments.values() if score >= 60) * 0.6,
        0.0,
        5.0,
    )

    signup = _parse_date(signals.get("signup_date", ""))
    last_active = _parse_date(signals.get("last_active_date", ""))
    active_days = max(0, (REFERENCE_DATE - last_active).days)
    response_rate = float(signals.get("recruiter_response_rate", 0.0))
    response_hours = float(signals.get("avg_response_time_hours", 999.0))

    behavior = {
        "open_to_work": bool(signals.get("open_to_work_flag", False)),
        "last_active_date": signals.get("last_active_date", ""),
        "days_since_active": active_days,
        "recruiter_response_rate": response_rate,
        "avg_response_time_hours": response_hours,
        "interview_completion_rate": float(signals.get("interview_completion_rate", 0.0)),
        "offer_acceptance_rate": float(signals.get("offer_acceptance_rate", -1.0)),
        "github_activity_score": float(signals.get("github_activity_score", -1.0)),
        "verified_email": bool(signals.get("verified_email", False)),
        "verified_phone": bool(signals.get("verified_phone", False)),
        "linkedin_connected": bool(signals.get("linkedin_connected", False)),
        "saved_by_recruiters_30d": int(signals.get("saved_by_recruiters_30d", 0)),
    }

    location = profile.get("location", "")
    logistics = {
        "notice_period_days": int(signals.get("notice_period_days", 180)),
        "willing_to_relocate": bool(signals.get("willing_to_relocate", False)),
        "preferred_work_mode": signals.get("preferred_work_mode", ""),
        "target_location": _contains_any(location, TARGET_LOCATION_TERMS),
        "country": profile.get("country", ""),
    }

    companies = [job.get("company", "").strip().lower() for job in careers]
    all_services = bool(companies) and all(company in SERVICE_COMPANIES for company in companies)

    risk_flags: list[str] = []
    weak_flags: list[str] = []
    total_months = round(float(profile.get("years_of_experience", 0.0)) * 12)
    expert_zero = [
        skill.get("name", "")
        for skill in record.get("skills", [])
        if skill.get("proficiency") == "expert" and skill.get("duration_months") == 0
    ]
    if expert_zero:
        risk_flags.append("expert_zero_duration:" + "/".join(expert_zero[:4]))
    if last_active < signup:
        weak_flags.append("activity_before_signup")
    salary = signals.get("expected_salary_range_inr_lpa", {})
    if float(salary.get("min", 0)) > float(salary.get("max", 0)):
        weak_flags.append("salary_range_inverted")
    long_skills = [
        skill.get("name", "")
        for skill in record.get("skills", [])
        if int(skill.get("duration_months", 0)) > total_months + 12
    ]
    if long_skills:
        weak_flags.append("skill_duration_overrun")
    descriptions = [job.get("description", "") for job in careers]
    if len(descriptions) > len(set(descriptions)):
        weak_flags.append("repeated_role_description")

    unsupported_ai = bool(
        (matched["rag_llm"]["skills"] or matched["vector_embedding"]["skills"])
        and not (ml_career or direct_current)
    )
    title_career_mismatch = nontech_title and bool(
        PATTERNS["applied_ml"].search(current_text) or PATTERNS["retrieval"].search(current_text)
    )
    if unsupported_ai and side_only:
        risk_flags.append("unsupported_ai_skill_stuffing")
    if title_career_mismatch and unsupported_ai:
        risk_flags.append("title_career_ai_mismatch")
    if len(weak_flags) >= 3 and unsupported_ai:
        risk_flags.append("multiple_contradictions_with_ai_claims")
    risk_flags.extend("weak:" + flag for flag in weak_flags)

    negatives: list[str] = []
    if side_only:
        negatives.append("AI evidence is limited to courses, experimentation, or side projects")
    if limited:
        negatives.append("profile states limited ownership of modeling or deployment")
    if all_services:
        negatives.append("career history is entirely in named services/consulting companies")
    if raw["cv_speech"] > 0.8 and direct_career_strength < 1.0:
        negatives.append("career evidence is primarily computer vision or speech rather than NLP/IR")
    if not behavior["open_to_work"]:
        negatives.append("not marked open to work")
    if active_days > 120:
        negatives.append(f"inactive for {active_days} days at the fixed reference date")
    if logistics["notice_period_days"] > 60:
        negatives.append(f"{logistics['notice_period_days']}-day notice period")

    positive = [_relevant_sentence(current.get("description", ""))]
    if relevant_assessments:
        best_name, best_score = max(relevant_assessments.items(), key=lambda item: item[1])
        positive.append(f"{best_name} assessment {best_score:.1f}/100")
    positive = [item for item in positive if item]

    return EvidenceLedger(
        candidate_id=record["candidate_id"],
        title=title,
        headline=profile.get("headline", ""),
        company=profile.get("current_company", ""),
        industry=profile.get("current_industry", ""),
        location=location,
        country=profile.get("country", ""),
        years_experience=float(profile.get("years_of_experience", 0.0)),
        current_description=current.get("description", ""),
        current_start_date=current.get("start_date", ""),
        career_titles=[job.get("title", "") for job in careers],
        skill_names=skill_names,
        assessments={name: float(value) for name, value in signals.get("skill_assessment_scores", {}).items()},
        matched=matched,
        raw=raw,
        band=band,
        band_name=BAND_NAMES[band],
        subtype=subtype,
        positive_evidence=positive,
        negative_evidence=negatives,
        risk_flags=risk_flags,
        behavior=behavior,
        logistics=logistics,
        all_services=all_services,
        skill_corroboration=round(skill_corroboration, 4),
    )
