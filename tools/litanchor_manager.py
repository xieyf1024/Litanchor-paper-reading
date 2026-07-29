#!/usr/bin/env python3
"""Install and manage LitAnchor in user-local, receipt-tracked directories."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any


MANIFEST_NAME = "litanchor-install.json"
STATE_NAME = "install-state.json"
CONFIG_NAME = "config.json"
MARKER_NAME = ".litanchor-managed"


class InstallError(RuntimeError):
    """Raised when an installation action would be unsafe or incomplete."""


def _atomic_write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.tmp")
    temporary.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    temporary.replace(path)


def _load_json(path: Path) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise InstallError(f"Cannot read valid JSON from {path}") from exc
    if not isinstance(payload, dict):
        raise InstallError(f"Expected a JSON object in {path}")
    return payload


def _source_root() -> Path:
    return Path(__file__).resolve().parents[1]


def load_manifest(source_root: Path | None = None) -> dict[str, Any]:
    root = (source_root or _source_root()).resolve()
    manifest = _load_json(root / MANIFEST_NAME)
    required = {"schema_version", "name", "version", "python", "dependencies", "payload", "paths", "license"}
    missing = sorted(required - set(manifest))
    if missing:
        raise InstallError(f"Install manifest is missing fields: {missing}")
    return manifest


def default_install_root() -> Path:
    local_app_data = os.environ.get("LOCALAPPDATA")
    if local_app_data:
        return Path(local_app_data) / "LitAnchor"
    return Path.home() / ".litanchor"


def default_skills_root() -> Path:
    codex_home = os.environ.get("CODEX_HOME")
    if codex_home:
        return Path(codex_home) / "skills"
    return Path.home() / ".codex" / "skills"


def _ensure_safe_root(path: Path, label: str) -> Path:
    resolved = path.expanduser().resolve()
    anchors = {Path(resolved.anchor).resolve(), Path.home().resolve()}
    if resolved in anchors or len(resolved.parts) < 3:
        raise InstallError(f"Refusing broad {label}: {resolved}")
    return resolved


def _inside(path: Path, root: Path) -> bool:
    try:
        path.relative_to(root)
        return True
    except ValueError:
        return False


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def tree_sha256(root: Path) -> str:
    digest = hashlib.sha256()
    for path in sorted(item for item in root.rglob("*") if item.is_file()):
        relative = path.relative_to(root).as_posix()
        if "__pycache__" in path.parts or path.suffix in {".pyc", ".pyo"}:
            continue
        digest.update(relative.encode("utf-8"))
        digest.update(b"\0")
        digest.update(file_sha256(path).encode("ascii"))
        digest.update(b"\n")
    return digest.hexdigest()


def _venv_python(install_root: Path) -> Path:
    return install_root / ".venv" / "Scripts" / "python.exe"


def _run(command: list[str]) -> None:
    completed = subprocess.run(command, check=False)
    if completed.returncode:
        raise InstallError(f"Command failed with exit code {completed.returncode}: {command}")


def python_compatibility(
    manifest: dict[str, Any],
    version_info: tuple[int, int] | None = None,
    *,
    is_64_bit: bool | None = None,
) -> dict[str, Any]:
    policy = manifest["python"]
    minimum = tuple(int(part) for part in str(policy["minimum_version"]).split(".", 1))
    observed_tuple = version_info or (sys.version_info.major, sys.version_info.minor)
    observed = f"{observed_tuple[0]}.{observed_tuple[1]}"
    tested = set(policy.get("tested_versions", []))
    bits_ok = sys.maxsize > 2**32 if is_64_bit is None else is_64_bit
    if not bits_ok:
        return {
            "status": "fail",
            "observed": observed,
            "reason": "LitAnchor requires 64-bit Python.",
        }
    if observed_tuple < minimum:
        return {
            "status": "fail",
            "observed": observed,
            "reason": f"LitAnchor requires Python {minimum[0]}.{minimum[1]} or newer.",
        }
    if observed in tested:
        return {"status": "pass", "observed": observed, "reason": "version is in the CI matrix"}
    return {
        "status": "warning",
        "observed": observed,
        "reason": (
            "version is newer than or outside the tested matrix; continue with dependency "
            "and doctor probes before declaring support"
        ),
    }


def _check_python(manifest: dict[str, Any]) -> None:
    result = python_compatibility(manifest)
    if result["status"] == "fail":
        raise InstallError(str(result["reason"]))
    if result["status"] == "warning":
        print(f"LitAnchor compatibility warning: {result['reason']} (observed {result['observed']})", file=sys.stderr)


def _copy_release_metadata(source_root: Path, version_root: Path, manifest: dict[str, Any]) -> None:
    for relative in (
        MANIFEST_NAME,
        manifest["dependencies"]["core"],
        manifest["dependencies"]["mineru"],
        "LICENSE",
        "NOTICE.md",
        "THIRD_PARTY.md",
    ):
        source = source_root / relative
        if not source.is_file():
            raise InstallError(f"Release payload is incomplete: {source}")
        shutil.copy2(source, version_root / source.name)


def _prepare_version_payload(
    source_root: Path,
    install_root: Path,
    manifest: dict[str, Any],
) -> tuple[Path, str]:
    version = str(manifest["version"])
    skill_source = source_root / manifest["payload"]["skill_source"]
    if not (skill_source / "SKILL.md").is_file():
        raise InstallError(f"Skill payload is missing: {skill_source}")
    source_hash = tree_sha256(skill_source)
    version_root = install_root / "versions" / version
    payload = version_root / "skill"
    if payload.is_dir():
        if tree_sha256(payload) != source_hash:
            raise InstallError(
                f"Installed archive for immutable version {version} differs from this payload."
            )
        return payload, source_hash

    staging_parent = install_root / ".staging"
    staging_parent.mkdir(parents=True, exist_ok=True)
    staging = Path(tempfile.mkdtemp(prefix=f"{version}-", dir=staging_parent))
    try:
        staged_version = staging / version
        staged_payload = staged_version / "skill"
        shutil.copytree(
            skill_source,
            staged_payload,
            ignore=shutil.ignore_patterns("__pycache__", "*.pyc", "*.pyo"),
        )
        _copy_release_metadata(source_root, staged_version, manifest)
        (staged_version / MARKER_NAME).write_text(
            json.dumps({"version": version, "skill_sha256": source_hash}) + "\n",
            encoding="utf-8",
        )
        version_root.parent.mkdir(parents=True, exist_ok=True)
        staged_version.replace(version_root)
    finally:
        shutil.rmtree(staging, ignore_errors=True)
    return payload, source_hash


def _sync_dependencies(
    *,
    install_root: Path,
    version_root: Path,
    include_mineru: bool,
    skip_dependencies: bool,
) -> Path:
    python = _venv_python(install_root)
    if skip_dependencies:
        return Path(sys.executable).resolve()
    if not python.is_file():
        install_root.mkdir(parents=True, exist_ok=True)
        _run([sys.executable, "-m", "venv", str(install_root / ".venv")])
    _run(
        [
            str(python),
            "-m",
            "pip",
            "install",
            "--disable-pip-version-check",
            "-r",
            str(version_root / "requirements.txt"),
        ]
    )
    if include_mineru:
        _run(
            [
                str(python),
                "-m",
                "pip",
                "install",
                "--disable-pip-version-check",
                "-r",
                str(version_root / "requirements-mineru.txt"),
            ]
        )
    return python


def _state_path(install_root: Path) -> Path:
    return install_root / STATE_NAME


def _load_state(install_root: Path) -> dict[str, Any]:
    path = _state_path(install_root)
    return _load_json(path) if path.is_file() else {}


def _assert_owned_active_skill(
    target: Path,
    state: dict[str, Any],
    *,
    allow_missing: bool = True,
) -> None:
    if not target.exists():
        if allow_missing:
            return
        raise InstallError(f"Managed Skill is missing: {target}")
    active_path = state.get("active_skill_path")
    expected_hash = state.get("active_skill_sha256")
    if not active_path or Path(active_path).resolve() != target.resolve() or not expected_hash:
        raise InstallError(
            f"Existing Skill is not tracked by this LitAnchor installation: {target}"
        )
    if tree_sha256(target) != expected_hash:
        raise InstallError(
            "Installed Skill has local modifications. Preserve or remove those changes before repair, "
            "upgrade, rollback or uninstall."
        )


def _activate_skill(payload: Path, target: Path, state: dict[str, Any]) -> str:
    _assert_owned_active_skill(target, state)
    target.parent.mkdir(parents=True, exist_ok=True)
    staging = target.parent / f".{target.name}.litanchor-next"
    backup = target.parent / f".{target.name}.litanchor-previous"
    if staging.exists() or backup.exists():
        raise InstallError(
            f"Interrupted activation needs repair before continuing: {staging} or {backup}"
        )
    shutil.copytree(payload, staging)
    try:
        if target.exists():
            target.replace(backup)
        staging.replace(target)
        shutil.rmtree(backup, ignore_errors=True)
    except Exception:
        if target.exists():
            shutil.rmtree(target, ignore_errors=True)
        if backup.exists():
            backup.replace(target)
        raise
    return tree_sha256(target)


def _install_manager_files(source_root: Path, install_root: Path) -> None:
    bin_dir = install_root / "bin"
    bin_dir.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source_root / "tools" / "litanchor_manager.py", bin_dir / "litanchor_manager.py")
    shutil.copy2(source_root / "litanchor.ps1", bin_dir / "litanchor.ps1")
    shutil.copy2(source_root / MANIFEST_NAME, install_root / MANIFEST_NAME)


def _update_local_config(
    *,
    install_root: Path,
    config_path: Path,
    version: str,
    python: Path,
    skill_target: Path,
    include_mineru: bool,
) -> None:
    payload = _load_json(config_path) if config_path.is_file() else {}
    payload.setdefault("schema_version", "0.2")
    payload["installation"] = {
        "version": version,
        "install_root": str(install_root),
        "runtime_root": str(install_root / "runtime"),
        "venv_python": str(python),
        "skill_path": str(skill_target),
        "mineru_dependency_installed": include_mineru,
    }
    _atomic_write_json(config_path, payload)


def install(
    *,
    source_root: Path,
    install_root: Path,
    skills_root: Path,
    config_path: Path,
    include_mineru: bool,
    skip_dependencies: bool = False,
    action: str = "install",
) -> dict[str, Any]:
    source_root = source_root.resolve()
    install_root = _ensure_safe_root(install_root, "install root")
    skills_root = _ensure_safe_root(skills_root, "Skills root")
    manifest = load_manifest(source_root)
    _check_python(manifest)
    install_root.mkdir(parents=True, exist_ok=True)
    (install_root / MARKER_NAME).write_text(
        json.dumps({"name": manifest["name"]}) + "\n",
        encoding="utf-8",
    )
    payload, payload_hash = _prepare_version_payload(source_root, install_root, manifest)
    state = _load_state(install_root)
    version = str(manifest["version"])
    skill_target = skills_root / manifest["payload"]["skill_directory_name"]
    version_root = payload.parent
    python = _sync_dependencies(
        install_root=install_root,
        version_root=version_root,
        include_mineru=include_mineru,
        skip_dependencies=skip_dependencies,
    )

    if (
        state.get("active_version") == version
        and skill_target.is_dir()
        and tree_sha256(skill_target) == payload_hash
    ):
        activation = "unchanged"
        active_hash = payload_hash
    else:
        active_hash = _activate_skill(payload, skill_target, state)
        activation = "activated"

    history = [str(item) for item in state.get("installed_versions", []) if isinstance(item, str)]
    if version not in history:
        history.append(version)
    state = {
        "schema_version": "1.0",
        "name": manifest["name"],
        "active_version": version,
        "active_skill_path": str(skill_target.resolve()),
        "active_skill_sha256": active_hash,
        "install_root": str(install_root),
        "venv_python": str(python),
        "mineru_dependency_installed": include_mineru,
        "installed_versions": history,
    }
    _atomic_write_json(_state_path(install_root), state)
    _install_manager_files(source_root, install_root)
    _update_local_config(
        install_root=install_root,
        config_path=config_path,
        version=version,
        python=python,
        skill_target=skill_target,
        include_mineru=include_mineru,
    )
    receipt = {
        "schema_version": "1.0",
        "status": "completed",
        "action": action,
        "activation": activation,
        "version": version,
        "install_root": str(install_root),
        "skill_path": str(skill_target),
        "skill_sha256": active_hash,
        "venv_python": str(python),
        "config_path": str(config_path),
        "mineru_dependency_installed": include_mineru,
        "dependencies_skipped_for_test": skip_dependencies,
    }
    _atomic_write_json(version_root / "install-receipt.json", receipt)
    return receipt


def repair(
    *,
    install_root: Path,
    skills_root: Path,
    config_path: Path,
    skip_dependencies: bool = False,
    include_mineru: bool = False,
) -> dict[str, Any]:
    install_root = _ensure_safe_root(install_root, "install root")
    state = _load_state(install_root)
    if not state:
        raise InstallError("LitAnchor is not installed; use install instead of repair.")
    version = str(state["active_version"])
    version_root = install_root / "versions" / version
    manifest = _load_json(version_root / MANIFEST_NAME)
    payload = version_root / "skill"
    target = _ensure_safe_root(skills_root, "Skills root") / manifest["payload"]["skill_directory_name"]
    changed = False
    staging = target.parent / f".{target.name}.litanchor-next"
    backup = target.parent / f".{target.name}.litanchor-previous"
    if not target.exists() and backup.is_dir():
        backup.replace(target)
        changed = True
    if staging.is_dir():
        shutil.rmtree(staging)
        changed = True
    _assert_owned_active_skill(target, state)
    mineru_enabled = bool(state.get("mineru_dependency_installed")) or include_mineru
    python = _sync_dependencies(
        install_root=install_root,
        version_root=version_root,
        include_mineru=mineru_enabled,
        skip_dependencies=skip_dependencies,
    )
    expected = tree_sha256(payload)
    if not target.exists():
        _activate_skill(payload, target, state)
        changed = True
    elif tree_sha256(target) != expected:
        raise InstallError("Managed Skill differs from its immutable archive; refusing silent replacement.")
    _update_local_config(
        install_root=install_root,
        config_path=config_path,
        version=version,
        python=python,
        skill_target=target,
        include_mineru=mineru_enabled,
    )
    state["mineru_dependency_installed"] = mineru_enabled
    state["venv_python"] = str(python)
    _atomic_write_json(_state_path(install_root), state)
    return {
        "status": "completed",
        "action": "repair",
        "version": version,
        "skill_path": str(target),
        "venv_python": str(python),
        "mineru_dependency_installed": mineru_enabled,
        "changed": changed,
    }


def rollback(
    *,
    install_root: Path,
    skills_root: Path,
    config_path: Path,
    target_version: str | None,
    skip_dependencies: bool = False,
) -> dict[str, Any]:
    install_root = _ensure_safe_root(install_root, "install root")
    state = _load_state(install_root)
    if not state:
        raise InstallError("LitAnchor installation state is missing.")
    versions = [str(item) for item in state.get("installed_versions", [])]
    active = str(state.get("active_version"))
    candidates = [version for version in versions if version != active]
    target_version = target_version or (candidates[-1] if candidates else None)
    if not target_version or target_version not in versions:
        raise InstallError("No installed rollback target is available.")
    version_root = install_root / "versions" / target_version
    manifest = _load_json(version_root / MANIFEST_NAME)
    target = _ensure_safe_root(skills_root, "Skills root") / manifest["payload"]["skill_directory_name"]
    _assert_owned_active_skill(target, state, allow_missing=False)
    active_hash = _activate_skill(version_root / "skill", target, state)
    python = _sync_dependencies(
        install_root=install_root,
        version_root=version_root,
        include_mineru=bool(state.get("mineru_dependency_installed")),
        skip_dependencies=skip_dependencies,
    )
    state.update(
        {
            "active_version": target_version,
            "active_skill_path": str(target.resolve()),
            "active_skill_sha256": active_hash,
            "venv_python": str(python),
        }
    )
    _atomic_write_json(_state_path(install_root), state)
    _update_local_config(
        install_root=install_root,
        config_path=config_path,
        version=target_version,
        python=python,
        skill_target=target,
        include_mineru=bool(state.get("mineru_dependency_installed")),
    )
    return {
        "status": "completed",
        "action": "rollback",
        "from_version": active,
        "version": target_version,
        "skill_path": str(target),
    }


def uninstall(
    *,
    install_root: Path,
    skills_root: Path,
    config_path: Path,
    confirm: bool,
    remove_config: bool,
) -> dict[str, Any]:
    if not confirm:
        raise InstallError("Uninstall requires --confirm.")
    install_root = _ensure_safe_root(install_root, "install root")
    state = _load_state(install_root)
    if not state or not (install_root / MARKER_NAME).is_file():
        raise InstallError("Refusing uninstall without a LitAnchor ownership marker and state receipt.")
    manifest_path = install_root / MANIFEST_NAME
    manifest = _load_json(manifest_path) if manifest_path.is_file() else None
    directory_name = (
        manifest["payload"]["skill_directory_name"]
        if manifest
        else "litanchor-paper-reading"
    )
    target = _ensure_safe_root(skills_root, "Skills root") / directory_name
    _assert_owned_active_skill(target, state, allow_missing=True)
    removed: list[str] = []
    if target.exists():
        shutil.rmtree(target)
        removed.append(str(target))
    for child in (
        install_root / ".venv",
        install_root / "versions",
        install_root / "bin",
        install_root / ".staging",
    ):
        if child.exists() and _inside(child.resolve(), install_root):
            shutil.rmtree(child)
            removed.append(str(child))
    for child in (manifest_path, _state_path(install_root), install_root / MARKER_NAME):
        if child.is_file():
            child.unlink()
            removed.append(str(child))
    if remove_config and config_path.is_file():
        if config_path.resolve().parent != install_root:
            raise InstallError("Refusing to remove a configuration outside the managed install root.")
        config_path.unlink()
        removed.append(str(config_path))
    return {
        "status": "completed",
        "action": "uninstall",
        "removed": removed,
        "config_preserved": config_path.is_file(),
    }


def status(install_root: Path) -> dict[str, Any]:
    install_root = _ensure_safe_root(install_root, "install root")
    state = _load_state(install_root)
    if not state:
        return {"status": "not_installed", "install_root": str(install_root)}
    target = Path(state["active_skill_path"])
    observed_hash = tree_sha256(target) if target.is_dir() else None
    return {
        "status": "installed" if observed_hash == state.get("active_skill_sha256") else "needs_repair",
        **state,
        "observed_skill_sha256": observed_hash,
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="LitAnchor user-local installation manager")
    parser.add_argument("--source-root", type=Path, default=_source_root())
    parser.add_argument("--install-root", type=Path, default=default_install_root())
    parser.add_argument("--skills-root", type=Path, default=default_skills_root())
    parser.add_argument("--config-path", type=Path)
    subparsers = parser.add_subparsers(dest="action", required=True)
    for name in ("install", "upgrade"):
        command = subparsers.add_parser(name)
        command.add_argument("--include-mineru", action="store_true")
        command.add_argument("--skip-dependencies", action="store_true", help=argparse.SUPPRESS)
    repair_parser = subparsers.add_parser("repair")
    repair_parser.add_argument("--include-mineru", action="store_true")
    repair_parser.add_argument("--skip-dependencies", action="store_true", help=argparse.SUPPRESS)
    rollback_parser = subparsers.add_parser("rollback")
    rollback_parser.add_argument("--version")
    rollback_parser.add_argument("--skip-dependencies", action="store_true", help=argparse.SUPPRESS)
    uninstall_parser = subparsers.add_parser("uninstall")
    uninstall_parser.add_argument("--confirm", action="store_true")
    uninstall_parser.add_argument("--remove-config", action="store_true")
    subparsers.add_parser("status")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    install_root = args.install_root.expanduser().resolve()
    skills_root = args.skills_root.expanduser().resolve()
    config_path = (
        args.config_path.expanduser().resolve()
        if args.config_path
        else install_root / CONFIG_NAME
    )
    try:
        if args.action in {"install", "upgrade"}:
            result = install(
                source_root=args.source_root,
                install_root=install_root,
                skills_root=skills_root,
                config_path=config_path,
                include_mineru=args.include_mineru,
                skip_dependencies=args.skip_dependencies,
                action=args.action,
            )
        elif args.action == "repair":
            result = repair(
                install_root=install_root,
                skills_root=skills_root,
                config_path=config_path,
                skip_dependencies=args.skip_dependencies,
                include_mineru=args.include_mineru,
            )
        elif args.action == "rollback":
            result = rollback(
                install_root=install_root,
                skills_root=skills_root,
                config_path=config_path,
                target_version=args.version,
                skip_dependencies=args.skip_dependencies,
            )
        elif args.action == "uninstall":
            result = uninstall(
                install_root=install_root,
                skills_root=skills_root,
                config_path=config_path,
                confirm=args.confirm,
                remove_config=args.remove_config,
            )
        else:
            result = status(install_root)
        print(json.dumps(result, ensure_ascii=True, indent=2))
        return 0 if result["status"] not in {"needs_repair"} else 2
    except InstallError as exc:
        print(json.dumps({"status": "blocked", "error": str(exc)}, ensure_ascii=True), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
