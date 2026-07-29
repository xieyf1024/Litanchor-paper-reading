#!/usr/bin/env python3
"""Configure and diagnose a local LitAnchor installation without hidden writes."""

from __future__ import annotations

import argparse
import importlib.metadata
import importlib.util
import json
import os
import platform
import re
import shutil
import socket
import sys
import tempfile
from pathlib import Path
from typing import Any

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from autonomous_deep_reading import (  # noqa: E402
    MINERU_CONSENT_MODES,
    default_litanchor_config_path,
)
from litanchor_local import SKILL_VERSION  # noqa: E402
from zotero_local import DEFAULT_BASE_URL, ZoteroLocalClient  # noqa: E402


SETUP_VERSION = "0.6.0-beta.1"
CONFIG_SCHEMA_VERSION = "0.2"
DEFAULT_INBOX = Path("LitAnchor") / "00_Inbox"
MINIMUM_PYTHON = (3, 10)
TESTED_PYTHON_VERSIONS = {
    (3, 10),
    (3, 11),
    (3, 12),
    (3, 13),
    (3, 14),
}
MINIMUM_ZOTERO_MAJOR = 7
TESTED_ZOTERO_MAJORS = {7}
REQUIRED_ZOTERO_API_VERSION = "3"


class SetupError(RuntimeError):
    """Raised when setup would create an unsafe or ambiguous configuration."""


def _atomic_write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.tmp")
    temporary.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    temporary.replace(path)


def _inside(path: Path, root: Path) -> bool:
    try:
        path.relative_to(root)
        return True
    except ValueError:
        return False


def _load_json_object(path: Path) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise SetupError(f"Cannot read valid JSON from {path}") from exc
    if not isinstance(payload, dict):
        raise SetupError(f"Expected a JSON object in {path}")
    return payload


def load_config(path: Path | None = None) -> dict[str, Any]:
    config_path = (path or default_litanchor_config_path()).expanduser().resolve()
    if not config_path.is_file():
        return {}
    return _load_json_object(config_path)


def default_obsidian_registry_path() -> Path:
    configured = os.environ.get("LITANCHOR_OBSIDIAN_REGISTRY")
    if configured:
        return Path(configured).expanduser()
    app_data = os.environ.get("APPDATA")
    if app_data:
        return Path(app_data) / "obsidian" / "obsidian.json"
    return Path.home() / "AppData" / "Roaming" / "obsidian" / "obsidian.json"


def discover_vaults(registry_path: Path | None = None) -> list[dict[str, Any]]:
    path = (registry_path or default_obsidian_registry_path()).expanduser().resolve()
    if not path.is_file():
        return []
    payload = _load_json_object(path)
    raw_vaults = payload.get("vaults", {})
    if not isinstance(raw_vaults, dict):
        raise SetupError(f"Obsidian registry has no valid vault map: {path}")
    discovered: list[dict[str, Any]] = []
    for vault_id, record in raw_vaults.items():
        if not isinstance(record, dict) or not isinstance(record.get("path"), str):
            continue
        vault_path = Path(record["path"]).expanduser().resolve()
        discovered.append(
            {
                "vault_id": str(vault_id),
                "name": vault_path.name,
                "path": str(vault_path),
                "exists": vault_path.is_dir(),
                "open": bool(record.get("open")),
            }
        )
    return sorted(discovered, key=lambda item: (item["name"].casefold(), item["path"].casefold()))


def resolve_vault_name(
    name: str,
    registry_path: Path | None = None,
) -> Path:
    exact = [
        item
        for item in discover_vaults(registry_path)
        if item["name"].casefold() == name.strip().casefold() and item["exists"]
    ]
    if not exact:
        raise SetupError(f"No existing Obsidian Vault is named {name!r}")
    paths = {str(item["path"]) for item in exact}
    if len(paths) != 1:
        raise SetupError(f"Obsidian Vault name {name!r} is ambiguous: {sorted(paths)}")
    return Path(next(iter(paths))).resolve()


def _validated_vault(path: Path) -> Path:
    vault = path.expanduser().resolve()
    if not vault.is_dir():
        raise SetupError(f"Obsidian Vault does not exist: {vault}")
    if not (vault / ".obsidian").is_dir():
        raise SetupError(f"Directory is not an Obsidian Vault (missing .obsidian): {vault}")
    return vault


