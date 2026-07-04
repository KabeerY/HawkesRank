from __future__ import annotations

import csv
import io
import json
import sys
from pathlib import Path
from typing import Any

import streamlit as st


APP_DIR = Path(__file__).resolve().parent
ROOT = APP_DIR if (APP_DIR / "sample_candidates.json").exists() else APP_DIR.parent
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


def humanize(value: str) -> str:
    return value.replace("_", " ").title()


st.set_page_config(
    page_title="HawkesRank · Evidence-first talent ranking",
    page_icon="◈",
    layout="wide",
    initial_sidebar_state="expanded",
)
st.markdown(
    """
    <style>
    #MainMenu, footer, .stDeployButton, [data-testid="stToolbar"] { display: none !important; }
    header[data-testid="stHeader"] { background: transparent; }
    .block-container { max-width: 1320px; padding-top: 2.4rem; padding-bottom: 4rem; }
    [data-testid="stSidebar"] { background: #17211f; border-right: 1px solid #2e3a37; }
    [data-testid="stSidebar"] h1, [data-testid="stSidebar"] h2,
    [data-testid="stSidebar"] h3, [data-testid="stSidebar"] p,
    [data-testid="stSidebar"] label, [data-testid="stSidebar"] li { color: #f4f0e6 !important; }
    [data-testid="stFileUploaderDropzone"] {
        background: #22302c; border: 1px dashed #7f938c; border-radius: 14px;
    }
    [data-testid="stSidebar"] [data-testid="stFileUploaderDropzoneInstructions"] span {
        color: #f4f0e6 !important;
    }
    [data-testid="stSidebar"] [data-testid="stFileUploaderDropzoneInstructions"] small {
        color: #bdc9c3 !important;
    }
    .hr-hero {
        background: linear-gradient(120deg, #17211f 0%, #263934 62%, #355248 100%);
        border-radius: 24px; padding: 38px 42px; color: #fbf7ed; margin-bottom: 24px;
        box-shadow: 0 18px 55px rgba(23,33,31,.16); position: relative; overflow: hidden;
    }
    .hr-hero:after {
        content: ""; position: absolute; width: 280px; height: 280px; border-radius: 50%;
        right: -85px; top: -120px; border: 46px solid rgba(226,106,69,.18);
    }
    .hr-kicker { color: #f09a75; font-size: 12px; font-weight: 800; letter-spacing: .18em; }
    .hr-title { font-size: clamp(36px, 5vw, 62px); line-height: 1.02; font-weight: 750; max-width: 760px; margin: 12px 0; }
    .hr-subtitle { color: #d8e1dc; max-width: 720px; font-size: 17px; line-height: 1.6; }
    .hr-pill { display: inline-block; padding: 7px 11px; margin: 14px 7px 0 0; border-radius: 99px;
        background: rgba(255,255,255,.09); border: 1px solid rgba(255,255,255,.15); font-size: 12px; }
    .hr-scope-note { color: #52605b; font-size: 13px; margin: -10px 2px 20px; }
    .hr-metrics { display: grid; grid-template-columns: repeat(4, minmax(0,1fr)); gap: 12px; margin: 4px 0 26px; }
    .hr-metric { background: #fffdf8; border: 1px solid #ded8cb; border-radius: 16px; padding: 18px 20px; }
    .hr-metric-label { color: #6f756f; font-size: 12px; font-weight: 700; text-transform: uppercase; letter-spacing: .08em; }
    .hr-metric-value { color: #17211f; font-size: 22px; line-height: 1.12; font-weight: 760; margin-top: 8px; min-height: 49px; }
    .hr-section-label { color: #d76643; font-size: 12px; font-weight: 800; letter-spacing: .15em; text-transform: uppercase; }
    div[data-testid="stDataFrame"] { border: 1px solid #ded8cb; border-radius: 16px; overflow: hidden; }
    div[data-testid="stDownloadButton"] button { background: #d85f3d; color: white; border: 0; border-radius: 12px; font-weight: 700; }
    div[data-testid="stDownloadButton"] button:hover { background: #b9482d; color: white; }
    div[data-testid="stAlert"] { border-radius: 14px; }
    @media (max-width: 900px) { .hr-metrics { grid-template-columns: repeat(2,1fr); } .hr-hero { padding: 30px 24px; } }
    </style>
    """,
    unsafe_allow_html=True,
)

