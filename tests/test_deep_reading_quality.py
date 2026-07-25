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

    def test_internalize_requires_learning_layer_but_deep_uses_mode_placeholder(self):
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
        self.assertIn(
            "**本模式未生成（仅 internalize 模式要求）**",
            markdown,
        )
        self.assertIn("**待用户补充**", markdown)

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
        self.assertIn('generation_mode: "human_assisted_regression"', markdown)
        self.assertIn("autonomous_generation: false", markdown)
        self.assertNotIn("**完整图题**", markdown)

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
                        "discussion_location": "PDF p.1",
                    }
                ],
                "rejected": [],
                "no_selection_reason": None,
            },
            {"run_id": "run", "reading_mode": "skim"},
            "completed",
        )

        self.assertIn("![[figures/figure-1.png]]", markdown)
        self.assertIn("选择理由：核心方法图", markdown)
        self.assertNotIn("图题：", markdown)
        self.assertNotIn(caption, markdown)

    def test_cross_section_consistency_rejects_placeholder_for_known_metric(self):
        claims = minimal_claims()
        claims[0]["claim_type"] = "metric"
        markdown = (
            "## 1. 论文速览\n\n| 评价指标 | RMSE |\n\n"
            "### 3.4 核心公式与评价指标\n\n**原文未说明**\n\n"
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
            "## 4. 核心结果与证据",
            "## 5. 重要图表",
            "## 6. 讨论、结论与限制",
            "## 7. 对研究与学习的价值",
            "## 8. 术语、原文证据与滚雪球阅读",
        )
        for heading in required:
            self.assertIn(heading, markdown)
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
        )
        claims = []
        for index, claim_type in enumerate(claim_types, start=1):
            claim_text = (
                "这是用于验证 Final 模板的结构化内容，"
                "说明论文问题、方法、关键设计、主要价值、实验结果及其边界之间的"
                "明确关系，并保留从研究问题到方法和结果的完整逻辑链及适用条件。"
                if claim_type == "summary"
                else (
                    "这是用于验证 Final 模板的结构化内容，"
                    "说明论文问题、方法、证据、结果及其边界之间的明确关系。"
                )
            )
            claims.append(
                {
                    "claim_id": f"C-{index:03d}",
                    "claim_text_zh": claim_text,
                    "claim_type": claim_type,
                    "title_zh": f"结构化要点 {index}",
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
            )

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
            self.assertIn("## 4. 核心结果与证据", markdown)
            self.assertIn("### R1.", markdown)
            self.assertIn("### R2.", markdown)
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
                "experiment",
                "discussion",
                "future_work",
                "learning_value",
                "term",
                "writing_expression",
                "reference",
            }.issubset(claim_types)
        )
        self.assertIn("title_zh", schema["properties"])
        self.assertIn("detail_points_zh", schema["properties"])
        self.assertIn("importance", schema["properties"])
        self.assertIn("conditions_zh", schema["properties"])

    def test_final_template_asset_is_canonical_and_slot_driven(self):
        template = (SKILL / "assets" / "Paper Template - Final.md").read_text(
            encoding="utf-8"
        )
        for heading in (
            "## 1. 论文速览",
            "### 2.3 贡献与创新",
            "### 3.5 实验、比较与复现要点",
            "## 4. 核心结果与证据",
            "## 5. 重要图表",
            "### 6.3 局限性与不确定性",
            "### 7.2 125 提炼",
            "### 8.3 值得继续追踪的参考文献",
        ):
            self.assertIn(heading, template)
        self.assertIn("{{overview_rows}}", template)
        self.assertIn("{{results}}", template)
        self.assertIn("<!-- litanchor:user:start -->", template)
        self.assertIn("<!-- litanchor:user:end -->", template)


if __name__ == "__main__":
    unittest.main()