def _resolve_inbox(vault: Path, inbox: Path) -> Path:
    candidate = inbox.expanduser()
    if not candidate.is_absolute():
        candidate = vault / candidate
    resolved = candidate.resolve()
    if resolved == vault or not _inside(resolved, vault) or resolved.parent == vault:
        raise SetupError(
            "Literature Inbox must be inside a dedicated child root in the selected Vault"
        )
    return resolved


def configure(
    *,
    vault_path: Path,
    inbox: Path,
    consent_mode: str,
    config_path: Path | None = None,
    create_inbox: bool = False,
    zotero_base_url: str = DEFAULT_BASE_URL,
) -> dict[str, Any]:
    if consent_mode not in MINERU_CONSENT_MODES:
        raise SetupError(f"Unsupported MinerU consent mode: {consent_mode}")
    try:
        validated_base_url = ZoteroLocalClient(zotero_base_url).base_url
    except Exception as exc:
        raise SetupError(str(exc)) from exc
    vault = _validated_vault(vault_path)
    resolved_inbox = _resolve_inbox(vault, inbox)
    if create_inbox:
        resolved_inbox.mkdir(parents=True, exist_ok=True)
    if not resolved_inbox.is_dir():
        raise SetupError(
            f"Literature Inbox does not exist: {resolved_inbox}. "
            "Repeat with --create-inbox after confirming the path."
        )
    allowed_root = resolved_inbox.parent.resolve()
    path = (config_path or default_litanchor_config_path()).expanduser().resolve()
    payload = load_config(path)
    payload["schema_version"] = CONFIG_SCHEMA_VERSION
    payload["runtime_version"] = SETUP_VERSION
    payload["obsidian"] = {
        "vault_name": vault.name,
        "vault_path": str(vault),
        "allowed_root": str(allowed_root),
        "inbox_path": str(resolved_inbox),
    }
    payload["zotero"] = {"base_url": validated_base_url}
    mineru = payload.setdefault("mineru", {})
    mineru["enabled"] = consent_mode != "never"
    mineru["consent_mode"] = consent_mode
    mineru.setdefault("max_file_mib", 10)
    mineru.setdefault("max_pages", 20)
    _atomic_write_json(path, payload)
    return {
        "status": "configured",
        "config_path": str(path),
        "vault_name": vault.name,
        "vault_path": str(vault),
        "allowed_root": str(allowed_root),
        "inbox_path": str(resolved_inbox),
        "mineru_consent_mode": consent_mode,
    }


def _check(
    check_id: str,
    status: str,
    observed: Any,
    expected: Any,
    *,
    automatic_fix_available: bool = False,
    user_action: str | None = None,
) -> dict[str, Any]:
    return {
        "check_id": check_id,
        "status": status,
        "observed": observed,
        "expected": expected,
        "automatic_fix_available": automatic_fix_available,
        "user_action": user_action,
    }


def _distribution_version(name: str) -> str | None:
    try:
        return importlib.metadata.version(name)
    except importlib.metadata.PackageNotFoundError:
        return None


def runtime_compatibility(
    version_info: tuple[int, int],
    *,
    is_64_bit: bool,
) -> tuple[str, str]:
    if not is_64_bit:
        return "fail", "LitAnchor requires 64-bit Python."
    if version_info < MINIMUM_PYTHON:
        return "fail", "LitAnchor requires Python 3.10 or newer."
    if version_info in TESTED_PYTHON_VERSIONS:
        return "pass", "version is covered by the current CI matrix"
    return (
        "warning",
        "version meets the minimum but is not yet in the CI matrix; dependency probes decide whether this run may continue",
    )


def zotero_compatibility(version: str | None) -> tuple[str, str]:
    if not version:
        return "warning", "Zotero did not expose its desktop version; Local API probes still continue"
    match = re.match(r"\s*(\d+)", version)
    if match is None:
        return "warning", f"Could not parse Zotero version {version!r}"
    major = int(match.group(1))
    if major < MINIMUM_ZOTERO_MAJOR:
        return "fail", f"LitAnchor requires Zotero {MINIMUM_ZOTERO_MAJOR} or newer."
    if major in TESTED_ZOTERO_MAJORS:
        return "pass", "major version is covered by the current compatibility matrix"
    return (
        "warning",
        "newer Zotero major detected; Local API and PDF-resolution probes decide whether this run may continue",
    )


