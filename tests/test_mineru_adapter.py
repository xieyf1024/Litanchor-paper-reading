import importlib.util
import json
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "skills" / "litanchor-paper-reading" / "scripts" / "mineru_adapter.py"
SPEC = importlib.util.spec_from_file_location("mineru_adapter", SCRIPT)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(MODULE)


@unittest.skipUnless(importlib.util.find_spec("pypdf"), "pypdf is not installed")
class MinerUAdapterTests(unittest.TestCase):
    def make_pdf_and_bundle(self, root: Path, page_count: int = 2):
        from pypdf import PdfWriter

        pdf = root / "paper.pdf"
        writer = PdfWriter()
        for _ in range(page_count):
            writer.add_blank_page(width=612, height=792)
        with pdf.open("wb") as handle:
            writer.write(handle)
        pages = [
            {
                "page_index": page,
                "raw_text": (
                    "Introduction This paper presents a lightweight test method."
                    if page == 1
                    else "Results The method improves the reported result."
                ),
            }
            for page in range(1, page_count + 1)
        ]
        bundle = {
            "paper_id": "pdf-test",
            "pdf": {
                "path": str(pdf),
                "sha256": MODULE.sha256_file(pdf),
                "page_count": page_count,
            },
            "pages": pages,
        }
        bundle_path = root / "source-bundle.json"
        bundle_path.write_text(json.dumps(bundle), encoding="utf-8")
        return pdf, bundle_path

    def test_requires_explicit_external_upload_consent(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            pdf, bundle = self.make_pdf_and_bundle(root)
            with self.assertRaises(MODULE.MinerUAdapterError):
                MODULE.run_flash(
                    pdf,
                    bundle,
                    root / "mineru",
                    consent_external_upload=False,
                    client_factory=lambda: object(),
                )

    def test_blocks_files_over_flash_page_limit(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            pdf, bundle = self.make_pdf_and_bundle(root, page_count=21)
            with self.assertRaises(MODULE.MinerUAdapterError):
                MODULE.run_flash(
                    pdf,
                    bundle,
                    root / "mineru",
                    consent_external_upload=True,
                    client_factory=lambda: object(),
                )

    def test_selected_page_subset_preserves_original_page_mapping(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            pdf, bundle = self.make_pdf_and_bundle(root, page_count=22)
            selected = [9, 11, 12, 13, 14, 15]
            subset_pdf, subset_bundle = MODULE.create_flash_subset(
                pdf,
                bundle,
                selected,
                root / "subset",
            )
            payload = json.loads(subset_bundle.read_text(encoding="utf-8"))
            self.assertEqual(payload["pdf"]["page_count"], 6)
            self.assertEqual(
                [page["page_index"] for page in payload["pages"]],
                selected,
            )
            self.assertEqual(payload["pdf"]["original_physical_pages"], selected)
            self.assertEqual(payload["pdf"]["original_pdf_sha256"], MODULE.sha256_file(pdf))
            self.assertEqual(payload["pdf"]["sha256"], MODULE.sha256_file(subset_pdf))

    def test_writes_raw_markdown_alignment_and_privacy_receipt(self):
        class FakeClient:
            def flash_extract(self, source, **options):
                self.source = source
                self.options = options
                return SimpleNamespace(
                    task_id="task-123",
                    state="done",
                    filename="paper.pdf",
                    err_code="",
                    error=None,
                    markdown=(
                        "# Introduction\n\n"
                        "This paper presents a lightweight test method.\n\n"
                        "# Results\n\n"
                        "The method improves the reported result."
                    ),
                )

        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            pdf, bundle = self.make_pdf_and_bundle(root)
            output = root / "mineru"
            result = MODULE.run_flash(
                pdf,
                bundle,
                output,
                consent_external_upload=True,
                client_factory=FakeClient,
                language="en",
            )
            self.assertEqual(result["status"], "completed")
            self.assertTrue((output / "mineru_raw.md").is_file())
            alignment = json.loads((output / "alignment.json").read_text(encoding="utf-8"))
            self.assertTrue(alignment["blocks"])
            self.assertEqual({item["status"] for item in alignment["blocks"]}, {"exact"})
            self.assertEqual(
                {item["pdf_page"] for item in alignment["blocks"] if item["pdf_page"]},
                {1, 2},
            )
            privacy = json.loads(
                (output / "privacy_receipt.json").read_text(encoding="utf-8")
            )
            self.assertTrue(privacy["consent_external_upload"])
            self.assertFalse(privacy["token_used"])
            self.assertEqual(privacy["service"], "MinerU Flash")
            self.assertFalse((output / "evidence.json").exists())


if __name__ == "__main__":
    unittest.main()
