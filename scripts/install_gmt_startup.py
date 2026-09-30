"""Configure the uv environment for repository-local GMT and ESMF runtimes."""

from __future__ import annotations

import sys
import sysconfig
from pathlib import Path

HOOK_NAME = "zz_runtime_startup.pth"


def discover_runtime_import(project_root: Path) -> str:
    """Find the package containing gmt_runtime.py and return its import statement."""
    src_dir = project_root / "src"

    if not src_dir.is_dir():
        raise SystemExit(f"Source directory does not exist: {src_dir}")

    candidates = [
        package.name
        for package in src_dir.iterdir()
        if package.is_dir()
        and (package / "gmt_runtime.py").is_file()
        and (package / "__init__.py").is_file()
    ]

    if len(candidates) != 1:
        raise SystemExit(
            f"Expected exactly one package containing gmt_runtime.py under {src_dir}; "
            f"found: {candidates}"
        )

    return f"import {candidates[0]}.gmt_runtime\n"


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
            "        _ESMF = np.ctypeslib.load_library(\n"
            "            'esmf_fullylinked', os.path.dirname(esmfmk))\n"
            "    else:\n        _ESMF = ct.CDLL(os.path.join(libsdir,'libesmf_fullylinked.so'),",
        )
    else:
        loader_text = loader_text.replace(
            "_ESMF = np.ctypeslib.load_library('esmf_fullylinked', libsdir)",
            "_ESMF = np.ctypeslib.load_library(\n"
            "            'esmf_fullylinked', os.path.dirname(esmfmk))",
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
    hook.write_text(
        discover_runtime_import(project_root),
        encoding="utf-8",
    )
    print(f"Installed GMT startup hook: {hook}")
    patch_esmpy_for_windows(site_packages)


if __name__ == "__main__":
    main()
