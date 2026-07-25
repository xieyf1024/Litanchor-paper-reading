import json
import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SKILL = ROOT / "skills" / "litanchor-paper-reading"


class RepositoryContractTests(unittest.TestCase):
    def test_required_repository_files_exist(self):
        for relative in (
            "README.md",
            "LICENSE",
            ".gitignore",
            "THIRD_PARTY.md",
            "NOTICE.md",
            "requirements.txt",
            "requirements-mineru.txt",
            "Paper Template.md",
            "科研文献入门.md",
            "docs/PRODUCT.md",
            "docs/PROJECT_SPEC_V0.2.md",
            "docs/WORKFLOW.md",
            "docs/DATA_SCHEMA.md",
            "docs/EVALUATION.md",
            "docs/INTEGRATIONS.md",
            "skills/litanchor-paper-reading/scripts/litanchor_local.py",
            "skills/litanchor-paper-reading/scripts/zotero_local.py",
            "skills/litanchor-paper-reading/scripts/export_obsidian.py",
            "skills/litanchor-paper-reading/scripts/pdf_figures.py",
            "skills/litanchor-paper-reading/scripts/mineru_adapter.py",
            "skills/litanchor-paper-reading/scripts/paper_quality_gate.py",
        ):
            self.assertTrue((ROOT / relative).is_file(), relative)

    def test_skill_frontmatter_is_minimal_and_triggerable(self):
        text = (SKILL / "SKILL.md").read_text(encoding="utf-8")
        self.assertNotIn("TODO", text)
        self.assertLessEqual(len(text.splitlines()), 100)
        match = re.match(r"^---\n(.*?)\n---\n", text, flags=re.DOTALL)
        self.assertIsNotNone(match)
        fields = {}
        for line in match.group(1).splitlines():
            key, value = line.split(":", 1)
            fields[key.strip()] = value.strip()
        self.assertEqual(set(fields), {"name", "description"})
        self.assertEqual(fields["name"], "litanchor-paper-reading")
        self.assertIn("Use when", fields["description"])
        self.assertLessEqual(len(fields["description"]), 1024)

    def test_skill_references_and_assets_exist(self):
        text = (SKILL / "SKILL.md").read_text(encoding="utf-8")
        paths = set(re.findall(r"`((?:references|assets)/[^`]+)`", text))
        self.assertGreaterEqual(len(paths), 7)
        for relative in paths:
            self.assertTrue((SKILL / relative).is_file(), relative)
        self.assertIn("scripts/litanchor_local.py", text)
        self.assertIn("scripts/zotero_local.py", text)
        self.assertIn("scripts/export_obsidian.py", text)
        self.assertIn("scripts/pdf_figures.py", text)
        self.assertIn("scripts/mineru_adapter.py", text)

    def test_runtime_dependency_stays_lightweight(self):
        requirements = (ROOT / "requirements.txt").read_text(encoding="utf-8").splitlines()
        requirements = [line for line in requirements if line.strip() and not line.lstrip().startswith("#")]
        self.assertEqual(
            requirements,
            ["pypdf>=6.0,<7.0", "PyMuPDF>=1.26,<2.0"],
        )

    def test_openai_metadata_mentions_skill(self):
        text = (SKILL / "agents" / "openai.yaml").read_text(encoding="utf-8")
        self.assertIn('display_name: "LitAnchor 文锚"', text)
        self.assertIn("$litanchor-paper-reading", text)
        match = re.search(r'short_description: "([^"]+)"', text)
        self.assertIsNotNone(match)
        self.assertGreaterEqual(len(match.group(1)), 25)
        self.assertLessEqual(len(match.group(1)), 64)

    def test_json_schemas_parse_and_use_expected_draft(self):
        schema_dir = SKILL / "schemas"
        schemas = sorted(schema_dir.glob("*.schema.json"))
        self.assertEqual(len(schemas), 7)
        for path in schemas:
            payload = json.loads(path.read_text(encoding="utf-8"))
            self.assertEqual(payload["$schema"], "https://json-schema.org/draft/2020-12/schema")
            self.assertEqual(payload["type"], "object")

    def test_claim_schema_requires_evidence_and_pages(self):
        path = SKILL / "schemas" / "claim-record.schema.json"
        payload = json.loads(path.read_text(encoding="utf-8"))
        self.assertEqual(payload["properties"]["evidence_ids"]["minItems"], 1)
        self.assertEqual(payload["properties"]["page_refs"]["minItems"], 1)
        evidence = json.loads(
            (SKILL / "schemas" / "evidence-unit.schema.json").read_text(encoding="utf-8")
        )
        self.assertIn("page_verified", evidence["required"])
        self.assertIn("source_match_kind", evidence["required"])

    def test_note_template_protects_user_content_and_limits_evidence(self):
        text = (SKILL / "assets" / "Paper Template - Final.md").read_text(encoding="utf-8")
        self.assertIn("<!-- litanchor:user:start -->", text)
        self.assertIn("<!-- litanchor:user:end -->", text)
        self.assertIn("以下属于学习启发，不是作者原文结论", text)
        self.assertIn("## 4. 核心结果与证据", text)
        self.assertIn("{{evidence_quotes}}", text)

    def test_project_license_and_notice_match_pymupdf_distribution_choice(self):
        license_text = (ROOT / "LICENSE").read_text(encoding="utf-8")
        notice_text = (ROOT / "NOTICE.md").read_text(encoding="utf-8")
        third_party = (ROOT / "THIRD_PARTY.md").read_text(encoding="utf-8")
        self.assertIn("GNU AFFERO GENERAL PUBLIC LICENSE", license_text)
        self.assertIn("PyMuPDF", notice_text)
        self.assertIn("AGPL-3.0-only", third_party)

    def test_private_and_copyrighted_artifacts_are_ignored(self):
        text = (ROOT / ".gitignore").read_text(encoding="utf-8")
        self.assertIn("Test-PDF/", text)
        self.assertIn("*.pdf", text)
        self.assertIn("runtime/", text)
        self.assertRegex(text, r"(?m)^\.env$")


if __name__ == "__main__":
    unittest.main()
