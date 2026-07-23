#!/usr/bin/env python3
"""Crop an auditable figure image from an original PDF with PyMuPDF."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import sys
from pathlib import Path
from typing import Any


class FigureCropError(RuntimeError):
    """Raised when a figure cannot be cropped without guessing."""


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _load_pymupdf() -> Any:
    try:
        import pymupdf
    except ImportError as exc:
        raise FigureCropError(
            "PyMuPDF is required for figure rendering. Install repository requirements first."
        ) from exc
    return pymupdf


def _caption_pattern(label: str) -> re.Pattern[str]:
    match = re.fullmatch(r"\s*(?:fig(?:ure)?\.?)\s*(\d+[A-Za-z]?)\s*", label, re.IGNORECASE)
    if match is None:
        raise FigureCropError("Figure label must look like 'Figure 1' or 'Fig. 2'")
    number = re.escape(match.group(1))
    return re.compile(rf"^\s*fig(?:ure)?\.?\s*{number}\s*[:.]", re.IGNORECASE)


def _caption_blocks(page: Any, label: str, pymupdf: Any) -> list[tuple[Any, str]]:
    pattern = _caption_pattern(label)
    matches: list[tuple[Any, str]] = []
    for block in page.get_text("blocks"):
        text = " ".join(str(block[4]).split())
        if pattern.search(text):
            matches.append((pymupdf.Rect(block[:4]), text))
    return matches


def _image_rectangles(page: Any) -> list[Any]:
    rectangles: list[Any] = []
    seen: set[tuple[float, float, float, float]] = set()
    for image in page.get_images(full=True):
        for rectangle in page.get_image_rects(image[0]):
            key = tuple(round(value, 3) for value in rectangle)
            if key not in seen:
                rectangles.append(rectangle)
                seen.add(key)
    return rectangles


def _union_rect(pymupdf: Any, rectangles: list[Any]) -> Any:
    if not rectangles:
        raise FigureCropError("No rectangles were supplied for the crop")
    result = pymupdf.Rect(rectangles[0])
    for rectangle in rectangles[1:]:
        result |= rectangle
    return result


def _parse_bbox(value: str | None, pymupdf: Any, page_rect: Any) -> Any | None:
    if value is None:
        return None
    try:
        coordinates = [float(part.strip()) for part in value.split(",")]
    except ValueError as exc:
        raise FigureCropError("--bbox must contain four comma-separated numbers") from exc
    if len(coordinates) != 4:
        raise FigureCropError("--bbox must contain x0,y0,x1,y1")
    rectangle = pymupdf.Rect(coordinates)
    if rectangle.is_empty or rectangle.is_infinite or not page_rect.contains(rectangle):
        raise FigureCropError("--bbox must be a non-empty rectangle inside the physical PDF page")
    return rectangle


def _atomic_pixmap_save(pixmap: Any, destination: Path) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    if destination.exists():
        raise FigureCropError(f"Refusing to overwrite existing figure image: {destination}")
    temporary = destination.with_name(f".{destination.name}.tmp-{os.getpid()}.png")
    try:
        pixmap.save(temporary)
        os.replace(temporary, destination)
    finally:
        if temporary.exists():
            temporary.unlink()


def _atomic_json_save(destination: Path, payload: dict[str, Any]) -> None:
    if destination.exists():
        raise FigureCropError(f"Refusing to overwrite existing figure manifest: {destination}")
    destination.parent.mkdir(parents=True, exist_ok=True)
    temporary = destination.with_name(f".{destination.name}.tmp-{os.getpid()}")
    try:
        temporary.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
            newline="\n",
        )
        os.replace(temporary, destination)
    finally:
        if temporary.exists():
            temporary.unlink()


def crop_figure(
    pdf_path: Path,
    *,
    page_number: int,
    label: str,
    output_path: Path,
    manifest_path: Path | None = None,
    bbox: str | None = None,
    margin: float = 8.0,
    dpi: int = 200,
) -> dict[str, Any]:
    """Crop one figure and its caption from the original physical PDF page."""
    pymupdf = _load_pymupdf()
    pdf_path = pdf_path.resolve()
    output_path = output_path.resolve()
    manifest_path = (manifest_path or output_path.with_suffix(".json")).resolve()
    if not pdf_path.is_file() or pdf_path.suffix.casefold() != ".pdf":
        raise FigureCropError(f"Input is not a readable PDF: {pdf_path}")
    if output_path.suffix.casefold() != ".png":
        raise FigureCropError("Figure output must use a .png filename")
    if output_path == manifest_path:
        raise FigureCropError("Figure image and manifest paths must differ")
    if margin < 0 or dpi < 72 or dpi > 600:
        raise FigureCropError("margin must be non-negative and dpi must be between 72 and 600")

    with pymupdf.open(pdf_path) as document:
        if page_number < 1 or page_number > document.page_count:
            raise FigureCropError(
                f"Physical PDF page {page_number} is outside 1..{document.page_count}"
            )
        page = document[page_number - 1]
        caption_matches = _caption_blocks(page, label, pymupdf)
        if len(caption_matches) != 1:
            raise FigureCropError(
                f"{label!r} must resolve to exactly one caption on physical PDF page "
                f"{page_number}; matches found: {len(caption_matches)}"
            )
        caption_rect, caption_text = caption_matches[0]
        explicit_rect = _parse_bbox(bbox, pymupdf, page.rect)
        candidate_rects: list[Any] = []
        if explicit_rect is None:
            for rectangle in _image_rectangles(page):
                vertical_gap = caption_rect.y0 - rectangle.y1
                if (
                    rectangle.y0 < caption_rect.y0
                    and vertical_gap >= -3
                    and vertical_gap <= page.rect.height * 0.5
                    and rectangle.get_area() >= 500
                ):
                    candidate_rects.append(rectangle)
            if not candidate_rects:
                raise FigureCropError(
                    "No embedded figure image was found immediately above the caption. "
                    "Inspect the rendered page and retry with an explicit --bbox."
                )
            clip = _union_rect(pymupdf, [*candidate_rects, caption_rect])
            clip = pymupdf.Rect(
                max(page.rect.x0, clip.x0 - margin),
                max(page.rect.y0, clip.y0 - margin),
                min(page.rect.x1, clip.x1 + margin),
                min(page.rect.y1, clip.y1 + margin),
            )
            crop_method = "caption_plus_embedded_images"
        else:
            clip = explicit_rect
            crop_method = "explicit_bbox"

        pixmap = page.get_pixmap(dpi=dpi, clip=clip, alpha=False)
        pymupdf_version = getattr(pymupdf, "pymupdf_version", None) or getattr(
            pymupdf, "__version__", "unknown"
        )

    _atomic_pixmap_save(pixmap, output_path)
    manifest = {
        "schema_version": "0.1",
        "figure_label": label,
        "physical_pdf_page": page_number,
        "caption_original": caption_text,
        "source_pdf": str(pdf_path),
        "source_pdf_sha256": sha256_file(pdf_path),
        "crop_method": crop_method,
        "clip_bbox": [round(value, 3) for value in clip],
        "candidate_image_rects": [
            [round(value, 3) for value in rectangle] for rectangle in candidate_rects
        ],
        "render_dpi": dpi,
        "renderer": f"PyMuPDF {pymupdf_version}",
        "output_image": str(output_path),
        "output_image_sha256": sha256_file(output_path),
    }
    _atomic_json_save(manifest_path, manifest)
    manifest["manifest"] = str(manifest_path)
    return manifest


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Crop a verified figure and caption from an original PDF"
    )
    parser.add_argument("pdf", type=Path)
    parser.add_argument("--page", type=int, required=True, help="one-based physical PDF page")
    parser.add_argument("--label", required=True, help="for example: Figure 1")
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--manifest", type=Path)
    parser.add_argument("--bbox", help="optional explicit x0,y0,x1,y1 in PDF points")
    parser.add_argument("--margin", type=float, default=8.0)
    parser.add_argument("--dpi", type=int, default=200)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        result = crop_figure(
            args.pdf,
            page_number=args.page,
            label=args.label,
            output_path=args.output,
            manifest_path=args.manifest,
            bbox=args.bbox,
            margin=args.margin,
            dpi=args.dpi,
        )
        print(json.dumps(result, ensure_ascii=False))
        return 0
    except FigureCropError as exc:
        print(json.dumps({"status": "blocked", "error": str(exc)}, ensure_ascii=False), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
