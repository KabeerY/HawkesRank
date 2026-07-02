#!/usr/bin/env python3
from __future__ import annotations

import argparse

from hawkesrank.validation import strict_validate


def main() -> None:
    parser = argparse.ArgumentParser(description="Strict HawkesRank submission validator.")
    parser.add_argument("submission")
    parser.add_argument("--candidates", required=True)
    args = parser.parse_args()
    errors = strict_validate(args.submission, args.candidates)
    if errors:
        print(f"Strict validation failed ({len(errors)} issue(s)):")
        for error in errors:
            print(f"- {error}")
        raise SystemExit(1)
    print("Strict validation passed.")


if __name__ == "__main__":
    main()
