import json
import sys
import tempfile
import unittest
from pathlib import Path


SCRIPT_DIR = (
    Path(__file__).resolve().parents[1]
    / "skills"
    / "litanchor-paper-reading"
    / "scripts"
)
sys.path.insert(0, str(SCRIPT_DIR))

from autonomous_semantic import (  # noqa: E402
    SemanticContractError,
    materialize_semantic_ledgers,
    validate_authoritative_evidence,
    validate_section_synthesis,
    validate_visual_analysis,
)
from litanchor_local import _render_section_synthesis  # noqa: E402


def valid_evidence() -> dict:
    return {
        "evidence_id": "E-001",
        "origin": "auto_extracted",
        "evidence_type": "method_step",
        "page_index": 2,
        "printed_page": None,
        "section": "Method",
        "block_id": "P002-B001",
        "bounding_box": [50.0, 50.0, 500.0, 90.0],
        "quote_original": "The encoder maps the visible patches into a latent representation.",
        "context_before": "We first describe the architecture.",
        "context_after": "The decoder then reconstructs the missing patches.",
        "epistemic_status": "observed",
        "epistemic_markers": [],
        "contains_number": False,
        "contains_unit": False,
        "contains_variable": False,
        "confidence": 0.99,
        "extraction_confidence": 0.99,
        "needs_review": False,
        "page_verified": True,
        "source_match_kind": "exact",
        "alignment_kind": "exact",
        "mineru_used_as": "structure_hint",
        "authoritative_source": "pymupdf_page",
        "issues": [],
    }


