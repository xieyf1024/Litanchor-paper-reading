#!/usr/bin/env python3
"""Read one paper from Zotero's loopback-only Local API and prepare LitAnchor artifacts."""

from __future__ import annotations

import argparse
import ipaddress
import json
import re
import sys
import unicodedata
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode, urlparse
from urllib.request import Request, url2pathname, urlopen

from litanchor_local import PipelineError, prepare_pdf


DEFAULT_BASE_URL = "http://127.0.0.1:23119/api"
ITEM_KEY_PATTERN = re.compile(r"^[A-Z0-9]{8}$")


def _normalized_text(value: str) -> str:
    normalized = unicodedata.normalize("NFKC", value).casefold()
    return "".join(character for character in normalized if character.isalnum())


def _title_search_queries(value: str) -> list[str]:
    words = re.findall(r"[^\W_]+", unicodedata.normalize("NFKC", value), re.UNICODE)
    queries = [value]
    for length in (8, 5, 3):
        if len(words) >= length:
            queries.append(" ".join(words[:length]))
    return list(dict.fromkeys(query.strip() for query in queries if query.strip()))


def _normalized_doi(value: str) -> str:
    value = value.strip().casefold()
    value = re.sub(r"^(?:https?://(?:dx\.)?doi\.org/|doi:\s*)", "", value)
    return value.rstrip("./ ")


def _citation_key(data: dict[str, Any]) -> str | None:
    direct = data.get("citationKey")
    if isinstance(direct, str) and direct.strip():
        return direct.strip()
    extra = data.get("extra")
    if isinstance(extra, str):
        match = re.search(r"(?im)^citation key:\s*(\S+)\s*$", extra)
        if match:
            return match.group(1)
    return None


def _loopback_base_url(value: str) -> str:
    parsed = urlparse(value)
    if parsed.scheme != "http" or parsed.username or parsed.password or parsed.query or parsed.fragment:
        raise PipelineError("Zotero Local API URL must be a plain loopback HTTP URL")
    hostname = parsed.hostname
    try:
        loopback = hostname == "localhost" or (hostname is not None and ipaddress.ip_address(hostname).is_loopback)
    except ValueError:
        loopback = False
    if not loopback or not parsed.path.rstrip("/").endswith("/api"):
        raise PipelineError("Refusing a Zotero API URL that is not loopback /api")
    return value.rstrip("/")


