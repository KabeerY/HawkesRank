#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path

from hawkesrank.pipeline import run_pipeline


def main() -> None:
    parser = argparse.ArgumentParser(description="Run HawkesRank v1 over a candidate JSONL file.")
    parser.add_argument("--candidates", required=True, help="Path to candidates.jsonl")
    parser.add_argument("--output-root", default=".", help="Directory receiving outputs/ and final/")
    parser.add_argument("--pool-size", type=int, default=2000)
    parser.add_argument("--inspection-size", type=int, default=300)
    parser.add_argument("--final-size", type=int, default=100)
    args = parser.parse_args()

    summary = run_pipeline(
        candidates_path=Path(args.candidates),
        output_root=Path(args.output_root),
        pool_size=args.pool_size,
        inspection_size=args.inspection_size,
        final_size=args.final_size,
    )
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