st.markdown(
    """
    <section class="hr-hero">
      <div class="hr-kicker">HAWKESRANK · REDROB TALENT INTELLIGENCE</div>
      <div class="hr-title">Find the proof behind the profile.</div>
      <div class="hr-subtitle">An evidence-first ranking console that separates candidates who look relevant from candidates who have shipped relevant systems.</div>
      <span class="hr-pill">Deterministic</span><span class="hr-pill">CPU only</span><span class="hr-pill">No external APIs</span><span class="hr-pill">Explainable by design</span>
    </section>
    """,
    unsafe_allow_html=True,
)

st.markdown(
    '<div class="hr-scope-note">Sandbox ranks uploaded samples ≤100 profiles. Official <code>rank.py</code> processes the full 100K pool in ~73 seconds.</div>',
    unsafe_allow_html=True,
)

with st.sidebar:
    st.markdown("### Candidate pool")
    st.caption("Upload a small sample or explore the bundled profiles.")
    upload = st.file_uploader("JSONL or JSON array", type=["jsonl", "json"])
    st.caption(f"Maximum {MAX_PROFILES} profiles · processed locally")
    st.divider()
    st.markdown("### Decision hierarchy")
    st.markdown("**01** Career proof  \n**02** Production + evaluation  \n**03** Corroborated skills  \n**04** Bounded feasibility  \n**05** Hard-negative suppression")
    st.divider()
    st.caption("The hosted sandbox handles ≤100 profiles. The official two-pass pipeline ranks all 100K in ~73 seconds.")

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
top_n = min(10, len(ledgers))
top_open = sum(ledger.behavior["open_to_work"] for ledger in ledgers[:top_n])
review_flags = sum(any(not flag.startswith("weak:") for flag in ledger.risk_flags) for ledger in ledgers)
st.markdown(
    f"""
    <div class="hr-metrics">
      <div class="hr-metric"><div class="hr-metric-label">Profiles ranked</div><div class="hr-metric-value">{len(ledgers)}</div></div>
      <div class="hr-metric"><div class="hr-metric-label">Highest evidence state</div><div class="hr-metric-value">{humanize(top_band)}</div></div>
      <div class="hr-metric"><div class="hr-metric-label">Top-{top_n} open to work</div><div class="hr-metric-value">{top_open} / {top_n}</div></div>
      <div class="hr-metric"><div class="hr-metric-label">Review flags</div><div class="hr-metric-value">{review_flags}</div></div>
    </div>
    """,
    unsafe_allow_html=True,
)

shortlist_tab, evidence_tab, method_tab = st.tabs(["Shortlist", "Evidence workspace", "How it ranks"])

with shortlist_tab:
    st.markdown('<div class="hr-section-label">Ranked shortlist</div>', unsafe_allow_html=True)
    st.subheader("Decision-ready candidates")
    st.caption(f"{source_label} · career evidence establishes relevance; behavior only reorders comparable candidates")
    shortlist_rows = [
        {
            "Rank": index,
            "Candidate": ledger.candidate_id,
            "Current role": f"{ledger.title} · {ledger.company}",
            "Evidence state": humanize(ledger.band_name),
            "Score": round(ledger.final_score, 3),
            "Availability": "Open" if ledger.behavior["open_to_work"] else "Passive",
        }
        for index, ledger in enumerate(ledgers, start=1)
    ]
    st.dataframe(
        shortlist_rows,
        width="stretch",
        hide_index=True,
        height=510,
        column_config={
            "Rank": st.column_config.NumberColumn(width="small", format="#%d"),
            "Candidate": st.column_config.TextColumn(width="medium"),
            "Current role": st.column_config.TextColumn(width="large"),
            "Evidence state": st.column_config.TextColumn(width="medium"),
            "Score": st.column_config.ProgressColumn(min_value=0, max_value=225, format="%.3f"),
            "Availability": st.column_config.TextColumn(width="small"),
        },
    )
    st.download_button(
        "Export ranked CSV",
        data=rows_to_csv(rows),
        file_name="hawkesrank_sample.csv",
        mime="text/csv",
        icon=":material/download:",
    )

