from __future__ import annotations

import copy
import json
import unittest
from pathlib import Path

from hawkesrank.evidence import extract_ledger
from hawkesrank.reasoning import generate_reasoning
from hawkesrank.scoring import score_pass1, score_pass2


ROOT = Path(__file__).resolve().parents[1]


class HawkesRankTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.samples = json.loads((ROOT / "sample_candidates.json").read_text(encoding="utf-8"))

    def test_keyword_skills_do_not_override_nontechnical_career(self) -> None:
        record = copy.deepcopy(self.samples[20])  # CAND_0000021: project manager + AI keywords
        ledger = extract_ledger(record)
        self.assertLessEqual(ledger.band, 1)

    def test_direct_search_career_beats_skill_only_copy(self) -> None:
        direct = copy.deepcopy(self.samples[30])  # CAND_0000031
        direct_ledger = extract_ledger(direct)
        score_pass1(direct_ledger)
        score_pass2(direct_ledger)

        fake = copy.deepcopy(self.samples[20])
        fake["skills"] = copy.deepcopy(direct["skills"])
        fake_ledger = extract_ledger(fake)
        score_pass1(fake_ledger)
        score_pass2(fake_ledger)

        self.assertGreater(direct_ledger.band, fake_ledger.band)
        self.assertGreater(direct_ledger.final_score, fake_ledger.final_score)

    def test_behavior_does_not_change_professional_band(self) -> None:
        record = copy.deepcopy(self.samples[30])
        base = extract_ledger(record)
        record["redrob_signals"]["open_to_work_flag"] = False
        record["redrob_signals"]["recruiter_response_rate"] = 0.0
        record["redrob_signals"]["last_active_date"] = "2025-01-01"
        weak_behavior = extract_ledger(record)
        self.assertEqual(base.band, weak_behavior.band)

    def test_reasoning_is_grounded_in_profile_facts(self) -> None:
        ledger = extract_ledger(copy.deepcopy(self.samples[30]))
        score_pass2(ledger)
        reason = generate_reasoning(ledger, 1)
        self.assertIn(ledger.title, reason)
        self.assertIn(f"{ledger.years_experience:.1f}", reason)
        self.assertGreaterEqual(len(reason.split()), 12)

    def test_plain_language_relevance_ownership_is_recognized(self) -> None:
        record = copy.deepcopy(self.samples[30])
        current = next(job for job in record["career_history"] if job.get("is_current"))
        record["profile"]["current_title"] = "Senior AI Engineer"
        current["title"] = "Senior AI Engineer"
        current["description"] = (
            "Led infrastructure to surface relevant content across millions of documents. "
            "Owned query understanding, ranking calibration, and production dashboards."
        )
        ledger = extract_ledger(record)
        self.assertEqual(ledger.subtype, "relevance_ownership")


if __name__ == "__main__":
    unittest.main()
