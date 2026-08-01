#!/usr/bin/env python3
"""Build a deterministic LitAnchor Windows release ZIP and SHA-256 receipt."""

from __future__ import annotations

import argparse
import hashlib
import json
import zipfile
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
FIXED_ZIP_TIME = (2026, 1, 1, 0, 0, 0)


def sha256_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def release_files(root: Path = ROOT) -> list[Path]:
    fixed = [
        root / "litanchor-install.json",
        root / "install.ps1",
        root / "litanchor.ps1",
        root / "requirements.txt",
        root / "requirements-mineru.txt",
        root / "requirements-dev.txt",
        root / "README.md",
        root / "README_EN.md",
        root / "CHANGELOG.md",
        root / "LICENSE",
        root / "NOTICE.md",
        root / "THIRD_PARTY.md",
        root / "tools" / "litanchor_manager.py",
        root / "tools" / "validate_skill.py",
        root / "docs" / "INSTALLATION_REQUIREMENTS.md",
        root / "docs" / "README.md",
        root / "docs" / "ROADMAP.md",
    ]
    skill = root / "skills" / "litanchor-paper-reading"
    dynamic = [
        path
        for path in skill.rglob("*")
        if path.is_file()
        and "__pycache__" not in path.parts
        and path.suffix not in {".pyc", ".pyo"}
    ]
    files = sorted({path.resolve() for path in [*fixed, *dynamic]})
    missing = [str(path) for path in files if not path.is_file()]
    if missing:
        raise FileNotFoundError(f"Release files are missing: {missing}")
    return files


def build_package_manifest(files: list[Path], root: Path = ROOT) -> dict[str, Any]:
    return {
        "schema_version": "1.0",
        "hash_algorithm": "sha256",
        "files": [
            {
                "path": path.relative_to(root).as_posix(),
                "size": path.stat().st_size,
                "sha256": sha256_file(path),
            }
            for path in files
        ],
    }


def _write_zip_member(archive: zipfile.ZipFile, name: str, payload: bytes) -> None:
    info = zipfile.ZipInfo(name, date_time=FIXED_ZIP_TIME)
    info.compress_type = zipfile.ZIP_DEFLATED
    info.external_attr = 0o644 << 16
    archive.writestr(info, payload)


def build_release(output_dir: Path, root: Path = ROOT) -> dict[str, Any]:
    manifest = json.loads((root / "litanchor-install.json").read_text(encoding="utf-8"))
    version = str(manifest["version"])
    output_dir = output_dir.resolve()
    output_dir.mkdir(parents=True, exist_ok=True)
    files = release_files(root)
    package_manifest = build_package_manifest(files, root)
    prefix = f"LitAnchor-{version}"
    archive_path = output_dir / f"{prefix}-windows.zip"
    with zipfile.ZipFile(archive_path, mode="w") as archive:
        for path in files:
            relative = path.relative_to(root).as_posix()
            _write_zip_member(archive, f"{prefix}/{relative}", path.read_bytes())
        package_payload = (
            json.dumps(package_manifest, ensure_ascii=False, indent=2) + "\n"
        ).encode("utf-8")
        _write_zip_member(
            archive,
            f"{prefix}/package-manifest.json",
            package_payload,
        )
    archive_hash = sha256_file(archive_path)
    checksum_path = output_dir / "SHA256SUMS.txt"
    checksum_path.write_text(
        f"{archive_hash}  {archive_path.name}\n",
        encoding="utf-8",
        newline="\n",
    )
    external_manifest = output_dir / "package-manifest.json"
    external_manifest.write_text(
        json.dumps(package_manifest, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    return {
        "status": "completed",
        "version": version,
        "archive": str(archive_path),
        "archive_sha256": archive_hash,
        "checksum": str(checksum_path),
        "package_manifest": str(external_manifest),
        "file_count": len(files),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Build LitAnchor release artifacts")
    parser.add_argument("--output", type=Path, default=Path("dist"))
    args = parser.parse_args()
    print(json.dumps(build_release(args.output), ensure_ascii=True, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
