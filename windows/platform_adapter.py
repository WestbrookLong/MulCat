from __future__ import annotations

import os
import shutil
import subprocess
from pathlib import Path

from mulcat_core.platforms import LaunchResult


class WindowsAdapter:
    name = "windows"

    def launch_script(self, script_path: Path, app_dir: Path, profile_id: str) -> LaunchResult:
        try:
            wt = shutil.which("wt.exe") or shutil.which("wt")
            if wt:
                subprocess.Popen(
                    [
                        wt,
                        "new-tab",
                        "powershell.exe",
                        "-NoExit",
                        "-ExecutionPolicy",
                        "Bypass",
                        "-File",
                        str(script_path),
                    ],
                    cwd=str(app_dir),
                    close_fds=True,
                )
            else:
                subprocess.Popen(
                    [
                        "powershell.exe",
                        "-NoExit",
                        "-ExecutionPolicy",
                        "Bypass",
                        "-File",
                        str(script_path),
                    ],
                    cwd=str(app_dir),
                    close_fds=True,
                )
            return LaunchResult(True, f"Launched {profile_id}.", str(script_path))
        except Exception as exc:
            return LaunchResult(False, f"Launch failed: {exc}", str(script_path))

    def open_directory(self, path: Path) -> None:
        os.startfile(str(path))

    def copy_text(self, text: str) -> None:
        subprocess.run(
            ["powershell.exe", "-NoProfile", "-Command", "Set-Clipboard -Value $args[0]", str(text)],
            check=True,
            capture_output=True,
            text=True,
            timeout=5,
        )

    def webview_gui(self) -> str | None:
        return "edgechromium"

    def script_encoding(self) -> str:
        return "utf-8-sig"

    def after_script_write(self, path: Path) -> None:
        return None


def create_adapter() -> WindowsAdapter:
    return WindowsAdapter()

