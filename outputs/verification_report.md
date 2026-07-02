# HawkesRank verification report

- Full dataset: 100,000 JSONL records
- Canonical run: 72.7654 seconds, 72.33 MB peak RSS
- Independent repeat run: 71.1447 seconds, 72.30 MB peak RSS
- Determinism: byte-identical CSVs
- SHA-256: `6740a92f6d1b781e6510aca3fce15269f48416523ca2363b78597f6d79b587a2`
- Organizer `validate_submission.py`: passed
- Project `strict_validate.py`: passed
- Unit tests: 5/5 passed
- Python bytecode compilation: passed
- XLSX ZIP integrity: passed
- Reasoning uniqueness: 100/100
- Grounding audit: every reason contains the candidate's current title and at least one exact profile/signal fact
- Streamlit sandbox AppTest: passed with bundled 50-profile sample, evidence ledger, and CSV download
- Top-100 professional bands: 25 senior relevance owners; 75 direct search/ranking candidates
- Top-10: all ten are senior relevance owners
- Manual-risk report: six top-100 profiles have materially weak behavior; none is in the top 10

Measured on Apple Silicon macOS with Python 3.12.13. Runtime and RSS vary by machine.
