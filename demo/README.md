# HawkesRank sandbox

This Streamlit app is the isolated small-sample demo required by the competition portal. It accepts a JSON array or JSONL upload of at most 100 candidates, ranks them without network calls, exposes the evidence/score breakdown, and downloads the required CSV columns.

Live deployment: [huggingface.co/spaces/KabeerY/HawkesRank](https://huggingface.co/spaces/KabeerY/HawkesRank)

Run locally from the repository root:

```bash
python3 -m pip install -r demo/requirements.txt
streamlit run demo/app.py
```

Or build the container:

```bash
docker build -f demo/Dockerfile -t hawkesrank-demo .
docker run --rm -p 8501:8501 hawkesrank-demo
```

For Hugging Face Docker Spaces, use the repository root as the build context and `demo/Dockerfile` as the Dockerfile.

The demo dependency is intentionally separate from the official ranker. `rank.py` remains standard-library-only and is the sole full-dataset reproduction command.
