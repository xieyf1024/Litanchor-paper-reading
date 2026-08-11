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
        page.insert_text((80, 34), "Synthetic Architecture")
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
            self.assertLess(
                manifest["clip_bbox"][1],
                manifest["related_figure_text_blocks"][0]["bbox"][1],
            )
            self.assertEqual(manifest["crop_validation_status"], "pass")
            self.assertGreaterEqual(manifest["crop_confidence"], 0.9)
            self.assertFalse(manifest["needs_human_review"])
            self.assertEqual(result["figure_label"], "Figure 1")

    def test_dynamic_margin_includes_title_above_embedded_image(self):
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
                dpi=200,
            )
            title = result["related_figure_text_blocks"][0]
            self.assertEqual(title["text"], "Synthetic Architecture")
            self.assertLess(result["clip_bbox"][1], title["bbox"][1])
            self.assertGreater(result["clip_bbox"][3], 225)

    def test_adjacent_previous_figure_is_excluded_by_caption_boundary(self):
        import pymupdf

        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            pdf = root / "adjacent.pdf"
            image = root / "figure-2.png"
            document = pymupdf.open()
            page = document.new_page(width=300, height=500)
            pixmap = pymupdf.Pixmap(pymupdf.csRGB, (0, 0, 100, 80), False)
            pixmap.clear_with(0x88CCFF)
            page.insert_image(pymupdf.Rect(70, 40, 230, 140), pixmap=pixmap)
            page.insert_text((45, 175), "Figure 1: Previous complete result figure and caption.")
            page.insert_image(pymupdf.Rect(70, 230, 230, 330), pixmap=pixmap)
            page.insert_text((45, 365), "Figure 2: Target complete result figure and caption.")
            document.save(pdf)
            document.close()

            result = MODULE.crop_figure(
                pdf,
                page_number=1,
                label="Figure 2",
                output_path=image,
                dpi=144,
            )

            self.assertEqual(len(result["candidate_image_rects"]), 1)
            self.assertGreater(result["clip_bbox"][1], 200)
            self.assertEqual(
                result["preceding_figure_caption"]["label"],
                "Figure 1",
            )

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

    def test_explicit_bbox_is_preserved_for_review_instead_of_full_page_fallback(self):
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
                bbox="70,40,230,230",
                dpi=144,
            )

            self.assertEqual(result["crop_method"], "explicit_bbox")
            self.assertEqual(result["clip_bbox"], [70.0, 40.0, 230.0, 230.0])
            self.assertEqual(result["crop_validation_status"], "needs_human_review")
            self.assertTrue(result["needs_human_review"])
            self.assertEqual(
                result["validation_attempts"][-1]["attempt"],
                "explicit_bbox_preserved",
            )

    def test_caption_detection_allows_short_axis_prefix_but_ignores_body_reference(self):
        import pymupdf

        document = pymupdf.open()
        page = document.new_page(width=300, height=400)
        page.insert_text((40, 60), "See Figure 8.")
        page.insert_text(
            (40, 220),
            "params (M) Figure 8. Scaling comparison across model sizes.",
        )
        matches = MODULE._caption_blocks(page, "Figure 8", pymupdf)
        document.close()

        self.assertEqual(len(matches), 1)
        self.assertIn("Scaling comparison", matches[0][1])

    def test_caption_detection_accepts_caption_without_punctuation(self):
        import pymupdf

        document = pymupdf.open()
        page = document.new_page(width=300, height=400)
        page.insert_text((40, 60), "Figure 4")
        page.insert_text(
            (40, 220),
            "Figure 4 Overlapping fossil-coral records across three intervals.",
        )
        matches = MODULE._caption_blocks(page, "Figure 4", pymupdf)
        document.close()

        self.assertEqual(len(matches), 1)
        self.assertIn("Overlapping fossil-coral", matches[0][1])

    def test_caption_detection_accepts_spaced_figure_word(self):
        import pymupdf

        document = pymupdf.open()
        page = document.new_page(width=300, height=400)
        page.insert_text(
            (40, 220),
            "F I G U R E 2 Migration trajectories and ocean currents.",
        )
        matches = MODULE._caption_blocks(page, "Figure 2", pymupdf)
        document.close()

        self.assertEqual(len(matches), 1)
        self.assertIn("Migration trajectories", matches[0][1])

    def test_split_caption_page_renders_verified_figure_plate(self):
        import pymupdf

        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            pdf = root / "split-caption.pdf"
            image = root / "figure-2.png"
            document = pymupdf.open()
            caption_page = document.new_page(width=300, height=400)
            caption_page.insert_text(
                (40, 80),
                "Figure 2: Workflow shown on the following figure plate.",
            )
            plate_page = document.new_page(width=300, height=400)
            pixmap = pymupdf.Pixmap(pymupdf.csRGB, (0, 0, 160, 180), False)
            pixmap.clear_with(0x88CCFF)
            plate_page.insert_image(pymupdf.Rect(50, 50, 250, 300), pixmap=pixmap)
            plate_page.insert_text((90, 330), "Verified workflow plate")
            document.save(pdf)
            document.close()

            result = MODULE.crop_figure(
                pdf,
                page_number=2,
                caption_page_number=1,
                label="Figure 2",
                output_path=image,
                dpi=144,
            )

            self.assertEqual(result["physical_pdf_page"], 2)
            self.assertEqual(result["caption_physical_pdf_page"], 1)
            self.assertEqual(result["crop_method"], "split_caption_page_body")
            self.assertIn("following figure plate", result["caption_original"])
            self.assertEqual(result["crop_validation_status"], "pass")
            self.assertFalse(result["needs_human_review"])
            self.assertTrue(image.is_file())

    def test_split_caption_can_span_pages_and_stops_at_next_figure(self):
        import pymupdf

        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            pdf = root / "continued-caption.pdf"
            image = root / "figure-3.png"
            document = pymupdf.open()
            first_caption = document.new_page(width=300, height=400)
            first_caption.insert_text(
                (40, 300),
                "Figure 3: Long result caption begins on this page.",
            )
            continued_caption = document.new_page(width=300, height=400)
            continued_caption.insert_text(
                (40, 60),
                "The caption continues with uncertainty and sample details.",
            )
            continued_caption.insert_text(
                (40, 120),
                "Figure 4: The next caption must not be included.",
            )
            plate_page = document.new_page(width=300, height=400)
            pixmap = pymupdf.Pixmap(pymupdf.csRGB, (0, 0, 160, 180), False)
            pixmap.clear_with(0x88CCFF)
            plate_page.insert_image(pymupdf.Rect(50, 50, 250, 320), pixmap=pixmap)
            document.save(pdf)
            document.close()

            result = MODULE.crop_figure(
                pdf,
                page_number=3,
                caption_page_number=1,
                caption_end_page_number=2,
                label="Figure 3",
                output_path=image,
                dpi=144,
            )

            self.assertEqual(result["caption_physical_pdf_pages"], [1, 2])
            self.assertIn("caption continues", result["caption_original"])
            self.assertNotIn("next caption", result["caption_original"])


if __name__ == "__main__":
    unittest.main()