def _write_probe(directory: Path) -> tuple[bool, str]:
    probe: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            prefix=".litanchor-write-probe-",
            suffix=".tmp",
            dir=directory,
            delete=False,
        ) as handle:
            probe = Path(handle.name)
            handle.write("LitAnchor UTF-8 path probe: 文锚\n")
        return True, "temporary UTF-8 write and cleanup succeeded"
    except OSError as exc:
        return False, str(exc)
    finally:
        if probe is not None and probe.exists():
            probe.unlink(missing_ok=True)


def _mineru_network_check() -> tuple[bool, str]:
    try:
        addresses = socket.getaddrinfo("mineru.net", 443, type=socket.SOCK_STREAM)
    except OSError as exc:
        return False, str(exc)
    return bool(addresses), "mineru.net resolved" if addresses else "no address returned"


def run_doctor(
    *,
    config_path: Path | None = None,
    zotero_base_url: str | None = None,
    paper_title: str | None = None,
    write_probe: bool = True,
    check_mineru_network: bool = False,
) -> dict[str, Any]:
    checks: list[dict[str, Any]] = []
    windows = platform.system() == "Windows"
    checks.append(
        _check(
            "platform",
            "pass" if windows else "warning",
            f"{platform.system()} {platform.machine()}",
            "Windows 10/11 x64",
            user_action=None if windows else "Use a supported Windows host for public-beta runs.",
        )
    )
    in_venv = sys.prefix != getattr(sys, "base_prefix", sys.prefix)
    pip_version = _distribution_version("pip")
    venv_available = importlib.util.find_spec("venv") is not None
    checks.append(
        _check(
            "python_environment",
            "pass" if in_venv and pip_version and venv_available else "warning",
            {
                "virtual_environment": in_venv,
                "pip": pip_version,
                "venv_module": venv_available,
            },
            "isolated virtual environment with pip and venv",
            automatic_fix_available=not in_venv,
            user_action=(
                None
                if in_venv and pip_version and venv_available
                else "Run the LitAnchor install or repair action to restore its isolated environment."
            ),
        )
    )
    checks.append(
        _check(
            "runtime_version",
            "pass" if SKILL_VERSION == SETUP_VERSION else "fail",
            {"skill": SKILL_VERSION, "setup": SETUP_VERSION},
            "matching Skill and setup versions",
            automatic_fix_available=SKILL_VERSION != SETUP_VERSION,
            user_action=None if SKILL_VERSION == SETUP_VERSION else "Run the LitAnchor repair action.",
        )
    )
    version_tuple = (sys.version_info.major, sys.version_info.minor)
    version = f"{version_tuple[0]}.{version_tuple[1]}"
    python_status, python_detail = runtime_compatibility(
        version_tuple,
        is_64_bit=sys.maxsize > 2**32,
    )
    checks.append(
        _check(
            "python",
            python_status,
            {
                "version": version,
                "executable": sys.executable,
                "bits": 64 if sys.maxsize > 2**32 else 32,
                "detail": python_detail,
            },
            "64-bit Python >=3.10; tested versions are maintained by the release CI matrix",
            user_action=(
                "Install supported 64-bit Python and rerun setup."
                if python_status == "fail"
                else None
            ),
        )
    )
    for distribution, import_label in (("pypdf", "pypdf"), ("PyMuPDF", "PyMuPDF")):
        observed = _distribution_version(distribution)
        checks.append(
            _check(
                f"dependency_{import_label.casefold()}",
                "pass" if observed else "fail",
                observed,
                "installed",
                automatic_fix_available=observed is None,
                user_action=None if observed else "Run the LitAnchor repair action.",
            )
        )

    path = (config_path or default_litanchor_config_path()).expanduser().resolve()
    try:
        config = load_config(path)
        config_error = None
    except SetupError as exc:
        config = {}
        config_error = str(exc)
    if config_error:
        checks.append(_check("config", "fail", config_error, "valid local JSON configuration"))
    elif not config:
        checks.append(
            _check(
                "config",
                "warning",
                "missing",
                str(path),
                automatic_fix_available=True,
                user_action="Run LitAnchor setup and choose a Vault, Inbox and MinerU consent mode.",
            )
        )
    else:
        checks.append(_check("config", "pass", str(path), f"schema {CONFIG_SCHEMA_VERSION} compatible"))

    obsidian = config.get("obsidian", {}) if isinstance(config, dict) else {}
    vault_value = obsidian.get("vault_path") if isinstance(obsidian, dict) else None
    inbox_value = obsidian.get("inbox_path") if isinstance(obsidian, dict) else None
    allowed_value = obsidian.get("allowed_root") if isinstance(obsidian, dict) else None
    if all(isinstance(value, str) and value for value in (vault_value, inbox_value, allowed_value)):
        vault = Path(vault_value).expanduser().resolve()
        inbox = Path(inbox_value).expanduser().resolve()
        allowed = Path(allowed_value).expanduser().resolve()
        valid_paths = (
            vault.is_dir()
            and (vault / ".obsidian").is_dir()
            and allowed.is_dir()
            and inbox.is_dir()
            and _inside(allowed, vault)
            and _inside(inbox, allowed)
            and inbox != allowed
        )
        checks.append(
            _check(
                "obsidian_paths",
                "pass" if valid_paths else "fail",
                {"vault": str(vault), "allowed_root": str(allowed), "inbox": str(inbox)},
                "existing contained Vault/allowed-root/Inbox paths",
                user_action=None if valid_paths else "Run setup again with an existing Inbox inside the selected Vault.",
            )
        )
        if valid_paths and write_probe:
            probe_ok, detail = _write_probe(inbox)
            checks.append(
                _check(
                    "obsidian_write_utf8",
                    "pass" if probe_ok else "fail",
                    detail,
                    "temporary UTF-8 write and cleanup",
                    user_action=None if probe_ok else "Grant write access only to the configured LitAnchor root.",
                )
            )
        if vault.is_dir():
            longest_path = max(len(str(value)) for value in (vault, allowed, inbox))
            checks.append(
                _check(
                    "windows_path_shape",
                    "pass" if longest_path < 240 else "warning",
                    {"longest_path_characters": longest_path, "contains_non_ascii": any(ord(ch) > 127 for ch in str(inbox))},
                    "UTF-8-capable path shorter than the legacy 260-character boundary",
                    user_action=None if longest_path < 240 else "Choose a shorter authorized Inbox path.",
                )
            )
            free_mib = shutil.disk_usage(vault).free // (1024 * 1024)
            checks.append(
                _check(
                    "disk_space",
                    "pass" if free_mib >= 512 else "warning",
                    f"{free_mib} MiB free",
                    "at least 512 MiB free",
                    user_action=None if free_mib >= 512 else "Free disk space before processing image-heavy papers.",
                )
            )
    else:
        checks.append(
            _check(
                "obsidian_paths",
                "warning",
                "not configured",
                "one Vault, authorized root and Inbox",
                automatic_fix_available=True,
                user_action="Run LitAnchor setup.",
            )
        )
    checks.append(
        _check(
            "no_overwrite_policy",
            "pass",
            "export requires confirmation and rejects existing destinations",
            "existing notes are never overwritten",
        )
    )

    configured_base = (
        config.get("zotero", {}).get("base_url")
        if isinstance(config.get("zotero"), dict)
        else None
    )
    base_url = zotero_base_url or configured_base or DEFAULT_BASE_URL
    try:
        client = ZoteroLocalClient(str(base_url), timeout=3.0)
        health = client.health()
        checks.append(_check("zotero_local_api", "pass", health, "read-only loopback API reachable"))
        api_version = health.get("api_version")
        checks.append(
            _check(
                "zotero_api_version",
                "pass" if api_version == REQUIRED_ZOTERO_API_VERSION else "fail",
                api_version,
                REQUIRED_ZOTERO_API_VERSION,
                user_action=(
                    None
                    if api_version == REQUIRED_ZOTERO_API_VERSION
                    else "Use a Zotero release exposing Local API version 3."
                ),
            )
        )
        zotero_status, zotero_detail = zotero_compatibility(health.get("zotero_version"))
        checks.append(
            _check(
                "zotero_version",
                zotero_status,
                {
                    "version": health.get("zotero_version"),
                    "detail": zotero_detail,
                },
                "Zotero >=7; newer major versions are accepted after Local API probes",
                user_action=(
                    f"Upgrade to Zotero {MINIMUM_ZOTERO_MAJOR} or newer."
                    if zotero_status == "fail"
                    else None
                ),
            )
        )
        if paper_title:
            item = client.resolve_item("title", paper_title)
            attachment = client.resolve_pdf_attachment(item)
            pdf_path = client.attachment_path(attachment)
            checks.append(
                _check(
                    "zotero_unique_pdf",
                    "pass",
                    {"item_key": item.get("key"), "pdf_path": str(pdf_path)},
                    "one uniquely resolved local PDF",
                )
            )
    except Exception as exc:  # Normalize adapter diagnostics into the doctor contract.
        checks.append(
            _check(
                "zotero_local_api",
                "fail",
                str(exc),
                "Zotero running with Local API enabled",
                user_action="Start Zotero and enable local application communication in Advanced settings.",
            )
        )

    mineru = config.get("mineru", {}) if isinstance(config.get("mineru"), dict) else {}
    consent = mineru.get("consent_mode", "ask_each_time")
    consent_valid = consent in MINERU_CONSENT_MODES
    checks.append(
        _check(
            "mineru_consent",
            "pass" if consent_valid else "fail",
            consent,
            sorted(MINERU_CONSENT_MODES),
            user_action=None if consent_valid else "Run setup and choose a valid MinerU consent mode.",
        )
    )
    mineru_version = _distribution_version("mineru-open-sdk")
    mineru_required = consent in {"always_for_eligible_files", "ask_each_time"}
    checks.append(
        _check(
            "dependency_mineru",
            "pass" if mineru_version else ("warning" if mineru_required else "skipped"),
            mineru_version or "not installed",
            "installed when MinerU may be used",
            automatic_fix_available=mineru_required and mineru_version is None,
            user_action="Run LitAnchor repair with MinerU enabled." if mineru_required and not mineru_version else None,
        )
    )
    if check_mineru_network and mineru_required:
        network_ok, detail = _mineru_network_check()
        checks.append(
            _check(
                "mineru_network",
                "pass" if network_ok else "warning",
                detail,
                "mineru.net DNS reachable without uploading a file",
                user_action=None if network_ok else "Check network access; PyMuPDF fallback remains available.",
            )
        )

    statuses = {item["status"] for item in checks}
    overall = (
        "blocked"
        if "fail" in statuses
        else "completed_with_warnings"
        if "warning" in statuses
        else "completed"
    )
    return {
        "schema_version": "1.0",
        "status": overall,
        "setup_version": SETUP_VERSION,
        "config_path": str(path),
        "checks": checks,
    }


