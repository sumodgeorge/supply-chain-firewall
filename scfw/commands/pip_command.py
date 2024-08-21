import os
import subprocess
import sys
from typing import Optional

from scfw.command import PackageManagerCommand
from scfw.ecosystem import ECOSYSTEM
from scfw.target import InstallTarget


class PipCommand(PackageManagerCommand):
    def __init__(self, command: list[str], executable: Optional[str] = None):
        # TODO: Deal with the fact that pip commands can specify the executable to use
        def get_executable() -> str:
            if (venv := os.environ.get("VIRTUAL_ENV")):
                return os.path.join(venv, "bin/python")
            else:
                return sys.executable

        if not command or command[0] != "pip":
            raise Exception("Malformed pip command")
        self._command = command

        if "install" not in command or any(opt in command for opt in {"-h", "--help", "--dry-run"}):
            self._install_subcommand = None
        else:
            # The index of the first token of the install subcommand, if it exists
            self._install_subcommand = command.index("install") + 1

        # TODO: Validate the given executable path
        self._executable = executable if executable else get_executable()

    def run(self):
        subprocess.run([self._executable, "-m"] + self._command)

    def would_install(self) -> list[InstallTarget]:
        def str_to_install_target(target_str: str) -> InstallTarget:
            package, _, version = target_str.rpartition('-')
            if version == target_str:
                raise Exception("Failed to parse pip install target")

            return InstallTarget(ECOSYSTEM.PIP, package, version)

        if not self._install_subcommand:
            return []

        # TODO: Make use of the `--report` option of `pip install`
        # Inserting the `--dry-run` flag at the opening of the `install` subcommand
        dry_run_command = (
            [self._executable, "-m"] + self._command[:self._install_subcommand] + ["--dry-run"] + self._command[self._install_subcommand:]
        )

        dry_run = subprocess.run(dry_run_command, text=True, check=True, capture_output=True)
        for line in dry_run.stdout.split('\n'):
            if line.startswith("Would install"):
                return list(map(str_to_install_target, line.split()[2:]))

        return []
