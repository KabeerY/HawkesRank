from __future__ import annotations

import re

from .evidence import EvidenceLedger


def _short_company(company: str) -> str:
    return company.strip() or "their current company"


def _specific_positive(ledger: EvidenceLedger) -> str:
    text = ledger.current_description.lower()
    if ledger.subtype == "hybrid_retrieval":
        if "35m" in text:
            return "owns hybrid sparse/dense search over a 35M-item corpus with NDCG and latency evidence"
        if "30m" in text:
            return "led a 30M-candidate migration from keyword to embedding search with live A/B validation"
        return "owns hybrid sparse/dense retrieval and its production evaluation"
    if ledger.subtype == "search_ranking":
        if "relevance labeling" in text:
            return "owned the search ranker, relevance-labeling pipeline, features, and training/evaluation workflow"
        if "offline-online" in text:
            return "shipped discovery ranking and analyzed which offline metrics predicted A/B outcomes"
        if "rag-based ranking" in text:
            return "built a 50M-query RAG ranking pipeline and calibrated NDCG, MRR, and recall against A/B outcomes"
        if "recommendation system" in text:
            return "shipped a production recommender with behavioral reranking and live A/B evidence"
        return "owns a production ranking pipeline with explicit relevance evaluation"
    if ledger.subtype == "semantic_search":
        if "faiss" in text:
            return "built sentence-transformer/FAISS semantic search and validated relevance beyond keyword BM25"
        if "recommendation system" in text:
            return "built a 10M-user recommender using embedding similarity, engagement features, and A/B testing"
        return "built embedding-based retrieval with explicit relevance validation"
    if ledger.subtype == "relevance_ownership":
        if "migration from keyword" in text or "migrated" in text:
            return "owns the migration from keyword matching to an evaluated embedding-ranker system"
        if "query understanding" in text and "ranking calibration" in text:
            return "led large-scale relevance infrastructure spanning query understanding, ranking calibration, and operations"
        if "flagship product" in text:
            return "owned the flagship ranking layer, its data pipeline, evaluation framework, and production health"
        return "owns a production relevance system with explicit evaluation and operational evidence"
    if ledger.subtype == "recommendation":
        if "10m" in text:
            return "built a recommendation system serving 10M+ users with feature and A/B-test infrastructure"
        return "built production recommendation and behavioral reranking components"
    if ledger.subtype == "rag_system":
        return "implemented a production RAG pipeline spanning ingestion, embeddings, retrieval, and evaluation"
    if ledger.subtype == "historical_search_evidence":
        return "shows prior professional search/ranking evidence despite a less direct current assignment"
    if ledger.subtype == "ml_platform":
        return "operates production ML pipelines, feature infrastructure, monitoring, and drift checks"
    if ledger.subtype == "applied_ml":
        return "has shipped applied-ML work with concrete modeling and production evidence"
    if ledger.subtype == "cv_speech_ml":
        return "has hands-on production ML training and inference experience"
    if ledger.subtype in {"data_platform", "backend_platform"}:
        return "brings strong Python/data-platform foundations adjacent to production ML"
    return "shows relevant engineering evidence in the current career record"


def _concern(ledger: EvidenceLedger) -> str:
    concerns: list[str] = []
    if ledger.years_experience > 11:
        concerns.append(f"{ledger.years_experience:.1f} years is above the preferred experience band")
    elif ledger.years_experience < 4:
        concerns.append(f"{ledger.years_experience:.1f} years is below the preferred experience band")
    if not ledger.behavior["open_to_work"]:
        concerns.append("not marked open to work")
    if ledger.behavior["days_since_active"] > 120:
        concerns.append(f"last active {ledger.behavior['days_since_active']} days before the fixed reference date")
    if ledger.behavior["recruiter_response_rate"] < 0.35:
        concerns.append(f"recruiter response rate is only {ledger.behavior['recruiter_response_rate']:.2f}")
    if ledger.logistics["notice_period_days"] > 60:
        concerns.append(f"notice period is {ledger.logistics['notice_period_days']} days")
    if (
        not ledger.logistics["target_location"]
        and not ledger.logistics["willing_to_relocate"]
    ):
        concerns.append("location/relocation fit is weaker")
    if ledger.all_services:
        concerns.append("career history is entirely services/consulting")
    hard_risk = [flag for flag in ledger.risk_flags if not flag.startswith("weak:")]
    if hard_risk:
        concerns.append("profile contains corroboration concerns")
    if not concerns and ledger.subtype == "recommendation" and ledger.raw["evaluation"] < 0.8:
        concerns.append("ranking-evaluation depth is less explicit than the strongest profiles")
    return " and ".join(concerns[:2]) if concerns else ""


def generate_reasoning(ledger: EvidenceLedger, rank: int) -> str:
    title = ledger.title or "Candidate"
    company = _short_company(ledger.company)
    positive = _specific_positive(ledger)
    concern = _concern(ledger)
    response = ledger.behavior["recruiter_response_rate"]
    notice = ledger.logistics["notice_period_days"]

    if concern:
        variants = [
            (
                f"{title} with {ledger.years_experience:.1f} years at {company}; {positive}. "
                f"Main concern: {concern}."
            ),
            (
                f"Career evidence from this {title} ({ledger.years_experience:.1f} years) {positive}. "
                f"Hiring feasibility is tempered because {concern}."
            ),
            (
                f"At {company}, this {title} {positive}, directly supporting Redrob's intelligence-layer mandate. "
                f"The profile records a {response:.2f} recruiter response rate and {notice}-day notice; {concern}."
            ),
            (
                f"This {ledger.years_experience:.1f}-year {title} {positive}. "
                f"Relative to nearby candidates, {concern}."
            ),
        ]
    else:
        variants = [
            (
                f"{title} with {ledger.years_experience:.1f} years at {company}; {positive}. "
                f"The profile is open to work with a {response:.2f} recruiter response rate and {notice}-day notice."
            ),
            (
                f"Career evidence from this {title} ({ledger.years_experience:.1f} years) {positive}. "
                f"Availability signals are supportive: open to work, {response:.2f} response rate, and {notice}-day notice."
            ),
            (
                f"At {company}, this {title} {positive}, directly supporting Redrob's intelligence-layer mandate. "
                f"They are open to work and the recorded notice period is {notice} days."
            ),
            (
                f"This {ledger.years_experience:.1f}-year {title} {positive}. "
                f"A {response:.2f} response rate and {notice}-day notice make the profile workable for outreach."
            ),
        ]
    reason = variants[(rank - 1) % len(variants)]
    reason = re.sub(r"\s+", " ", reason).strip()
    return reason
