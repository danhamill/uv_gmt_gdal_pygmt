# uv-gmt-gdal-pygmt

This GDAL and PyGMT development environment combines a prebuilt native runtime
with a uv-managed Python environment:

- The native GMT and ESMF runtimes are downloaded from the
	[`gmt_builder` v.0.3 release](https://github.com/danhamill/gmt_builder/releases/tag/v.0.3)
	and extracted into `.gmt`.
- **uv** creates `.venv` and installs Python packages, including PyGMT, GDAL,
	and ESMPy.

## Prerequisites

Install [uv](https://docs.astral.sh/uv/) and ensure it is available on `PATH`.

## Windows setup

Open a terminal in the repository root and download the native runtime:

```console
uv run --no-project python scripts/install_gmt_runtime.py
```

The installer verifies the release asset's SHA-256 checksum and extracts its
contents into `.gmt`. It leaves an existing installation unchanged; pass
`--force` to replace it.

Then create or update the uv environment:

```console
uv sync --locked
uv run python scripts/install_gmt_startup.py
```

The committed `.vscode/settings.json` exposes GMT to new VS Code integrated
terminals by configuring:

- `ESMFMKFILE` as `${workspaceFolder}\.gmt\Library\lib\esmf.mk`
- `GMT_LIBRARY_PATH` as `${workspaceFolder}\.gmt\Library\bin`
- `PATH` to include `.gmt\Library\bin` and `.gmt\Scripts`

After setup, **close existing terminals and open a new VS Code integrated
terminal** so these environment variables take effect. In VS Code notebooks,
select the `.venv` Python kernel and restart it after installing the startup
hook.

The second command installs a small `.pth` file into the generated `.venv`.
Python reads that hook before Jupyter starts and imports the tracked
`uv_gmt_gdal_pygmt.gmt_runtime` module. The module configures both native
runtimes and enforces the Windows DLL load order needed by GDAL, ESMF, and GMT.
The installer also applies the historical conda-forge Windows loader patch to
the uv-installed ESMPy 8.4.2 source package. The generated `.pth` file and
patched files under `.venv` are intentionally not committed; the installer and
runtime module are committed and recreate them on every computer.

ESMPy is not available from PyPI. `pyproject.toml` therefore installs ESMPy
8.4.2 with uv from the matching ESMF Git tag. The release archive also contains
ESMF 8.4.2; keep these versions synchronized when updating the runtime asset.

## Verify the installation

```console
uv run python -c "import esmpy, pygmt; from osgeo import gdal; print(esmpy.__version__); print(gdal.VersionInfo('--version')); pygmt.show_versions()"
```

PyGMT must be able to load `.gmt\Library\bin\gmt.dll`. If it reports
`GMTCLibNotFoundError`, confirm that GMT was installed under `.gmt` and that the
command is running in a newly opened VS Code integrated terminal.

## Rebuilding the environment

Both generated environments are ignored by Git. To recreate them:

```console
uv run --no-project python scripts/install_gmt_runtime.py --force
uv sync --locked
uv run python scripts/install_gmt_startup.py
```

Run the startup-hook installer again whenever `.venv` is deleted and recreated.
