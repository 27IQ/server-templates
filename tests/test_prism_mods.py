import hashlib
import importlib.util
import io
import json
from pathlib import Path
import tempfile
import unittest
import zipfile
from unittest.mock import patch
from urllib.parse import parse_qs, urlparse


SCRIPT = Path(__file__).resolve().parents[1] / "docker_1.21.1_neo_forge_pic/resources/prism-mods.py"
spec = importlib.util.spec_from_file_location("prism_mods", SCRIPT)
prism = importlib.util.module_from_spec(spec)
if SCRIPT.exists():
    spec.loader.exec_module(prism)

jar_buffer = io.BytesIO()
with zipfile.ZipFile(jar_buffer, "w") as archive:
    archive.writestr("META-INF/MANIFEST.MF", "Manifest-Version: 1.0\n")
JAR = jar_buffer.getvalue()
SHA512 = hashlib.sha512(JAR).hexdigest()
ENTRY = {"name": "Example", "url": "https://modrinth.com/mod/example", "version": "1.0", "filename": "example-1.0.jar"}
FILE = {"filename": "example-1.0.jar", "url": "https://cdn.modrinth.com/example.jar", "hashes": {"sha512": SHA512}}
CF_FILE = {"id": 456, "name": "example-1.0.jar", "filesize": len(JAR), "versions": ["1.21.1", "NeoForge"]}