def build_run_plan(
    *,
    paper: str,
    selector: str,
    vault_name: str | None,
    config_path: Path | None = None,
) -> dict[str, Any]:
    config = load_config(config_path)
    if not config:
        raise SetupError("LitAnchor is not configured; run setup first")
    obsidian = config.get("obsidian")
    if not isinstance(obsidian, dict):
        raise SetupError("Configuration has no Obsidian target")
    configured_name = str(obsidian.get("vault_name") or "")
    if vault_name and vault_name.casefold() != configured_name.casefold():
        raise SetupError(
            f"Requested Vault {vault_name!r} does not match configured Vault {configured_name!r}; "
            "run setup to authorize another target."
        )
    mineru = config.get("mineru", {})
    consent_mode = (
        mineru.get("consent_mode", "ask_each_time")
        if isinstance(mineru, dict)
        else "ask_each_time"
    )
    install = config.get("installation", {})
    runtime_root = (
        Path(install.get("runtime_root"))
        if isinstance(install, dict) and install.get("runtime_root")
        else default_litanchor_config_path().parent / "runtime"
    )
    return {
        "schema_version": "1.0",
        "status": "ready_for_agent_execution",
        "paper_selector": {"type": selector, "value": paper},
        "reading_mode": "deep",
        "external_knowledge_allowed": False,
        "zotero": {
            "base_url": config.get("zotero", {}).get("base_url", DEFAULT_BASE_URL),
            "read_only": True,
        },
        "obsidian": {
            "vault_name": configured_name,
            "vault_path": obsidian.get("vault_path"),
            "allowed_root": obsidian.get("allowed_root"),
            "inbox_path": obsidian.get("inbox_path"),
            "overwrite": False,
        },
        "mineru": {
            "consent_mode": consent_mode,
            "automatic_for_eligible_files": consent_mode == "always_for_eligible_files",
        },
        "runtime_root": str(runtime_root),
        "stages": [
            "resolve_one_zotero_item_and_pdf",
            "pymupdf_physical_page_baseline",
            "consent_aware_mineru_structure_enhancement",
            "six_pass_deep_reading",
            "evidence_and_claim_ledgers",
            "section_synthesis_and_visual_selection",
            "fidelity_and_recall_review",
            "final_template",
            "contained_no_overwrite_obsidian_export",
        ],
        "interrupt_only_for": [
            "source_ambiguity",
            "multiple_pdf_attachments",
            "missing_mineru_consent",
            "unreadable_required_page",
            "quality_blocker",
            "target_collision",
        ],
    }


