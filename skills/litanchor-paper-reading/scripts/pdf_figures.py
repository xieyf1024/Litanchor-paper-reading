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
    figure_word = r"f\s*i\s*g(?:\s*u\s*r\s*e)?"
    return re.compile(
        rf"^\s*{figure_word}\.?\s*{number}(?:\s*[:.]|\s+)",
        re.IGNORECASE,
    )


def _caption_blocks(page: Any, label: str, pymupdf: Any) -> list[tuple[Any, str]]:
    pattern = _caption_pattern(label)
    matches: list[tuple[Any, str]] = []
    for block in page.get_text("blocks"):
        text = " ".join(str(block[4]).split())
        direct_match = pattern.search(text)
        if direct_match is None:
            embedded_match = re.search(
                pattern.pattern.lstrip("^"),
                text,
                flags=pattern.flags,
            )
            suffix = text[embedded_match.end() :].strip() if embedded_match else ""
            prefix = text[: embedded_match.start()].strip() if embedded_match else ""
            if (
                embedded_match is None
                or len(prefix) > 24
                or len(suffix) < 20
            ):
                continue
        elif len(text[direct_match.end() :].strip()) < 20:
            continue
        if direct_match is not None or embedded_match is not None:
            matches.append((pymupdf.Rect(block[:4]), text))
    return matches


def _split_caption_text(
    document: Any,
    *,
    start_page_number: int,
    end_page_number: int,
    label: str,
    pymupdf: Any,
) -> tuple[Any, str]:
    """Collect an explicitly bounded caption that may continue across pages."""
    start_page = document[start_page_number - 1]
    matches = _caption_blocks(start_page, label, pymupdf)
    if len(matches) != 1:
        raise FigureCropError(
            f"{label!r} must resolve to exactly one caption on physical PDF page "
            f"{start_page_number}; matches found: {len(matches)}"
        )
    first_rect, first_text = matches[0]
    generic_caption = re.compile(
        r"^\s*f\s*i\s*g(?:\s*u\s*r\s*e)?\.?\s*\d+[A-Za-z]?"
        r"(?:\s*[:.]|\s+)",
        re.IGNORECASE,
    )
    caption_parts = [first_text]
    for page_number in range(start_page_number, end_page_number + 1):
        page = document[page_number - 1]
        blocks = sorted(page.get_text("blocks"), key=lambda block: (block[1], block[0]))
        started = page_number > start_page_number
        for block in blocks:
            rectangle = pymupdf.Rect(block[:4])
            text = " ".join(str(block[4]).split())
            if not text or text.casefold() == "article in press":
                continue
            if page_number == start_page_number and not started:
                if rectangle == first_rect:
                    started = True
                continue
            if not started:
                continue
            if generic_caption.search(text):
                return first_rect, " ".join(caption_parts)
            caption_parts.append(text)
    return first_rect, " ".join(caption_parts)


def _preceding_figure_caption(
    page: Any,
    target_caption_rect: Any,
    pymupdf: Any,
) -> dict[str, Any] | None:
    """Return the closest earlier figure caption as a vertical crop boundary."""
    generic_pattern = re.compile(
        r"f\s*i\s*g(?:\s*u\s*r\s*e)?\.?\s*(\d+[A-Za-z]?)"
        r"(?:\s*[:.]|\s+)",
        re.IGNORECASE,
    )
    candidates: list[dict[str, Any]] = []
    for block in page.get_text("blocks"):
        rectangle = pymupdf.Rect(block[:4])
        if rectangle.y1 > target_caption_rect.y0 + 1.0:
            continue
        text = " ".join(str(block[4]).split())
        match = generic_pattern.search(text)
        if match is None:
            continue
        prefix = text[: match.start()].strip()
        suffix = text[match.end() :].strip()
        if len(prefix) > 24 or len(suffix) < 20:
            continue
        candidates.append(
            {
                "label": f"Figure {match.group(1)}",
                "text": text,
                "bbox": [round(value, 3) for value in rectangle],
                "_rect": rectangle,
            }
        )
    if not candidates:
        return None
    candidates.sort(key=lambda item: (item["_rect"].y1, item["_rect"].x0))
    return candidates[-1]


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


def _horizontal_overlap(left: Any, right: Any) -> float:
    return max(0.0, min(left.x1, right.x1) - max(left.x0, right.x0))


