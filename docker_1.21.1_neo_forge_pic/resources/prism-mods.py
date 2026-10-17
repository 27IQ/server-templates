#!/usr/bin/env python3
"""Install exact jar filenames from Prism Launcher's Export List JSON."""

import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import sys
import tempfile
import zipfile
import zlib
from urllib.error import HTTPError, URLError
from urllib.parse import quote, urlencode, urlparse
from urllib.request import Request, urlopen


USER_AGENT = "server-templates/prism-profile/1.0"


def get_json(url, headers=None):
    request = Request(url, headers={"User-Agent": USER_AGENT, **(headers or {})})
    with urlopen(request, timeout=60) as response:
        return json.load(response)


def safe_filename(filename):
    if (not isinstance(filename, str) or not filename.endswith(".jar")
            or any(char in filename for char in '/\\:\x00\n\r') or filename.startswith(".")):
        raise ValueError(f"Invalid filename {filename!r}; export with File Name enabled in Prism.")
    return filename


def resolve_mod(entry, game_version):
    filename = safe_filename(entry.get("filename"))
    parsed = urlparse(entry.get("url", ""))
    parts = parsed.path.strip("/").split("/")
    if parsed.scheme == "https" and parsed.hostname in ("modrinth.com", "www.modrinth.com") and len(parts) >= 2 and parts[0] == "mod":
        query = urlencode({"loaders": json.dumps(["neoforge"]), "game_versions": json.dumps([game_version])})
        versions = get_json(f"https://api.modrinth.com/v2/project/{quote(parts[1], safe='')}/version?{query}")
        for version in versions:
            for file in version["files"]:
                if file["filename"] == filename:
                    return file
    elif parsed.scheme == "https" and parsed.hostname in ("curseforge.com", "www.curseforge.com"):
        if len(parts) >= 2 and parts[0] == "projects" and parts[1].isdigit():
            project_path = parts[1]
        elif len(parts) >= 3 and parts[:2] == ["minecraft", "mc-mods"]:
            project_path = "/".join(quote(part, safe="") for part in parts[:3])
        else:
            raise ValueError(f"{filename}: unsupported CurseForge project URL.")
        # CFWidget provides public project/file metadata without credentials.
        # Deliberately inspect files, never its "download" (latest-file) shortcut.
        try:
            project = get_json(f"https://api.cfwidget.com/{project_path}")
        except HTTPError as error:
            raise ValueError(f"{filename}: public CurseForge metadata lookup failed (HTTP {error.code}). Try a numeric https://www.curseforge.com/projects/<id> URL or copy the jar into server/mods manually.") from error
        project_id = project.get("id")
        if not isinstance(project_id, int) or project_id <= 0:
            raise ValueError(f"{filename}: public CurseForge metadata is unavailable; retry later or copy the jar into server/mods manually.")
        for file in project.get("files", []):
            versions = file.get("versions", [])
            if file.get("name") == filename and game_version in versions and "NeoForge" in versions:
                file_id = file.get("id")
                size = file.get("filesize")
                if not isinstance(file_id, int) or file_id <= 0 or not isinstance(size, int) or size <= 0:
                    raise ValueError(f"{filename}: public CurseForge file metadata is incomplete.")
                return {"filename": filename, "url": f"https://www.curseforge.com/api/v1/mods/{project_id}/files/{file_id}/download", "size": size}
    else:
        raise ValueError(f"{filename}: missing or unsupported project URL. Export with URL enabled, use a Modrinth/CurseForge project URL, or copy the jar into server/mods manually.")
    raise ValueError(f"{filename}: exact file not found for Minecraft {game_version} / NeoForge. No newer version was substituted.")


def file_hash(path, algorithm="sha512"):
    digest = hashlib.new(algorithm)
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def download_file(file, target):
    if urlparse(file["url"]).scheme != "https":
        raise ValueError(f"{target.name}: download URL must use HTTPS.")
    hashes = file.get("hashes", {})
    algorithm = next((name for name in ("sha512", "sha1", "md5") if hashes.get(name)), None)
    size = file.get("size")
    if algorithm is None and (not isinstance(size, int) or size <= 0):
        raise ValueError(f"{target.name}: download metadata contains no supported hash or file size.")
    temporary = target.with_suffix(".jar.part")
    try:
        request = Request(file["url"], headers={"User-Agent": USER_AGENT})
        with urlopen(request, timeout=120) as source, temporary.open("wb") as destination:
            shutil.copyfileobj(source, destination)
        if size is not None and temporary.stat().st_size != size:
            raise ValueError(f"Size mismatch for {target.name}; download is incomplete or not the expected jar.")
        if algorithm and file_hash(temporary, algorithm).lower() != hashes[algorithm].lower():
            raise ValueError(f"Hash mismatch for {target.name}; refusing to start the server.")
        try:
            with zipfile.ZipFile(temporary) as archive:
                if not archive.namelist() or archive.testzip() is not None:
                    raise ValueError(f"Invalid or corrupt jar: {target.name}")
        except (zipfile.BadZipFile, RuntimeError, NotImplementedError, zlib.error) as error:
            raise ValueError(f"Invalid jar for {target.name}; the download may be an HTML error page.") from error
        temporary.replace(target)
    finally:
        temporary.unlink(missing_ok=True)