class ZoteroLocalClient:
    """A deliberately read-only Zotero Local API client."""

    def __init__(self, base_url: str = DEFAULT_BASE_URL, timeout: float = 10.0) -> None:
        self.base_url = _loopback_base_url(base_url)
        self.timeout = timeout

    def _request(self, path: str, params: dict[str, Any] | None = None) -> tuple[bytes, Any]:
        url = f"{self.base_url}/{path.lstrip('/')}"
        if params:
            url = f"{url}?{urlencode(params)}"
        request = Request(url, headers={"Zotero-API-Version": "3"}, method="GET")
        try:
            with urlopen(request, timeout=self.timeout) as response:
                return response.read(), response.headers
        except HTTPError as exc:
            if exc.code == 403:
                raise PipelineError("Zotero Local API is disabled (HTTP 403)") from exc
            raise PipelineError(f"Zotero Local API returned HTTP {exc.code} for {path}") from exc
        except URLError as exc:
            raise PipelineError(f"Cannot reach Zotero Local API: {exc.reason}") from exc

    def _get_json(self, path: str, params: dict[str, Any] | None = None) -> Any:
        payload, _headers = self._request(path, params)
        try:
            return json.loads(payload.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise PipelineError(f"Zotero Local API returned invalid JSON for {path}") from exc

    def _get_text(self, path: str) -> str:
        payload, _headers = self._request(path)
        try:
            return payload.decode("utf-8").strip()
        except UnicodeDecodeError as exc:
            raise PipelineError(f"Zotero Local API returned invalid text for {path}") from exc

    def health(self) -> dict[str, str | None]:
        _payload, headers = self._request("")
        return {
            "api_version": headers.get("Zotero-API-Version"),
            "schema_version": headers.get("Zotero-Schema-Version"),
            "zotero_version": headers.get("X-Zotero-Version"),
        }

    def _search(self, query: str, *, everything: bool = False) -> list[dict[str, Any]]:
        payload = self._get_json(
            "/users/0/items/top",
            {
                "q": query,
                "qmode": "everything" if everything else "titleCreatorYear",
                "limit": 25,
                "v": 3,
            },
        )
        if not isinstance(payload, list):
            raise PipelineError("Zotero item search returned an unexpected response")
        return [item for item in payload if isinstance(item, dict) and isinstance(item.get("data"), dict)]

    def resolve_item(self, selector: str, value: str) -> dict[str, Any]:
        value = value.strip()
        if not value:
            raise PipelineError(f"Empty Zotero {selector} selector")
        if selector == "item_key":
            key = value.upper()
            if ITEM_KEY_PATTERN.fullmatch(key) is None:
                raise PipelineError("Zotero Item Key must contain exactly eight letters/digits")
            item = self._get_json(f"/users/0/items/{key}", {"v": 3})
            if not isinstance(item, dict) or not isinstance(item.get("data"), dict):
                raise PipelineError("Zotero Item Key did not resolve to an item")
            return item

        if selector == "title":
            target = _normalized_text(value)
            candidates_by_key: dict[str, dict[str, Any]] = {}
            for query in _title_search_queries(value):
                for item in self._search(query):
                    key = str(item.get("key", ""))
                    if key:
                        candidates_by_key[key] = item
                matches = [
                    item
                    for item in candidates_by_key.values()
                    if _normalized_text(str(item["data"].get("title", ""))) == target
                ]
                if matches:
                    break
            else:
                matches = []
        elif selector == "doi":
            candidates = self._search(value, everything=True)
            target = _normalized_doi(value)
            matches = [item for item in candidates if _normalized_doi(str(item["data"].get("DOI", ""))) == target]
        elif selector == "citekey":
            candidates = self._search(value, everything=True)
            matches = [item for item in candidates if (_citation_key(item["data"]) or "").casefold() == value.casefold()]
        else:
            raise PipelineError(f"Unsupported Zotero selector: {selector}")
        if len(matches) != 1:
            raise PipelineError(
                f"Zotero {selector} must resolve to exactly one item; exact matches found: {len(matches)}"
            )
        return matches[0]

    @staticmethod
    def _is_pdf_attachment(item: dict[str, Any]) -> bool:
        data = item.get("data", {})
        return (
            data.get("itemType") == "attachment"
            and (
                str(data.get("contentType", "")).casefold() == "application/pdf"
                or str(data.get("filename", "")).casefold().endswith(".pdf")
            )
        )

    def resolve_pdf_attachment(
        self,
        item: dict[str, Any],
        attachment_key: str | None = None,
    ) -> dict[str, Any]:
        if self._is_pdf_attachment(item):
            candidates = [item]
        else:
            item_key = str(item.get("key", ""))
            if ITEM_KEY_PATTERN.fullmatch(item_key) is None:
                raise PipelineError("Resolved Zotero item has no valid Item Key")
            children = self._get_json(f"/users/0/items/{item_key}/children", {"v": 3})
            if not isinstance(children, list):
                raise PipelineError("Zotero child-item lookup returned an unexpected response")
            candidates = [candidate for candidate in children if isinstance(candidate, dict) and self._is_pdf_attachment(candidate)]
        if attachment_key:
            key = attachment_key.upper()
            candidates = [candidate for candidate in candidates if candidate.get("key") == key]
        if len(candidates) != 1:
            raise PipelineError(f"Expected exactly one PDF attachment; matches found: {len(candidates)}")
        return candidates[0]

    def attachment_path(self, attachment: dict[str, Any]) -> Path:
        key = str(attachment.get("key", ""))
        if ITEM_KEY_PATTERN.fullmatch(key) is None:
            raise PipelineError("Resolved PDF attachment has no valid attachment key")
        file_url = self._get_text(f"/users/0/items/{key}/file/view/url").strip('"')
        parsed = urlparse(file_url)
        if parsed.scheme != "file" or parsed.query or parsed.fragment:
            raise PipelineError("Zotero attachment did not resolve to a local file URL")
        native = url2pathname(parsed.path)
        if parsed.netloc:
            native = f"//{parsed.netloc}{native}"
        path = Path(native).resolve()
        if not path.is_file() or path.suffix.casefold() != ".pdf":
            raise PipelineError("Zotero PDF attachment is missing or not a PDF")
        return path


def _authors(data: dict[str, Any]) -> list[str]:
    authors: list[str] = []
    for creator in data.get("creators", []):
        if not isinstance(creator, dict) or creator.get("creatorType") != "author":
            continue
        name = creator.get("name") or " ".join(
            part for part in (str(creator.get("firstName", "")).strip(), str(creator.get("lastName", "")).strip()) if part
        )
        if name:
            authors.append(str(name))
    return authors


def prepare_zotero_item(
    client: ZoteroLocalClient,
    selector: str,
    value: str,
    output_root: Path,
    *,
    reading_mode: str = "deep",
    attachment_key: str | None = None,
) -> tuple[Path, dict[str, Any]]:
    item = client.resolve_item(selector, value)
    attachment = client.resolve_pdf_attachment(item, attachment_key)
    pdf_path = client.attachment_path(attachment)
    data = item["data"]
    title = str(data.get("title", "")).strip() or pdf_path.stem
    date = str(data.get("date", ""))
    year_match = re.search(r"(?<!\d)(\d{4})(?!\d)", date)
    return prepare_pdf(
        pdf_path,
        output_root,
        reading_mode=reading_mode,
        title=title,
        authors=_authors(data),
        year=int(year_match.group(1)) if year_match else None,
        journal=str(data.get("publicationTitle", "")).strip() or None,
        doi=str(data.get("DOI", "")).strip() or None,
        citekey=_citation_key(data),
        acquisition_method="zotero_local_api",
        source_query=f"{selector}:{value}",
        zotero_item_key=str(item["key"]),
        zotero_attachment_key=str(attachment["key"]),
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="LitAnchor read-only Zotero Local API adapter")
    parser.add_argument("--base-url", default=DEFAULT_BASE_URL)
    subparsers = parser.add_subparsers(dest="command", required=True)
    subparsers.add_parser("check", help="verify the local read-only API")
    prepare = subparsers.add_parser("prepare", help="resolve one Zotero item and prepare its PDF")
    selectors = prepare.add_mutually_exclusive_group(required=True)
    selectors.add_argument("--item-key")
    selectors.add_argument("--title")
    selectors.add_argument("--doi")
    selectors.add_argument("--citekey")
    prepare.add_argument("--attachment-key")
    prepare.add_argument("--output-root", type=Path, default=Path("runtime/runs"))
    prepare.add_argument("--mode", choices=("skim", "deep", "internalize"), default="deep")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        client = ZoteroLocalClient(args.base_url)
        if args.command == "check":
            print(json.dumps({"status": "available", **client.health()}, ensure_ascii=False))
            return 0
        selector = next(name for name in ("item_key", "title", "doi", "citekey") if getattr(args, name))
        value = getattr(args, selector)
        run_dir, bundle = prepare_zotero_item(
            client,
            selector,
            value,
            args.output_root,
            reading_mode=args.mode,
            attachment_key=args.attachment_key,
        )
        print(
            json.dumps(
                {
                    "run_dir": str(run_dir),
                    "preflight_status": bundle["pdf"]["preflight_status"],
                    "zotero_item_key": bundle["source"]["zotero_item_key"],
                    "zotero_attachment_key": bundle["source"]["zotero_attachment_key"],
                },
                ensure_ascii=False,
            )
        )
        return 0 if bundle["pdf"]["preflight_status"] in {"PASS", "PASS_WITH_WARNINGS"} else 2
    except PipelineError as exc:
        print(json.dumps({"status": "blocked", "error": str(exc)}, ensure_ascii=False), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
