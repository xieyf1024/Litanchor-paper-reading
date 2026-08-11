import importlib.util
import json
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SKILL = ROOT / "skills" / "litanchor-paper-reading"
SCRIPT = SKILL / "scripts" / "litanchor_local.py"
SPEC = importlib.util.spec_from_file_location("litanchor_local_deep_quality", SCRIPT)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(MODULE)


def write_json(path: Path, payload):
    path.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")


def minimal_source():
    sentence = "The study defines a question, applies a method, reports a result, and states a limitation."
    return {
        "schema_version": "0.1",
        "paper_id": "deep-quality-test",
        "source": {
            "acquisition_method": "manual_pdf",
            "query": "test.pdf",
            "zotero_item_key": None,
            "zotero_attachment_key": None,
            "external_knowledge_allowed": False,
        },
        "metadata": {
            "title": "Deep Quality Test",
            "authors": ["First Author", "Second Author"],
            "year": 2026,
            "journal": "Test Journal",
            "doi": None,
            "citekey": None,
        },
        "annotations": [],
        "pdf": {
            "path": "test.pdf",
            "sha256": "a" * 64,
            "page_count": 1,
            "preflight_status": "PASS",
            "warnings": [],
        },
        "pages": [
            {
                "page_index": 1,
                "printed_page": None,
                "raw_text": sentence,
                "extraction_method": "native_text",
                "confidence": 1.0,
                "warnings": [],
            }
        ],
    }


def minimal_evidence():
    return [
        {
            "evidence_id": "E-001",
            "evidence_type": "result",
            "page_index": 1,
            "printed_page": None,
            "section": "Results",
            "block_id": None,
            "bounding_box": None,
            "quote_original": "The study defines a question, applies a method, reports a result, and states a limitation.",
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
        }
    ]


def minimal_claims():
    validation = {
        "traceable": True,
        "semantic_support": "pass",
        "numeric_fidelity": "pass",
        "modality_fidelity": "pass",
        "final_status": "pass",
    }
    return [
        {
            "claim_id": "C-001",
            "claim_text_zh": "论文报告了一项结果。",
            "claim_type": "result",
            "epistemic_status": "observed",
            "evidence_ids": ["E-001"],
            "page_refs": [1],
            "numeric_items": [],
            "display_level": "inline",
            "validation": validation,
        }
    ]


