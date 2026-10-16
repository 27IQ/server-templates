"""Exercise the real installers; redirect systemd operations into a temporary directory."""

import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
BASH = Path("C:/Program Files/Git/bin/bash.exe") if os.name == "nt" else shutil.which("bash")


def shell_path(path):
    path = Path(path).resolve()
    return f"/{path.drive[0].lower()}{path.as_posix()[2:]}" if os.name == "nt" else str(path)


@unittest.skipUnless(BASH and Path(BASH).is_file(), "Bash is required")
class TemplateInstallerTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(dir=ROOT / "tests")
        self.addCleanup(self.temp.cleanup)
        self.work = Path(self.temp.name)
        self.profile = self.work / "profile"
        self.profile.mkdir()
        shutil.copyfile(ROOT / "docker_1.21.1_neo_forge_pic/.env-template", self.profile / ".env-template")
        self.bin = self.work / "bin"
        self.bin.mkdir()
        self.units = self.work / "units"
        self.units.mkdir()
        self.log = self.work / "calls.log"
        self.wrapper("chmod", 'printf "chmod %s\\n" "$*" >> "$TEST_LOG"\n')
        self.wrapper("id", 'printf "0\\n"\n')
        self.wrapper("systemctl", 'printf "systemctl %s\\n" "$*" >> "$TEST_LOG"\n')
        self.wrapper("install", '''
destination="${@: -1}"
case "$destination" in
  /etc/systemd/system/*)
    source="${@: -2:1}"
    cp "$source" "$TEST_UNITS/${destination##*/}"
    ;;
  *) /usr/bin/install "$@" ;;
esac
''')

    def wrapper(self, name, body):
        target = self.bin / name
        target.write_text("#!/usr/bin/env bash\nset -euo pipefail\n" + body, encoding="utf-8", newline="\n")
        target.chmod(0o755)

    def run_script(self, script):
        env = {**os.environ, "TEST_LOG": shell_path(self.log), "TEST_UNITS": shell_path(self.units)}
        result = subprocess.run(
            [str(BASH), "-c", 'export PATH="$1:$PATH"; bash "$2" "$3"', "test", shell_path(self.bin), script, shell_path(self.profile)],
            cwd=ROOT, env=env, capture_output=True, text=True,
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        return result

    def test_hooks_copy_scripts_preserve_env_and_allow_owner_directory_access(self):
        self.run_script("install-template-hooks.sh")
        for name in ("auto-restart.sh", "mcron.sh", "backup.sh", "scheduled-maintenance.sh"):
            self.assertEqual((self.profile / name).read_bytes(), (ROOT / "scripts" / name).read_bytes())
        for name in ("start-mcserver.sh", "auto-restart-container-hook.sh", "mcron-container-hook.sh"):
            self.assertEqual((self.profile / "resources" / name).read_bytes(), (ROOT / "scripts" / name).read_bytes())
        self.assertTrue((self.profile / "server").is_dir())
        self.assertTrue((self.profile / "backups").is_dir())
        modes = [int(line.split()[1], 8) for line in self.log.read_text().splitlines() if line.startswith("chmod ")]
        self.assertEqual(len(modes), 2)
        for mode in modes:
            self.assertEqual(mode & 0o700, 0o700, "The directory owner needs read, write, and search permission")
        env_file = self.profile / ".env"
        original = env_file.read_bytes() + b"\n# Keep my settings\n"
        env_file.write_bytes(original)
        self.run_script("install-template-hooks.sh")
        self.assertEqual(env_file.read_bytes(), original)

    def test_schedule_uses_prism_name_interval_and_maintenance_script(self):
        self.run_script("install-template-hooks.sh")
        env_file = self.profile / ".env"
        env_file.write_text(env_file.read_text().replace('RESTART_INTERVAL="24h"', 'RESTART_INTERVAL="12h"'), encoding="utf-8", newline="\n")
        self.run_script("install-systemd-schedule.sh")
        service = (self.units / "docker_1.21.1_neo_forge_prism-maintenance.service").read_text()
        timer = (self.units / "docker_1.21.1_neo_forge_prism-maintenance.timer").read_text()
        self.assertIn(f"WorkingDirectory={shell_path(self.profile)}\n", service)
        self.assertIn(f"ExecStart={shell_path(self.profile)}/scheduled-maintenance.sh\n", service)
        self.assertIn("Requires=docker.service\n", service)
        self.assertIn("OnUnitActiveSec=12h\n", timer)
        self.assertIn("Unit=docker_1.21.1_neo_forge_prism-maintenance.service\n", timer)
        calls = self.log.read_text()
        self.assertIn("systemctl daemon-reload\n", calls)
        self.assertIn("systemctl enable --now docker_1.21.1_neo_forge_prism-maintenance.timer\n", calls)

    def test_scheduled_maintenance_runs_backup_before_restart(self):
        self.run_script("install-template-hooks.sh")
        for filename, action in (("backup.sh", "backup"), ("auto-restart.sh", "restart")):
            target = self.profile / filename
            target.write_text(f'#!/usr/bin/env bash\nprintf "{action}\\n" >> "$TEST_LOG"\n', encoding="utf-8", newline="\n")
            target.chmod(0o755)
        self.log.write_text("", encoding="utf-8")
        self.run_script(str(self.profile.relative_to(ROOT).as_posix()) + "/scheduled-maintenance.sh")
        self.assertEqual(self.log.read_text().splitlines(), ["backup", "restart"])


if __name__ == "__main__":
    unittest.main()
