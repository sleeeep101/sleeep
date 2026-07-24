import importlib.util
import unittest
from pathlib import Path


MODULE_PATH = Path(__file__).resolve().parent.parent / "00_core_scripts" / "meeting_evidence_gate.py"
SPEC = importlib.util.spec_from_file_location("meeting_evidence_gate", MODULE_PATH)
gate = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(gate)


class MeetingEvidenceGateTests(unittest.TestCase):
    def valid_brief(self) -> dict:
        return {
            "meeting_id": "2026-07-week-4",
            "research_question": "How does terrain affect erosion risk?",
            "claims": [
                {
                    "statement": "Slope class is associated with observed erosion risk.",
                    "evidence": ["Figure 2; model run 2026-07-24"],
                    "certainty": "probable",
                }
            ],
            "discussion_questions": [
                "Is the spatial scale appropriate for the mechanism?",
                "Which sensitivity analysis should be run next?",
            ],
            "next_steps": [
                {"action": "Run a scale sensitivity check.", "success_criterion": "Compare estimates across three resolutions."}
            ],
        }

    def test_complete_brief_passes(self) -> None:
        self.assertEqual(gate.validate_brief(self.valid_brief()), [])

    def test_claim_without_evidence_or_certainty_fails(self) -> None:
        brief = self.valid_brief()
        brief["claims"][0]["evidence"] = []
        brief["claims"][0]["certainty"] = ""
        issues = gate.validate_brief(brief)
        self.assertTrue(any("evidence" in issue for issue in issues))
        self.assertTrue(any("certainty" in issue for issue in issues))

    def test_two_discussion_questions_are_required(self) -> None:
        brief = self.valid_brief()
        brief["discussion_questions"] = ["What should we check?"]
        self.assertTrue(any("two concrete questions" in issue for issue in gate.validate_brief(brief)))


if __name__ == "__main__":
    unittest.main()
