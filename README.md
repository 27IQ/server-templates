# Minecraft Docker Server Templates

`docker_1.10.2_forge_forever_stranded-2.0.9` is the reference template for creating more Minecraft docker templates.

The shared helper scripts live in `scripts/`:

- `scripts/auto-restart.sh`
- `scripts/mcron.sh`
- `scripts/backup.sh`
- `scripts/scheduled-maintenance.sh`
- `scripts/auto-restart-container-hook.sh`
- `scripts/mcron-container-hook.sh`

When creating or refreshing a template, install the shared scripts into that template directory:

```bash
./install-template-hooks.sh ./docker_1.10.2_forge_forever_stranded-2.0.9
```

The installer copies the host-side scripts into the template root, the container hook scripts into `resources/`, and creates `.env` from `.env-template` when `.env` does not already exist.

To remove the installed template helper files:

```bash
./remove-template-hooks.sh ./docker_1.10.2_forge_forever_stranded-2.0.9
```

Pass `--remove-env` if you also want to delete the generated `.env`:

```bash
./remove-template-hooks.sh --remove-env ./docker_1.10.2_forge_forever_stranded-2.0.9
```

To install scheduled restarts through systemd, edit the generated `.env` first:

```bash
RESTART_INTERVAL="24h"
BACKUP_ENABLED="true"
BACKUP_DIR="./backups"
```

Then create and enable the systemd service and timer:

```bash
./install-systemd-schedule.sh ./docker_1.10.2_forge_forever_stranded-2.0.9
```

The timer uses systemd `Persistent=true`, so a missed restart runs after the machine comes back online.

To remove the systemd service and timer:

```bash
./remove-systemd-schedule.sh ./docker_1.10.2_forge_forever_stranded-2.0.9
```
