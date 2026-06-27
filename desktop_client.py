import os
import sys
import threading
from pathlib import Path

import webview

from profile_manager import (
    APP_DIR,
    SCRIPTS_DIR,
    ProfileError,
    delete_profile,
    generate_all_scripts,
    launch_profile,
    load_profiles,
    save_profile,
    script_path,
)


def app_root() -> Path:
    if getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"):
        return Path(sys._MEIPASS)
    return Path(__file__).resolve().parent


def ui_index_path() -> Path:
    return app_root() / "desktop_ui" / "dist" / "index.html"


def ui_url() -> str:
    dev_url = os.environ.get("MULCAT_UI_DEV_URL")
    if dev_url:
        return dev_url
    index_path = ui_index_path()
    if not index_path.exists():
        raise SystemExit(f"React desktop UI is not built: {index_path}")
    return index_path.as_uri()


class DesktopApi:
    def __init__(self) -> None:
        self.lock = threading.RLock()
        self._window: webview.Window | None = None
        self.maximized = False
        self.last_message = ""

    def _state(self) -> dict:
        return {
            "profiles": load_profiles(),
            "appDir": str(APP_DIR),
            "scriptsDir": str(SCRIPTS_DIR),
            "message": self.last_message,
        }

    def get_state(self) -> dict:
        with self.lock:
            return self._state()

    def save_profile(self, profile: dict) -> dict:
        with self.lock:
            try:
                saved = save_profile(profile)
                self.last_message = f"Saved and generated {saved['id']}."
            except ProfileError as exc:
                self.last_message = str(exc)
            except Exception as exc:
                self.last_message = f"Save failed: {exc}"
            return self._state()

    def delete_profile(self, kind: str, profile_id: str) -> dict:
        with self.lock:
            try:
                delete_profile(kind, profile_id)
                self.last_message = f"Deleted {profile_id}."
            except Exception as exc:
                self.last_message = f"Delete failed: {exc}"
            return self._state()

    def generate_all(self) -> dict:
        with self.lock:
            try:
                paths = generate_all_scripts()
                self.last_message = f"Generated {len(paths)} scripts."
            except Exception as exc:
                self.last_message = f"Generate failed: {exc}"
            return self._state()

    def read_script(self, kind: str, profile_id: str) -> dict:
        with self.lock:
            try:
                path = script_path(kind, profile_id)
                if not path.exists():
                    self.last_message = f"Script does not exist: {profile_id}."
                    return {**self._state(), "scriptText": "", "scriptPath": str(path)}
                text = path.read_text(encoding="utf-8-sig")
                return {**self._state(), "scriptText": text, "scriptPath": str(path)}
            except Exception as exc:
                self.last_message = f"Read script failed: {exc}"
                return {**self._state(), "scriptText": "", "scriptPath": ""}

    def save_script(self, kind: str, profile_id: str, text: str) -> dict:
        with self.lock:
            try:
                path = script_path(kind, profile_id)
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text(str(text), encoding="utf-8-sig")
                self.last_message = f"Saved script {profile_id}."
            except Exception as exc:
                self.last_message = f"Save script failed: {exc}"
            return self._state()

    def launch_profile(self, kind: str, profile_id: str) -> dict:
        with self.lock:
            result = launch_profile(kind, profile_id)
            self.last_message = result.message
            return self._state()

    def open_scripts_dir(self) -> dict:
        os.startfile(str(SCRIPTS_DIR))
        return self._state()

    def minimize_window(self) -> dict:
        if self._window is not None:
            self._window.minimize()
        return self._state()

    def toggle_maximize_window(self) -> dict:
        if self._window is not None:
            if self.maximized:
                self._window.restore()
                self.maximized = False
            else:
                self._window.maximize()
                self.maximized = True
        return self._state()

    def close_window(self) -> dict:
        state = self._state()

        def destroy_later() -> None:
            if self._window is not None:
                self._window.destroy()

        threading.Timer(0.05, destroy_later).start()
        return state


def main() -> None:
    if sys.platform != "win32":
        raise SystemExit("MulCat is currently implemented for Windows.")
    api = DesktopApi()
    window = webview.create_window(
        "MulCat",
        ui_url(),
        js_api=api,
        width=1280,
        height=860,
        min_size=(1120, 760),
        frameless=False,
        easy_drag=False,
        draggable=True,
        shadow=True,
        background_color="#000000",
    )
    api._window = window
    webview.start(gui="edgechromium", debug=False)


if __name__ == "__main__":
    main()
