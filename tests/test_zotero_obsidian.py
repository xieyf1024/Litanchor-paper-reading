import json
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "skills" / "litanchor-paper-reading" / "scripts"
sys.path.insert(0, str(SCRIPTS))

import export_obsidian  # noqa: E402
import litanchor_local  # noqa: E402
import zotero_local  # noqa: E402


def write_json(path: Path, payload):
    path.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")


class FixtureClient(zotero_local.ZoteroLocalClient):
    def __init__(self, candidates=None, children=None, file_url=None):
        self.candidates = candidates or []
        self.children = children or []
        self.file_url = file_url

    def _search(self, query, *, everything=False):
        return self.candidates

    def _get_json(self, path, params=None):
        if path.endswith("/children"):
            return self.children
        raise AssertionError(path)

    def _get_text(self, path):
        if path.endswith("/file/view/url"):
            return self.file_url
        raise AssertionError(path)


def item(key="ABCD1234", title="Exact Paper", *, doi="10.1000/example", extra=""):
    return {
        "key": key,
        "data": {
            "itemType": "journalArticle",
            "title": title,
            "DOI": doi,
            "extra": extra,
            "creators": [{"creatorType": "author", "firstName": "Ada", "lastName": "Lovelace"}],
        },
    }


def attachment(key="PDFD1234"):
    return {
        "key": key,
        "data": {
            "itemType": "attachment",
            "contentType": "application/pdf",
            "filename": "paper.pdf",
        },
    }


class ZoteroLocalTests(unittest.TestCase):
    def test_base_url_must_be_loopback_api(self):
        with self.assertRaises(litanchor_local.PipelineError):
            zotero_local.ZoteroLocalClient("https://api.zotero.org")

    def test_title_resolution_requires_one_normalized_exact_match(self):
        client = FixtureClient(candidates=[item(title="Exact Paper"), item(key="EFGH5678", title="Similar Paper")])
        self.assertEqual(client.resolve_item("title", "Exact-Paper")["key"], "ABCD1234")

    def test_title_resolution_blocks_ambiguous_matches(self):
        client = FixtureClient(candidates=[item(), item(key="EFGH5678")])
        with self.assertRaises(litanchor_local.PipelineError):
            client.resolve_item("title", "Exact Paper")

    def test_title_resolution_retries_with_punctuation_free_prefix(self):
        class PrefixClient(FixtureClient):
            def _search(self, query, *, everything=False):
                if query.casefold() == "increased frequency of multi year el niño southern":
                    return [
                        item(
                            title="Increased frequency of multi-year el niño–southern oscillation events across the holocene"
                        )
                    ]
                return []

        client = PrefixClient()
        resolved = client.resolve_item(
            "title",
            "Increased frequency of multi-year El Niño-Southern Oscillation events across the Holocene",
        )
        self.assertEqual(resolved["key"], "ABCD1234")

    def test_citekey_can_be_read_from_better_bibtex_extra(self):
        client = FixtureClient(candidates=[item(extra="Citation Key: Lovelace2026Exact")])
        self.assertEqual(client.resolve_item("citekey", "lovelace2026exact")["key"], "ABCD1234")

    def test_one_pdf_child_and_local_file_url_are_required(self):
        with tempfile.TemporaryDirectory() as temporary:
            pdf = Path(temporary) / "paper.pdf"
            pdf.write_bytes(b"%PDF-test")
            client = FixtureClient(children=[attachment()], file_url=pdf.as_uri())
            resolved = client.resolve_pdf_attachment(item())
            self.assertEqual(resolved["key"], "PDFD1234")
            self.assertEqual(client.attachment_path(resolved), pdf.resolve())