class PrismModsTests(unittest.TestCase):
    def setUp(self):
        self.assertTrue(SCRIPT.is_file(), "Prism JSON installer has not been implemented")
        self.temp = tempfile.TemporaryDirectory(dir=Path(__file__).parent)
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.manifest = self.root / "mods.json"
        self.manifest.write_text(json.dumps([ENTRY]), encoding="utf-8")
        self.excluded = self.root / "excluded-mods.txt"
        self.excluded.write_text("# client mods\n", encoding="utf-8")
        self.server = self.root / "server"

    def api(self, url, headers=None):
        parsed = urlparse(url)
        if parsed.path == "/v2/project/example":
            return {"server_side": "required"}
        if parsed.path == "/v2/project/example/version":
            self.assertEqual(parse_qs(parsed.query), {"loaders": ['["neoforge"]'], "game_versions": ['["1.21.1"]']})
            return [{"version_number": "9.0", "files": [{**FILE, "filename": "example-9.0.jar"}]}, {"version_number": "1.0", "files": [FILE]}]
        self.fail(f"Unexpected API request: {url}")

    def install(self):
        return prism.install_mods(self.manifest, self.server, self.excluded, "1.21.1")

    def test_downloads_exact_exported_filename_and_restarts_offline(self):
        with patch.object(prism, "get_json", side_effect=self.api), patch.object(prism, "urlopen", return_value=io.BytesIO(JAR)):
            self.install()
        self.assertEqual((self.server / "mods/example-1.0.jar").read_bytes(), JAR)
        with patch.object(prism, "get_json", side_effect=AssertionError("Restart should use verified local files")):
            self.install()

    def test_prism_index_metadata_is_skipped_while_mods_are_installed(self):
        self.manifest.write_text(json.dumps([{"name": ".index", "filename": ".index"}, ENTRY]), encoding="utf-8")
        with patch.object(prism, "get_json", side_effect=self.api), patch.object(prism, "urlopen", return_value=io.BytesIO(JAR)):
            self.install()
        self.assertEqual(self.server.joinpath("mods/example-1.0.jar").read_bytes(), JAR)
        state = json.loads(self.server.joinpath(".prism-mods-state.json").read_text())
        self.assertEqual(state["files"], {"example-1.0.jar": SHA512})

    def test_index_only_export_does_not_import_an_empty_pack(self):
        self.manifest.write_text(json.dumps([{"name": ".index", "filename": ".index"}]), encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "No mod jars"):
            self.install()
        self.assertFalse(self.server.joinpath(".prism-mods-state.json").exists())

    def test_index_skip_does_not_bypass_jar_filename_validation(self):
        for filename in ("../escape.jar", ".hidden.jar", ".index/escape.jar"):
            with self.subTest(filename=filename):
                self.manifest.write_text(json.dumps([{"filename": ".index"}, {**ENTRY, "filename": filename}]), encoding="utf-8")
                with self.assertRaisesRegex(ValueError, repr(filename).replace(".", r"\.")):
                    self.install()

    def test_rejects_hash_mismatch_without_committing_install_state(self):
        with patch.object(prism, "get_json", side_effect=self.api), patch.object(prism, "urlopen", return_value=io.BytesIO(b"corrupt")):
            with self.assertRaisesRegex(ValueError, "[Hh]ash"):
                self.install()
        self.assertFalse((self.server / "mods/example-1.0.jar").exists())
        self.assertFalse((self.server / ".prism-mods-state.json").exists())

    def test_missing_exported_file_never_falls_back_to_latest(self):
        entry = {**ENTRY, "filename": "missing.jar"}
        with patch.object(prism, "get_json", side_effect=self.api):
            with self.assertRaisesRegex(ValueError, "missing.jar"):
                prism.resolve_mod(entry, "1.21.1")

    def test_excluded_mod_does_not_need_a_url(self):
        self.manifest.write_text(json.dumps([{"name": "Client", "filename": "client.jar"}]), encoding="utf-8")
        self.excluded.write_text("client.jar\n", encoding="utf-8")
        with patch.object(prism, "get_json", side_effect=AssertionError("Excluded mod must not use network")):
            self.install()
        self.assertEqual(list((self.server / "mods").glob("*.jar")), [])

    def test_missing_filename_is_actionable(self):
        self.manifest.write_text(json.dumps([{"name": "Example", "url": ENTRY["url"]}]), encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "[Ff]ile ?[Nn]ame|filename"):
            self.install()

    def test_rejects_traversal_and_duplicate_filenames(self):
        for entries in ([{**ENTRY, "filename": "../escape.jar"}], [ENTRY, ENTRY]):
            with self.subTest(entries=entries):
                self.manifest.write_text(json.dumps(entries), encoding="utf-8")
                with self.assertRaises(ValueError):
                    self.install()
        self.assertFalse((self.server / "escape.jar").exists())

    def test_rejects_empty_list_and_instance_component_json(self):
        for data in ([], {"components": []}):
            with self.subTest(data=data):
                self.manifest.write_text(json.dumps(data), encoding="utf-8")
                with self.assertRaisesRegex(ValueError, "Export List"):
                    self.install()

    def test_reexport_removes_only_previously_managed_jars(self):
        with patch.object(prism, "get_json", side_effect=self.api), patch.object(prism, "urlopen", return_value=io.BytesIO(JAR)):
            self.install()
        manual = self.server / "mods/manual.jar"
        manual.write_bytes(b"manual")
        self.excluded.write_text("example-1.0.jar\n", encoding="utf-8")
        self.install()
        self.assertFalse((self.server / "mods/example-1.0.jar").exists())
        self.assertEqual(manual.read_bytes(), b"manual")

    def test_curseforge_resolves_exact_filename_without_credentials(self):
        def api(url, headers=None):
            self.assertIsNone(headers)
            self.assertEqual(url, "https://api.cfwidget.com/minecraft/mc-mods/example")
            return {"id": 123, "files": [{**CF_FILE, "id": 999, "name": "example-9.0.jar"}, CF_FILE], "download": {**CF_FILE, "name": "example-9.0.jar"}}
        with patch.dict(prism.os.environ, {}, clear=True), patch.object(prism, "get_json", side_effect=api):
            result = prism.resolve_mod({**ENTRY, "url": "https://www.curseforge.com/minecraft/mc-mods/example"}, "1.21.1")
        self.assertEqual(result["url"], "https://www.curseforge.com/api/v1/mods/123/files/456/download")
        self.assertEqual(result["size"], len(JAR))

    def test_curseforge_numeric_project_without_credentials(self):
        def api(url, headers=None):
            self.assertEqual(url, "https://api.cfwidget.com/123")
            self.assertIsNone(headers)
            return {"id": 123, "files": [CF_FILE]}
        with patch.dict(prism.os.environ, {}, clear=True), patch.object(prism, "get_json", side_effect=api):
            result = prism.resolve_mod({**ENTRY, "url": "https://www.curseforge.com/projects/123"}, "1.21.1")
        self.assertEqual(result["url"], "https://www.curseforge.com/api/v1/mods/123/files/456/download")

    def test_curseforge_never_uses_latest_or_incompatible_file(self):
        for file in ({**CF_FILE, "name": "example-9.0.jar"}, {**CF_FILE, "versions": ["1.20.1", "NeoForge"]}, {**CF_FILE, "versions": ["1.21.1", "Fabric"]}):
            with self.subTest(file=file), patch.object(prism, "get_json", return_value={"id": 123, "files": [file], "download": file}):
                with self.assertRaisesRegex(ValueError, "example-1.0.jar"):
                    prism.resolve_mod({**ENTRY, "url": "https://www.curseforge.com/projects/123"}, "1.21.1")

    def test_curseforge_download_checks_size_and_jar_instead_of_requiring_hash(self):
        target = self.root / "example.jar"
        file = {"url": "https://www.curseforge.com/api/v1/mods/123/files/456/download", "size": len(JAR)}
        with patch.object(prism, "urlopen", return_value=io.BytesIO(JAR)):
            prism.download_file(file, target)
        self.assertEqual(target.read_bytes(), JAR)

    def test_curseforge_download_rejects_html_and_wrong_size(self):
        corrupt_jar = JAR.replace(b"Manifest-Version", b"Xanifest-Version")
        for data, size in ((b"<html>blocked download</html>", 29), (JAR, len(JAR) + 1), (corrupt_jar, len(JAR))):
            with self.subTest(data=data):
                target = self.root / "bad.jar"
                with patch.object(prism, "urlopen", return_value=io.BytesIO(data)):
                    with self.assertRaises(ValueError):
                        prism.download_file({"url": "https://www.curseforge.com/api/v1/mods/123/files/456/download", "size": size}, target)
                self.assertFalse(target.exists())
                self.assertFalse(target.with_suffix(".jar.part").exists())

    def test_changed_cached_jar_is_downloaded_again(self):
        with patch.object(prism, "get_json", side_effect=self.api), patch.object(prism, "urlopen", return_value=io.BytesIO(JAR)):
            self.install()
        self.server.joinpath("mods/example-1.0.jar").write_bytes(b"corrupt")
        with patch.object(prism, "get_json", side_effect=self.api), patch.object(prism, "urlopen", return_value=io.BytesIO(JAR)):
            self.install()
        self.assertEqual(self.server.joinpath("mods/example-1.0.jar").read_bytes(), JAR)

    def test_failed_import_does_not_leave_partial_mods_for_next_start(self):
        self.manifest.write_text(json.dumps([ENTRY, {**ENTRY, "filename": "missing.jar"}]), encoding="utf-8")
        with patch.object(prism, "get_json", side_effect=self.api), patch.object(prism, "urlopen", return_value=io.BytesIO(JAR)):
            with self.assertRaisesRegex(ValueError, "missing.jar"):
                self.install()
        self.assertEqual(list(self.server.joinpath("mods").glob("*.jar")), [])
        self.assertFalse(self.server.joinpath(".prism-mods-state.json").exists())

    def test_failed_upgrade_preserves_previous_jars_and_state(self):
        with patch.object(prism, "get_json", side_effect=self.api), patch.object(prism, "urlopen", return_value=io.BytesIO(JAR)):
            self.install()
        old_state = self.server.joinpath(".prism-mods-state.json").read_bytes()
        self.manifest.write_text(json.dumps([{**ENTRY, "filename": "example-2.0.jar"}, {**ENTRY, "filename": "missing.jar"}]), encoding="utf-8")
        with patch.object(prism, "get_json", return_value=[{"files": [{**FILE, "filename": "example-2.0.jar"}]}]), patch.object(prism, "urlopen", return_value=io.BytesIO(JAR)):
            with self.assertRaisesRegex(ValueError, "missing.jar"):
                self.install()
        self.assertEqual(self.server.joinpath("mods/example-1.0.jar").read_bytes(), JAR)
        self.assertFalse(self.server.joinpath("mods/example-2.0.jar").exists())
        self.assertEqual(self.server.joinpath(".prism-mods-state.json").read_bytes(), old_state)

    def test_successful_upgrade_replaces_previous_managed_version(self):
        with patch.object(prism, "get_json", side_effect=self.api), patch.object(prism, "urlopen", return_value=io.BytesIO(JAR)):
            self.install()
        self.manifest.write_text(json.dumps([{**ENTRY, "filename": "example-2.0.jar"}]), encoding="utf-8")
        with patch.object(prism, "get_json", return_value=[{"files": [{**FILE, "filename": "example-2.0.jar"}]}]), patch.object(prism, "urlopen", return_value=io.BytesIO(JAR)):
            self.install()
        self.assertFalse(self.server.joinpath("mods/example-1.0.jar").exists())
        self.assertEqual(self.server.joinpath("mods/example-2.0.jar").read_bytes(), JAR)
        state = json.loads(self.server.joinpath(".prism-mods-state.json").read_text())
        self.assertEqual(state["files"], {"example-2.0.jar": SHA512})

    def test_manual_jar_with_unsupported_homepage_is_preserved(self):
        self.server.joinpath("mods").mkdir(parents=True)
        self.server.joinpath("mods/example-1.0.jar").write_bytes(JAR)
        self.manifest.write_text(json.dumps([{**ENTRY, "url": "https://example.org/mod"}]), encoding="utf-8")
        self.install()
        self.assertEqual(self.server.joinpath("mods/example-1.0.jar").read_bytes(), JAR)

    def test_config_updates_existing_properties_and_escapes_values(self):
        self.server.mkdir()
        props = self.server / "server.properties"
        props.write_text("motd=old\nlevel-name=my-world\nenable-rcon=false\nmotd=duplicate\n", encoding="utf-8")
        prism.configure_server(self.server, {"RCON_PWD": "secret\\pass", "MOTD": "Hello\nworld", "MEMORY": "8G", "JAVA_ARGS": "-XX:+UseZGC"})
        content = props.read_text(encoding="utf-8")
        self.assertIn("motd=Hello\\nworld\n", content)
        self.assertEqual(content.count("motd="), 1)
        self.assertIn("level-name=my-world\n", content)
        self.assertIn("enable-rcon=true\n", content)
        self.assertIn("rcon.password=secret\\\\pass\n", content)
        self.assertEqual(self.server.joinpath("user_jvm_args.txt").read_text(), "-Xms8G\n-Xmx8G\n-XX:+UseZGC\n")


if __name__ == "__main__":
    unittest.main()
