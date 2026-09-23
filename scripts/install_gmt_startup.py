"""Configure the uv environment for repository-local GMT and ESMF runtimes."""

from __future__ import annotations

import sys
import sysconfig
from pathlib import Path


HOOK_NAME = "zz_uv_gmt_gdal_pygmt.pth"
HOOK_CONTENT = "import uv_gmt_gdal_pygmt.gmt_runtime\n"


def patch_esmpy_for_windows(site_packages: Path) -> None:
    """Apply conda-forge's ESMPy 8.4 Windows loader compatibility patch."""
    constants = site_packages / "esmpy" / "api" / "constants.py"
    loader = site_packages / "esmpy" / "interface" / "loadESMF.py"

    if not constants.is_file() or not loader.is_file():
        raise SystemExit("ESMPy is not installed; run 'uv sync --locked' first.")

    constants_text = constants.read_text(encoding="utf-8")
    if "_ESMF_OS_WIN" not in constants_text:
        constants_text = constants_text.replace(
            "(_ESMF_OS_DARWIN,\n _ESMF_OS_LINUX,\n _ESMF_OS_UNICOS) = (-5,-4,-3)",
            "(_ESMF_OS_WIN,\n _ESMF_OS_DARWIN,\n _ESMF_OS_LINUX,\n _ESMF_OS_UNICOS) = (-6,-5,-4,-3)",
        )
        constants.write_text(constants_text, encoding="utf-8")

    loader_text = loader.read_text(encoding="utf-8")
    if 'if "MinGW" in esmfos:' not in loader_text:
        loader_text = loader_text.replace(
            'if "Darwin" in esmfos:',
            'if "MinGW" in esmfos:\n'
            "    constants._ESMF_OS = constants._ESMF_OS_WIN\n"
            'elif "Darwin" in esmfos:',
        )
    if "constants._ESMF_OS == constants._ESMF_OS_WIN" not in loader_text:
        loader_text = loader_text.replace(
            "    else:\n        _ESMF = ct.CDLL(os.path.join(libsdir,'libesmf_fullylinked.so'),",
            "    elif constants._ESMF_OS == constants._ESMF_OS_WIN:\n"
            "        _ESMF = np.ctypeslib.load_library('esmf_fullylinked', libsdir)\n"
            "    else:\n        _ESMF = ct.CDLL(os.path.join(libsdir,'libesmf_fullylinked.so'),",
        )
    loader.write_text(loader_text, encoding="utf-8")
    print(f"Patched ESMPy Windows loader: {loader}")


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
    patch_esmpy_for_windows(site_packages)


if __name__ == "__main__":
    main()