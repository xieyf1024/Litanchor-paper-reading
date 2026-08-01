import importlib.util
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "tools" / "audit_release.py"
SPEC = importlib.util.spec_from_file_location("audit_release", SCRIPT)
audit_release = importlib.util.module_from_spec(SPEC)
assert SPEC.loader
SPEC.loader.exec_module(audit_release)


class ReleaseAuditTests(unittest.TestCase):
    def test_private_runtime_detection_matches_directories_not_filename_words(self):
        self.assertTrue(
            audit_release._is_private_runtime_path(
                "skills/litanchor-paper-reading/runtime/run.json"
            )
        )
        self.assertTrue(
            audit_release._is_private_runtime_path(
                "evolution/feedback/feedback.jsonl"
            )
        )
        self.assertFalse(
            audit_release._is_private_runtime_path(
                ".github/ISSUE_TEMPLATE/runtime_pdf_failure.yml"
            )
        )

    def test_evaluation_tokens_include_v06_holdout_manifests(self):
        tokens = audit_release._evaluation_tokens()
        self.assertIn(
            "Prediction of total organic carbon at Rumaila oil field, "
            "Southern Iraq using conventional well logs and machine learning algorithms",
            tokens,
        )
        self.assertIn("10.5194/gmd-17-5413-2024", tokens)

    def test_distributable_skill_contains_no_evaluation_answers(self):
        result = audit_release.audit()
        self.assertEqual(result["status"], "passed", result["issues"])
        self.assertEqual(result["skill_compaction"]["status"], "passed")
        self.assertLessEqual(result["skill_compaction"]["skill_line_count"], 100)
        self.assertEqual(
            result["skill_compaction"]["duplicate_long_rule_count"], 0
        )
        self.assertEqual(result["skill_compaction"]["missing_resources"], [])


if __name__ == "__main__":
    unittest.main()
