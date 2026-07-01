from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Protocol


@dataclass
class LaunchResult:
    ok: bool
    message: str
    script_path: str | None = None


class PlatformAdapter(Protocol):
    name: str

    def launch_script(self, script_path: Path, app_dir: Path, profile_id: str) -> LaunchResult:
        ...

    def open_directory(self, path: Path) -> None:
        ...

    def copy_text(self, text: str) -> None:
        ...

    def webview_gui(self) -> str | None:
        ...

    def script_encoding(self) -> str:
        ...

    def after_script_write(self, path: Path) -> None:
        ...