def _related_figure_text_blocks(
    page: Any,
    image_rect: Any,
    caption_rect: Any,
    pymupdf: Any,
) -> list[dict[str, Any]]:
    """Find short figure titles immediately above the embedded artwork."""
    matches: list[dict[str, Any]] = []
    maximum_gap = max(36.0, page.rect.height * 0.08)
    for block in page.get_text("blocks"):
        rectangle = pymupdf.Rect(block[:4])
        text = " ".join(str(block[4]).split())
        if not text or rectangle.intersects(caption_rect):
            continue
        vertical_gap = image_rect.y0 - rectangle.y1
        overlap = _horizontal_overlap(rectangle, image_rect)
        minimum_width = max(1.0, min(rectangle.width, image_rect.width))
        if (
            -3.0 <= vertical_gap <= maximum_gap
            and overlap / minimum_width >= 0.25
            and len(text) <= 240
        ):
            matches.append(
                {
                    "bbox": [round(value, 3) for value in rectangle],
                    "text": text,
                    "_rect": rectangle,
                }
            )
    matches.sort(key=lambda item: (item["_rect"].y0, item["_rect"].x0))
    return matches


def _expand_rect(pymupdf: Any, rectangle: Any, page_rect: Any, margin: float) -> Any:
    return pymupdf.Rect(
        max(page_rect.x0, rectangle.x0 - margin),
        max(page_rect.y0, rectangle.y0 - margin),
        min(page_rect.x1, rectangle.x1 + margin),
        min(page_rect.y1, rectangle.y1 + margin),
    )


def _edge_ink_ratios(pixmap: Any, *, band: int = 4) -> dict[str, float]:
    """Estimate whether rendered content touches a crop boundary."""
    width = int(pixmap.width)
    height = int(pixmap.height)
    channels = int(pixmap.n)
    if width < 1 or height < 1 or channels < 3:
        return {"top": 1.0, "right": 1.0, "bottom": 1.0, "left": 1.0}
    band = max(1, min(band, width, height))
    samples = memoryview(pixmap.samples)

    def is_ink(x: int, y: int) -> bool:
        offset = (y * width + x) * channels
        return min(samples[offset], samples[offset + 1], samples[offset + 2]) < 235

    coordinates = {
        "top": ((x, y) for y in range(band) for x in range(width)),
        "right": ((x, y) for y in range(height) for x in range(width - band, width)),
        "bottom": ((x, y) for y in range(height - band, height) for x in range(width)),
        "left": ((x, y) for y in range(height) for x in range(band)),
    }
    ratios: dict[str, float] = {}
    for edge, points in coordinates.items():
        total = 0
        ink = 0
        for x, y in points:
            total += 1
            ink += is_ink(x, y)
        ratios[edge] = round(ink / total if total else 1.0, 6)
    return ratios


def _render_with_quality_gate(
    page: Any,
    clip: Any,
    *,
    pymupdf: Any,
    dpi: int,
    expansion_step: float,
    preserve_initial_on_failure: bool = False,
    expansion_bounds: Any | None = None,
) -> tuple[Any, Any, str, float, bool, list[dict[str, Any]]]:
    attempts: list[dict[str, Any]] = []
    current = pymupdf.Rect(clip)
    initial = pymupdf.Rect(clip)
    bounds = pymupdf.Rect(expansion_bounds or page.rect)
    threshold = 0.01
    for attempt_number in range(1, 4):
        pixmap = page.get_pixmap(dpi=dpi, clip=current, alpha=False)
        edge_ratios = _edge_ink_ratios(pixmap)
        touches = [edge for edge, ratio in edge_ratios.items() if ratio > threshold]
        attempts.append(
            {
                "attempt": attempt_number,
                "clip_bbox": [round(value, 3) for value in current],
                "edge_ink_ratios": edge_ratios,
                "touching_edges": touches,
            }
        )
        if not touches:
            return pixmap, current, "pass", 0.95, False, attempts
        if preserve_initial_on_failure:
            attempts.append(
                {
                    "attempt": "explicit_bbox_preserved",
                    "clip_bbox": [round(value, 3) for value in initial],
                    "reason": "Explicit user geometry is retained for visual review instead of expanding to a full page.",
                }
            )
            return pixmap, initial, "needs_human_review", 0.7, True, attempts
        expanded = _expand_rect(pymupdf, current, bounds, expansion_step)
        if expanded == current:
            break
        current = expanded

    bounded_region = page.get_pixmap(dpi=dpi, clip=bounds, alpha=False)
    bounded_edge_ratios = _edge_ink_ratios(bounded_region)
    bounded_touches = [
        edge for edge, ratio in bounded_edge_ratios.items() if ratio > threshold
    ]
    attempts.append(
        {
            "attempt": "bounded_region_fallback",
            "clip_bbox": [round(value, 3) for value in bounds],
            "edge_ink_ratios": bounded_edge_ratios,
            "touching_edges": bounded_touches,
        }
    )
    if not bounded_touches:
        return bounded_region, bounds, "pass", 0.9, False, attempts
    return bounded_region, bounds, "needs_human_review", 0.6, True, attempts


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


