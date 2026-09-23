"""Install the tracked GMT startup hook into the active Python environment."""

from __future__ import annotations

import sys
import sysconfig
from pathlib import Path


HOOK_NAME = "zz_uv_gmt_gdal_pygmt.pth"
HOOK_CONTENT = "import uv_gmt_gdal_pygmt.gmt_runtime\n"


def main() -> None:
    project_root = Path(__file__).resolve().parents[1]
    expected_environment = project_root / ".venv"

    if Path(sys.prefix).resolve() != expected_environment.resolve():
        raise SystemExit(
            f"Run this script with {expected_environment / 'Scripts' / 'python.exe'}"
        )

    site_packages = Path(sysconfig.get_path("purelib"))
    hook = site_packages / HOOK_NAME
    hook.write_text(HOOK_CONTENT, encoding="utf-8")
    print(f"Installed GMT startup hook: {hook}")


if __name__ == "__main__":
    main()