def _print_human_doctor(report: dict[str, Any]) -> None:
    print(f"LitAnchor doctor: {report['status']}")
    for item in report["checks"]:
        print(f"[{item['status'].upper():7}] {item['check_id']}: {item['observed']}")
        if item.get("user_action"):
            print(f"          action: {item['user_action']}")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="LitAnchor setup and diagnostic CLI")
    subparsers = parser.add_subparsers(dest="command", required=True)

    discover = subparsers.add_parser("discover-vaults")
    discover.add_argument("--registry-path", type=Path)

    setup = subparsers.add_parser("setup")
    vault_group = setup.add_mutually_exclusive_group(required=True)
    vault_group.add_argument("--vault")
    vault_group.add_argument("--vault-path", type=Path)
    setup.add_argument("--registry-path", type=Path)
    setup.add_argument("--inbox", type=Path, default=DEFAULT_INBOX)
    setup.add_argument("--mineru-consent", choices=sorted(MINERU_CONSENT_MODES), required=True)
    setup.add_argument("--config-path", type=Path)
    setup.add_argument("--create-inbox", action="store_true")
    setup.add_argument("--zotero-base-url", default=DEFAULT_BASE_URL)

    doctor = subparsers.add_parser("doctor")
    doctor.add_argument("--config-path", type=Path)
    doctor.add_argument("--zotero-base-url")
    doctor.add_argument("--paper-title")
    doctor.add_argument("--skip-write-probe", action="store_true")
    doctor.add_argument("--check-mineru-network", action="store_true")
    doctor.add_argument("--format", choices=("json", "human"), default="json")

    plan = subparsers.add_parser("run-plan")
    plan.add_argument("--paper", required=True)
    plan.add_argument("--selector", choices=("title", "doi", "citekey", "item_key"), default="title")
    plan.add_argument("--vault")
    plan.add_argument("--config-path", type=Path)
    plan.add_argument("--output", type=Path)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        if args.command == "discover-vaults":
            result: Any = {"status": "completed", "vaults": discover_vaults(args.registry_path)}
        elif args.command == "setup":
            vault_path = args.vault_path or resolve_vault_name(args.vault, args.registry_path)
            result = configure(
                vault_path=vault_path,
                inbox=args.inbox,
                consent_mode=args.mineru_consent,
                config_path=args.config_path,
                create_inbox=args.create_inbox,
                zotero_base_url=args.zotero_base_url,
            )
        elif args.command == "doctor":
            result = run_doctor(
                config_path=args.config_path,
                zotero_base_url=args.zotero_base_url,
                paper_title=args.paper_title,
                write_probe=not args.skip_write_probe,
                check_mineru_network=args.check_mineru_network,
            )
            if args.format == "human":
                _print_human_doctor(result)
                return 0 if result["status"] != "blocked" else 2
        else:
            result = build_run_plan(
                paper=args.paper,
                selector=args.selector,
                vault_name=args.vault,
                config_path=args.config_path,
            )
            if args.output:
                _atomic_write_json(args.output.expanduser().resolve(), result)
                result["output"] = str(args.output.expanduser().resolve())
        print(json.dumps(result, ensure_ascii=True, indent=2))
        return 0 if result.get("status") != "blocked" else 2
    except SetupError as exc:
        print(json.dumps({"status": "blocked", "error": str(exc)}, ensure_ascii=True), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