def _split_plate_content_rect(page: Any, pymupdf: Any) -> Any:
    """Return auditable page-body bounds for a separately captioned figure plate."""
    page_rect = pymupdf.Rect(page.rect)
    header_bottom = page_rect.y0
    text_rects: list[Any] = []
    for block in page.get_text("blocks"):
        rectangle = pymupdf.Rect(block[:4])
        text = " ".join(str(block[4]).split())
        if (
            text.casefold() == "article in press"
            and rectangle.y1 <= page_rect.y0 + page_rect.height * 0.12
        ):
            header_bottom = max(header_bottom, rectangle.y1 + 4.0)
            continue
        if text and not rectangle.is_empty and not rectangle.is_infinite:
            text_rects.append(rectangle)

    content_rects = [
        rectangle
        for rectangle in _image_rectangles(page)
        if rectangle.y1 > header_bottom and rectangle.get_area() >= 100
    ]
    for drawing in page.get_drawings():
        rectangle = pymupdf.Rect(drawing.get("rect"))
        if (
            not rectangle.is_empty
            and not rectangle.is_infinite
            and rectangle.y1 > header_bottom
            and rectangle.get_area() >= 1
        ):
            content_rects.append(rectangle)
    content_rects.extend(
        rectangle for rectangle in text_rects if rectangle.y1 > header_bottom
    )
    if not content_rects:
        raise FigureCropError(
            "No figure-plate content was found on the separate image page."
        )
    content = _union_rect(pymupdf, content_rects)
    body_bounds = pymupdf.Rect(
        page_rect.x0,
        header_bottom,
        page_rect.x1,
        page_rect.y1,
    )
    return _expand_rect(
        pymupdf,
        content,
        body_bounds,
        max(8.0, min(page_rect.width, page_rect.height) * 0.02),
    )


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
    caption_page_number: int | None = None,
    caption_end_page_number: int | None = None,
    label: str,
    output_path: Path,
    manifest_path: Path | None = None,
    bbox: str | None = None,
    margin: float = 8.0,
    dpi: int = 200,
    selection_reason: str | None = None,
    discussion_location: str | None = None,
    zotero_page_link: str | None = None,
) -> dict[str, Any]:
    """Crop one figure plate, using a same-page or explicitly separate caption."""
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
        caption_page_number = caption_page_number or page_number
        caption_end_page_number = caption_end_page_number or caption_page_number
        if caption_page_number < 1 or caption_page_number > document.page_count:
            raise FigureCropError(
                "Caption physical PDF page "
                f"{caption_page_number} is outside 1..{document.page_count}"
            )
        if (
            caption_end_page_number < caption_page_number
            or caption_end_page_number > document.page_count
        ):
            raise FigureCropError(
                "Caption end page must be within the document and not precede "
                "the caption start page."
            )
        page = document[page_number - 1]
        caption_page = document[caption_page_number - 1]
        if caption_page_number != page_number:
            caption_rect, caption_text = _split_caption_text(
                document,
                start_page_number=caption_page_number,
                end_page_number=caption_end_page_number,
                label=label,
                pymupdf=pymupdf,
            )
        else:
            caption_matches = _caption_blocks(caption_page, label, pymupdf)
            if len(caption_matches) != 1:
                raise FigureCropError(
                    f"{label!r} must resolve to exactly one caption on physical PDF page "
                    f"{caption_page_number}; matches found: {len(caption_matches)}"
                )
            caption_rect, caption_text = caption_matches[0]
        explicit_rect = _parse_bbox(bbox, pymupdf, page.rect)
        candidate_rects: list[Any] = []
        related_text_blocks: list[dict[str, Any]] = []
        preceding_caption: dict[str, Any] | None = None
        expansion_bounds = pymupdf.Rect(page.rect)
        dynamic_margin = max(margin, 12.0, min(page.rect.width, page.rect.height) * 0.025)
        plate_content_bbox: list[float] | None = None
        if explicit_rect is None and caption_page_number != page_number:
            clip = _split_plate_content_rect(page, pymupdf)
            plate_content_bbox = [round(value, 3) for value in clip]
            expansion_bounds = pymupdf.Rect(page.rect)
            crop_method = "split_caption_page_body"
        elif explicit_rect is None:
            preceding_caption = _preceding_figure_caption(
                page,
                caption_rect,
                pymupdf,
            )
            preceding_boundary = (
                preceding_caption["_rect"].y1 if preceding_caption is not None else page.rect.y0
            )
            expansion_bounds = pymupdf.Rect(
                page.rect.x0,
                min(caption_rect.y0, preceding_boundary + (2.0 if preceding_caption else 0.0)),
                page.rect.x1,
                min(page.rect.y1, caption_rect.y1 + dynamic_margin),
            )
            for rectangle in _image_rectangles(page):
                vertical_gap = caption_rect.y0 - rectangle.y1
                if (
                    rectangle.y0 < caption_rect.y0
                    and rectangle.y0 >= preceding_boundary - 3.0
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
            image_union = _union_rect(pymupdf, candidate_rects)
            related_text_blocks = _related_figure_text_blocks(
                page,
                image_union,
                caption_rect,
                pymupdf,
            )
            related_rects = [item["_rect"] for item in related_text_blocks]
            clip = _union_rect(
                pymupdf,
                [*candidate_rects, *related_rects, caption_rect],
            )
            clip = _expand_rect(pymupdf, clip, expansion_bounds, dynamic_margin)
            crop_method = "caption_plus_embedded_images"
        else:
            clip = explicit_rect
            crop_method = "explicit_bbox"

        (
            pixmap,
            clip,
            crop_validation_status,
            crop_confidence,
            needs_human_review,
            validation_attempts,
        ) = _render_with_quality_gate(
            page,
            clip,
            pymupdf=pymupdf,
            dpi=dpi,
            expansion_step=dynamic_margin,
            preserve_initial_on_failure=explicit_rect is not None,
            expansion_bounds=expansion_bounds,
        )
        pymupdf_version = getattr(pymupdf, "pymupdf_version", None) or getattr(
            pymupdf, "__version__", "unknown"
        )

    _atomic_pixmap_save(pixmap, output_path)
    manifest = {
        "schema_version": "0.1",
        "figure_label": label,
        "physical_pdf_page": page_number,
        "caption_physical_pdf_page": caption_page_number,
        "caption_physical_pdf_pages": list(
            range(caption_page_number, caption_end_page_number + 1)
        ),
        "caption_original": caption_text,
        "source_pdf": str(pdf_path),
        "source_pdf_sha256": sha256_file(pdf_path),
        "crop_method": crop_method,
        "clip_bbox": [round(value, 3) for value in clip],
        "candidate_image_rects": [
            [round(value, 3) for value in rectangle] for rectangle in candidate_rects
        ],
        "plate_content_bbox": plate_content_bbox,
        "related_figure_text_blocks": [
            {key: value for key, value in item.items() if key != "_rect"}
            for item in related_text_blocks
        ],
        "preceding_figure_caption": (
            {key: value for key, value in preceding_caption.items() if key != "_rect"}
            if preceding_caption is not None
            else None
        ),
        "dynamic_margin_points": round(dynamic_margin, 3),
        "crop_validation_status": crop_validation_status,
        "crop_confidence": crop_confidence,
        "needs_human_review": needs_human_review,
        "validation_attempts": validation_attempts,
        "selection_reason": selection_reason,
        "discussion_location": discussion_location,
        "zotero_page_link": zotero_page_link,
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
    parser.add_argument(
        "--caption-page",
        type=int,
        help="one-based caption page when the caption and figure plate are separate",
    )
    parser.add_argument(
        "--caption-end-page",
        type=int,
        help="last physical page when a separate caption continues across pages",
    )
    parser.add_argument("--label", required=True, help="for example: Figure 1")
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--manifest", type=Path)
    parser.add_argument("--bbox", help="optional explicit x0,y0,x1,y1 in PDF points")
    parser.add_argument("--margin", type=float, default=8.0)
    parser.add_argument("--dpi", type=int, default=200)
    parser.add_argument("--selection-reason")
    parser.add_argument("--discussion-location")
    parser.add_argument("--zotero-page-link")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        result = crop_figure(
            args.pdf,
            page_number=args.page,
            caption_page_number=args.caption_page,
            caption_end_page_number=args.caption_end_page,
            label=args.label,
            output_path=args.output,
            manifest_path=args.manifest,
            bbox=args.bbox,
            margin=args.margin,
            dpi=args.dpi,
            selection_reason=args.selection_reason,
            discussion_location=args.discussion_location,
            zotero_page_link=args.zotero_page_link,
        )
        print(json.dumps(result, ensure_ascii=True))
        return 0
    except FigureCropError as exc:
        print(json.dumps({"status": "blocked", "error": str(exc)}, ensure_ascii=False), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
