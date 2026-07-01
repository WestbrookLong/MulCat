from __future__ import annotations

import subprocess
import shlex
import shutil
from pathlib import Path

from mulcat_core.platforms import LaunchResult


class MacAdapter:
    name = "mac"

    def launch_script(self, script_path: Path, app_dir: Path, profile_id: str) -> LaunchResult:
        try:
            if not shutil.which("pwsh"):
                return LaunchResult(False, "Launch failed: PowerShell 7 (pwsh) is not installed.", str(script_path))
            command = " ".join(
                [
                    "cd",
                    shlex.quote(str(app_dir)),
                    "&&",
                    "pwsh",
                    "-NoExit",
                    "-ExecutionPolicy",
                    "Bypass",
                    "-File",
                    shlex.quote(str(script_path)),
                ]
            )
            subprocess.Popen(
                [
                    "osascript",
                    "-e",
                    f'tell application "Terminal" to do script {apple_script_quote(command)}',
                    "-e",
                    'tell application "Terminal" to activate',
                ],
                close_fds=True,
            )
            return LaunchResult(True, f"Launched {profile_id}.", str(script_path))
        except Exception as exc:
            return LaunchResult(False, f"Launch failed: {exc}", str(script_path))

    def open_directory(self, path: Path) -> None:
        subprocess.Popen(["open", str(path)], close_fds=True)

    def copy_text(self, text: str) -> None:
        subprocess.run(
            ["pbcopy"],
            input=str(text),
            check=True,
            capture_output=True,
            text=True,
            timeout=5,
        )

    def webview_gui(self) -> str | None:
        return "cocoa"

    def script_encoding(self) -> str:
        return "utf-8"

    def after_script_write(self, path: Path) -> None:
        path.chmod(path.stat().st_mode | 0o111)


def apple_script_quote(value: str) -> str:
    escaped = value.replace("\\", "\\\\").replace('"', '\\"')
    return f'"{escaped}"'


def create_adapter() -> MacAdapter:
    return MacAdapter()
