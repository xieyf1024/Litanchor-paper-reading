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


if __name__ == "__main__":
    unittest.main()
