#!/usr/bin/env python3
"""Run the token-free MinerU Flash API as a non-authoritative structure aid."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import sys
import time
import unicodedata
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable
from unittest.mock import patch


MAX_FLASH_BYTES = 10 * 1024 * 1024
MAX_FLASH_PAGES = 20


class MinerUAdapterError(RuntimeError):
    """Raised when a Flash request would violate LitAnchor boundaries."""


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _write_text(path: Path, text: str) -> None:
    if path.exists():
        raise MinerUAdapterError(f"Refusing to overwrite MinerU artifact: {path}")
    path.write_text(text, encoding="utf-8", newline="\n")


def _write_json(path: Path, payload: Any) -> None:
    _write_text(path, json.dumps(payload, ensure_ascii=False, indent=2) + "\n")


def _normalize(text: str) -> str:
    text = unicodedata.normalize("NFKC", text).replace("\u00ad", "")
    text = re.sub(r"!\[[^\]]*\]\([^)]*\)", " ", text)
    text = re.sub(r"\[([^\]]+)\]\([^)]*\)", r"\1", text)
    text = re.sub(r"^[#>*+\-\d.\s]+", "", text, flags=re.MULTILINE)
    text = re.sub(r"(?<=\w)-\s+(?=\w)", "", text)
    return re.sub(r"\s+", " ", text).strip().casefold()


def _words(text: str) -> set[str]:
    return set(re.findall(r"[A-Za-z0-9\u4e00-\u9fff]{2,}", _normalize(text)))


def _markdown_blocks(markdown: str) -> list[str]:
    blocks: list[str] = []
    for value in re.split(r"\n\s*\n", markdown):
        cleaned = value.strip()
        normalized = _normalize(cleaned)
        if len(normalized) >= 30 and not cleaned.startswith("!["):
            blocks.append(cleaned)
    return blocks


def align_markdown(markdown: str, pages: list[dict[str, Any]]) -> dict[str, Any]:
    page_records = [
        (
            int(page["page_index"]),
            _normalize(str(page.get("raw_text", ""))),
            _words(str(page.get("raw_text", ""))),
        )
        for page in pages
        if isinstance(page, dict) and isinstance(page.get("page_index"), int)
    ]
    aligned: list[dict[str, Any]] = []
    for index, block in enumerate(_markdown_blocks(markdown), start=1):
        normalized = _normalize(block)
        block_words = _words(block)
        exact_pages = [page_index for page_index, text, _ in page_records if normalized in text]
        if exact_pages:
            status = "exact"
            page_index = exact_pages[0]
            similarity = 1.0
        else:
            scored = []
            for candidate_page, _text, words in page_records:
                denominator = max(1, len(block_words))
                scored.append((len(block_words & words) / denominator, candidate_page))
            similarity, page_index = max(scored, default=(0.0, None))
            status = "fuzzy" if similarity >= 0.55 else "unmatched"
            if status == "unmatched":
                page_index = None
        aligned.append(
            {
                "mineru_block_id": f"MU-{index:04d}",
                "text": block,
                "status": status,
                "pdf_page": page_index,
                "similarity": round(float(similarity), 4),
                "authoritative_evidence": False,
            }
        )
    counts = Counter(item["status"] for item in aligned)
    return {
        "schema_version": "0.1",
        "blocks": aligned,
        "statistics": {
            "block_count": len(aligned),
            "exact": counts["exact"],
            "fuzzy": counts["fuzzy"],
            "unmatched": counts["unmatched"],
        },
        "policy": "MinerU alignment is structural only; accepted claims still require original-PDF evidence validation.",
    }


def _load_flash_client() -> Any:
    try:
        from mineru import MinerU
    except ImportError as exc:
        raise MinerUAdapterError(
            "mineru-open-sdk is required for Flash parsing. Install the optional MinerU requirements."
        ) from exc
    # Force the SDK into flash-only construction even when a developer shell has a precision token.
    with patch.dict(os.environ, {"MINERU_TOKEN": ""}):
        return MinerU(token=None)


def run_flash(
    pdf_path: Path,
    source_bundle_path: Path,
    output_dir: Path,
    *,
    consent_external_upload: bool,
    client_factory: Callable[[], Any] | None = None,
    language: str = "en",
    page_range: str | None = None,
    is_ocr: bool | None = None,
    enable_formula: bool | None = None,
    enable_table: bool | None = None,
    timeout: int = 300,
) -> dict[str, Any]:
    if not consent_external_upload:
        raise MinerUAdapterError("MinerU Flash requires explicit external-upload consent")
    pdf_path = pdf_path.resolve()
    source_bundle_path = source_bundle_path.resolve()
    output_dir = output_dir.resolve()
    if output_dir.exists():
        raise MinerUAdapterError(f"Refusing to reuse an existing MinerU output directory: {output_dir}")
    if not pdf_path.is_file() or pdf_path.suffix.casefold() != ".pdf":
        raise MinerUAdapterError(f"Input is not a readable PDF: {pdf_path}")
    if not source_bundle_path.is_file():
        raise MinerUAdapterError(f"SourceBundle is missing: {source_bundle_path}")
    file_size = pdf_path.stat().st_size
    if file_size > MAX_FLASH_BYTES:
        raise MinerUAdapterError("MinerU Flash file limit exceeded: maximum 10 MiB")
    source = json.loads(source_bundle_path.read_text(encoding="utf-8"))
    page_count = source.get("pdf", {}).get("page_count")
    if not isinstance(page_count, int) or page_count < 1:
        raise MinerUAdapterError("SourceBundle has no valid physical PDF page count")
    if page_count > MAX_FLASH_PAGES:
        raise MinerUAdapterError("MinerU Flash page limit exceeded: maximum 20 pages")
    digest = sha256_file(pdf_path)
    if source.get("pdf", {}).get("sha256") != digest:
        raise MinerUAdapterError("SourceBundle PDF hash does not match the upload file")

    options = {
        "language": language,
        "page_range": page_range,
        "is_ocr": is_ocr,
        "enable_formula": enable_formula,
        "enable_table": enable_table,
        "timeout": timeout,
    }
    started_at = utc_now()
    started_clock = time.monotonic()
    client = (client_factory or _load_flash_client)()
    result = client.flash_extract(str(pdf_path), **options)
    completed_at = utc_now()
    duration_seconds = round(time.monotonic() - started_clock, 3)
    if getattr(result, "state", None) != "done" or not getattr(result, "markdown", None):
        raise MinerUAdapterError(
            f"MinerU Flash did not return completed Markdown: "
            f"{getattr(result, 'state', None)!r} / {getattr(result, 'error', None)!r}"
        )

    markdown = str(result.markdown)
    alignment = align_markdown(markdown, source.get("pages", []))
    request = {
        "schema_version": "0.1",
        "mode": "flash",
        "source_pdf_sha256": digest,
        "file_size_bytes": file_size,
        "page_count": page_count,
        "options": options,
        "token_supplied": False,
    }
    response = {
        "schema_version": "0.1",
        "task_id": getattr(result, "task_id", None),
        "state": getattr(result, "state", None),
        "filename": getattr(result, "filename", None),
        "err_code": getattr(result, "err_code", ""),
        "error": getattr(result, "error", None),
        "markdown_sha256": hashlib.sha256(markdown.encode("utf-8")).hexdigest(),
        "started_at": started_at,
        "completed_at": completed_at,
        "duration_seconds": duration_seconds,
    }
    privacy = {
        "schema_version": "0.1",
        "service": "MinerU Flash",
        "service_host": "mineru.net",
        "consent_external_upload": True,
        "token_used": False,
        "uploaded_at": started_at,
        "source_pdf_sha256": digest,
        "file_size_bytes": file_size,
        "page_count": page_count,
        "purpose": "optional document-structure enhancement; not final evidence",
    }
    output_dir.mkdir(parents=True)
    _write_text(output_dir / "mineru_raw.md", markdown)
    _write_json(output_dir / "mineru_request.json", request)
    _write_json(output_dir / "mineru_response_metadata.json", response)
    _write_json(output_dir / "alignment.json", alignment)
    _write_json(output_dir / "privacy_receipt.json", privacy)
    return {
        "status": "completed",
        "output_dir": str(output_dir),
        "alignment": alignment["statistics"],
        "authoritative_evidence_created": False,
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Call token-free MinerU Flash and align its Markdown to original PDF pages"
    )
    parser.add_argument("pdf", type=Path)
    parser.add_argument("--source-bundle", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--consent-external-upload", action="store_true")
    parser.add_argument("--language", default="en")
    parser.add_argument("--page-range")
    parser.add_argument("--ocr", action=argparse.BooleanOptionalAction, default=None)
    parser.add_argument("--formula", action=argparse.BooleanOptionalAction, default=None)
    parser.add_argument("--table", action=argparse.BooleanOptionalAction, default=None)
    parser.add_argument("--timeout", type=int, default=300)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        result = run_flash(
            args.pdf,
            args.source_bundle,
            args.output,
            consent_external_upload=args.consent_external_upload,
            language=args.language,
            page_range=args.page_range,
            is_ocr=args.ocr,
            enable_formula=args.formula,
            enable_table=args.table,
            timeout=args.timeout,
        )
        print(json.dumps(result, ensure_ascii=False))
        return 0
    except (MinerUAdapterError, json.JSONDecodeError, OSError) as exc:
        print(
            json.dumps({"status": "blocked", "error": str(exc)}, ensure_ascii=False),
            file=sys.stderr,
        )
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