class ObsidianExportTests(unittest.TestCase):
    def make_run(self, root: Path, *, warning=False, zotero=False) -> Path:
        run_dir = root / "run"
        run_dir.mkdir()
        source = {
            "schema_version": "0.1",
            "paper_id": "pdf-test",
            "source": {
                "acquisition_method": "zotero_local_api" if zotero else "manual_pdf",
                "query": "title:Test Paper" if zotero else "test.pdf",
                "zotero_item_key": "ABCD1234" if zotero else None,
                "zotero_attachment_key": "PDFD1234" if zotero else None,
                "external_knowledge_allowed": False,
            },
            "metadata": {
                "title": "Test Paper",
                "authors": ["A. Author"],
                "year": 2026,
                "journal": None,
                "doi": None,
                "citekey": "Author2026Test" if zotero else None,
            },
            "annotations": [],
            "pdf": {
                "path": "test.pdf",
                "sha256": "a" * 64,
                "page_count": 1,
                "preflight_status": "PASS_WITH_WARNINGS" if warning else "PASS",
                "warnings": ["review"] if warning else [],
            },
            "pages": [{
                "page_index": 1,
                "printed_page": None,
                "raw_text": "The model achieved 95% accuracy on the test set.",
                "extraction_method": "native_text",
                "confidence": 1.0,
                "warnings": ["review"] if warning else [],
            }],
        }
        evidence = [{
            "evidence_id": "E-001",
            "evidence_type": "result",
            "page_index": 1,
            "printed_page": None,
            "section": "Results",
            "block_id": None,
            "bounding_box": None,
            "quote_original": "The model achieved 95% accuracy on the test set.",
            "epistemic_status": "observed",
            "epistemic_markers": [],
            "contains_number": True,
            "contains_unit": True,
            "contains_variable": False,
            "confidence": 1.0,
            "needs_review": False,
            "issues": [],
        }]
        claims = [{
            "claim_id": "C-001",
            "claim_text_zh": "作者报告模型在测试集上的准确率为 95%。",
            "claim_type": "result",
            "epistemic_status": "observed",
            "evidence_ids": ["E-001"],
            "page_refs": [1],
            "numeric_items": [{"value_original": "95", "unit_original": "%", "variable": None, "condition": "test set"}],
            "display_level": "collapsed",
            "validation": {
                "traceable": True,
                "semantic_support": "pass",
                "numeric_fidelity": "pass",
                "modality_fidelity": "pass",
                "final_status": "pass",
            },
        }]
        run = {
            "schema_version": "0.1",
            "run_id": "run",
            "paper_id": "pdf-test",
            "skill_version": "0.3.0",
            "reading_mode": "skim",
            "created": "2026-01-01T00:00:00+00:00",
            "status": "prepared",
            "artifacts": {},
        }
        write_json(run_dir / "source-bundle.json", source)
        write_json(run_dir / "evidence.json", evidence)
        write_json(run_dir / "claims.json", claims)
        write_json(run_dir / "run.json", run)
        litanchor_local.build_run(run_dir)
        return run_dir

    def test_export_requires_confirmation_and_contained_inbox(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            run_dir = self.make_run(root)
            vault = root / "vault"
            inbox = vault / "00_Inbox"
            inbox.mkdir(parents=True)
            with self.assertRaises(litanchor_local.PipelineError):
                export_obsidian.export_run(run_dir, vault, inbox)
            outside = root / "outside"
            outside.mkdir()
            with self.assertRaises(litanchor_local.PipelineError):
                export_obsidian.export_run(run_dir, vault, outside, confirmed=True)

    def test_export_writes_note_and_sidecars_without_overwrite(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            run_dir = self.make_run(root, zotero=True)
            vault = root / "vault"
            inbox = vault / "00_Inbox"
            inbox.mkdir(parents=True)
            result = export_obsidian.export_run(run_dir, vault, inbox, confirmed=True)
            note = Path(result["note"])
            self.assertTrue(note.is_file())
            markdown = note.read_text(encoding="utf-8")
            self.assertIn("zotero_item_key: \"ABCD1234\"", markdown)
            self.assertIn("zotero://open-pdf/library/items/PDFD1234?page=1", markdown)
            self.assertEqual(len(result["sidecars"]), 4)
            with self.assertRaises(litanchor_local.PipelineError):
                export_obsidian.export_run(run_dir, vault, inbox, confirmed=True)

    def test_warning_and_post_validation_tamper_are_blocked(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            warning_run = self.make_run(root, warning=True)
            vault = root / "vault"
            inbox = vault / "00_Inbox"
            inbox.mkdir(parents=True)
            with self.assertRaises(litanchor_local.PipelineError):
                export_obsidian.export_run(warning_run, vault, inbox, confirmed=True)
            (warning_run / "preview.md").write_text("tampered", encoding="utf-8")
            with self.assertRaises(litanchor_local.PipelineError):
                export_obsidian.export_run(warning_run, vault, inbox, allow_warnings=True, confirmed=True)


if __name__ == "__main__":
    unittest.main()