with evidence_tab:
    st.markdown('<div class="hr-section-label">Evidence ledger</div>', unsafe_allow_html=True)
    st.subheader("Why this candidate ranks here")
    selected_id = st.selectbox(
        "Candidate",
        options=[ledger.candidate_id for ledger in ledgers],
        format_func=lambda candidate_id: next(
            f"#{index + 1}  {ledger.title}  ·  {candidate_id}"
            for index, ledger in enumerate(ledgers)
            if ledger.candidate_id == candidate_id
        ),
    )
    selected = next(ledger for ledger in ledgers if ledger.candidate_id == selected_id)
    rank_lookup = next(index for index, ledger in enumerate(ledgers, start=1) if ledger.candidate_id == selected_id)
    info1, info2, info3, info4 = st.columns(4)
    info1.metric("Rank", f"#{rank_lookup}")
    info2.metric("Evidence state", humanize(selected.band_name))
    info3.metric("Experience", f"{selected.years_experience:.1f} years")
    info4.metric("Final score", f"{selected.final_score:.3f}")

    narrative, breakdown = st.columns([1.15, 0.85], gap="large")
    with narrative:
        st.markdown(f"#### {selected.title}")
        st.caption(f"{selected.company} · {selected.location} · {humanize(selected.subtype)}")
        with st.container(border=True):
            st.markdown("**Evidence-backed recommendation**")
            st.write(selected.reasoning)
        if selected.negative_evidence:
            st.warning("**Watch-outs:** " + " · ".join(selected.negative_evidence))
        strong_flags = [flag for flag in selected.risk_flags if not flag.startswith("weak:")]
        weak_flags = [flag.removeprefix("weak:") for flag in selected.risk_flags if flag.startswith("weak:")]
        if strong_flags:
            st.error("**Material coherence risk:** " + " · ".join(strong_flags))
        elif weak_flags:
            st.caption("Diagnostic-only flags: " + " · ".join(weak_flags))
        else:
            st.success("No material coherence risks detected.")
    with breakdown:
        component_rows = [
            {"Score component": humanize(name), "Points": value}
            for name, value in selected.components.items()
        ]
        st.markdown("#### Score composition")
        st.dataframe(
            component_rows,
            width="stretch",
            hide_index=True,
            height=430,
            column_config={"Points": st.column_config.NumberColumn(format="%.3f")},
        )

with method_tab:
    st.markdown('<div class="hr-section-label">Decision system</div>', unsafe_allow_html=True)
    st.subheader("Professional state before text similarity")
    st.write("HawkesRank scores what the candidate has proven professionally—not how many JD words appear in the profile.")
    m1, m2, m3 = st.columns(3)
    with m1:
        with st.container(border=True):
            st.markdown("#### 01 · Establish identity")
            st.write("Career history assigns an evidence-bounded professional state. Skills alone cannot manufacture ML or search relevance.")
    with m2:
        with st.container(border=True):
            st.markdown("#### 02 · Measure proof")
            st.write("Production ownership, retrieval/ranking depth, evaluation maturity, and corroboration create the evidence margin.")
    with m3:
        with st.container(border=True):
            st.markdown("#### 03 · Test hireability")
            st.write("Bounded behavior and logistics reorder comparable candidates while narrow risk checks suppress hard negatives.")
    st.code("professional proof + corroboration + bounded feasibility − near misses − coherence risk", language=None)
    st.info("The hosted sandbox ranks ≤100 supplied profiles. `rank.py` runs the official two-pass 100K pipeline.")
