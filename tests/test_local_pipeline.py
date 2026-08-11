import importlib.util
import json
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "skills" / "litanchor-paper-reading" / "scripts" / "litanchor_local.py"
SPEC = importlib.util.spec_from_file_location("litanchor_local", SCRIPT)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(MODULE)


def write_json(path, payload):
    path.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")


class LocalPipelineTests(unittest.TestCase):
    def test_quote_trace_tolerates_pdf_line_wrap_after_hyphen(self):
        quote = "the English-to-German task"
        page = "the English-\nto-German task"
        self.assertTrue(MODULE.quote_is_traceable(quote, page))

    def test_quote_trace_tolerates_mixed_semantic_and_line_wrap_hyphens(self):
        quote = "ice-covered continents use model-generated ice volume"
        page = "ice-covered con-\ntinents use model-\ngenerated ice volume"
        self.assertTrue(MODULE.quote_is_traceable(quote, page))

    def test_quote_trace_tolerates_soft_hyphen_line_wrap(self):
        quote = "general simulation features"
        page = "general simula\u00ad\n tion features"
        self.assertTrue(MODULE.quote_is_traceable(quote, page))

    def test_quote_trace_tolerates_pdf_space_after_slash(self):
        quote = "mixed sequential/concurrent mode"
        page = "mixed sequential/ concurrent mode"
        self.assertTrue(MODULE.quote_is_traceable(quote, page))

    def test_quote_trace_tolerates_unicode_hyphens_and_pdf_punctuation_spacing(self):
        quote = (
            "The neural network‐based method follows Lehtinen et al. (2018)."
        )
        page = (
            "The neural network‐\nbased method follows Lehtinen et al. ( 2018 )."
        )
        self.assertTrue(MODULE.quote_is_traceable(quote, page))

    def test_page_quote_trace_reconstructs_same_column_line_blocks(self):
        page = {
            "page_width": 600,
            "raw_text": (
                "Aim: The method inte-\nleft affiliation\n"
                "grates evidence across columns.\n"
            ),
            "text_blocks": [
                {
                    "block_id": "P1-B1",
                    "block_type": "text",
                    "bbox": [320, 100, 560, 112],
                    "text": "The method inte-",
                },
                {
                    "block_id": "P1-B2",
                    "block_type": "text",
                    "bbox": [40, 106, 250, 118],
                    "text": "left affiliation",
                },
                {
                    "block_id": "P1-B3",
                    "block_type": "text",
                    "bbox": [320, 114, 560, 126],
                    "text": "grates evidence across columns.",
                },
            ],
        }
        kind, blocks = MODULE.page_quote_match_location(
            "The method integrates evidence across columns.",
            page,
        )
        self.assertEqual(kind, "normalized")
        self.assertEqual([item["block_id"] for item in blocks], ["P1-B1", "P1-B3"])

    def test_page_quote_trace_reconstructs_across_column_boundary(self):
        page = {
            "page_width": 600,
            "raw_text": "right continuation\nleft sentence begins\nunrelated footer",
            "text_blocks": [
                {
                    "block_id": "P1-B1",
                    "block_type": "text",
                    "bbox": [40, 700, 250, 712],
                    "text": "The sentence begins in the left column and",
                },
                {
                    "block_id": "P1-B2",
                    "block_type": "text",
                    "bbox": [320, 100, 560, 112],
                    "text": "continues at the top of the right column.",
                },
            ],
        }
        kind, blocks = MODULE.page_quote_match_location(
            (
                "The sentence begins in the left column and continues at "
                "the top of the right column."
            ),
            page,
        )
        self.assertEqual(kind, "normalized")
        self.assertEqual([item["block_id"] for item in blocks], ["P1-B1", "P1-B2"])

    def test_trace_token_matches_unicode_numeric_range(self):
        self.assertTrue(
            MODULE.trace_token_present("1901–2020", "within the 1901-2020 period")
        )

    def test_page_extraction_uses_pymupdf_sorted_text(self):
        class FakePage:
            def __init__(self):
                self.calls = []
                self.rect = type("Rect", (), {"width": 612})()

            def get_text(self, extraction_mode, *, sort=False):
                self.calls.append((extraction_mode, sort))
                return {
                    "blocks": [
                        {
                            "type": 0,
                            "bbox": [36, 60, 576, 100],
                            "lines": [
                                {
                                    "spans": [
                                        {
                                            "text": "This is readable text in PyMuPDF reading order with enough context."
                                        }
                                    ]
                                }
                            ],
                        }
                    ]
                }

        page = FakePage()
        text, _warnings = MODULE._extract_page_text(page)
        self.assertIn("PyMuPDF reading order", text)
        self.assertEqual(page.calls, [("dict", False)])

    def test_page_extraction_removes_non_text_control_characters(self):
        class FakePage:
            rect = type("Rect", (), {"width": 612})()

            def get_text(self, extraction_mode, *, sort=False):
                return {"blocks": [{"type": 0, "bbox": [36, 60, 576, 100], "lines": [{"spans": [{"text": "F(x)\x01 + x is the residual output with readable surrounding text."}]}]}]}

        text, warnings = MODULE._extract_page_text(FakePage())
        self.assertNotIn("\x01", text)
        self.assertIn("control_characters_removed:1", warnings)

    def test_page_extraction_flags_broken_ligature_glyphs(self):
        class FakePage:
            rect = type("Rect", (), {"width": 612})()

            def get_text(self, extraction_mode, *, sort=False):
                return {"blocks": [{"type": 0, "bbox": [36, 60, 576, 100], "lines": [{"spans": [{"text": "The model ®nds ice ¯ow under the stated boundary conditions."}]}]}]}

        _text, warnings = MODULE._extract_page_text(FakePage())
        self.assertIn("suspicious_ligature_glyphs:2", warnings)

    def test_note_frontmatter_keeps_only_first_author(self):
        self.assertEqual(
            MODULE.first_author_name(["First Author", "Second Author"]),
            "First Author",
        )
        self.assertIsNone(MODULE.first_author_name([]))

    def test_note_frontmatter_uses_mode_tags_and_preserves_user_tags(self):
        source = {
            "metadata": {
                "title": "Tagged Paper",
                "authors": ["First Author", "Second Author"],
                "year": 2026,
                "journal": "Journal",
                "doi": None,
                "keywords": ["ocean", "climate", "ocean"],
            }
        }
        for mode in ("skim", "deep", "internalize"):
            frontmatter = MODULE.render_note_frontmatter(
                source,
                {
                    "reading_mode": mode,
                    "created": "2020-05-06T07:08:09+00:00",
                    "note_created_at": "2026-01-02T03:04:05+00:00",
                    "user_tags": ["my-project", "#skim", "LitAnchor"],
                },
                "completed",
                "empirical-research",
            )
            self.assertNotIn("reading_mode:", frontmatter)
            self.assertIn(f'  - "{mode}"', frontmatter)
            self.assertIn('  - "LitAnchor"', frontmatter)
            self.assertIn('  - "my-project"', frontmatter)
            self.assertEqual(frontmatter.count('  - "skim"'), int(mode == "skim"))
            self.assertIn('keywords: "ocean; climate"', frontmatter)
            self.assertIn('created: "2026-01-02"', frontmatter)
            self.assertNotIn('created: "2020-05-06"', frontmatter)

    def make_run(
        self,
        root: Path,
        *,
        quote="The model achieved 95% accuracy on the test set.",
        value="95",
        unit="%",
        reading_mode="skim",
    ):
        run_dir = root / "run"
        run_dir.mkdir()
        source = {
            "schema_version": "0.1",
            "paper_id": "pdf-test",
            "source": {
                "acquisition_method": "manual_pdf",
                "query": "test.pdf",
                "zotero_item_key": None,
                "zotero_attachment_key": None,
                "external_knowledge_allowed": False,
            },
            "metadata": {"title": "Test Paper", "authors": ["A. Author"], "year": 2026, "journal": None, "doi": None, "citekey": None},
            "annotations": [],
            "pdf": {"path": "test.pdf", "sha256": "a" * 64, "page_count": 1, "preflight_status": "PASS", "warnings": []},
            "pages": [{"page_index": 1, "printed_page": None, "raw_text": "The model achieved 95% accuracy on the test set.", "extraction_method": "native_text", "confidence": 1.0, "warnings": []}],
        }
        evidence = [{
            "evidence_id": "E-001",
            "evidence_type": "result",
            "page_index": 1,
            "printed_page": None,
            "section": "Results",
            "block_id": None,
            "bounding_box": None,
            "quote_original": quote,
            "epistemic_status": "observed",
            "epistemic_markers": [],
            "contains_number": True,
            "contains_unit": True,
            "contains_variable": False,
            "confidence": 1.0,
            "needs_review": False,
            "page_verified": True,
            "source_match_kind": "exact",
            "issues": [],
        }]
        claims = [{
            "claim_id": "C-001",
            "claim_text_zh": "作者报告模型在测试集上的准确率为 95%。",
            "claim_type": "result",
            "epistemic_status": "observed",
            "evidence_ids": ["E-001"],
            "page_refs": [1],
            "numeric_items": [{"value_original": value, "unit_original": unit, "variable": None, "condition": "test set"}],
            "display_level": "collapsed",
            "validation": {"traceable": True, "semantic_support": "pass", "numeric_fidelity": "pass", "modality_fidelity": "pass", "final_status": "pass"},
        }]
        run_record = {"schema_version": "0.1", "run_id": "run", "paper_id": "pdf-test", "skill_version": "0.4.1", "reading_mode": reading_mode, "created": "2026-01-01T00:00:00+00:00", "status": "prepared", "artifacts": {}}
        write_json(run_dir / "source-bundle.json", source)
        write_json(run_dir / "evidence.json", evidence)
        write_json(run_dir / "claims.json", claims)
        write_json(
            run_dir / "figures.json",
            {
                "schema_version": "0.1",
                "selection_status": "completed",
                "selected": [],
                "rejected": [],
                "no_selection_reason": "No key visual is required for this fixture.",
            },
        )
        write_json(run_dir / "run.json", run_record)
        return run_dir

    def test_builds_traceable_non_overwriting_preview(self):
        with tempfile.TemporaryDirectory() as temporary:
            run_dir = self.make_run(Path(temporary))
            destination, result = MODULE.build_run(run_dir)
            markdown = destination.read_text(encoding="utf-8")
            self.assertEqual(result["status"], "completed")
            self.assertTrue(result["quality"]["format_valid"])
            self.assertIn('first_author: "A. Author"', markdown)
            self.assertNotIn("reading_mode:", markdown)
            self.assertIn('  - "skim"', markdown)
            self.assertIn("〔p.1〕", markdown)
            self.assertNotIn("E-001", markdown)
            self.assertNotIn("PDF p.1", markdown)
            self.assertEqual(markdown.count("\n## "), 1)
            persisted_run = json.loads((run_dir / "run.json").read_text(encoding="utf-8"))
            self.assertIn("note_created_at", persisted_run)
            self.assertIn(
                f'created: "{persisted_run["note_created_at"][:10]}"',
                markdown,
            )
            coverage = json.loads((run_dir / "coverage_receipt.json").read_text(encoding="utf-8"))
            self.assertEqual(coverage["coverage_status"], "complete")
            self.assertEqual(coverage["pages_used_as_evidence"], [1])
            original = markdown
            with self.assertRaises(MODULE.PipelineError):
                MODULE.build_run(run_dir)
            self.assertEqual(destination.read_text(encoding="utf-8"), original)

    def test_blocks_untraceable_quote(self):
        with tempfile.TemporaryDirectory() as temporary:
            run_dir = self.make_run(Path(temporary), quote="This sentence does not occur on the source page.")
            with self.assertRaises(MODULE.PipelineError):
                MODULE.build_run(run_dir)
            result = json.loads((run_dir / "validation.json").read_text(encoding="utf-8"))
            self.assertEqual(result["status"], "blocked")
            self.assertIn("untraceable_quote", {item["issue_type"] for item in result["issues"]})
            self.assertFalse((run_dir / "preview.md").exists())

    def test_blocks_numeric_mismatch(self):
        with tempfile.TemporaryDirectory() as temporary:
            run_dir = self.make_run(Path(temporary), value="99")
            with self.assertRaises(MODULE.PipelineError):
                MODULE.build_run(run_dir)
            result = json.loads((run_dir / "validation.json").read_text(encoding="utf-8"))
            self.assertIn("numeric_fidelity", {item["issue_type"] for item in result["issues"]})

    def test_allows_dimensionless_numeric_item_with_empty_unit(self):
        with tempfile.TemporaryDirectory() as temporary:
            run_dir = self.make_run(Path(temporary), unit="")
            result, *_ = MODULE.validate_run(run_dir)
            self.assertNotIn(
                "numeric_fidelity",
                {item["issue_type"] for item in result["issues"]},
            )

    def test_blocks_number_in_claim_that_is_absent_from_evidence(self):
        with tempfile.TemporaryDirectory() as temporary:
            run_dir = self.make_run(Path(temporary))
            claims_path = run_dir / "claims.json"
            claims = json.loads(claims_path.read_text(encoding="utf-8"))
            claims[0]["claim_text_zh"] = "作者报告模型准确率为 99%。"
            write_json(claims_path, claims)
            with self.assertRaises(MODULE.PipelineError):
                MODULE.build_run(run_dir)
            result = json.loads((run_dir / "validation.json").read_text(encoding="utf-8"))
            self.assertIn("claim_number_untraceable", {item["issue_type"] for item in result["issues"]})

    def test_blocks_evidence_that_violates_required_contract(self):
        with tempfile.TemporaryDirectory() as temporary:
            run_dir = self.make_run(Path(temporary))
            evidence_path = run_dir / "evidence.json"
            evidence = json.loads(evidence_path.read_text(encoding="utf-8"))
            del evidence[0]["evidence_type"]
            write_json(evidence_path, evidence)
            with self.assertRaises(MODULE.PipelineError):
                MODULE.build_run(run_dir)
            result = json.loads((run_dir / "validation.json").read_text(encoding="utf-8"))
            self.assertIn("invalid_evidence_schema", {item["issue_type"] for item in result["issues"]})

    def test_blocks_unverified_evidence_page(self):
        with tempfile.TemporaryDirectory() as temporary:
            run_dir = self.make_run(Path(temporary))
            evidence_path = run_dir / "evidence.json"
            evidence = json.loads(evidence_path.read_text(encoding="utf-8"))
            evidence[0]["page_verified"] = False
            evidence[0]["source_match_kind"] = "unmatched"
            write_json(evidence_path, evidence)
            with self.assertRaises(MODULE.PipelineError):
                MODULE.build_run(run_dir)
            result = json.loads((run_dir / "validation.json").read_text(encoding="utf-8"))
            self.assertIn("unverified_evidence_page", {item["issue_type"] for item in result["issues"]})

    def test_selected_visual_must_pass_provenance_gate_and_is_embedded(self):
        with tempfile.TemporaryDirectory() as temporary:
            run_dir = self.make_run(Path(temporary))
            image = run_dir / "figure-1.png"
            image.write_bytes(b"verified-figure-image")
            manifest = run_dir / "figure-1.json"
            write_json(
                manifest,
                {
                    "schema_version": "0.1",
                    "figure_label": "Figure 1",
                    "physical_pdf_page": 1,
                    "source_pdf_sha256": "a" * 64,
                    "crop_validation_status": "pass",
                    "needs_human_review": False,
                    "output_image_sha256": MODULE.sha256_file(image),
                },
            )
            write_json(
                run_dir / "figures.json",
                {
                    "schema_version": "0.1",
                    "selection_status": "completed",
                    "selected": [
                        {
                            "figure_label": "Figure 1",
                            "physical_pdf_page": 1,
                            "caption_original": "Figure 1. Verified method schematic.",
                            "selection_reason": "It is indispensable to the method.",
                            "discussion_location": "3.2 Methods",
                            "image_path": str(image),
                            "manifest_path": str(manifest),
                            "embed_path": "LitAnchor-Test/_assets/test/figure-1.png",
                        }
                    ],
                    "rejected": [],
                    "no_selection_reason": None,
                },
            )
            destination, result = MODULE.build_run(run_dir)
            markdown = destination.read_text(encoding="utf-8")
            self.assertEqual(result["statistics"]["figure_count"], 1)
            self.assertIn("Figure 1（3.2 Methods；〔p.1〕）", markdown)
            self.assertNotIn("![[", markdown)

    def test_deep_run_with_only_first_page_evidence_is_incomplete(self):
        with tempfile.TemporaryDirectory() as temporary:
            run_dir = self.make_run(Path(temporary), reading_mode="deep")
            source_path = run_dir / "source-bundle.json"
            source = json.loads(source_path.read_text(encoding="utf-8"))
            source["pdf"]["page_count"] = 5
            source["pages"] = [
                {
                    "page_index": page,
                    "printed_page": None,
                    "raw_text": (
                        "The model achieved 95% accuracy on the test set."
                        if page == 1
                        else f"Readable source content for physical page {page} with sufficient detail."
                    ),
                    "extraction_method": "native_text",
                    "confidence": 1.0,
                    "warnings": [],
                }
                for page in range(1, 6)
            ]
            write_json(source_path, source)
            with self.assertRaises(MODULE.PipelineError):
                MODULE.build_run(run_dir)
            coverage = json.loads((run_dir / "coverage_receipt.json").read_text(encoding="utf-8"))
            self.assertEqual(coverage["extraction_status"], "complete")
            self.assertEqual(coverage["analysis_status"], "insufficient")
            self.assertEqual(coverage["coverage_status"], "incomplete")

    def test_deep_coverage_uses_last_relevant_main_page_not_pdf_midpoint(self):
        source = {
            "paper_id": "nature-layout",
            "pdf": {"page_count": 19, "preflight_status": "PASS"},
            "pages": [
                {
                    "page_index": page,
                    "raw_text": f"Readable content for physical page {page} with sufficient detail.",
                }
                for page in range(1, 20)
            ],
        }
        evidence = [
            {
                "page_index": page,
                "section": section,
                "page_verified": True,
                "source_match_kind": "exact",
            }
            for page, section in [(2, "Introduction"), (5, "Results"), (9, "Methods")]
        ]
        page_classification = {
            "pages": [
                {
                    "page_index": page,
                    "classification": (
                        "references_only"
                        if page == 7
                        else "appendix"
                        if page >= 10
                        else "main_content"
                    ),
                    "semantic_reviewed": True,
                }
                for page in range(1, 20)
            ]
        }

        for mode in ("deep", "internalize"):
            coverage = MODULE.build_coverage_receipt(
                source,
                evidence,
                {"run_id": "run", "reading_mode": mode},
                page_classification,
            )

            self.assertTrue(coverage["reaches_later_half"])
            self.assertEqual(coverage["analysis_status"], "complete")
            self.assertEqual(coverage["coverage_status"], "complete")

    def test_verified_pages_render_distinct_zotero_links(self):
        with tempfile.TemporaryDirectory() as temporary:
            # Page-link rendering is independent of deep-reading completeness.
            # Keep this fixture in skim mode so the deep quality gate is not bypassed.
            run_dir = self.make_run(Path(temporary), reading_mode="skim")
            source_path = run_dir / "source-bundle.json"
            source = json.loads(source_path.read_text(encoding="utf-8"))
            source["source"].update(
                {
                    "acquisition_method": "zotero_local_api",
                    "zotero_item_key": "ABCD1234",
                    "zotero_attachment_key": "PDFD1234",
                }
            )
            source["pdf"]["page_count"] = 10
            source["pages"] = [
                {
                    "page_index": page,
                    "printed_page": None,
                    "raw_text": (
                        {
                            2: "The paper defines the research question on physical page two.",
                            5: "The authors describe the central method on physical page five.",
                            10: "The final result is reported on physical page ten.",
                        }.get(page, f"Readable source content for physical page {page} with sufficient detail.")
                    ),
                    "extraction_method": "native_text",
                    "confidence": 1.0,
                    "warnings": [],
                }
                for page in range(1, 11)
            ]
            evidence = [
                {
                    "evidence_id": "E-002",
                    "evidence_type": "research_question",
                    "page_index": 2,
                    "printed_page": None,
                    "section": "Introduction",
                    "block_id": None,
                    "bounding_box": None,
                    "quote_original": "The paper defines the research question on physical page two.",
                    "epistemic_status": "observed",
                    "epistemic_markers": [],
                    "contains_number": False,
                    "contains_unit": False,
                    "contains_variable": False,
                    "confidence": 1.0,
                    "needs_review": False,
                    "page_verified": True,
                    "source_match_kind": "exact",
                    "issues": [],
                },
                {
                    "evidence_id": "E-005",
                    "evidence_type": "method_step",
                    "page_index": 5,
                    "printed_page": None,
                    "section": "Methods",
                    "block_id": None,
                    "bounding_box": None,
                    "quote_original": "The authors describe the central method on physical page five.",
                    "epistemic_status": "observed",
                    "epistemic_markers": [],
                    "contains_number": False,
                    "contains_unit": False,
                    "contains_variable": False,
                    "confidence": 1.0,
                    "needs_review": False,
                    "page_verified": True,
                    "source_match_kind": "exact",
                    "issues": [],
                },
                {
                    "evidence_id": "E-010",
                    "evidence_type": "result",
                    "page_index": 10,
                    "printed_page": None,
                    "section": "Results",
                    "block_id": None,
                    "bounding_box": None,
                    "quote_original": "The final result is reported on physical page ten.",
                    "epistemic_status": "observed",
                    "epistemic_markers": [],
                    "contains_number": False,
                    "contains_unit": False,
                    "contains_variable": False,
                    "confidence": 1.0,
                    "needs_review": False,
                    "page_verified": True,
                    "source_match_kind": "exact",
                    "issues": [],
                },
            ]
            claims = [
                {
                    "claim_id": f"C-{page:03d}",
                    "claim_text_zh": text,
                    "claim_type": claim_type,
                    "epistemic_status": "observed",
                    "evidence_ids": [evidence_id],
                    "page_refs": [page],
                    "numeric_items": [],
                    "display_level": "inline",
                    "validation": {
                        "traceable": True,
                        "semantic_support": "pass",
                        "numeric_fidelity": "pass",
                        "modality_fidelity": "pass",
                        "final_status": "pass",
                    },
                }
                for page, evidence_id, claim_type, text in (
                    (2, "E-002", "question", "论文提出了研究问题。"),
                    (5, "E-005", "method", "作者说明了核心方法。"),
                    (10, "E-010", "result", "作者报告了最终结果。"),
                )
            ]
            write_json(source_path, source)
            write_json(run_dir / "evidence.json", evidence)
            write_json(run_dir / "claims.json", claims)
            destination, result = MODULE.build_run(run_dir)
            markdown = destination.read_text(encoding="utf-8")
            self.assertEqual(result["status"], "completed")
            for page in (2, 5, 10):
                self.assertIn(
                    f"zotero://open-pdf/library/items/PDFD1234?page={page}",
                    markdown,
                )

    def test_preflight_warning_is_preserved_in_note_status(self):
        with tempfile.TemporaryDirectory() as temporary:
            run_dir = self.make_run(Path(temporary))
            source_path = run_dir / "source-bundle.json"
            source = json.loads(source_path.read_text(encoding="utf-8"))
            source["pdf"]["preflight_status"] = "PASS_WITH_WARNINGS"
            source["pdf"]["warnings"] = ["review_page_extraction_warnings"]
            source["pages"][0]["warnings"] = ["rotated_text_discovered"]
            write_json(source_path, source)
            destination, result = MODULE.build_run(run_dir)
            self.assertEqual(result["status"], "completed_with_warnings")
            self.assertIn(
                'validation_status: "completed_with_warnings"',
                destination.read_text(encoding="utf-8"),
            )

    @unittest.skipUnless(importlib.util.find_spec("pymupdf"), "PyMuPDF is not installed")
    def test_blank_pdf_requires_fallback(self):
        import pymupdf

        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            pdf = root / "blank.pdf"
            document = pymupdf.open()
            document.new_page(width=612, height=792)
            document.new_page(width=612, height=792)
            document.set_metadata({"author": "Unverified PDF uploader"})
            document.save(pdf)
            document.close()
            run_dir, bundle = MODULE.prepare_pdf(pdf, root / "runs", reading_mode="skim")
            self.assertEqual(bundle["pdf"]["preflight_status"], "FALLBACK_REQUIRED")
            self.assertEqual(len(bundle["pages"]), 2)
            self.assertEqual(bundle["metadata"]["authors"], [])
            self.assertTrue((run_dir / "source-bundle.json").is_file())

    @unittest.skipUnless(importlib.util.find_spec("pymupdf"), "PyMuPDF is not installed")
    def test_corrupt_pdf_is_blocked_before_run_creation(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            pdf = root / "corrupt.pdf"
            pdf.write_bytes(b"not a pdf")
            with self.assertRaises(MODULE.PipelineError):
                MODULE.prepare_pdf(pdf, root / "runs")


if __name__ == "__main__":
    unittest.main()
