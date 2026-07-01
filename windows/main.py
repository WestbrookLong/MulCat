from __future__ import annotations

from mulcat_core.desktop_app import run_desktop
from windows.platform_adapter import create_adapter


def main() -> None:
    run_desktop(create_adapter())


if __name__ == "__main__":
    main()

