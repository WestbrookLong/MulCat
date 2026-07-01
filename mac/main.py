from __future__ import annotations

from mac.platform_adapter import create_adapter
from mulcat_core.desktop_app import run_desktop


def main() -> None:
    run_desktop(create_adapter())


if __name__ == "__main__":
    main()

