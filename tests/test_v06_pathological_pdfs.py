import hashlib
import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT_DIR = ROOT / "skills" / "litanchor-paper-reading" / "scripts"
sys.path.insert(0, str(SCRIPT_DIR))


def load_script(name, relative_path):
    path = ROOT / relative_path
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


LOCAL = load_script(
    "litanchor_local_pathological",
    "skills/litanchor-paper-reading/scripts/litanchor_local.py",
)
AUTONOMOUS = load_script(
    "autonomous_deep_reading_pathological",
    "skills/litanchor-paper-reading/scripts/autonomous_deep_reading.py",
)


@unittest.skipUnless(importlib.util.find_spec("pymupdf"), "PyMuPDF is not installed")
class V06PathologicalPdfTests(unittest.TestCase):
    @staticmethod
    def make_pdf(path, page_texts, *, two_columns=False):
        import pymupdf

        document = pymupdf.open()
        for text in page_texts:
            page = document.new_page(width=612, height=792)
            if not text:
                continue
            if two_columns:
                left, right = text
                page.insert_textbox(
                    pymupdf.Rect(36, 60, 288, 740),
                    left,
                    fontsize=9,
                )
                page.insert_textbox(
                    pymupdf.Rect(324, 60, 576, 740),
                    right,
                    fontsize=9,
                )
            else:
                page.insert_textbox(
                    pymupdf.Rect(36, 60, 576, 740),
                    text,
                    fontsize=10,
                )
        document.save(path)
        document.close()

    def test_image_only_or_blank_pdf_requires_fallback(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            pdf = root / "scan.pdf"
            self.make_pdf(pdf, [""])

            _run_dir, bundle = LOCAL.prepare_pdf(pdf, root / "runs")

            self.assertEqual(bundle["pdf"]["preflight_status"], "FALLBACK_REQUIRED")
            self.assertIn(
                "native_text_coverage_insufficient",
                bundle["pdf"]["warnings"],
            )

    def test_mixed_readable_and_blank_pages_never_claims_clean_pass(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            pdf = root / "mixed.pdf"
            readable = (
                "Methods and results are described with enough native text. " * 20
            )
            self.make_pdf(pdf, [readable, ""])

            _run_dir, bundle = LOCAL.prepare_pdf(pdf, root / "runs")

            self.assertEqual(bundle["pdf"]["preflight_status"], "PASS_WITH_WARNINGS")
            self.assertIn(
                "review_page_extraction_warnings",
                bundle["pdf"]["warnings"],
            )

    def test_long_pdf_retains_all_physical_pages_and_warns(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            pdf = root / "long.pdf"
            page_text = "Readable research content with methods and results. " * 12
            self.make_pdf(pdf, [page_text] * 61)

            _run_dir, bundle = LOCAL.prepare_pdf(pdf, root / "runs")

            self.assertEqual(bundle["pdf"]["page_count"], 61)
            self.assertEqual(len(bundle["pages"]), 61)
            self.assertEqual(bundle["pdf"]["preflight_status"], "PASS_WITH_WARNINGS")
            self.assertIn("page_count_above_mvp_limit", bundle["pdf"]["warnings"])

    def test_two_column_pdf_keeps_left_column_before_right_column(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            pdf = root / "columns.pdf"
            left = "LEFT_START " + ("left-column evidence " * 35) + " LEFT_END"
            right = "RIGHT_START " + ("right-column evidence " * 35) + " RIGHT_END"
            self.make_pdf(pdf, [(left, right)], two_columns=True)

            _run_dir, bundle = LOCAL.prepare_pdf(pdf, root / "runs")
            text = bundle["pages"][0]["raw_text"]

            self.assertIn("LEFT_START", text)
            self.assertIn("RIGHT_START", text)
            self.assertLess(text.index("LEFT_END"), text.index("RIGHT_START"))

            pages = AUTONOMOUS.extract_pymupdf_pages(pdf)
            autonomous_text = pages[0]["raw_text"]
            self.assertLess(
                autonomous_text.index("LEFT_END"),
                autonomous_text.index("RIGHT_START"),
            )

    def test_methods_after_references_are_not_discarded_as_bibliography(self):
        pages = [
            {"page_index": 1, "raw_text": "Introduction and results.", "warnings": []},
            {"page_index": 2, "raw_text": "References\nAuthor A. 2024.", "warnings": []},
            {
                "page_index": 3,
                "raw_text": "Methods\nSubstantive post-reference methods.",
                "warnings": [],
            },
        ]
        sections = [
            {
                "normalized_type": "introduction",
                "start_page": 1,
                "title_original": "Introduction",
            },
            {
                "normalized_type": "references",
                "start_page": 2,
                "title_original": "References",
            },
            {
                "normalized_type": "methods",
                "start_page": 3,
                "title_original": "Methods",
            },
        ]

        result = AUTONOMOUS.classify_physical_pages(pages, sections)

        self.assertEqual(result["pages"][1]["classification"], "references_only")
        self.assertEqual(result["pages"][2]["classification"], "main_content")
        self.assertTrue(result["pages"][2]["semantic_review_required"])

    def test_mineru_timeout_records_failure_and_preserves_pymupdf_baseline(self):
        class TimeoutClient:
            def flash_extract(self, source, **options):
                del source, options
                raise TimeoutError("synthetic MinerU timeout")

        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            pdf = root / "paper.pdf"
            self.make_pdf(
                pdf,
                [
                    "Introduction. This synthetic paper contains enough text "
                    "to establish a PyMuPDF evidence baseline. " * 8
                ],
            )
            run_dir = root / "run"
            run_dir.mkdir()
            source = {
                "schema_version": "0.1",
                "paper_id": "path-mineru-service-failure",
                "source": {"external_knowledge_allowed": False},
                "metadata": {"title": "Synthetic timeout paper", "authors": []},
                "pdf": {
                    "path": str(pdf),
                    "sha256": hashlib.sha256(pdf.read_bytes()).hexdigest(),
                    "page_count": 1,
                    "preflight_status": "PASS",
                    "warnings": [],
                },
                "pages": [],
            }
            payloads = {
                "source-bundle.json": source,
                "evidence.json": [],
                "claims.json": [],
                "figures.json": {
                    "selection_status": "pending",
                    "selected": [],
                    "rejected": [],
                },
                "run.json": {
                    "run_id": "run",
                    "status": "prepared",
                    "reading_mode": "deep",
                },
            }
            for name, payload in payloads.items():
                (run_dir / name).write_text(json.dumps(payload), encoding="utf-8")
            AUTONOMOUS.build_autonomous_plan(
                run_dir,
                allow_mineru_upload=True,
                mineru_consent_mode="always_for_eligible_files",
            )

            result = AUTONOMOUS.execute_planned_mineru(
                run_dir,
                client_factory=TimeoutClient,
            )

            self.assertEqual(result["status"], "failed")
            self.assertEqual(result["failure_type"], "TimeoutError")
            self.assertFalse(result["authoritative_evidence_created"])
            self.assertTrue((run_dir / "pymupdf-pages.json").is_file())
            autonomous = json.loads(
                (run_dir / "autonomous-run.json").read_text(encoding="utf-8")
            )
            self.assertEqual(autonomous["status"], "awaiting_agent_analysis")


if __name__ == "__main__":
    unittest.main()
