import importlib.util
import json
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "skills" / "litanchor-paper-reading" / "scripts" / "pdf_figures.py"
SPEC = importlib.util.spec_from_file_location("pdf_figures", SCRIPT)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(MODULE)


@unittest.skipUnless(importlib.util.find_spec("pymupdf"), "PyMuPDF is not installed")
class FigureCropTests(unittest.TestCase):
    def make_pdf(self, path: Path) -> None:
        import pymupdf

        document = pymupdf.open()
        page = document.new_page(width=300, height=400)
        pixmap = pymupdf.Pixmap(pymupdf.csRGB, (0, 0, 120, 120), False)
        pixmap.clear_with(0x88CCFF)
        page.insert_image(pymupdf.Rect(70, 40, 230, 200), pixmap=pixmap)
        page.insert_text((60, 225), "Figure 1: Synthetic architecture.")
        page.insert_text((60, 270), "Body text must not enter the crop.")
        document.save(path)
        document.close()

    def test_caption_assisted_crop_creates_auditable_png_and_manifest(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            pdf = root / "source.pdf"
            image = root / "figure-1.png"
            self.make_pdf(pdf)
            result = MODULE.crop_figure(
                pdf,
                page_number=1,
                label="Figure 1",
                output_path=image,
                dpi=144,
            )
            self.assertTrue(image.is_file())
            manifest = json.loads(image.with_suffix(".json").read_text(encoding="utf-8"))
            self.assertEqual(manifest["physical_pdf_page"], 1)
            self.assertEqual(manifest["crop_method"], "caption_plus_embedded_images")
            self.assertEqual(manifest["source_pdf_sha256"], MODULE.sha256_file(pdf))
            self.assertEqual(manifest["output_image_sha256"], MODULE.sha256_file(image))
            self.assertEqual(result["figure_label"], "Figure 1")

    def test_refuses_missing_caption_and_overwrite(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            pdf = root / "source.pdf"
            image = root / "figure-1.png"
            self.make_pdf(pdf)
            with self.assertRaises(MODULE.FigureCropError):
                MODULE.crop_figure(
                    pdf,
                    page_number=1,
                    label="Figure 2",
                    output_path=image,
                )
            MODULE.crop_figure(
                pdf,
                page_number=1,
                label="Figure 1",
                output_path=image,
            )
            with self.assertRaises(MODULE.FigureCropError):
                MODULE.crop_figure(
                    pdf,
                    page_number=1,
                    label="Figure 1",
                    output_path=image,
                )


if __name__ == "__main__":
    unittest.main()
