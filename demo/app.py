from __future__ import annotations

import csv
import io
import json
import sys
from pathlib import Path
from typing import Any

import streamlit as st


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from hawkesrank.evidence import EvidenceLedger, extract_ledger  # noqa: E402
from hawkesrank.reasoning import generate_reasoning  # noqa: E402
from hawkesrank.scoring import score_pass2  # noqa: E402


MAX_PROFILES = 100


def parse_candidate_file(payload: bytes) -> list[dict[str, Any]]:
    text = payload.decode("utf-8-sig").strip()
    if not text:
        raise ValueError("The uploaded file is empty.")
    if text.startswith("["):
        records = json.loads(text)
    else:
        records = [json.loads(line) for line in text.splitlines() if line.strip()]
    if not isinstance(records, list) or not all(isinstance(item, dict) for item in records):
        raise ValueError("Expected a JSON array or one JSON object per JSONL line.")
    if len(records) > MAX_PROFILES:
        raise ValueError(f"The sandbox accepts at most {MAX_PROFILES} profiles per run.")
    required = {"candidate_id", "profile", "career_history", "skills", "redrob_signals"}
    for index, record in enumerate(records, start=1):
        missing = required - record.keys()
        if missing:
            raise ValueError(f"Profile {index} is missing: {', '.join(sorted(missing))}")
    return records


def rank_records(records: list[dict[str, Any]]) -> list[EvidenceLedger]:
    ledgers = [extract_ledger(record) for record in records]
    for ledger in ledgers:
        score_pass2(ledger)
    ledgers.sort(key=lambda ledger: (-ledger.final_score, ledger.candidate_id))
    for rank, ledger in enumerate(ledgers, start=1):
        ledger.reasoning = generate_reasoning(ledger, rank)
    return ledgers


def submission_rows(ledgers: list[EvidenceLedger]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    previous = float("inf")
    for rank, ledger in enumerate(ledgers, start=1):
        score = round(ledger.final_score, 6)
        if score >= previous:
            score = round(previous - 0.000001, 6)
        previous = score
        rows.append(
            {
                "candidate_id": ledger.candidate_id,
                "rank": rank,
                "score": f"{score:.6f}",
                "reasoning": ledger.reasoning,
            }
        )
    return rows


def rows_to_csv(rows: list[dict[str, Any]]) -> bytes:
    handle = io.StringIO(newline="")
    writer = csv.DictWriter(handle, fieldnames=["candidate_id", "rank", "score", "reasoning"])
    writer.writeheader()
    writer.writerows(rows)
    return handle.getvalue().encode("utf-8")


st.set_page_config(page_title="HawkesRank", page_icon="🦅", layout="wide")
st.title("HawkesRank")
st.caption("Professional-state candidate ranking: career proof first, vocabulary second.")

with st.sidebar:
    st.subheader("Run a sample")
    upload = st.file_uploader("Candidate JSONL or JSON array", type=["jsonl", "json"])
    st.caption(f"CPU-only · no network calls · maximum {MAX_PROFILES} profiles")
    st.divider()
    st.markdown(
        "**Evidence order**\n\n"
        "1. Career-proven search/ranking\n"
        "2. Production ownership and evaluation\n"
        "3. Corroborated skills\n"
        "4. Bounded behavior and logistics\n"
        "5. Near-miss and coherence penalties"
    )

try:
    if upload is None:
        records = json.loads((ROOT / "sample_candidates.json").read_text(encoding="utf-8"))
        source_label = "Bundled 50-profile sample"
    else:
        records = parse_candidate_file(upload.getvalue())
        source_label = upload.name
    ledgers = rank_records(records)
    rows = submission_rows(ledgers)
except (ValueError, KeyError, TypeError, json.JSONDecodeError) as exc:
    st.error(f"Could not rank this file: {exc}")
    st.stop()

top_band = ledgers[0].band_name if ledgers else "n/a"
risky = sum(bool(ledger.risk_flags) for ledger in ledgers)
col1, col2, col3, col4 = st.columns(4)
col1.metric("Profiles ranked", len(ledgers))
col2.metric("Highest evidence band", top_band.replace("_", " ").title())
col3.metric("Profiles with risk flags", risky)
col4.metric("External API calls", "0")

st.subheader("Ranked candidates")
st.caption(source_label)
st.dataframe(rows, width="stretch", hide_index=True, height=480)
st.download_button(
    "Download ranked CSV",
    data=rows_to_csv(rows),
    file_name="hawkesrank_sample.csv",
    mime="text/csv",
)

st.subheader("Evidence ledger")
selected_id = st.selectbox(
    "Inspect a candidate",
    options=[ledger.candidate_id for ledger in ledgers],
    format_func=lambda candidate_id: next(
        f"#{index + 1} · {ledger.title} · {candidate_id}"
        for index, ledger in enumerate(ledgers)
        if ledger.candidate_id == candidate_id
    ),
)
selected = next(ledger for ledger in ledgers if ledger.candidate_id == selected_id)

left, right = st.columns([1, 1])
with left:
    st.markdown(f"**Professional band:** {selected.band_name.replace('_', ' ').title()}")
    st.markdown(f"**Current-work subtype:** {selected.subtype.replace('_', ' ').title()}")
    st.markdown(f"**Role:** {selected.title} at {selected.company}")
    st.markdown(f"**Experience:** {selected.years_experience:.1f} years")
    st.markdown(f"**Reasoning:** {selected.reasoning}")
    if selected.negative_evidence:
        st.warning(" · ".join(selected.negative_evidence))
    if selected.risk_flags:
        st.error("Risk flags: " + " · ".join(selected.risk_flags))
with right:
    component_rows = [
        {"component": name, "value": value}
        for name, value in selected.components.items()
    ]
    st.dataframe(component_rows, width="stretch", hide_index=True)

st.info(
    "This sandbox ranks only the supplied sample. The official submission is produced by "
    "the two-pass 100K pipeline in rank.py."
)
