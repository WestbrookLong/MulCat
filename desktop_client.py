from __future__ import annotations

import sys

from mac.main import main as mac_main
from windows.main import main as windows_main


def main() -> None:
    if sys.platform == "darwin":
        mac_main()
    else:
        windows_main()


if __name__ == "__main__":
    main()
