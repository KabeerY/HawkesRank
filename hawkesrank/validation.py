from __future__ import annotations

import csv
import hashlib
import json
import math
from pathlib import Path
from typing import Any


REQUIRED_HEADER = ["candidate_id", "rank", "score", "reasoning"]


def candidate_ids_from_jsonl(path: str | Path) -> set[str]:
    ids: set[str] = set()
    with Path(path).open("r", encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
                ids.add(json.loads(line)["candidate_id"])
    return ids


def strict_validate(
    submission_path: str | Path,
    candidates_path: str | Path,
    expected_rows: int = 100,
) -> list[str]:
    errors: list[str] = []
    submission_path = Path(submission_path)
    with submission_path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        if reader.fieldnames != REQUIRED_HEADER:
            errors.append(f"Header must be exactly {REQUIRED_HEADER}; found {reader.fieldnames}")
        rows = list(reader)

    if len(rows) != expected_rows:
        errors.append(f"Expected {expected_rows} data rows; found {len(rows)}")
        return errors

    ids = [row["candidate_id"].strip() for row in rows]
    ranks: list[int] = []
    scores: list[float] = []
    reasons = [row["reasoning"].strip() for row in rows]
    for index, row in enumerate(rows, start=1):
        try:
            ranks.append(int(row["rank"]))
        except ValueError:
            errors.append(f"Row {index}: invalid rank {row['rank']!r}")
        try:
            score = float(row["score"])
            if not math.isfinite(score):
                errors.append(f"Row {index}: score is not finite")
            scores.append(score)
        except ValueError:
            errors.append(f"Row {index}: invalid score {row['score']!r}")

    if ranks != list(range(1, expected_rows + 1)):
        errors.append("Ranks must be ordered integers 1 through 100")
    if len(set(ids)) != expected_rows:
        errors.append("Candidate IDs are not unique")
    if len(scores) == expected_rows:
        for index in range(expected_rows - 1):
            if not scores[index] > scores[index + 1]:
                errors.append(
                    f"Scores must be strictly decreasing: rank {index + 1}={scores[index]} "
                    f"and rank {index + 2}={scores[index + 1]}"
                )
                break
    if any(not reason for reason in reasons):
        errors.append("Reasoning must be non-empty for every row")
    if len(set(reasons)) != expected_rows:
        errors.append("Reasoning strings must be unique")
    if any(len(reason.split()) < 12 for reason in reasons):
        errors.append("Every reasoning entry must contain at least 12 words")

    available_ids = candidate_ids_from_jsonl(candidates_path)
    missing = sorted(set(ids) - available_ids)
    if missing:
        errors.append(f"Submission contains unknown candidate IDs: {missing[:10]}")
    return errors


def sha256_file(path: str | Path) -> str:
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()