class AutonomousSemanticTests(unittest.TestCase):
    def test_materialization_preserves_original_page_symbol_receipt(self):
        quote = "The interval spans 12±18 years under the selected forcing."
        with tempfile.TemporaryDirectory() as temporary:
            run_dir = Path(temporary)
            (run_dir / "pymupdf-pages.json").write_text(
                json.dumps(
                    [
                        {
                            "page_index": 1,
                            "printed_page": None,
                            "raw_text": quote,
                            "text_blocks": [
                                {
                                    "block_id": "P001-B001",
                                    "block_type": "text",
                                    "bbox": [10.0, 10.0, 500.0, 40.0],
                                    "text": quote,
                                }
                            ],
                        }
                    ]
                ),
                encoding="utf-8",
            )
            (run_dir / "semantic-generation.json").write_text(
                json.dumps({"status": "pending"}),
                encoding="utf-8",
            )
            draft = {
                "evidence": [
                    {
                        "evidence_id": "E-RANGE",
                        "evidence_type": "result",
                        "page_index": 1,
                        "section": "Results",
                        "quote_original": quote,
                        "epistemic_status": "observed",
                        "symbol_verification": {
                            "status": "corrected_from_original_page",
                            "method": "pymupdf_page_render",
                            "corrections": [
                                {"extracted": "12±18", "verified": "12–18"}
                            ],
                        },
                    }
                ],
                "claims": [
                    {
                        "claim_id": "C-RANGE",
                        "claim_text_zh": "原页核验后，该范围为十二至十八年。",
                        "claim_type": "result",
                        "section_target": "4",
                        "importance": "core",
                        "epistemic_status": "observed",
                        "evidence_ids": ["E-RANGE"],
                        "numeric_items": [],
                    }
                ],
            }
            draft_path = run_dir / "semantic-draft.json"
            draft_path.write_text(json.dumps(draft), encoding="utf-8")

            evidence, _claims = materialize_semantic_ledgers(
                run_dir,
                draft_path,
            )

        self.assertEqual(
            evidence[0]["symbol_verification"]["corrections"][0]["verified"],
            "12–18",
        )

    def test_visual_analysis_must_cover_every_selected_figure(self):
        claims = [{"claim_id": "C-001"}]
        figures = {
            "selected": [
                {
                    "figure_label": "Figure 1",
                    "discussion_location": "3.2 方法与研究设计",
                }
            ]
        }
        valid = {
            "inventory_complete": True,
            "analyses": [
                {
                    "figure_label": "Figure 1",
                    "crop_validation_status": "pass",
                    "origin": "auto_synthesized",
                    "caption_original": "Figure 1. Complete caption.",
                    "interpretation_zh": (
                        "该图完整展示输入、核心计算模块、信息流方向与输出之间的关系。"
                        "关键连接区分训练阶段与下游使用阶段。"
                        "作者借此说明各组件在整体方法中的作用，避免把不同阶段混为一谈。"
                    ),
                    "reading_cautions": "不能把训练阶段使用的全部组件都视为下游推理的必要组成。",
                    "supported_claim_ids": ["C-001"],
                }
            ],
        }

        validate_visual_analysis(valid, figures, claims)

        invalid = {**valid, "analyses": []}
        with self.assertRaises(SemanticContractError):
            validate_visual_analysis(invalid, figures, claims)

    def test_section_synthesis_renders_prose_and_verified_source_marker(self):
        synthesis = {
            "sections": [
                {
                    "section_target": "3.2",
                    "status": "present",
                    "paragraphs_zh": ["第一段综合方法逻辑。", "第二段解释步骤关系。"],
                    "claim_ids": ["C-001", "C-002"],
                }
            ]
        }
        claims = [
            {
                "claim_id": "C-001",
                "evidence_ids": ["E-001"],
                "page_refs": [2],
            },
            {
                "claim_id": "C-002",
                "evidence_ids": ["E-002"],
                "page_refs": [5],
            },
        ]
        source = {
            "source": {
                "acquisition_method": "zotero_local_api",
                "zotero_attachment_key": "ABCDEFGH",
            }
        }

        rendered = _render_section_synthesis(
            synthesis,
            "3.2",
            claims,
            source,
            {2, 5},
        )

        self.assertIn("第一段综合方法逻辑。", rendered)
        self.assertNotIn("E-001", rendered)
        self.assertNotIn("PDF", rendered)
        self.assertIn("[p.2]", rendered)
        self.assertIn("?page=2", rendered)
        self.assertIn("?page=5", rendered)

    def test_rejects_fuzzy_mineru_text_as_final_evidence(self):
        evidence = valid_evidence()
        evidence["alignment_kind"] = "fuzzy"
        evidence["authoritative_source"] = "mineru_markdown"
        pages = [
            {
                "page_index": 2,
                "raw_text": evidence["quote_original"],
            }
        ]
        with self.assertRaises(SemanticContractError):
            validate_authoritative_evidence([evidence], pages)

    def test_accepts_pymupdf_verified_complete_quote(self):
        evidence = valid_evidence()
        pages = [
            {
                "page_index": 2,
                "raw_text": evidence["quote_original"],
            }
        ]
        validate_authoritative_evidence([evidence], pages)

    def test_accepts_verified_text_block_when_multicolumn_raw_text_is_interleaved(self):
        evidence = valid_evidence()
        pages = [
            {
                "page_index": 2,
                "raw_text": "Left column fragment. Right column fragment.",
                "text_blocks": [
                    {
                        "block_id": "P002-B001",
                        "block_type": "text",
                        "bbox": [50.0, 50.0, 500.0, 90.0],
                        "text": evidence["quote_original"],
                    }
                ],
            }
        ]
        validate_authoritative_evidence([evidence], pages)

    def test_deep_section_rejects_one_claim_one_line_synthesis(self):
        synthesis = {
            "schema_version": "0.1",
            "paper_type": "method-algorithm",
            "origin": "auto_synthesized",
            "sections": [
                {
                    "section_target": "3.3",
                    "heading_zh": "方法与模型",
                    "status": "present",
                    "depth_requirement": "deep",
                    "claim_ids": ["C-001"],
                    "evidence_ids": ["E-001"],
                    "coverage_groups": ["method"],
                    "paragraphs_zh": ["该方法使用一个编码器。"],
                    "clause_support": [
                        {
                            "clause_text_zh": "该方法使用一个编码器。",
                            "evidence_ids": ["E-001"],
                        }
                    ],
                }
            ],
        }
        claims = [
            {
                "claim_id": "C-001",
                "evidence_ids": ["E-001"],
                "section_target": "3.3",
            }
        ]
        with self.assertRaises(SemanticContractError):
            validate_section_synthesis(synthesis, claims, [])

    def test_deep_section_accepts_multi_claim_cohesive_synthesis(self):
        long_paragraph = (
            "该方法先随机遮蔽大部分输入块，只把可见块送入非对称编码器，以减少预训练计算。"
            "轻量解码器随后接收编码表示与掩码标记，在像素空间重建缺失块；这种设计把表征学习"
            "与重建开销分离，并明确限定了训练目标、输入范围和各模块在预训练阶段的职责。"
            "因此，方法描述同时覆盖了信息流、优化目标、效率动机和适用阶段。"
        )
        clauses = [
            clause
            for clause in (
                "该方法先随机遮蔽大部分输入块，只把可见块送入非对称编码器，以减少预训练计算。",
                "轻量解码器随后接收编码表示与掩码标记，在像素空间重建缺失块；",
                "这种设计把表征学习与重建开销分离，并明确限定了训练目标、输入范围和各模块在预训练阶段的职责。",
                "因此，方法描述同时覆盖了信息流、优化目标、效率动机和适用阶段。",
            )
        ]
        synthesis = {
            "schema_version": "0.1",
            "paper_type": "method-algorithm",
            "origin": "auto_synthesized",
            "sections": [
                {
                    "section_target": "3.3",
                    "heading_zh": "方法与模型",
                    "status": "present",
                    "depth_requirement": "deep",
                    "claim_ids": ["C-001", "C-002"],
                    "evidence_ids": ["E-001", "E-002"],
                    "coverage_groups": ["method", "model"],
                    "paragraphs_zh": [long_paragraph],
                    "clause_support": [
                        {
                            "clause_text_zh": clause,
                            "evidence_ids": ["E-001", "E-002"],
                        }
                        for clause in clauses
                    ],
                }
            ],
        }
        claims = [
            {
                "claim_id": "C-001",
                "evidence_ids": ["E-001"],
                "section_target": "3.3",
            },
            {
                "claim_id": "C-002",
                "evidence_ids": ["E-002"],
                "section_target": "3.3",
            },
        ]
        validate_section_synthesis(synthesis, claims, [])

    def test_section_synthesis_rejects_uncovered_factual_clause(self):
        synthesis = {
            "schema_version": "0.1",
            "paper_type": "method-algorithm",
            "origin": "auto_synthesized",
            "sections": [
                {
                    "section_target": "3.1",
                    "heading_zh": "数据",
                    "status": "present",
                    "depth_requirement": "supporting",
                    "claim_ids": ["C-001"],
                    "evidence_ids": ["E-001"],
                    "coverage_groups": ["data"],
                    "paragraphs_zh": [
                        "论文使用公开数据集。该数据集还包含一个未获证据支持的事实。"
                    ],
                    "clause_support": [
                        {
                            "clause_text_zh": "论文使用公开数据集。",
                            "evidence_ids": ["E-001"],
                        }
                    ],
                }
            ],
        }
        claims = [
            {
                "claim_id": "C-001",
                "evidence_ids": ["E-001"],
                "section_target": "1",
            }
        ]

        with self.assertRaises(SemanticContractError):
            validate_section_synthesis(synthesis, claims, [])


if __name__ == "__main__":
    unittest.main()