def install_mods(manifest_path, server_dir, excluded_path, game_version):
    entries = json.loads(manifest_path.read_text(encoding="utf-8-sig"))
    if not isinstance(entries, list) or not entries:
        raise ValueError("Expected a non-empty Prism Mods > Export List > JSON array, with URL and File Name enabled.")
    exclusions = {line.strip() for line in excluded_path.read_text(encoding="utf-8-sig").splitlines() if line.strip() and not line.lstrip().startswith("#")}
    selected = []
    seen = set()
    for entry in entries:
        if not isinstance(entry, dict):
            raise ValueError("Each Export List entry must be a JSON object.")
        filename = entry.get("filename")
        if filename == ".index":
            print("Skipping Prism metadata directory .index", flush=True)
            continue
        filename = safe_filename(filename)
        if filename in seen:
            raise ValueError(f"Duplicate filename in export: {filename}")
        seen.add(filename)
        if filename in exclusions or entry.get("name") in exclusions:
            print(f"Excluded {filename}", flush=True)
        else:
            selected.append(entry)

    if not seen:
        raise ValueError("No mod jars found in Prism Export List JSON; select the enabled mods when exporting.")

    mods_dir = server_dir / "mods"
    mods_dir.mkdir(parents=True, exist_ok=True)
    state_path = server_dir / ".prism-mods-state.json"
    previous = json.loads(state_path.read_text(encoding="utf-8")) if state_path.exists() else {}
    old_files = previous.get("files", {})
    for filename in old_files:
        safe_filename(filename)
    signature = hashlib.sha256(json.dumps([entries, sorted(exclusions), game_version, "neoforge-v1"], sort_keys=True).encode()).hexdigest()
    if previous.get("signature") == signature and all((mods_dir / name).is_file() and file_hash(mods_dir / name) == digest for name, digest in old_files.items()):
        print("Prism mods unchanged; using verified local jars.", flush=True)
        return

    installed = {}
    # Stage downloads so a failed import cannot leave untracked jars in mods/.
    with tempfile.TemporaryDirectory(prefix=".prism-download-", dir=server_dir) as staging:
        staged_files = []
        for entry in selected:
            filename = entry["filename"]
            target = mods_dir / filename
            # A manually supplied jar also supports private mods and blocked API downloads.
            if target.is_file() and (filename not in old_files or file_hash(target) == old_files[filename]):
                print(f"Using local {filename}", flush=True)
                installed[filename] = file_hash(target)
            else:
                print(f"Resolving {filename}...", flush=True)
                staged = Path(staging) / filename
                download_file(resolve_mod(entry, game_version), staged)
                installed[filename] = file_hash(staged)
                staged_files.append(staged)
        for staged in staged_files:
            staged.replace(mods_dir / staged.name)

    # Only remove jars managed by an earlier successful import, after all downloads succeed.
    for filename in old_files.keys() - installed.keys():
        (mods_dir / filename).unlink(missing_ok=True)
    temporary = state_path.with_suffix(".json.tmp")
    temporary.write_text(json.dumps({"signature": signature, "files": installed}, indent=2) + "\n", encoding="utf-8")
    temporary.replace(state_path)


def configure_server(server_dir, environ):
    password = environ.get("RCON_PWD", "")
    if not password:
        raise ValueError("RCON_PWD must be set in .env.")
    memory = environ.get("MEMORY", "8G")
    if not re.fullmatch(r"[1-9][0-9]*[kKmMgG]?", memory):
        raise ValueError("MEMORY must be a Java heap size such as 8G.")
    settings = {
        "motd": environ.get("MOTD", "Prism NeoForge Server"),
        "enable-rcon": "true", "rcon.port": environ.get("RCON_PORT", "25575"),
        "rcon.password": password, "white-list": environ.get("ENABLE_WHITELIST", "true"),
        "difficulty": environ.get("DIFFICULTY", "hard"),
    }
    properties = server_dir / "server.properties"
    lines = properties.read_text(encoding="utf-8").splitlines() if properties.exists() else []
    lines = [line for line in lines if not any(re.match(r"^\s*" + re.escape(key) + r"\s*[=:]", line) for key in settings)]
    lines.extend(f"{key}={json.dumps(value, ensure_ascii=True)[1:-1]}" for key, value in settings.items())
    properties.write_text("\n".join(lines) + "\n", encoding="utf-8")
    (server_dir / "user_jvm_args.txt").write_text(f"-Xms{memory}\n-Xmx{memory}\n{environ.get('JAVA_ARGS', '')}\n", encoding="utf-8")
    (server_dir / "eula.txt").write_text("eula=true\n", encoding="utf-8")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, default=Path("/opt/prism/mods.json"))
    parser.add_argument("--exclude", type=Path, default=Path("/opt/prism/excluded-mods.txt"))
    parser.add_argument("--server-dir", type=Path, default=Path("/opt/mcserver"))
    args = parser.parse_args()
    try:
        configure_server(args.server_dir, os.environ)
        install_mods(args.manifest, args.server_dir, args.exclude, "1.21.1")
    except (OSError, ValueError, KeyError, TypeError, URLError) as error:
        print(f"Prism setup failed: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