class DeepReadingQualityTests(unittest.TestCase):
    def test_numeric_renderer_does_not_repeat_unit_already_in_value(self):
        claims = minimal_claims()
        claims[0]["numeric_items"] = [
            {
                "value_original": "4.49%",
                "unit_original": "%",
                "variable": "top-5 error",
                "condition": "ImageNet",
            },
            {
                "value_original": "0.05°C",
                "unit_original": "°C",
                "variable": "RMSE",
                "condition": "test set",
            },
            {
                "value_original": "100 years",
                "unit_original": "years",
                "variable": "integration",
                "condition": None,
            },
        ]

        markdown = MODULE.render_markdown(
            minimal_source(),
            minimal_evidence(),
            claims,
            {
                "schema_version": "0.1",
                "selection_status": "completed",
                "selected": [],
                "rejected": [],
                "no_selection_reason": "The fixture has no figure.",
            },
            {"run_id": "run", "reading_mode": "deep"},
            "completed",
        )

        self.assertIn("top-5 error 4.49%", markdown)
        self.assertIn("RMSE 0.05°C", markdown)
        self.assertIn("integration 100 years", markdown)
        self.assertNotIn("%%", markdown)
        self.assertNotIn("°C°C", markdown)
        self.assertNotIn("yearsyears", markdown)

    def test_final_template_maps_data_metric_and_experiment_to_distinct_sections(self):
        claims = []
        for claim_type, marker in (
            ("data", "DATA_SECTION_MARKER"),
            ("metric", "METRIC_SECTION_MARKER"),
            ("experiment", "EXPERIMENT_SECTION_MARKER"),
        ):
            claim = minimal_claims()[0]
            claim["claim_id"] = f"C-{claim_type.upper()}"
            claim["claim_type"] = claim_type
            claim["claim_text_zh"] = marker
            claims.append(claim)

        markdown = MODULE.render_markdown(
            minimal_source(),
            minimal_evidence(),
            claims,
            {
                "schema_version": "0.1",
                "selection_status": "completed",
                "selected": [],
                "rejected": [],
                "no_selection_reason": "The fixture has no figure.",
            },
            {"run_id": "run", "reading_mode": "deep"},
            "completed",
        )

        section_31 = markdown[
            markdown.index("### 3.1"):markdown.index("### 3.2")
        ]
        section_34 = markdown[
            markdown.index("### 3.4"):markdown.index("### 3.5")
        ]
        section_35 = markdown[
            markdown.index("### 3.5"):markdown.index("## 4.")
        ]
        self.assertIn("DATA_SECTION_MARKER", section_31)
        self.assertIn("METRIC_SECTION_MARKER", section_34)
        self.assertIn("EXPERIMENT_SECTION_MARKER", section_35)

    def test_incomplete_prose_evidence_is_blocked(self):
        source = minimal_source()
        source["pages"][0]["raw_text"] = (
            "Most remarkably, on the challenging dataset we obtain a 6.0% increase in "
            "the standard metric, which is a 28% relative improvement."
        )
        evidence = minimal_evidence()
        evidence[0]["quote_original"] = "we obtain a 6.0% increase in"
        evidence[0]["source_match_kind"] = "normalized"

        with tempfile.TemporaryDirectory() as temporary:
            run_dir = Path(temporary) / "run"
            run_dir.mkdir()
            write_json(run_dir / "source-bundle.json", source)
            write_json(run_dir / "evidence.json", evidence)
            write_json(run_dir / "claims.json", minimal_claims())
            write_json(
                run_dir / "figures.json",
                {
                    "schema_version": "0.1",
                    "selection_status": "completed",
                    "inventory_complete": True,
                    "candidate_count": 0,
                    "candidates_evaluated": [],
                    "selected": [],
                    "rejected": [],
                    "no_selection_reason": "The fixture has no figure.",
                    "no_result_visual_reason": "The fixture has no visual source.",
                },
            )
            write_json(
                run_dir / "run.json",
                {
                    "schema_version": "0.1",
                    "run_id": "run",
                    "paper_id": "deep-quality-test",
                    "skill_version": "0.4.1",
                    "reading_mode": "deep",
                    "created": "2026-01-01T00:00:00+00:00",
                    "status": "prepared",
                    "artifacts": {},
                },
            )

            result, *_ = MODULE.validate_run(run_dir)

        issue_types = {item["issue_type"] for item in result["issues"]}
        self.assertIn("evidence_quote_completeness", issue_types)

    def test_paper_type_profiles_control_metric_and_experiment_recall(self):
        empirical_findings = MODULE.evaluate_deep_claims(
            minimal_claims(),
            page_count=1,
            paper_type="empirical-research",
        )
        empirical_types = {item["issue_type"] for item in empirical_findings}
        self.assertIn("metric_recall", empirical_types)
        self.assertIn("experiment_recall", empirical_types)
        self.assertIn("paper_type_required_sections", empirical_types)

        review_findings = MODULE.evaluate_deep_claims(
            minimal_claims(),
            page_count=1,
            paper_type="review",
        )
        review_types = {item["issue_type"] for item in review_findings}
        self.assertNotIn("metric_recall", review_types)
        self.assertNotIn("experiment_recall", review_types)

    def test_autonomous_paper_profile_is_the_effective_paper_type(self):
        with tempfile.TemporaryDirectory() as temporary:
            run_dir = Path(temporary)
            source = minimal_source()
            write_json(
                run_dir / "paper-profile.json",
                {"paper_type": "method-algorithm"},
            )
            self.assertEqual(
                MODULE.resolve_paper_type(run_dir, source),
                "method-algorithm",
            )

    def test_internalize_requires_learning_layer_and_deep_omits_it(self):
        claims = minimal_claims()
        findings = MODULE.evaluate_deep_claims(
            claims,
            page_count=1,
            paper_type="review",
            reading_mode="internalize",
        )
        self.assertIn(
            "internalize_required_sections",
            {item["issue_type"] for item in findings},
        )

        markdown = MODULE.render_markdown(
            minimal_source(),
            minimal_evidence(),
            claims,
            {
                "schema_version": "0.1",
                "selection_status": "completed",
                "selected": [],
                "rejected": [],
                "no_selection_reason": "The fixture has no figure.",
            },
            {"run_id": "run", "reading_mode": "deep"},
            "completed",
        )
        self.assertNotIn("## 7. 对研究与学习的价值", markdown)
        self.assertNotIn("## 8. 术语与滚雪球阅读", markdown)

        internalize = MODULE.render_markdown(
            minimal_source(),
            minimal_evidence(),
            claims,
            {
                "schema_version": "0.1",
                "selection_status": "completed",
                "selected": [],
                "rejected": [],
                "no_selection_reason": "The fixture has no figure.",
            },
            {"run_id": "run", "reading_mode": "internalize"},
            "completed",
        )
        self.assertIn("## 7. 对研究与学习的价值", internalize)
        self.assertIn("## 8. 术语与滚雪球阅读", internalize)
        self.assertIn("**待用户补充**", internalize)

    def test_beta3_quality_gates_require_experiment_chain_and_provenance(self):
        experiment = minimal_claims()[0]
        experiment["claim_id"] = "C-EXP"
        experiment["claim_type"] = "experiment"
        experiment["importance"] = "core"
        boundary = minimal_claims()[0]
        boundary["claim_id"] = "C-BOUNDARY"
        boundary["claim_type"] = "conclusion_boundary"
        findings = MODULE.evaluate_deep_claims(
            [experiment, boundary],
            page_count=1,
            paper_type="method-algorithm",
        )
        issue_types = {item["issue_type"] for item in findings}
        self.assertIn("experiment_evidence_chain_missing", issue_types)
        self.assertIn("provenance_contract", issue_types)

        experiment["evidence_chain"] = {
            "tested_claim_zh": "检验目标主张。",
            "comparison_conditions_zh": "在固定条件下比较基线。",
            "observed_result_zh": "观察到目标指标改善。",
            "supported_conclusion_zh": "支持在给定条件下有效。",
            "unsupported_stronger_interpretation_zh": "不支持普遍有效的结论。",
        }
        boundary["provenance_class"] = "analysis"
        repaired = MODULE.evaluate_deep_claims(
            [experiment, boundary],
            page_count=1,
            paper_type="method-algorithm",
        )
        repaired_types = {item["issue_type"] for item in repaired}
        self.assertNotIn("experiment_evidence_chain_missing", repaired_types)
        self.assertNotIn("provenance_contract", repaired_types)

    def test_formal_deep_render_rejects_non_page_grounded_source(self):
        with self.assertRaisesRegex(MODULE.PipelineError, "page-grounded"):
            MODULE.render_markdown(
                minimal_source(),
                minimal_evidence(),
                minimal_claims(),
                {
                    "schema_version": "0.1",
                    "selection_status": "completed",
                    "selected": [],
                    "rejected": [],
                    "no_selection_reason": "The fixture has no figure.",
                },
                {
                    "run_id": "run",
                    "reading_mode": "deep",
                    "source_coverage": "partial",
                    "locator_mode": "structure-grounded",
                },
                "completed",
            )

    def test_internalize_research_idea_is_structured_and_source_labelled(self):
        boundary = minimal_claims()[0]
        boundary.update(
            {
                "claim_id": "C-BOUNDARY",
                "claim_type": "conclusion_boundary",
                "claim_text_zh": "该证据不能支持超出测试条件的普遍结论。",
                "title_zh": "外推边界",
                "provenance_class": "analysis",
            }
        )
        idea = minimal_claims()[0]
        idea.update(
            {
                "claim_id": "C-IDEA",
                "claim_type": "research_idea",
                "claim_text_zh": "检验该机制在新条件下是否仍成立。",
                "title_zh": "跨条件复验",
                "provenance_class": "hypothesis",
                "research_idea": {
                    "source_observation_zh": "论文只验证了一个受限条件。",
                    "hypothesis_zh": "改变条件后效应方向仍保持。",
                    "delta_zh": "把原论文的单一条件扩展为条件梯度。",
                    "validation_zh": "预注册条件梯度并比较效应方向与大小。",
                    "failure_modes_zh": [
                        "效应只存在于原始样本。",
                        "测量误差掩盖条件差异。",
                    ],
                    "novelty_status": "unverified",
                },
            }
        )
        markdown = MODULE.render_markdown(
            minimal_source(),
            minimal_evidence(),
            [boundary, idea],
            {
                "schema_version": "0.1",
                "selection_status": "completed",
                "selected": [],
                "rejected": [],
                "no_selection_reason": "The fixture has no figure.",
            },
            {"run_id": "run", "reading_mode": "internalize"},
            "completed",
        )
        self.assertIn("[分析] 外推边界", markdown)
        self.assertIn("[假设] 跨条件复验", markdown)
        self.assertIn("**可证伪假设**", markdown)
        self.assertIn("**新颖性核查状态**：未检索", markdown)
        self.assertNotIn("reading_mode:", markdown)
        self.assertIn('  - "internalize"', markdown)
        self.assertIn('locator_mode: "page-grounded"', markdown)

    def test_internalize_terms_use_the_two_column_v1_table(self):
        term = minimal_claims()[0]
        term.update(
            {
                "claim_id": "C-TERM",
                "claim_type": "term",
                "title_zh": "掩码率",
                "claim_text_zh": "输入图像块中被遮蔽的比例。",
                "detail_points_zh": ["用于控制模型可见信息量。"],
            }
        )
        markdown = MODULE.render_markdown(
            minimal_source(),
            minimal_evidence(),
            [term],
            {
                "schema_version": "0.1",
                "selection_status": "completed",
                "selected": [],
                "rejected": [],
                "no_selection_reason": "The fixture has no figure.",
            },
            {"run_id": "run", "reading_mode": "internalize"},
            "completed",
        )
        terms_section = markdown.split("### 8.1 术语与待解决问题", 1)[1].split(
            "### 8.2", 1
        )[0]
        self.assertIn("| 术语 / 问题 | 通俗解释或当前理解 |", terms_section)
        self.assertIn("| 掩码率 | 输入图像块中被遮蔽的比例。<br>用于控制模型可见信息量。 |", terms_section)
        self.assertNotIn("| 类型 |", terms_section)
        self.assertNotIn("| 定位 |", terms_section)
        self.assertNotIn("| 状态 |", terms_section)

    def test_review_metadata_is_rendered_without_claiming_autonomy(self):
        markdown = MODULE.render_markdown(
            minimal_source(),
            minimal_evidence(),
            minimal_claims(),
            {
                "schema_version": "0.1",
                "selection_status": "completed",
                "selected": [],
                "rejected": [],
                "no_selection_reason": "The fixture has no figure.",
            },
            {
                "run_id": "run",
                "reading_mode": "deep",
                "review_status": "reviewed",
                "generation_mode": "human_assisted_regression",
                "autonomous_generation": False,
            },
            "completed",
        )
        self.assertIn('validation_status: "completed"', markdown)
        self.assertIn('review_status: "reviewed"', markdown)
        self.assertNotIn("generation_mode:", markdown)
        self.assertNotIn("autonomous_generation:", markdown)
        self.assertNotIn("**完整图题**", markdown)

    def test_note_frontmatter_rejects_values_outside_the_frozen_contract(self):
        markdown = MODULE.render_markdown(
            minimal_source(),
            minimal_evidence(),
            minimal_claims(),
            {
                "schema_version": "0.1",
                "selection_status": "completed",
                "selected": [],
                "rejected": [],
                "no_selection_reason": "The fixture has no figure.",
            },
            {"run_id": "run", "reading_mode": "skim"},
            "completed",
        )
        invalid = (
            markdown.replace("paper_type: null", 'paper_type: "essay"')
            .replace('source_coverage: "full-paper"', 'source_coverage: "unknown"')
            .replace('locator_mode: "page-grounded"', 'locator_mode: "page-ish"')
            .replace('template_version: "1.0"', 'template_version: "draft"')
        )

        issue_types = {
            item["issue_type"] for item in MODULE.validate_note_frontmatter(invalid)
        }

        self.assertEqual(
            issue_types,
            {
                "paper_type_enum",
                "source_coverage_enum",
                "locator_mode_enum",
                "template_version_contract",
            },
        )

    def test_skim_visual_does_not_repeat_caption_already_kept_in_crop(self):
        caption = "Figure 1. Complete original caption."
        markdown = MODULE.render_markdown(
            minimal_source(),
            minimal_evidence(),
            minimal_claims(),
            {
                "schema_version": "0.1",
                "selection_status": "completed",
                "selected": [
                    {
                        "figure_label": "Figure 1",
                        "physical_pdf_page": 1,
                        "embed_path": "figures/figure-1.png",
                        "selection_reason": "核心方法图",
                        "caption_original": caption,
                        "discussion_location": "3.2 方法与研究设计",
                    }
                ],
                "rejected": [],
                "no_selection_reason": None,
            },
            {"run_id": "run", "reading_mode": "skim"},
            "completed",
        )

        self.assertIn("Figure 1（3.2 方法与研究设计；〔p.1〕）", markdown)
        self.assertNotIn("![[", markdown)
        self.assertNotIn("图题：", markdown)
        self.assertNotIn(caption, markdown)

    def test_skim_records_source_mode_and_labels_analysis(self):
        summary = minimal_claims()[0]
        summary.update(
            {
                "claim_id": "C-SUMMARY",
                "claim_type": "summary",
                "claim_text_zh": "论文提出并检验一个受限结论。",
            }
        )
        boundary = minimal_claims()[0]
        boundary.update(
            {
                "claim_id": "C-BOUNDARY",
                "claim_type": "conclusion_boundary",
                "claim_text_zh": "该结果不能外推到未测试条件。",
                "provenance_class": "analysis",
            }
        )
        markdown = MODULE.render_markdown(
            minimal_source(),
            minimal_evidence(),
            [summary, boundary],
            {
                "schema_version": "0.1",
                "selection_status": "completed",
                "selected": [],
                "rejected": [],
                "no_selection_reason": "The fixture has no figure.",
            },
            {"run_id": "run", "reading_mode": "skim"},
            "completed",
        )
        self.assertIn("## 1. 论文速览", markdown)
        self.assertNotIn("## 2.", markdown)
        self.assertIn("[分析] 该结果不能外推", markdown)
        self.assertIn('source_coverage: "full-paper"', markdown)
        self.assertIn('locator_mode: "page-grounded"', markdown)

    def test_renderer_does_not_duplicate_existing_provenance_marker(self):
        summary = minimal_claims()[0]
        summary.update(
            {
                "claim_id": "C-SUMMARY",
                "claim_type": "summary",
                "claim_text_zh": "论文提出并检验一个受限结论。",
            }
        )
        boundary = minimal_claims()[0]
        boundary.update(
            {
                "claim_id": "C-BOUNDARY",
                "claim_type": "conclusion_boundary",
                "claim_text_zh": "[分析] 该结果不能外推到未测试条件。",
                "provenance_class": "analysis",
            }
        )

        markdown = MODULE.render_markdown(
            minimal_source(),
            minimal_evidence(),
            [summary, boundary],
            {
                "schema_version": "0.1",
                "selection_status": "completed",
                "selected": [],
                "rejected": [],
                "no_selection_reason": "The fixture has no figure.",
            },
            {"run_id": "run", "reading_mode": "skim"},
            "completed",
        )

        self.assertIn("[分析] 该结果不能外推", markdown)
        self.assertNotIn("[分析] [分析]", markdown)

    def test_cross_section_consistency_rejects_placeholder_for_known_metric(self):
        claims = minimal_claims()
        claims[0]["claim_type"] = "metric"
        markdown = (
            "## 1. 论文速览\n\n| 评价指标 | RMSE |\n\n"
            "### 3.4 核心公式、评价指标与关键参数\n\n**原文未说明**\n\n"
            "### 3.5 实验、比较与复现要点\n\n内容\n"
        )

        findings = MODULE.validate_cross_section_consistency(
            markdown,
            claims,
            paper_type="empirical-research",
        )

        self.assertEqual(findings[0]["issue_type"], "cross_section_consistency")
        self.assertIn("3.4", findings[0]["message"])

    def test_numeric_rendering_integrity_rejects_duplicate_suffixes(self):
        findings = MODULE.validate_numeric_rendering_integrity(
            "4.49%%；0.05°C°C；100 yearsyears；2.5 GhzGhz"
        )

        self.assertEqual(findings[0]["issue_type"], "numeric_rendering_integrity")

    def test_numeric_rendering_integrity_accepts_legitimate_mm_unit(self):
        findings = MODULE.validate_numeric_rendering_integrity(
            "The precipitation is 0.6 mm d−1 and the distance is 15 km."
        )

        self.assertEqual(findings, [])

    def test_range_symbol_integrity_requires_original_page_verification(self):
        evidence = [
            {
                **minimal_evidence()[0],
                "quote_original": (
                    "The interval spans 12±18 years under the selected forcing."
                ),
            }
        ]

        findings = MODULE.validate_range_symbol_integrity(evidence)

        self.assertEqual(findings[0]["issue_type"], "range_symbol_integrity")
        evidence[0]["symbol_verification"] = {
            "status": "corrected_from_original_page",
            "method": "pymupdf_page_render",
            "corrections": [
                {
                    "extracted": "12±18",
                    "verified": "12–18",
                }
            ],
        }
        self.assertEqual(MODULE.validate_range_symbol_integrity(evidence), [])

    def test_range_symbol_integrity_accepts_plausible_uncertainty(self):
        evidence = [
            {
                **minimal_evidence()[0],
                "quote_original": "The measured value was 12 ± 2 kg (mean ± s.d.).",
            }
        ]

        self.assertEqual(MODULE.validate_range_symbol_integrity(evidence), [])

    def test_range_symbol_integrity_accepts_unchanged_symbol_verified_on_page(self):
        evidence = [
            {
                **minimal_evidence()[0],
                "quote_original": "The mean error was 0.52 ± 0.95 °C.",
                "symbol_verification": {
                    "status": "verified_on_original_page",
                    "method": "pymupdf_page_render",
                    "corrections": [
                        {
                            "extracted": "0.52 ± 0.95",
                            "verified": "0.52 ± 0.95",
                        }
                    ],
                },
            }
        ]

        self.assertEqual(MODULE.validate_range_symbol_integrity(evidence), [])

    def test_trace_token_normalizes_spaces_around_range_dash(self):
        self.assertTrue(MODULE.trace_token_present("30−60", "30 − 60 m³"))

    def test_range_symbol_integrity_requires_verification_for_word_pairs(self):
        evidence = [
            {
                **minimal_evidence()[0],
                "quote_original": (
                    "The model uses a latitude±longitude grid and compares "
                    "land±ocean configurations."
                ),
            }
        ]

        findings = MODULE.validate_range_symbol_integrity(evidence)

        self.assertEqual(findings[0]["issue_type"], "range_symbol_integrity")
        evidence[0]["symbol_verification"] = {
            "status": "corrected_from_original_page",
            "method": "pymupdf_page_render",
            "corrections": [
                {
                    "extracted": "latitude±longitude",
                    "verified": "latitude–longitude",
                },
                {
                    "extracted": "land±ocean",
                    "verified": "land–ocean",
                },
            ],
        }
        self.assertEqual(MODULE.validate_range_symbol_integrity(evidence), [])

    def test_range_symbol_integrity_does_not_flag_short_math_variables(self):
        evidence = [
            {
                **minimal_evidence()[0],
                "quote_original": "The interval is expressed as x ± y.",
            }
        ]

        self.assertEqual(MODULE.validate_range_symbol_integrity(evidence), [])

    def test_generic_heading_detection_rejects_empty_labels(self):
        claim = minimal_claims()[0]
        claim["claim_type"] = "result"
        claim["title_zh"] = "核心结果 1"

        findings = MODULE.validate_generic_claim_headings([claim])

        self.assertEqual(findings[0]["issue_type"], "generic_heading_detection")
        claim["title_zh"] = "低温强迫触发状态跃迁"
        self.assertEqual(MODULE.validate_generic_claim_headings([claim]), [])

    def test_metadata_consistency_separates_machine_type_and_missing_metadata(self):
        source = minimal_source()
        source["metadata"]["journal"] = None

        findings = MODULE.validate_metadata_consistency(
            source,
            "method-algorithm",
        )

        self.assertEqual(findings[0]["issue_type"], "metadata_consistency")
        self.assertEqual(findings[0]["severity"], "info")
        missing_type = MODULE.validate_metadata_consistency(source, None)
        self.assertEqual(missing_type[0]["severity"], "blocker")

    def test_frontmatter_uses_machine_paper_type_and_separate_chinese_label(self):
        source = minimal_source()
        source["metadata"]["paper_type"] = "empirical-research"
        source["metadata"]["primary_paper_type"] = "empirical-research"
        source["metadata"]["secondary_paper_types"] = ["benchmark", "method"]
        source["metadata"]["paper_type_label_zh"] = "实证研究论文"
        source["metadata"]["metadata_warnings"] = ["journal 未由 Zotero 提供"]

        markdown = MODULE.render_markdown(
            source,
            minimal_evidence(),
            minimal_claims(),
            {
                "schema_version": "0.1",
                "selection_status": "completed",
                "selected": [],
                "rejected": [],
                "no_selection_reason": "The fixture has no figure.",
            },
            {"run_id": "run", "reading_mode": "skim"},
            "completed",
        )

        self.assertIn('paper_type: "empirical-research"', markdown)
        self.assertNotIn("primary_paper_type:", markdown)
        self.assertNotIn("secondary_paper_types:", markdown)
        self.assertNotIn("paper_type_label_zh:", markdown)
        self.assertNotIn("metadata_warning:", markdown)
        self.assertIn("实证研究论文；次级类型：基准评测、方法", markdown)

    def test_parameter_claim_renders_as_parameter_not_metric(self):
        source = minimal_source()
        source["metadata"]["paper_type"] = "method-algorithm"
        source["metadata"]["primary_paper_type"] = "method-algorithm"
        source["metadata"]["secondary_paper_types"] = []
        claims = minimal_claims()
        claims[0]["claim_type"] = "parameter"
        claims[0]["title_zh"] = "条件参数 μ"
        claims[0]["claim_text_zh"] = "μ 控制条件信息的注入强度。"

        markdown = MODULE.render_markdown(
            source,
            minimal_evidence(),
            claims,
            {
                "schema_version": "0.1",
                "selection_status": "completed",
                "selected": [],
                "rejected": [],
                "no_selection_reason": "The fixture has no figure.",
            },
            {"run_id": "run", "reading_mode": "deep"},
            "completed",
        )

        self.assertIn("### 3.4 核心公式、评价指标与关键参数", markdown)
        self.assertIn("#### 条件参数 μ", markdown)
        self.assertIn("- **类型**：关键参数", markdown)
        self.assertNotIn("#### Metric 1", markdown)

    def test_duplicate_section_content_rejects_verbatim_reuse(self):
        sentence = (
            "该方法先构建统一模型，再通过独立实验评估核心结果并说明适用条件。"
        )
        markdown = (
            f"## 1. 论文速览\n\n{sentence}\n\n"
            f"### 3.2 方法与研究设计\n\n{sentence}\n"
        )

        findings = MODULE.validate_duplicated_section_content(markdown)

        self.assertEqual(findings[0]["issue_type"], "duplicated_section_content")

    def test_duplicate_section_content_ignores_repeated_source_markers(self):
        markdown = (
            "## 2. 背景\n\n背景内容。〔[p.1](zotero://page=1)、[p.2](zotero://page=2)〕\n\n"
            "## 3. 方法\n\n方法内容。〔[p.3](zotero://page=3)、[p.4](zotero://page=4)〕\n"
        )

        self.assertEqual(
            MODULE.validate_duplicated_section_content(markdown),
            [],
        )

    def test_experiment_table_renderer_avoids_mechanical_punctuation(self):
        claim = minimal_claims()[0]
        claim["claim_type"] = "experiment"
        claim["claim_text_zh"] = "先进行预训练。"
        claim["detail_points_zh"] = ["随后完成微调。", "最后报告测试结果；"]

        markdown = MODULE.render_markdown(
            minimal_source(),
            minimal_evidence(),
            [claim],
            {
                "schema_version": "0.1",
                "selection_status": "completed",
                "selected": [],
                "rejected": [],
                "no_selection_reason": "The fixture has no figure.",
            },
            {"run_id": "run", "reading_mode": "deep"},
            "completed",
        )

        self.assertNotIn("。；", markdown)
        self.assertFalse(MODULE.validate_table_sentence_rendering_integrity(markdown))

    def test_supporting_reproducibility_record_does_not_leak_internal_placeholder(self):
        claim = minimal_claims()[0]
        claim["claim_type"] = "experiment"
        claim["importance"] = "supporting"
        claim["title_zh"] = "开放代码支持实验复现"
        claim["claim_text_zh"] = "作者公开了代码与运行说明。"
        claim["detail_points_zh"] = ["仓库提供了主要实验入口。"]
        claim["conditions_zh"] = "具体依赖版本仍以原仓库为准。"
        claim.pop("evidence_chain", None)

        markdown = MODULE.render_markdown(
            minimal_source(),
            minimal_evidence(),
            [claim],
            {
                "schema_version": "0.1",
                "selection_status": "completed",
                "selected": [],
                "rejected": [],
                "no_selection_reason": "The fixture has no figure.",
            },
            {"run_id": "run", "reading_mode": "deep"},
            "completed",
        )

        self.assertIn("#### 开放代码支持实验复现", markdown)
        self.assertIn("作者公开了代码与运行说明", markdown)
        self.assertNotIn("正式 deep/internalize 输出必须补齐", markdown)

    def test_summary_completeness_requires_problem_method_and_result_evidence(self):
        evidence = [
            {**minimal_evidence()[0], "evidence_id": "E-Q", "evidence_type": "research_question"},
            {**minimal_evidence()[0], "evidence_id": "E-M", "evidence_type": "method_step"},
            {**minimal_evidence()[0], "evidence_id": "E-R", "evidence_type": "result"},
        ]
        summary = minimal_claims()[0]
        summary["claim_type"] = "summary"
        summary["claim_text_zh"] = (
            "论文围绕一个明确研究问题提出核心方法与关键设计，并通过主要实验结果"
            "说明该设计的价值、适用范围以及相对于基线的改进，从而形成问题、方法和"
            "结果相互衔接的一句话摘要。"
        )
        summary["evidence_ids"] = ["E-Q", "E-M", "E-R"]

        self.assertFalse(MODULE.evaluate_summary_completeness([summary], evidence))
        summary["evidence_ids"] = ["E-Q"]
        findings = MODULE.evaluate_summary_completeness([summary], evidence)
        self.assertEqual(findings[0]["issue_type"], "summary_completeness")

    def test_page_semantic_coverage_rejects_unreviewed_appendix(self):
        classification = {
            "pages": [
                {
                    "page_index": 1,
                    "classification": "main_content",
                    "semantic_review_required": True,
                    "semantic_reviewed": True,
                    "review_outcome": "evidence_captured",
                    "review_notes": None,
                    "exclusion_reason": None,
                },
                {
                    "page_index": 2,
                    "classification": "references_only",
                    "semantic_review_required": False,
                    "semantic_reviewed": True,
                    "review_outcome": "excluded_reference",
                    "review_notes": None,
                    "exclusion_reason": "Reference list only.",
                },
                {
                    "page_index": 3,
                    "classification": "appendix",
                    "semantic_review_required": True,
                    "semantic_reviewed": False,
                    "review_outcome": "pending",
                    "review_notes": None,
                    "exclusion_reason": None,
                },
            ]
        }

        findings = MODULE.validate_page_semantic_coverage(classification, 3)

        self.assertEqual(findings[0]["issue_type"], "page_semantic_coverage")

    def test_visual_result_coverage_requires_full_inventory_and_result_choice(self):
        figures = {
            "schema_version": "0.1",
            "selection_status": "completed",
            "inventory_complete": False,
            "candidate_count": 1,
            "candidates_evaluated": [
                {
                    "figure_label": "Figure 1",
                    "visual_role": "method",
                    "decision": "selected",
                    "reason": "Method overview.",
                }
            ],
            "selected": [{"figure_label": "Figure 1", "visual_role": "method"}],
            "rejected": [],
            "no_selection_reason": None,
        }

        findings = MODULE.evaluate_visual_result_coverage(
            figures,
            minimal_claims(),
        )

        self.assertEqual(findings[0]["issue_type"], "visual_result_coverage")

    def test_deep_minimal_ledger_is_blocked_instead_of_exported(self):
        with tempfile.TemporaryDirectory() as temporary:
            run_dir = Path(temporary) / "run"
            run_dir.mkdir()
            write_json(run_dir / "source-bundle.json", minimal_source())
            write_json(run_dir / "evidence.json", minimal_evidence())
            write_json(run_dir / "claims.json", minimal_claims())
            write_json(
                run_dir / "figures.json",
                {
                    "schema_version": "0.1",
                    "selection_status": "completed",
                    "selected": [],
                    "rejected": [],
                    "no_selection_reason": "The fixture has no figure.",
                },
            )
            write_json(
                run_dir / "run.json",
                {
                    "schema_version": "0.1",
                    "run_id": "run",
                    "paper_id": "deep-quality-test",
                    "skill_version": "0.4.1",
                    "reading_mode": "deep",
                    "created": "2026-01-01T00:00:00+00:00",
                    "status": "prepared",
                    "artifacts": {},
                },
            )

            with self.assertRaises(MODULE.PipelineError):
                MODULE.build_run(run_dir)

            validation = json.loads((run_dir / "validation.json").read_text(encoding="utf-8"))
            issue_types = {item["issue_type"] for item in validation["issues"]}
            self.assertIn("deep_required_section_missing", issue_types)
            self.assertIn("deep_content_recall_insufficient", issue_types)

    def test_deep_renderer_uses_final_template_headings(self):
        markdown = MODULE.render_markdown(
            minimal_source(),
            minimal_evidence(),
            minimal_claims(),
            {
                "schema_version": "0.1",
                "selection_status": "completed",
                "selected": [],
                "rejected": [],
                "no_selection_reason": "The fixture has no figure.",
            },
            {"run_id": "run", "reading_mode": "deep"},
            "completed",
        )
        required = (
            "## 1. 论文速览",
            "## 2. 背景、问题与贡献",
            "## 3. 数据、材料与方法",
            "## 4. 核心结果",
            "## 5. 重要图表",
            "## 6. 讨论、结论、边界与限制",
        )
        for heading in required:
            self.assertIn(heading, markdown)
        self.assertNotIn("## 7. 对研究与学习的价值", markdown)
        self.assertNotIn("## 8. 术语与滚雪球阅读", markdown)
        self.assertNotIn("## 1. 核心科学问题", markdown)

    def test_rich_deep_ledger_builds_final_template_preview(self):
        validation = {
            "traceable": True,
            "semantic_support": "pass",
            "numeric_fidelity": "pass",
            "modality_fidelity": "pass",
            "final_status": "pass",
        }
        claim_types = (
            "summary",
            "metric",
            "question",
            "background",
            "gap",
            "contribution",
            "data",
            "method",
            "model",
            "experiment",
            "result",
            "result",
            "interpretation",
            "limitation",
            "conclusion",
            "conclusion_boundary",
        )
        claims = []
        for index, claim_type in enumerate(claim_types, start=1):
            fixture_role = (
                "主要结果" if claim_type == "result" and index == 11
                else "补充结果" if claim_type == "result"
                else claim_type
            )
            claim_text = (
                "这是用于验证 Final 模板的结构化内容，"
                "说明论文问题、方法、关键设计、主要价值、实验结果及其边界之间的"
                "明确关系，并保留从研究问题到方法和结果的完整逻辑链及适用条件。"
                if claim_type == "summary"
                else (
                    "这是用于验证 Final 模板的结构化内容，"
                    f"说明 {fixture_role} 与论文问题、方法、证据、"
                    "结果及其边界之间的明确关系。"
                )
            )
            claim = {
                    "claim_id": f"C-{index:03d}",
                    "claim_text_zh": claim_text,
                    "claim_type": claim_type,
                    "title_zh": f"{fixture_role}的证据定位与作用",
                    "detail_points_zh": [
                        "补充解释这一要点为何重要、如何由研究设计得到，并说明它与相邻环节的关系。",
                        "保留适用范围、作者语气和证据边界，避免把局部发现扩写为普遍结论。",
                    ],
                    "section_id": claim_type,
                    "importance": "core",
                    "conditions_zh": "仅适用于测试夹具所声明的研究范围。",
                    "epistemic_status": "observed",
                    "evidence_ids": (
                        ["E-Q", "E-M", "E-R"]
                        if claim_type == "summary"
                        else ["E-001"]
                    ),
                    "page_refs": [1],
                    "numeric_items": [],
                    "display_level": "inline",
                    "validation": validation,
                }
            if claim_type == "experiment":
                claim["evidence_chain"] = {
                    "tested_claim_zh": "该设计是否改善目标结果。",
                    "comparison_conditions_zh": "在固定数据与评价条件下对照基线。",
                    "observed_result_zh": "实验观察到目标指标改善。",
                    "supported_conclusion_zh": "证据支持该设计在测试条件下有效。",
                    "unsupported_stronger_interpretation_zh": "不能据此推出对所有数据和任务都有效。",
                }
            if claim_type == "conclusion_boundary":
                claim["provenance_class"] = "analysis"
            claims.append(claim)

        with tempfile.TemporaryDirectory() as temporary:
            run_dir = Path(temporary) / "run"
            run_dir.mkdir()
            source = minimal_source()
            source["metadata"]["paper_type"] = ["method-algorithm"]
            evidence = [
                *minimal_evidence(),
                {
                    **minimal_evidence()[0],
                    "evidence_id": "E-Q",
                    "evidence_type": "research_question",
                },
                {
                    **minimal_evidence()[0],
                    "evidence_id": "E-M",
                    "evidence_type": "method_step",
                },
                {
                    **minimal_evidence()[0],
                    "evidence_id": "E-R",
                    "evidence_type": "result",
                },
            ]
            write_json(run_dir / "source-bundle.json", source)
            write_json(run_dir / "evidence.json", evidence)
            write_json(run_dir / "claims.json", claims)
            write_json(
                run_dir / "figures.json",
                {
                    "schema_version": "0.1",
                    "selection_status": "completed",
                    "inventory_complete": True,
                    "candidate_count": 0,
                    "candidates_evaluated": [],
                    "selected": [],
                    "rejected": [],
                    "no_selection_reason": "The fixture has no figure.",
                    "no_result_visual_reason": "The fixture has no visual source.",
                },
            )
            write_json(
                run_dir / "run.json",
                {
                    "schema_version": "0.1",
                    "run_id": "run",
                    "paper_id": "deep-quality-test",
                    "skill_version": "0.4.1",
                    "reading_mode": "deep",
                    "created": "2026-01-01T00:00:00+00:00",
                    "status": "prepared",
                    "artifacts": {},
                },
            )

            validation, *_ = MODULE.validate_run(run_dir)
            self.assertEqual(
                validation["statistics"]["blocker_count"],
                0,
                validation["issues"],
            )
            destination, result = MODULE.build_run(run_dir)
            markdown = destination.read_text(encoding="utf-8")
            self.assertEqual(result["status"], "completed")
            self.assertTrue(result["quality"]["format_valid"])
            self.assertEqual(result["quality"]["template_completeness"], 1.0)
            self.assertTrue(result["quality"]["content_recall_pass"])
            self.assertTrue(result["quality"]["section_depth_pass"])
            self.assertIn("## 4. 核心结果", markdown)
            self.assertNotIn("### R1.", markdown)
            self.assertNotIn("### R2.", markdown)
            self.assertIn("### 主要结果的证据定位与作用", markdown)
            self.assertIn("### 补充结果的证据定位与作用", markdown)
            self.assertNotRegex(markdown, r"\{\{[a-zA-Z0-9_ -]+\}\}")

    def test_claim_schema_supports_deep_reading_knowledge_types(self):
        schema = json.loads(
            (SKILL / "schemas" / "claim-record.schema.json").read_text(encoding="utf-8")
        )
        claim_types = set(schema["properties"]["claim_type"]["enum"])
        self.assertTrue(
            {
                "summary",
                "prior_work",
                "contribution",
                "data",
                "material",
                "preprocessing",
                "model",
                "equation",
                "metric",
                "parameter",
                "experiment",
                "discussion",
                "future_work",
                "learning_value",
                "term",
                "writing_expression",
                "reference",
                "conclusion_boundary",
                "research_idea",
            }.issubset(claim_types)
        )
        self.assertIn("title_zh", schema["properties"])
        self.assertIn("detail_points_zh", schema["properties"])
        self.assertIn("importance", schema["properties"])
        self.assertIn("conditions_zh", schema["properties"])
        self.assertIn("provenance_class", schema["properties"])
        self.assertIn("evidence_chain", schema["properties"])
        self.assertIn("research_idea", schema["properties"])

    def test_final_template_is_human_readable_and_runtime_is_slot_driven(self):
        template = (SKILL / "assets" / "Paper Template.md").read_text(
            encoding="utf-8"
        )
        runtime = (SKILL / "assets" / "Paper Template - Runtime.md").read_text(
            encoding="utf-8"
        )
        for heading in (
            "## 1. 论文速览",
            "### 2.3 贡献与创新",
            "### 3.4 核心公式、评价指标与关键参数",
            "### 3.5 实验、比较与复现要点",
            "## 4. 核心结果",
            "## 5. 重要图表",
            "### 6.3 结论边界：本文不能推出什么",
            "### 6.4 作者明确说明的局限性与不确定性",
            "### 7.2 125 提炼",
            "### 8.2 值得继续追踪的参考文献",
        ):
            self.assertIn(heading, template)
            self.assertIn(heading, runtime)
        self.assertNotIn("{{", template)
        self.assertIn("标题判断", template)
        self.assertIn("摘要四要素", template)
        self.assertIn("[分析] 精读建议", template)
        self.assertIn("证据不能支持的更强说法", template)
        self.assertIn("至少两个失败模式", template)
        self.assertIn("{{overview_rows}}", runtime)
        self.assertIn("{{results}}", runtime)
        self.assertNotIn("{{evidence_limits}}", runtime)
        self.assertIn("{{conclusion_boundaries}}", runtime)
        self.assertNotIn("{{evidence_quotes}}", runtime)
        self.assertNotIn("<!--", template)
        self.assertEqual(template.count("> [!abstract]"), 1)
        self.assertNotIn("<!-- litanchor:user:start -->", runtime)
        self.assertNotIn("<!-- litanchor:user:end -->", runtime)

        rendered = MODULE.render_markdown(
            minimal_source(),
            minimal_evidence(),
            minimal_claims(),
            {
                "schema_version": "0.1",
                "selection_status": "completed",
                "selected": [],
                "rejected": [],
                "no_selection_reason": "The fixture has no figure.",
            },
            {"run_id": "run", "reading_mode": "internalize"},
            "completed",
        )
        self.assertNotIn("<!--", rendered)
        self.assertNotIn("### 6.5", rendered)
        self.assertIn("| :--- | :--- |", rendered)


if __name__ == "__main__":
    unittest.main()
