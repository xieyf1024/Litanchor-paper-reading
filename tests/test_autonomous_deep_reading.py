import json
import sys
import tempfile
import unittest
from pathlib import Path

import pymupdf


SCRIPT_DIR = (
    Path(__file__).resolve().parents[1]
    / "skills"
    / "litanchor-paper-reading"
    / "scripts"
)
sys.path.insert(0, str(SCRIPT_DIR))

from autonomous_deep_reading import (  # noqa: E402
    AutonomousPipelineError,
    accept_visual_review,
    build_autonomous_plan,
    build_reading_passes,
    classify_physical_pages,
    classify_paper_type,
    detect_sections,
    discover_figure_candidates,
    promote_reviewed_claims,
    fuse_mineru_figure_candidates,
    fuse_mineru_sections,
    validate_independent_reviews,
    validate_autonomous_origins,
)


def make_pdf(path: Path, page_texts: list[str]) -> None:
    document = pymupdf.open()
    for text in page_texts:
        page = document.new_page()
        page.insert_textbox(pymupdf.Rect(50, 50, 545, 792), text, fontsize=10)
    document.save(path)
    document.close()


class AutonomousDeepReadingTests(unittest.TestCase):
    def test_visual_review_acceptance_requires_pending_review(self):
        with tempfile.TemporaryDirectory() as temporary:
            run_dir = Path(temporary)
            (run_dir / "run.json").write_text(
                json.dumps({"review_status": "independently_reviewed"}),
                encoding="utf-8",
            )
            (run_dir / "validation.json").write_text(
                json.dumps({"issues": []}),
                encoding="utf-8",
            )
            (run_dir / "figures.json").write_text(
                json.dumps({"selected": [{"figure_label": "Figure 1"}]}),
                encoding="utf-8",
            )

            with self.assertRaises(AutonomousPipelineError):
                accept_visual_review(run_dir)

    def test_claims_are_promoted_only_after_complete_passing_fidelity_review(self):
        claims = [
            {"claim_id": "C-001", "validation": {"final_status": "warning"}},
            {"claim_id": "C-002", "validation": {"final_status": "warning"}},
        ]
        review = {
            "final_status": "pass",
            "checked_claim_ids": ["C-001", "C-002"],
        }

        promoted = promote_reviewed_claims(claims, review)

        self.assertTrue(
            all(item["validation"]["final_status"] == "pass" for item in promoted)
        )
        review["checked_claim_ids"] = ["C-001"]
        with self.assertRaises(AutonomousPipelineError):
            promote_reviewed_claims(claims, review)

    def test_classifies_paper_types_without_prefilled_answer(self):
        cases = [
            (
                {"title": "A framework for an earth system model"},
                [{"normalized_type": "model", "title_original": "Model components"}],
                "model-description",
            ),
            (
                {"title": "Masked autoencoders are scalable vision learners"},
                [
                    {"normalized_type": "method", "title_original": "Approach"},
                    {"normalized_type": "experiments", "title_original": "Experiments"},
                ],
                "method-algorithm",
            ),
            (
                {"title": "Attention Is All You Need"},
                [
                    {"normalized_type": "methods", "title_original": "Training"},
                    {"normalized_type": "model", "title_original": "Model"},
                    {"normalized_type": "results", "title_original": "Results"},
                ],
                "method-algorithm",
            ),
            (
                {"title": "A comprehensive review of ocean observations"},
                [{"normalized_type": "review", "title_original": "Review scope"}],
                "review",
            ),
            (
                {"title": "ENSO variability during the last millennium"},
                [
                    {"normalized_type": "methods", "title_original": "Methods"},
                    {"normalized_type": "results", "title_original": "Results"},
                ],
                "empirical-research",
            ),
        ]
        for metadata, sections, expected in cases:
            with self.subTest(expected=expected):
                pages = (
                    [
                        {
                            "raw_text": (
                                "We propose a new simple network architecture, "
                                "the Transformer, based solely on attention mechanisms."
                            )
                        }
                    ]
                    if metadata["title"] == "Attention Is All You Need"
                    else []
                )
                result = classify_paper_type(metadata, sections, pages)
                self.assertEqual(result["paper_type"], expected)
                self.assertGreater(result["confidence"], 0)
                self.assertTrue(result["signals"])

    def test_section_mapping_and_reading_passes_cover_every_page(self):
        pages = [
            {"page_index": 1, "raw_text": "Abstract\nSummary.\n1. Introduction\nBackground."},
            {"page_index": 2, "raw_text": "2. Methods\nWe run an experiment."},
            {"page_index": 3, "raw_text": "3. Results\nThe result improves accuracy."},
            {"page_index": 4, "raw_text": "4. Discussion\nLimitations are discussed."},
        ]
        sections = detect_sections(pages)
        self.assertTrue(any(item["normalized_type"] == "introduction" for item in sections))
        self.assertTrue(any(item["normalized_type"] == "methods" for item in sections))
        passes = build_reading_passes(4, sections, {"paper_type": "empirical-research"})
        self.assertEqual([item["pass_id"] for item in passes], [
            "pass-1-structure",
            "pass-2-problem",
            "pass-3-method",
            "pass-4-results",
            "pass-5-ledgers",
            "pass-6-compose-review",
        ])
        source_pages = {
            page
            for item in passes[:4]
            for page in item["source_pages"]
        }
        self.assertEqual(source_pages, {1, 2, 3, 4})

    def test_page_classification_keeps_appendix_in_semantic_recall(self):
        pages = [
            {"page_index": 1, "raw_text": "Main text.", "warnings": []},
            {
                "page_index": 2,
                "raw_text": (
                    "Conclusion text with substantive analysis that explains the "
                    "main result, its scope, and the final implication for the stated "
                    "research question.\nReferences\n[1] A."
                ),
                "warnings": [],
            },
            {"page_index": 3, "raw_text": "[2] B.", "warnings": []},
            {
                "page_index": 4,
                "raw_text": "Appendix A. Implementation Details\nTraining settings.",
                "warnings": [],
            },
            {"page_index": 5, "raw_text": "Robustness evaluation.", "warnings": []},
        ]
        sections = [
            {"normalized_type": "conclusion", "start_page": 2, "end_page": 2},
            {"normalized_type": "references", "start_page": 2, "end_page": 4},
            {
                "normalized_type": "methods",
                "title_original": "A. Implementation Details",
                "start_page": 4,
                "end_page": 5,
            },
        ]

        result = classify_physical_pages(pages, sections)
        classes = {
            item["page_index"]: item["classification"] for item in result["pages"]
        }

        self.assertEqual(classes[2], "main_content")
        self.assertEqual(classes[3], "references_only")
        self.assertEqual(classes[4], "appendix")
        self.assertEqual(classes[5], "appendix")
        self.assertTrue(
            next(item for item in result["pages"] if item["page_index"] == 4)[
                "semantic_review_required"
            ]
        )

    def test_page_classification_recovers_visual_appendix_after_references(self):
        pages = [
            {"page_index": 1, "raw_text": "Main text.", "warnings": []},
            {"page_index": 2, "raw_text": "References\n[1] A.", "warnings": []},
            {"page_index": 3, "raw_text": "[2] B.", "warnings": []},
            {
                "page_index": 4,
                "raw_text": (
                    "Attention Visualizations\n"
                    "Figure 3: An example of the attention mechanism."
                ),
                "warnings": [],
            },
            {
                "page_index": 5,
                "raw_text": "Figure 4: Two attention heads.",
                "warnings": [],
            },
        ]
        sections = [
            {"normalized_type": "references", "start_page": 2, "end_page": 5},
        ]

        result = classify_physical_pages(pages, sections)
        classes = {
            item["page_index"]: item["classification"] for item in result["pages"]
        }

        self.assertEqual(classes[2], "references_only")
        self.assertEqual(classes[3], "references_only")
        self.assertEqual(classes[4], "appendix")
        self.assertEqual(classes[5], "appendix")

    def test_page_classification_recovers_methods_after_references(self):
        pages = [
            {"page_index": 1, "raw_text": "Main text.", "warnings": []},
            {"page_index": 2, "raw_text": "References\n[1] A.", "warnings": []},
            {"page_index": 3, "raw_text": "[2] B.", "warnings": []},
            {
                "page_index": 4,
                "raw_text": "Methods\nProxy reconstructions\nWe analyse monthly records.",
                "warnings": [],
            },
            {
                "page_index": 5,
                "raw_text": "Data availability\nThe source data are archived.",
                "warnings": [],
            },
            {
                "page_index": 6,
                "raw_text": "Supplementary information\nExtended data are available.",
                "warnings": [],
            },
        ]
        sections = [
            {"normalized_type": "references", "start_page": 2, "end_page": 4},
            {
                "normalized_type": "methods",
                "title_original": "Methods",
                "start_page": 4,
                "end_page": 5,
            },
            {
                "normalized_type": "appendix",
                "title_original": "Supplementary information",
                "start_page": 6,
                "end_page": 6,
            },
        ]

        result = classify_physical_pages(pages, sections)
        classes = {
            item["page_index"]: item["classification"] for item in result["pages"]
        }

        self.assertEqual(classes[2], "references_only")
        self.assertEqual(classes[3], "references_only")
        self.assertEqual(classes[4], "main_content")
        self.assertEqual(classes[5], "main_content")
        self.assertEqual(classes[6], "appendix")

    def test_figure_discovery_accepts_nature_pipe_captions(self):
        pages = [
            {
                "page_index": 3,
                "raw_text": (
                    "Fig. 2 | Multi-year ENSO in proxies and simulations during "
                    "the past 7 ka.\nBody text cites Fig. 2."
                ),
            },
            {
                "page_index": 5,
                "raw_text": (
                    "Fig. 4 | Influence of orbital forcing on the upper ocean "
                    "in the Eastern Pacific."
                ),
            },
        ]

        candidates = discover_figure_candidates(pages)

        self.assertEqual(
            [item["label"] for item in candidates],
            ["Figure 2", "Figure 4"],
        )
        self.assertEqual(candidates[0]["page_index"], 3)
        self.assertIn("Multi-year ENSO", candidates[0]["caption_original"])

    def test_origin_policy_rejects_curated_or_user_records(self):
        evidence = [{"evidence_id": "E-001", "origin": "auto_extracted"}]
        claims = [{"claim_id": "C-001", "origin": "auto_synthesized"}]
        validate_autonomous_origins(evidence, claims)
        evidence[0]["origin"] = "curated"
        with self.assertRaises(AutonomousPipelineError):
            validate_autonomous_origins(evidence, claims)

    def test_build_plan_uses_pymupdf_and_creates_agent_work_packets(self):
        with tempfile.TemporaryDirectory() as temporary:
            run_dir = Path(temporary) / "run"
            run_dir.mkdir()
            pdf_path = Path(temporary) / "paper.pdf"
            make_pdf(
                pdf_path,
                [
                    "Title\nAbstract\nThis paper proposes a method.\n1. Introduction\nBackground.",
                    "2. Method\nThe model uses an encoder and decoder.\nFigure 1. Model architecture.",
                    "3. Experiments\nWe evaluate accuracy.\n4. Conclusion\nThe method improves results.",
                ],
            )
            source = {
                "schema_version": "0.1",
                "paper_id": "pdf-test",
                "source": {
                    "external_knowledge_allowed": False,
                    "zotero_item_key": "ABCDEFGH",
                    "zotero_attachment_key": "HGFEDCBA",
                },
                "metadata": {
                    "title": "A scalable encoder method",
                    "authors": ["First Author", "Second Author"],
                },
                "pdf": {
                    "path": str(pdf_path),
                    "sha256": __import__("hashlib").sha256(pdf_path.read_bytes()).hexdigest(),
                    "page_count": 3,
                    "preflight_status": "PASS",
                    "warnings": [],
                },
                "pages": [],
            }
            (run_dir / "source-bundle.json").write_text(
                json.dumps(source), encoding="utf-8"
            )
            (run_dir / "evidence.json").write_text("[]", encoding="utf-8")
            (run_dir / "claims.json").write_text("[]", encoding="utf-8")
            (run_dir / "figures.json").write_text(
                json.dumps({"selection_status": "pending", "selected": [], "rejected": []}),
                encoding="utf-8",
            )
            (run_dir / "run.json").write_text(
                json.dumps({"run_id": "run", "status": "prepared", "reading_mode": "deep"}),
                encoding="utf-8",
            )

            plan = build_autonomous_plan(run_dir, allow_mineru_upload=False)

            self.assertEqual(plan["status"], "awaiting_agent_analysis")
            self.assertEqual(plan["baseline_engine"], "PyMuPDF")
            self.assertEqual(plan["page_count"], 3)
            self.assertEqual(len(plan["passes"]), 6)
            self.assertTrue((run_dir / "pymupdf-pages.json").is_file())
            self.assertTrue((run_dir / "sections.json").is_file())
            self.assertTrue((run_dir / "page-classification.json").is_file())
            self.assertTrue((run_dir / "paper-profile.json").is_file())
            self.assertTrue((run_dir / "reading-passes.json").is_file())
            self.assertTrue((run_dir / "figure-candidates.json").is_file())
            self.assertTrue((run_dir / "section-synthesis.json").is_file())
            self.assertTrue((run_dir / "missing-information-check.json").is_file())
            self.assertTrue((run_dir / "visual-analysis.json").is_file())
            self.assertTrue((run_dir / "semantic-generation.json").is_file())
            self.assertTrue((run_dir / "fidelity-review.json").is_file())
            self.assertTrue((run_dir / "recall-review.json").is_file())
            self.assertTrue((run_dir / "autonomous-run.json").is_file())

            updated_source = json.loads(
                (run_dir / "source-bundle.json").read_text(encoding="utf-8")
            )
            self.assertEqual(
                updated_source["pdf"]["authoritative_text_engine"], "PyMuPDF"
            )
            self.assertEqual(updated_source["pdf"]["preflight_status"], "PASS")
            self.assertEqual(updated_source["pdf"]["pymupdf_warning_pages"], [1, 2, 3])
            self.assertEqual(len(updated_source["pages"]), 3)
            self.assertTrue(updated_source["pages"][1]["text_blocks"])

    def test_build_plan_refuses_prefilled_blind_ledgers(self):
        with tempfile.TemporaryDirectory() as temporary:
            run_dir = Path(temporary)
            (run_dir / "evidence.json").write_text(
                json.dumps([{"evidence_id": "E-001"}]), encoding="utf-8"
            )
            (run_dir / "claims.json").write_text("[]", encoding="utf-8")
            with self.assertRaises(AutonomousPipelineError):
                build_autonomous_plan(run_dir, allow_mineru_upload=False)

    def test_independent_reviews_must_cover_claims_and_required_content(self):
        with tempfile.TemporaryDirectory() as temporary:
            run_dir = Path(temporary)
            evidence = [{"evidence_id": "E-001", "origin": "auto_extracted"}]
            claims = [
                {
                    "claim_id": "C-001",
                    "claim_type": "method",
                    "origin": "auto_synthesized",
                }
            ]
            (run_dir / "evidence.json").write_text(
                json.dumps(evidence), encoding="utf-8"
            )
            (run_dir / "claims.json").write_text(
                json.dumps(claims), encoding="utf-8"
            )
            (run_dir / "paper-profile.json").write_text(
                json.dumps({"paper_type": "method-algorithm"}), encoding="utf-8"
            )
            fidelity = {
                "reviewer_role": "fidelity-reviewer",
                "independent_from_composer": True,
                "checked_claim_ids": ["C-001"],
                "findings": [],
                "final_status": "pass",
            }
            required_content = [
                "question",
                "contribution",
                "method",
                "model",
                "metric",
                "experiment",
                "result",
                "limitation",
            ]
            recall = {
                "reviewer_role": "recall-reviewer",
                "independent_from_composer": True,
                "required_content_groups": required_content,
                "observed_content_groups": required_content,
                "missing_content_groups": [],
                "findings": [],
                "final_status": "pass",
            }
            (run_dir / "fidelity-review.json").write_text(
                json.dumps(fidelity), encoding="utf-8"
            )
            (run_dir / "recall-review.json").write_text(
                json.dumps(recall), encoding="utf-8"
            )

            validate_independent_reviews(run_dir)

            fidelity["checked_claim_ids"] = []
            (run_dir / "fidelity-review.json").write_text(
                json.dumps(fidelity), encoding="utf-8"
            )
            with self.assertRaises(AutonomousPipelineError):
                validate_independent_reviews(run_dir)

    def test_mineru_headings_enhance_sections_without_becoming_evidence(self):
        with tempfile.TemporaryDirectory() as temporary:
            run_dir = Path(temporary)
            mineru_dir = run_dir / "mineru"
            mineru_dir.mkdir()
            (run_dir / "sections.json").write_text("[]", encoding="utf-8")
            (run_dir / "pymupdf-pages.json").write_text(
                json.dumps(
                    [
                        {
                            "page_index": page,
                            "raw_text": f"Page {page} content.",
                            "warnings": [],
                        }
                        for page in range(1, 5)
                    ]
                ),
                encoding="utf-8",
            )
            (run_dir / "mineru-plan.json").write_text(
                json.dumps(
                    {
                        "status": "pending",
                        "selected_original_pages": [2, 4],
                    }
                ),
                encoding="utf-8",
            )
            (run_dir / "autonomous-run.json").write_text(
                json.dumps({"mineru": {"status": "pending"}, "page_count": 4}),
                encoding="utf-8",
            )
            (run_dir / "paper-profile.json").write_text(
                json.dumps({"paper_type": "method-algorithm"}),
                encoding="utf-8",
            )
            (mineru_dir / "mineru_raw.md").write_text(
                "## 3. Approach\n\nThe encoder processes visible patches only.\n\n"
                "## 4. ImageNet Experiments\n\nWe evaluate the model on ImageNet.\n",
                encoding="utf-8",
            )
            (mineru_dir / "alignment.json").write_text(
                json.dumps(
                    {
                        "blocks": [
                            {
                                "text": "The encoder processes visible patches only.",
                                "status": "fuzzy",
                                "pdf_page": 2,
                                "authoritative_evidence": False,
                            },
                            {
                                "text": "We evaluate the model on ImageNet.",
                                "status": "fuzzy",
                                "pdf_page": 4,
                                "authoritative_evidence": False,
                            },
                        ],
                        "statistics": {
                            "block_count": 2,
                            "exact": 0,
                            "fuzzy": 2,
                            "unmatched": 0,
                        },
                    }
                ),
                encoding="utf-8",
            )
            (mineru_dir / "privacy_receipt.json").write_text(
                json.dumps(
                    {
                        "consent_external_upload": True,
                        "original_physical_pages": [2, 4],
                    }
                ),
                encoding="utf-8",
            )

            sections = fuse_mineru_sections(run_dir, mineru_dir)

            self.assertEqual(
                {section["normalized_type"] for section in sections},
                {"model", "experiments"},
            )
            self.assertTrue(
                all(section["source"] == "mineru_aligned_heading" for section in sections)
            )
            self.assertTrue(
                all(section["authoritative_evidence"] is False for section in sections)
            )

    def test_mineru_fusion_preserves_only_still_valid_page_reviews(self):
        with tempfile.TemporaryDirectory() as temporary:
            run_dir = Path(temporary)
            mineru_dir = run_dir / "mineru"
            mineru_dir.mkdir()
            (run_dir / "sections.json").write_text(
                json.dumps(
                    [
                        {
                            "section_id": "S-001",
                            "title_original": "References",
                            "normalized_type": "references",
                            "start_page": 2,
                            "end_page": 2,
                            "confidence": 1.0,
                            "source": "pymupdf_heading",
                        }
                    ]
                ),
                encoding="utf-8",
            )
            (run_dir / "pymupdf-pages.json").write_text(
                json.dumps(
                    [
                        {
                            "page_index": 1,
                            "raw_text": "Main paper content with results and discussion.",
                            "warnings": [],
                        },
                        {
                            "page_index": 2,
                            "raw_text": "References\n[1] Example reference.",
                            "warnings": [],
                        },
                    ]
                ),
                encoding="utf-8",
            )
            (run_dir / "page-classification.json").write_text(
                json.dumps(
                    {
                        "schema_version": "0.1",
                        "pages": [
                            {
                                "page_index": 1,
                                "classification": "main_content",
                                "semantic_reviewed": True,
                                "review_outcome": "evidence_captured",
                                "review_notes": "Reviewed before MinerU fusion.",
                                "evidence_ids": ["E-001"],
                            },
                            {
                                "page_index": 2,
                                "classification": "main_content",
                                "semantic_reviewed": True,
                                "review_outcome": "evidence_captured",
                                "review_notes": "This stale review must be discarded.",
                                "evidence_ids": ["E-002"],
                            },
                        ],
                    }
                ),
                encoding="utf-8",
            )
            (run_dir / "mineru-plan.json").write_text(
                json.dumps(
                    {
                        "status": "pending",
                        "selected_original_pages": [1, 2],
                    }
                ),
                encoding="utf-8",
            )
            (run_dir / "autonomous-run.json").write_text(
                json.dumps({"mineru": {"status": "pending"}, "page_count": 2}),
                encoding="utf-8",
            )
            (run_dir / "paper-profile.json").write_text(
                json.dumps({"paper_type": "empirical-research"}),
                encoding="utf-8",
            )
            (mineru_dir / "mineru_raw.md").write_text(
                "## Results\n\nMain paper content with results and discussion.\n",
                encoding="utf-8",
            )
            (mineru_dir / "alignment.json").write_text(
                json.dumps(
                    {
                        "blocks": [
                            {
                                "text": "Main paper content with results and discussion.",
                                "status": "exact",
                                "pdf_page": 1,
                                "authoritative_evidence": False,
                            }
                        ],
                        "statistics": {
                            "block_count": 1,
                            "exact": 1,
                            "fuzzy": 0,
                            "unmatched": 0,
                        },
                    }
                ),
                encoding="utf-8",
            )
            (mineru_dir / "privacy_receipt.json").write_text(
                json.dumps(
                    {
                        "consent_external_upload": True,
                        "original_physical_pages": [1, 2],
                    }
                ),
                encoding="utf-8",
            )

            fuse_mineru_sections(run_dir, mineru_dir)

            pages = json.loads(
                (run_dir / "page-classification.json").read_text(encoding="utf-8")
            )["pages"]
            self.assertEqual(pages[0]["review_outcome"], "evidence_captured")
            self.assertEqual(pages[0]["evidence_ids"], ["E-001"])
            self.assertEqual(pages[1]["classification"], "references_only")
            self.assertEqual(pages[1]["review_outcome"], "excluded_reference")
            self.assertEqual(pages[1]["evidence_ids"], [])

    def test_mineru_figure_inventory_recovers_all_labels_as_structure_hints(self):
        with tempfile.TemporaryDirectory() as temporary:
            run_dir = Path(temporary)
            mineru_dir = run_dir / "mineru"
            mineru_dir.mkdir()
            (run_dir / "figure-candidates.json").write_text(
                json.dumps(
                    [
                        {
                            "visual_id": "V-001",
                            "label": "Figure 2",
                            "page_index": 3,
                            "caption_original": "Short caption.",
                            "origin": "auto_extracted",
                        }
                    ]
                ),
                encoding="utf-8",
            )
            (mineru_dir / "alignment.json").write_text(
                json.dumps(
                    {
                        "blocks": [
                            {
                                "text": (
                                    "Figure 1. Complete architecture caption with "
                                    "encoder and decoder."
                                ),
                                "status": "fuzzy",
                                "pdf_page": 2,
                                "similarity": 0.97,
                                "authoritative_evidence": False,
                            },
                            {
                                "text": "Figure 2. Longer complete result caption.",
                                "status": "exact",
                                "pdf_page": 3,
                                "similarity": 1.0,
                                "authoritative_evidence": False,
                            },
                        ]
                    }
                ),
                encoding="utf-8",
            )

            figures = fuse_mineru_figure_candidates(run_dir, mineru_dir)

            self.assertEqual([item["label"] for item in figures], ["Figure 1", "Figure 2"])
            self.assertTrue(all(item["mineru_used_as"] == "structure_hint" for item in figures))
            self.assertTrue(all(item["authoritative_evidence"] is False for item in figures))


if __name__ == "__main__":
    unittest.main()
