#!/usr/bin/env python3
"""Coordinate-aware PyMuPDF text order shared by all LitAnchor PDF paths."""

from __future__ import annotations

from typing import Any


def block_text(block: dict[str, Any]) -> str:
    lines: list[str] = []
    for line in block.get("lines", []):
        spans = line.get("spans", []) if isinstance(line, dict) else []
        value = "".join(
            str(span.get("text", ""))
            for span in spans
            if isinstance(span, dict)
        )
        if value.strip():
            lines.append(value.strip())
    return "\n".join(lines)


def _bbox(block: dict[str, Any]) -> tuple[float, float, float, float]:
    value = block.get("bbox")
    if not isinstance(value, (list, tuple)) or len(value) != 4:
        return (0.0, 0.0, 0.0, 0.0)
    return tuple(float(item) for item in value)


def _position_key(block: dict[str, Any]) -> tuple[float, float]:
    x0, y0, _x1, _y1 = _bbox(block)
    return (round(y0, 3), round(x0, 3))


def _column_band(
    blocks: list[dict[str, Any]],
    midpoint: float,
) -> tuple[list[dict[str, Any]], bool]:
    left = [block for block in blocks if (_bbox(block)[0] + _bbox(block)[2]) / 2 < midpoint]
    right = [block for block in blocks if (_bbox(block)[0] + _bbox(block)[2]) / 2 >= midpoint]
    if not left or not right:
        return sorted(blocks, key=_position_key), False
    return sorted(left, key=_position_key) + sorted(right, key=_position_key), True


def order_text_blocks(
    blocks: list[dict[str, Any]],
    page_width: float,
) -> tuple[list[dict[str, Any]], bool]:
    """Return text blocks in spanning-heading and left-then-right column order."""
    text_blocks = [
        block
        for block in blocks
        if isinstance(block, dict)
        and block.get("type") == 0
        and block_text(block).strip()
    ]
    if len(text_blocks) < 2 or page_width <= 0:
        return sorted(text_blocks, key=_position_key), False

    midpoint = page_width / 2
    spanning: list[dict[str, Any]] = []
    column_candidates: list[dict[str, Any]] = []
    for block in text_blocks:
        x0, _y0, x1, _y1 = _bbox(block)
        if x0 < midpoint < x1 or (x1 - x0) >= page_width * 0.6:
            spanning.append(block)
        else:
            column_candidates.append(block)

    has_left = any((_bbox(block)[0] + _bbox(block)[2]) / 2 < midpoint for block in column_candidates)
    has_right = any((_bbox(block)[0] + _bbox(block)[2]) / 2 >= midpoint for block in column_candidates)
    if not has_left or not has_right:
        return sorted(text_blocks, key=_position_key), False

    ordered: list[dict[str, Any]] = []
    remaining = list(column_candidates)
    cursor = float("-inf")
    used_columns = False
    for heading in sorted(spanning, key=_position_key):
        _x0, y0, _x1, y1 = _bbox(heading)
        band = [
            block
            for block in remaining
            if cursor <= (_bbox(block)[1] + _bbox(block)[3]) / 2 < y0
        ]
        if band:
            band_order, detected = _column_band(band, midpoint)
            ordered.extend(band_order)
            used_columns = used_columns or detected
            remaining = [block for block in remaining if block not in band]
        ordered.append(heading)
        cursor = max(cursor, y1)

    if remaining:
        band_order, detected = _column_band(remaining, midpoint)
        ordered.extend(band_order)
        used_columns = used_columns or detected
    return ordered, used_columns


def extract_page_text(page: Any) -> tuple[str, bool]:
    page_dict = page.get_text("dict", sort=False)
    blocks = page_dict.get("blocks", []) if isinstance(page_dict, dict) else []
    ordered, multicolumn = order_text_blocks(
        [block for block in blocks if isinstance(block, dict)],
        float(page.rect.width),
    )
    return "\n".join(block_text(block) for block in ordered).strip(), multicolumn
