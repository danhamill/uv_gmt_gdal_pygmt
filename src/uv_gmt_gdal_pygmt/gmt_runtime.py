"""Configure repository-local native runtimes during Python startup on Windows."""

from __future__ import annotations

import ctypes
import os
from pathlib import Path


_DLL_DIRECTORY_HANDLES: list[object] = []
_ESMF_LIBRARY_HANDLE: object | None = None
_GMT_LIBRARY_HANDLE: object | None = None


def configure_gmt_runtime() -> None:
    """Expose and preload the repository-local GMT and ESMF libraries."""
    global _ESMF_LIBRARY_HANDLE, _GMT_LIBRARY_HANDLE

    if os.name != "nt" or _GMT_LIBRARY_HANDLE is not None:
        return

    project_root = Path(__file__).resolve().parents[2]
    gmt_bin = project_root / ".gmt" / "Library" / "bin"
    gmt_library = gmt_bin / "gmt.dll"
    mingw_bin = project_root / ".gmt" / "Library" / "mingw-w64" / "bin"
    esmf_lib = project_root / ".gmt" / "Library" / "lib"
    esmf_mk = esmf_lib / "esmf.mk"

    if not gmt_library.is_file():
        return

    os.environ["GMT_LIBRARY_PATH"] = str(gmt_bin)
    os.environ["PATH"] = f"{gmt_bin}{os.pathsep}{os.environ.get('PATH', '')}"
    if esmf_mk.is_file():
        os.environ["ESMFMKFILE"] = str(esmf_mk)

    # General conda runtime dependencies are stored alongside GMT.
    _DLL_DIRECTORY_HANDLES.append(os.add_dll_directory(str(gmt_bin)))

    # Import GDAL before ESMF's legacy MinGW runtime is loaded. Both stacks
    # contain DLLs with identical names but different exported procedures.
    try:
        from osgeo import gdal  # noqa: F401
    except ImportError:
        pass

    # ESMF 8.4.2 uses an older MinGW runtime. Expose it only while preloading
    # ESMF so GDAL cannot later bind against those incompatible DLL versions.
    esmf_handles = [
        os.add_dll_directory(str(path))
        for path in (mingw_bin, esmf_lib)
        if path.is_dir()
    ]
    try:
        esmf_library = esmf_lib / "esmf_fullylinked.dll"
        if esmf_library.is_file():
            _ESMF_LIBRARY_HANDLE = ctypes.CDLL(str(esmf_library))
    finally:
        for handle in esmf_handles:
            handle.close()

    # Preload GMT before ipykernel/ZeroMQ loads potentially conflicting DLLs.
    _GMT_LIBRARY_HANDLE = ctypes.CDLL(str(gmt_library))


configure_gmt_runtime()