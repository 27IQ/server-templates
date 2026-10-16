# Prism NeoForge server profile

Minecraft **1.21.1**, NeoForge **21.1.259**, and GraalVM Java **21**.
This profile installs NeoForge directly, then downloads your individual mods from a Prism Launcher JSON mod list. No published server pack is needed.

## Export from Prism

1. Edit your instance and open **Mods**.
2. Select the enabled mods you want to export, then choose **Export List**.
3. Select **JSON** and enable **URL** and **File Name**. Version and authors are optional.
4. Save the result as `mods.json` in this profile directory. `mods.example.json` shows the shape; replace its example with your actual export.
5. Put client-only mods in `excluded-mods.txt`, one exact exported name or jar filename per line. The JSON list has no reliable client/server classification, so review it before starting a dedicated server.

The downloader supports Modrinth project links and CurseForge project links (including numeric `/projects/<id>` URLs). It looks for the **exact exported filename** among releases for Minecraft 1.21.1 and NeoForge. Modrinth downloads use the platform's checksum. CurseForge downloads use public [CFWidget metadata](https://cfwidget.com/) to identify the file, then download directly from CurseForge without an API key. CFWidget supplies file sizes rather than checksums, so these downloads are checked for the expected size and JAR/ZIP integrity. It fails with an explanation if the file cannot be resolved; it never substitutes a newer release. All required dependencies must also be included in your export.

Prism exports a mod's homepage as its URL, which can sometimes be a GitHub or author website. For these entries, replace `url` with the correct Modrinth/CurseForge project link, or manually copy the exact exported jar into `server/mods/` before starting. If CFWidget cannot resolve a project slug, try `https://www.curseforge.com/projects/<id>` using the Project ID shown on its CurseForge page. Public metadata can be unavailable or stale; manual copies remain available for those cases and for downloads blocked by CurseForge. These locally supplied jars are trusted as supplied.

## Start the server

From the repository root, on the Linux Docker host:

```bash
./install-template-hooks.sh ./docker_1.21.1_neo_forge_pic
cd docker_1.21.1_neo_forge_pic
# Edit .env: change RCON_PWD, and adjust memory, MOTD, ports, whitelist, etc.
# If needed, create server/mods/ and place manually downloaded jars there.
docker compose up -d --build
docker compose logs -f
```

No API key or CurseForge account is needed. Existing API-key entries in `.env` are unused and can be removed.

The first start seeds `SERVER_DIR` (default `./server`) with NeoForge and the shared hooks, downloads the mods, applies the `.env` server settings, and starts Java. As with the other profiles, startup writes `eula=true`; running this server means accepting the [Minecraft EULA](https://www.minecraft.net/eula). RCON is available to the shared scripts inside the container; only the Minecraft game port is published.

Copy any server-relevant instance files such as `config/`, `defaultconfigs/`, `kubejs/`, and `scripts/` into `SERVER_DIR` before starting. A mod-list JSON does not contain pack configuration, scripts, resource packs, or worlds. Whitelisting defaults to enabled; add players with `./mcron.sh 'whitelist add PlayerName'` after startup.

## Updates, restarts, and backups

Stop the server before replacing `mods.json`, editing exclusions, or copying new configuration, then start it again with `docker compose up -d --force-recreate`. Recreating ensures that bind-mounted JSON and exclusion files are refreshed even if your editor replaced them. For `.env` changes, recreate the container too. An image rebuild is needed only when changing the Dockerfile or bundled startup scripts.

Successful imports record jar checksums in `server/.prism-mods-state.json`. Unchanged, verified jars allow offline restarts. Missing or changed managed jars are resolved and downloaded again. A successful changed export removes jars managed by the previous import that are no longer selected; jars outside the import remain untouched. A failed import prevents Java from starting and keeps the previous import state for retry.

Use a fresh `SERVER_DIR` when switching to another pack or NeoForge version: the shared entrypoint seeds an existing directory only when `start.sh` is absent.

The existing host helpers work as usual:

```bash
./mcron.sh 'list'
./backup.sh
./auto-restart.sh
../install-systemd-schedule.sh .
```

Shared backups exclude jars. Keep `mods.json`, `excluded-mods.txt`, `.env`, and any manually supplied jars separately so you can restore the pack.

To run downloader tests from the repository root:

```bash
python3 -m unittest discover -s tests -v
```

References: [Prism's JSON export implementation](https://github.com/PrismLauncher/PrismLauncher/blob/develop/launcher/modplatform/helpers/ExportToModList.cpp), [NeoForge server installation](https://docs.neoforged.net/user/docs/server/), [Modrinth versions API](https://docs.modrinth.com/api/operations/getprojectversions/), [CFWidget public metadata](https://cfwidget.com/).
