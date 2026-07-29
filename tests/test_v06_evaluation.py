import importlib.util
import json
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "tools" / "evaluate_v06.py"
SPEC = importlib.util.spec_from_file_location("evaluate_v06", SCRIPT)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(MODULE)


class V06EvaluationTests(unittest.TestCase):
    def test_frozen_manifest_is_reproducible_and_has_no_private_keys(self):
        result = MODULE.validate_manifest()
        self.assertEqual(result["status"], "pass")
        self.assertEqual(result["case_count"], 3)

    def test_pathological_contract_has_at_least_five_synthetic_cases(self):
        contract = json.loads(
            (ROOT / "evals" / "cases" / "v0.6-pathological-pdfs.json").read_text(
                encoding="utf-8"
            )
        )
        self.assertGreaterEqual(len(contract["cases"]), 5)
        self.assertIn("temporary", contract["fixture_policy"])

    def test_run_summary_reports_mineru_structure_without_evidence_authority(self):
        with tempfile.TemporaryDirectory() as temporary:
            run_dir = Path(temporary)
            payloads = {
                "source-bundle.json": {
                    "metadata": {"title": "Synthetic paper"},
                    "pdf": {"sha256": "a" * 64, "page_count": 2},
                },
                "run.json": {"status": "prepared"},
                "autonomous-run.json": {"status": "completed"},
                "evidence.json": [{"evidence_id": "E-001"}],
                "claims.json": [{"claim_id": "C-001"}],
                "sections.json": [
                    {"source": "pymupdf_heading"},
                    {"source": "mineru_aligned_heading"},
                ],
                "figure-candidates.json": [
                    {"mineru_used_as": "structure_hint"}
                ],
                "mineru-plan.json": {
                    "route": "whole_document",
                    "status": "completed",
                    "selected_original_pages": [1, 2],
                    "authoritative_evidence_created": False,
                },
                "fidelity-review.json": {"final_status": "pass"},
                "recall-review.json": {"final_status": "pass"},
                "validation.json": {
                    "status": "completed",
                    "quality": {"format_valid": True},
                },
            }
            for name, payload in payloads.items():
                (run_dir / name).write_text(json.dumps(payload), encoding="utf-8")
            mineru = run_dir / "mineru"
            mineru.mkdir()
            (mineru / "alignment.json").write_text(
                json.dumps({"statistics": {"exact": 2, "unmatched": 0}}),
                encoding="utf-8",
            )
            (run_dir / "final-note.md").write_text("# Note\n", encoding="utf-8")

            result = MODULE.summarize_run(run_dir)

            self.assertEqual(result["evidence_count"], 1)
            self.assertEqual(result["claim_count"], 1)
            self.assertTrue(result["final_note_present"])
            self.assertEqual(result["mineru"]["mineru_added_section_count"], 1)
            self.assertEqual(
                result["mineru"]["mineru_added_figure_candidate_count"],
                1,
            )
            self.assertFalse(result["mineru"]["authoritative_evidence_created"])

    def test_candidate_note_counts_as_a_generated_note(self):
        with tempfile.TemporaryDirectory() as temporary:
            run_dir = Path(temporary)
            payloads = {
                "source-bundle.json": {
                    "metadata": {"title": "Synthetic paper"},
                    "pdf": {"sha256": "a" * 64, "page_count": 1},
                },
                "run.json": {"status": "completed"},
                "evidence.json": [{"evidence_id": "E-001"}],
                "claims.json": [{"claim_id": "C-001"}],
            }
            for name, payload in payloads.items():
                (run_dir / name).write_text(json.dumps(payload), encoding="utf-8")
            (run_dir / "candidate-note.md").write_text("# Candidate\n", encoding="utf-8")

            result = MODULE.summarize_run(run_dir)

            self.assertTrue(result["final_note_present"])

    def test_holdout_failure_promotion_requires_replacement(self):
        manifest = json.loads(MODULE.DEFAULT_MANIFEST.read_text(encoding="utf-8"))
        statuses = MODULE.load_holdout_status(manifest)

        self.assertEqual(
            statuses["holdout-madagascar-biogeography"]["status"],
            "promoted_to_development",
        )
        self.assertTrue(
            statuses["holdout-madagascar-biogeography"]["replacement_required"]
        )

    def test_release_gate_enforces_quality_and_non_authoritative_mineru(self):
        summary = {
            "status": "completed_with_warnings",
            "evidence_count": 20,
            "claim_count": 12,
            "fidelity_status": "pass",
            "recall_status": "pass",
            "final_note_present": True,
            "mineru": {
                "route": "whole_document",
                "authoritative_evidence_created": False,
            },
            "quality": {
                "evidence_coverage": 1.0,
                "page_reference_accuracy": 1.0,
                "numeric_fidelity": 1.0,
                "template_completeness": 1.0,
                "content_recall_pass": True,
                "format_valid": True,
            },
        }

        result = MODULE.release_gate_status(summary, "whole_document")

        self.assertEqual(result["status"], "pass")
        summary["mineru"]["authoritative_evidence_created"] = True
        self.assertEqual(
            MODULE.release_gate_status(summary, "whole_document")["status"],
            "fail",
        )


if __name__ == "__main__":
    unittest.main()
