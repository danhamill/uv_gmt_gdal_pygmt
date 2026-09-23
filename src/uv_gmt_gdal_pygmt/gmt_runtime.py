"""Configure the native GMT runtime during Python startup on Windows."""

from __future__ import annotations

import ctypes
import os
from pathlib import Path


_DLL_DIRECTORY_HANDLE: object | None = None
_GMT_LIBRARY_HANDLE: object | None = None


def configure_gmt_runtime() -> None:
    """Expose and preload the repository-local GMT shared library."""
    global _DLL_DIRECTORY_HANDLE, _GMT_LIBRARY_HANDLE

    if os.name != "nt" or _GMT_LIBRARY_HANDLE is not None:
        return

    project_root = Path(__file__).resolve().parents[2]
    gmt_bin = project_root / ".gmt" / "Library" / "bin"
    gmt_library = gmt_bin / "gmt.dll"

    if not gmt_library.is_file():
        return

    os.environ["GMT_LIBRARY_PATH"] = str(gmt_bin)
    os.environ["PATH"] = f"{gmt_bin}{os.pathsep}{os.environ.get('PATH', '')}"

    # Preload GMT before ipykernel/ZeroMQ loads potentially conflicting DLLs.
    _DLL_DIRECTORY_HANDLE = os.add_dll_directory(str(gmt_bin))
    _GMT_LIBRARY_HANDLE = ctypes.CDLL(str(gmt_library))


configure_gmt_runtime()