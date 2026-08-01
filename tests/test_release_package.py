import importlib.util
import json
import tempfile
import unittest
import zipfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "tools" / "build_release.py"
SPEC = importlib.util.spec_from_file_location("build_release", SCRIPT)
build_release = importlib.util.module_from_spec(SPEC)
assert SPEC.loader
SPEC.loader.exec_module(build_release)


class ReleasePackageTests(unittest.TestCase):
    def test_builds_versioned_zip_with_manifest_and_no_private_artifacts(self):
        with tempfile.TemporaryDirectory() as temporary:
            result = build_release.build_release(Path(temporary), ROOT)
            archive = Path(result["archive"])
            self.assertTrue(archive.is_file())
            self.assertEqual(
                build_release.sha256_file(archive),
                result["archive_sha256"],
            )
            with zipfile.ZipFile(archive) as package:
                names = package.namelist()
                self.assertTrue(any(name.endswith("/litanchor-install.json") for name in names))
                self.assertTrue(any(name.endswith("/package-manifest.json") for name in names))
                self.assertTrue(any(name.endswith("/README_EN.md") for name in names))
                self.assertTrue(any(name.endswith("/docs/ROADMAP.md") for name in names))
                self.assertFalse(any(name.casefold().endswith(".pdf") for name in names))
                self.assertFalse(any("/runtime/" in name for name in names))
                self.assertFalse(any("examples/v0.4.1" in name for name in names))
            manifest = json.loads(
                Path(result["package_manifest"]).read_text(encoding="utf-8")
            )
            self.assertGreater(manifest["files"].__len__(), 20)


if __name__ == "__main__":
    unittest.main()
