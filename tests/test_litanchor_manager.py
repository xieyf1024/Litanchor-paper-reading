import importlib.util
import json
import shutil
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "tools" / "litanchor_manager.py"
SPEC = importlib.util.spec_from_file_location("litanchor_manager", SCRIPT)
manager = importlib.util.module_from_spec(SPEC)
assert SPEC.loader
SPEC.loader.exec_module(manager)


class LitAnchorManagerTests(unittest.TestCase):
    def _minimal_release(self, root: Path, version: str, marker: str) -> Path:
        source = root / version
        skill = source / "skills" / "litanchor-paper-reading"
        (skill / "scripts").mkdir(parents=True)
        (skill / "SKILL.md").write_text(
            f"---\nname: litanchor-paper-reading\ndescription: Use when testing.\n---\n\n{marker}\n",
            encoding="utf-8",
        )
        (skill / "scripts" / "marker.txt").write_text(marker, encoding="utf-8")
        (source / "tools").mkdir()
        shutil.copy2(ROOT / "tools" / "litanchor_manager.py", source / "tools" / "litanchor_manager.py")
        shutil.copy2(ROOT / "litanchor.ps1", source / "litanchor.ps1")
        manifest = json.loads((ROOT / "litanchor-install.json").read_text(encoding="utf-8"))
        manifest["version"] = version
        (source / "litanchor-install.json").write_text(
            json.dumps(manifest),
            encoding="utf-8",
        )
        for name in (
            "requirements.txt",
            "requirements-mineru.txt",
            "LICENSE",
            "NOTICE.md",
            "THIRD_PARTY.md",
        ):
            shutil.copy2(ROOT / name, source / name)
        return source

    def test_install_is_idempotent_and_uninstall_preserves_config(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            install_root = root / "Local App Data" / "LitAnchor"
            skills_root = root / "Codex Home" / "skills"
            config = install_root / "config.json"
            first = manager.install(
                source_root=ROOT,
                install_root=install_root,
                skills_root=skills_root,
                config_path=config,
                include_mineru=False,
                skip_dependencies=True,
            )
            second = manager.install(
                source_root=ROOT,
                install_root=install_root,
                skills_root=skills_root,
                config_path=config,
                include_mineru=False,
                skip_dependencies=True,
            )
            self.assertEqual(first["activation"], "activated")
            self.assertEqual(second["activation"], "unchanged")
            self.assertEqual(manager.status(install_root)["status"], "installed")
            payload = json.loads(config.read_text(encoding="utf-8"))
            self.assertEqual(payload["installation"]["version"], first["version"])
            removed = manager.uninstall(
                install_root=install_root,
                skills_root=skills_root,
                config_path=config,
                confirm=True,
                remove_config=False,
            )
            self.assertTrue(removed["config_preserved"])
            self.assertTrue(config.is_file())
            self.assertFalse((skills_root / "litanchor-paper-reading").exists())

    def test_python_policy_uses_a_floor_and_probes_newer_versions(self):
        manifest = manager.load_manifest(ROOT)
        self.assertEqual(
            manager.python_compatibility(manifest, (3, 10), is_64_bit=True)["status"],
            "pass",
        )
        self.assertEqual(
            manager.python_compatibility(manifest, (3, 15), is_64_bit=True)["status"],
            "warning",
        )
        self.assertEqual(
            manager.python_compatibility(manifest, (3, 9), is_64_bit=True)["status"],
            "fail",
        )
        self.assertEqual(
            manager.python_compatibility(manifest, (3, 12), is_64_bit=False)["status"],
            "fail",
        )

    def test_install_blocks_unmanaged_existing_skill(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            install_root = root / "Local" / "LitAnchor"
            skills_root = root / "Agent" / "skills"
            unmanaged = skills_root / "litanchor-paper-reading"
            unmanaged.mkdir(parents=True)
            (unmanaged / "SKILL.md").write_text("user data", encoding="utf-8")
            with self.assertRaises(manager.InstallError):
                manager.install(
                    source_root=ROOT,
                    install_root=install_root,
                    skills_root=skills_root,
                    config_path=install_root / "config.json",
                    include_mineru=False,
                    skip_dependencies=True,
                )
            self.assertEqual((unmanaged / "SKILL.md").read_text(encoding="utf-8"), "user data")

    def test_uninstall_requires_confirmation(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            with self.assertRaises(manager.InstallError):
                manager.uninstall(
                    install_root=root / "Local" / "LitAnchor",
                    skills_root=root / "Agent" / "skills",
                    config_path=root / "Local" / "LitAnchor" / "config.json",
                    confirm=False,
                    remove_config=False,
                )

    def test_upgrade_and_rollback_activate_only_archived_versions(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            release_one = self._minimal_release(root / "releases", "0.6.0-test1", "first")
            release_two = self._minimal_release(root / "releases", "0.6.0-test2", "second")
            install_root = root / "Local" / "LitAnchor"
            skills_root = root / "Agent" / "skills"
            config = install_root / "config.json"
            manager.install(
                source_root=release_one,
                install_root=install_root,
                skills_root=skills_root,
                config_path=config,
                include_mineru=False,
                skip_dependencies=True,
            )
            manager.install(
                source_root=release_two,
                install_root=install_root,
                skills_root=skills_root,
                config_path=config,
                include_mineru=False,
                skip_dependencies=True,
                action="upgrade",
            )
            active = skills_root / "litanchor-paper-reading" / "scripts" / "marker.txt"
            self.assertEqual(active.read_text(encoding="utf-8"), "second")
            result = manager.rollback(
                install_root=install_root,
                skills_root=skills_root,
                config_path=config,
                target_version="0.6.0-test1",
                skip_dependencies=True,
            )
            self.assertEqual(result["version"], "0.6.0-test1")
            self.assertEqual(active.read_text(encoding="utf-8"), "first")

    def test_repair_restores_a_missing_managed_skill(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            install_root = root / "Local" / "LitAnchor"
            skills_root = root / "Agent" / "skills"
            config = install_root / "config.json"
            manager.install(
                source_root=ROOT,
                install_root=install_root,
                skills_root=skills_root,
                config_path=config,
                include_mineru=False,
                skip_dependencies=True,
            )
            active = skills_root / "litanchor-paper-reading"
            shutil.rmtree(active)
            result = manager.repair(
                install_root=install_root,
                skills_root=skills_root,
                config_path=config,
                skip_dependencies=True,
            )
            self.assertTrue(result["changed"])
            self.assertTrue((active / "SKILL.md").is_file())

    def test_repair_recovers_interrupted_activation_artifacts(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            install_root = root / "本地 数据" / "LitAnchor"
            skills_root = root / "Agent Skills" / "skills"
            config = install_root / "config.json"
            manager.install(
                source_root=ROOT,
                install_root=install_root,
                skills_root=skills_root,
                config_path=config,
                include_mineru=False,
                skip_dependencies=True,
            )
            active = skills_root / "litanchor-paper-reading"
            backup = active.parent / ".litanchor-paper-reading.litanchor-previous"
            staging = active.parent / ".litanchor-paper-reading.litanchor-next"
            shutil.copytree(active, backup)
            staging.mkdir()
            (staging / "partial.txt").write_text("interrupted", encoding="utf-8")
            result = manager.repair(
                install_root=install_root,
                skills_root=skills_root,
                config_path=config,
                skip_dependencies=True,
            )
            self.assertTrue(result["changed"])
            self.assertTrue((active / "SKILL.md").is_file())
            self.assertFalse(backup.exists())
            self.assertFalse(staging.exists())

    def test_upgrade_and_uninstall_preserve_vault_and_user_configuration(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            release_one = self._minimal_release(root / "releases", "0.6.0-a", "first")
            release_two = self._minimal_release(root / "releases", "0.6.0-b", "second")
            install_root = root / "Local App Data" / "LitAnchor"
            skills_root = root / "Codex Home" / "skills"
            config = install_root / "config.json"
            vault = root / "研究 Vault"
            note = vault / "LitAnchor" / "00_Inbox" / "user-note.md"
            note.parent.mkdir(parents=True)
            note.write_text("user-owned note", encoding="utf-8")
            manager.install(
                source_root=release_one,
                install_root=install_root,
                skills_root=skills_root,
                config_path=config,
                include_mineru=False,
                skip_dependencies=True,
            )
            payload = json.loads(config.read_text(encoding="utf-8"))
            payload["obsidian"] = {
                "vault_name": vault.name,
                "vault_path": str(vault),
                "inbox_path": str(note.parent),
            }
            config.write_text(json.dumps(payload), encoding="utf-8")
            manager.install(
                source_root=release_two,
                install_root=install_root,
                skills_root=skills_root,
                config_path=config,
                include_mineru=False,
                skip_dependencies=True,
                action="upgrade",
            )
            upgraded = json.loads(config.read_text(encoding="utf-8"))
            self.assertEqual(upgraded["obsidian"]["vault_name"], vault.name)
            manager.uninstall(
                install_root=install_root,
                skills_root=skills_root,
                config_path=config,
                confirm=True,
                remove_config=False,
            )
            self.assertEqual(note.read_text(encoding="utf-8"), "user-owned note")
            self.assertTrue(config.is_file())


if __name__ == "__main__":
    unittest.main()
