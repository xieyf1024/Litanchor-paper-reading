import importlib.util
import json
import tempfile
import threading
import unittest
import zipfile
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "skills" / "litanchor-paper-reading" / "scripts" / "litanchor_setup.py"
SPEC = importlib.util.spec_from_file_location("litanchor_setup", SCRIPT)
litanchor_setup = importlib.util.module_from_spec(SPEC)
assert SPEC.loader
SPEC.loader.exec_module(litanchor_setup)


class _ZoteroHealthHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Zotero-API-Version", "3")
        self.send_header("X-Zotero-Version", "7.0")
        self.end_headers()
        self.wfile.write(b"{}")

    def log_message(self, _format, *_args):
        return


class LitAnchorSetupTests(unittest.TestCase):
    def test_discovers_and_resolves_unicode_vault_name(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            vault = root / "研究 Vault"
            (vault / ".obsidian").mkdir(parents=True)
            registry = root / "obsidian.json"
            registry.write_text(
                json.dumps({"vaults": {"abc": {"path": str(vault), "open": True}}}),
                encoding="utf-8",
            )
            discovered = litanchor_setup.discover_vaults(registry)
            self.assertEqual(discovered[0]["name"], "研究 Vault")
            self.assertEqual(
                litanchor_setup.resolve_vault_name("研究 vault", registry),
                vault.resolve(),
            )

    def test_setup_writes_contained_config_and_run_plan(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            vault = root / "论文 Vault"
            (vault / ".obsidian").mkdir(parents=True)
            config = root / "profile" / "config.json"
            result = litanchor_setup.configure(
                vault_path=vault,
                inbox=Path("LitAnchor") / "00_Inbox",
                consent_mode="always_for_eligible_files",
                config_path=config,
                create_inbox=True,
            )
            self.assertEqual(result["status"], "configured")
            payload = json.loads(config.read_text(encoding="utf-8"))
            inbox = Path(payload["obsidian"]["inbox_path"])
            self.assertTrue(inbox.is_dir())
            self.assertTrue(inbox.is_relative_to(vault.resolve()))
            plan = litanchor_setup.build_run_plan(
                paper="Example Paper",
                selector="title",
                vault_name="论文 Vault",
                config_path=config,
            )
            self.assertEqual(plan["status"], "ready_for_agent_execution")
            self.assertFalse(plan["obsidian"]["overwrite"])
            self.assertTrue(plan["mineru"]["automatic_for_eligible_files"])

    def test_direct_pdf_run_plan_needs_no_zotero_or_obsidian_config(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            source = root / "paper.pdf"
            source.write_bytes(b"%PDF-1.7\n")

            plan = litanchor_setup.build_run_plan(
                pdf_path=source,
                reading_mode="deep",
            )

            self.assertEqual(plan["status"], "ready_for_agent_execution")
            self.assertEqual(plan["source"]["type"], "user_pdf")
            self.assertEqual(plan["destination"]["type"], "standalone_markdown")
            self.assertEqual(
                Path(plan["destination"]["output_path"]),
                source.with_name("paper.litanchor.md").resolve(),
            )
            self.assertIsNone(plan["zotero"])
            self.assertIsNone(plan["obsidian"])
            self.assertIn("safe_non_overwrite_markdown_export", plan["stages"])

    def test_direct_pdf_run_plan_rejects_existing_output(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            source = root / "paper.pdf"
            output = root / "note.md"
            source.write_bytes(b"%PDF-1.7\n")
            output.write_text("existing", encoding="utf-8")

            with self.assertRaises(litanchor_setup.SetupError):
                litanchor_setup.build_run_plan(
                    pdf_path=source,
                    output_note=output,
                )

    def test_setup_rejects_inbox_outside_vault(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            vault = root / "vault"
            outside = root / "outside"
            (vault / ".obsidian").mkdir(parents=True)
            outside.mkdir()
            with self.assertRaises(litanchor_setup.SetupError):
                litanchor_setup.configure(
                    vault_path=vault,
                    inbox=outside,
                    consent_mode="never",
                    config_path=root / "config.json",
                )

    def test_setup_rejects_inbox_directly_under_whole_vault_root(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            vault = root / "vault"
            (vault / ".obsidian").mkdir(parents=True)
            with self.assertRaises(litanchor_setup.SetupError):
                litanchor_setup.configure(
                    vault_path=vault,
                    inbox=Path("00_Inbox"),
                    consent_mode="never",
                    config_path=root / "config.json",
                    create_inbox=True,
                )

    def test_doctor_uses_read_only_loopback_health_and_cleans_probe(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            vault = root / "中文 Vault"
            (vault / ".obsidian").mkdir(parents=True)
            config = root / "config.json"
            server = ThreadingHTTPServer(("127.0.0.1", 0), _ZoteroHealthHandler)
            thread = threading.Thread(target=server.serve_forever, daemon=True)
            thread.start()
            try:
                base_url = f"http://127.0.0.1:{server.server_port}/api"
                litanchor_setup.configure(
                    vault_path=vault,
                    inbox=Path("LitAnchor") / "00_Inbox",
                    consent_mode="never",
                    config_path=config,
                    create_inbox=True,
                    zotero_base_url=base_url,
                )
                report = litanchor_setup.run_doctor(config_path=config)
            finally:
                server.shutdown()
                server.server_close()
                thread.join(timeout=2)
            checks = {item["check_id"]: item for item in report["checks"]}
            self.assertEqual(checks["zotero_local_api"]["status"], "pass")
            self.assertEqual(checks["zotero_api_version"]["status"], "pass")
            self.assertEqual(checks["zotero_version"]["status"], "pass")
            self.assertEqual(checks["obsidian_write_utf8"]["status"], "pass")
            inbox = vault / "LitAnchor" / "00_Inbox"
            self.assertEqual(list(inbox.glob(".litanchor-write-probe-*")), [])

    def test_runtime_and_zotero_compatibility_use_minimums_without_maximums(self):
        self.assertEqual(
            litanchor_setup.runtime_compatibility((3, 10), is_64_bit=True)[0],
            "pass",
        )
        self.assertEqual(
            litanchor_setup.runtime_compatibility((3, 15), is_64_bit=True)[0],
            "warning",
        )
        self.assertEqual(
            litanchor_setup.runtime_compatibility((3, 9), is_64_bit=True)[0],
            "fail",
        )
        self.assertEqual(litanchor_setup.zotero_compatibility("7.0.24")[0], "pass")
        self.assertEqual(litanchor_setup.zotero_compatibility("8.0")[0], "warning")
        self.assertEqual(litanchor_setup.zotero_compatibility("6.0.37")[0], "fail")

    def test_support_bundle_uses_allowlist_and_excludes_private_values(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            secret_install = root / "Users" / "PrivateUser" / "LitAnchor"
            secret_install.mkdir(parents=True)
            config = secret_install / "config.json"
            config.write_text(
                json.dumps(
                    {
                        "installation": {
                            "version": "0.6.0-beta.1",
                            "install_root": str(secret_install),
                            "skill_path": str(root / "Secret Skills"),
                            "mineru_dependency_installed": True,
                        },
                        "obsidian": {
                            "vault_name": "PrivateVault",
                            "vault_path": str(root / "PrivateVault"),
                            "inbox_path": str(root / "PrivateVault" / "Secret Inbox"),
                        },
                    }
                ),
                encoding="utf-8",
            )
            (secret_install / "install-state.json").write_text(
                json.dumps(
                    {
                        "active_version": "0.6.0-beta.1",
                        "active_skill_sha256": "a" * 64,
                        "installed_versions": ["0.6.0-beta.1"],
                        "active_skill_path": str(root / "PrivateUser" / "skill"),
                    }
                ),
                encoding="utf-8",
            )
            report = {
                "status": "blocked",
                "setup_version": "0.6.0-beta.1",
                "config_path": str(config),
                "checks": [
                    {
                        "check_id": "python",
                        "status": "pass",
                        "observed": {
                            "version": "3.12",
                            "bits": 64,
                            "detail": "verified",
                            "executable": str(root / "PrivateUser" / "python.exe"),
                        },
                    },
                    {
                        "check_id": "obsidian_paths",
                        "status": "fail",
                        "observed": {
                            "vault": str(root / "PrivateVault"),
                            "inbox": str(root / "PrivateVault" / "Secret Inbox"),
                        },
                    },
                    {
                        "check_id": "zotero_unique_pdf",
                        "status": "fail",
                        "observed": {
                            "item_key": "SECRETKEY",
                            "pdf_path": str(root / "Private Paper.pdf"),
                            "title": "Private Paper Title",
                            "doi": "10.0000/private",
                        },
                    },
                    {
                        "check_id": "mineru_consent",
                        "status": "pass",
                        "observed": "always_for_eligible_files",
                    },
                    {
                        "check_id": "dependency_mineru",
                        "status": "pass",
                        "observed": "1.2.3",
                    },
                ],
            }
            destination = root / "support.zip"
            created = litanchor_setup.create_support_bundle(
                report=report,
                config_path=config,
                output_path=destination,
            )
            self.assertEqual(created, destination.resolve())
            with zipfile.ZipFile(created) as archive:
                self.assertEqual(
                    set(archive.namelist()), {"support-report.json", "summary.txt"}
                )
                combined = "\n".join(
                    archive.read(name).decode("utf-8") for name in archive.namelist()
                )
                payload = json.loads(archive.read("support-report.json"))
            for forbidden in (
                "PrivateUser",
                "PrivateVault",
                "Secret Inbox",
                "SECRETKEY",
                "Private Paper Title",
                "10.0000/private",
                "python.exe",
            ):
                self.assertNotIn(forbidden, combined)
            checks = {item["check_id"]: item for item in payload["checks"]}
            self.assertEqual(checks["obsidian_paths"]["error_code"], "LA-DOCTOR-OBSIDIAN_PATHS")
            self.assertNotIn("observed", checks["obsidian_paths"])
            self.assertNotIn("observed", checks["zotero_unique_pdf"])
            self.assertEqual(payload["mineru"]["route"], "automatic_for_eligible_files")
            self.assertEqual(payload["install_receipt"]["active_skill_sha256"], "a" * 64)

    def test_doctor_support_bundle_flag_does_not_require_an_output_path(self):
        args = litanchor_setup.build_parser().parse_args(
            ["doctor", "--support-bundle"]
        )
        self.assertEqual(args.command, "doctor")
        self.assertEqual(args.support_bundle, "")

    def test_doctor_reports_unavailable_zotero_as_stable_failed_check(self):
        with tempfile.TemporaryDirectory() as temporary:
            report = litanchor_setup.run_doctor(
                config_path=Path(temporary) / "missing-config.json",
                zotero_base_url="http://127.0.0.1:1/api",
                write_probe=False,
            )
            checks = {item["check_id"]: item for item in report["checks"]}
            self.assertEqual(checks["zotero_local_api"]["status"], "fail")
            self.assertEqual(report["status"], "blocked")


if __name__ == "__main__":
    unittest.main()
