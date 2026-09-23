# uv-gmt-gdal-pygmt

This GDAL and PyGMT development environment uses two environment managers with
separate responsibilities:

- **Micromamba** installs the native GMT and ESMF runtimes and their DLL
	dependencies into `.gmt`.
- **uv** creates `.venv` and installs Python packages, including PyGMT, GDAL,
	and ESMPy.

## Prerequisites

Install [uv](https://docs.astral.sh/uv/) and
[Micromamba](https://mamba.readthedocs.io/en/latest/installation/micromamba-installation.html),
then ensure both commands are available on `PATH`.

## Windows setup

Open **Command Prompt (`cmd.exe`)** in the repository root and install the
native runtimes. Install `esmf`, not `esmpy`, with Micromamba:

```cmd
micromamba create --prefix .\.gmt --channel conda-forge gmt esmf=8.4.2 --yes
```

Then create/update the uv environment from either Command Prompt or PowerShell:

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
8.4.2 with uv from the matching ESMF Git tag. Keep the Micromamba `esmf=8.4.2`
pin and the uv ESMPy Git tag synchronized.

## Verify the installation

```console
uv run python -c "import esmpy, pygmt; from osgeo import gdal; print(esmpy.__version__); print(gdal.VersionInfo('--version')); pygmt.show_versions()"
```

PyGMT must be able to load `.gmt\Library\bin\gmt.dll`. If it reports
`GMTCLibNotFoundError`, confirm that GMT was installed under `.gmt` and that the
command is running in a newly opened VS Code integrated terminal.

## Rebuilding the environment

Both generated environments are ignored by Git. To recreate them, first use
Command Prompt:

```cmd
rmdir /s /q .gmt
rmdir /s /q .venv
micromamba create --prefix .\.gmt --channel conda-forge gmt esmf=8.4.2 --yes
uv sync --locked
uv run python scripts/install_gmt_startup.py
```

Run the startup-hook installer again whenever `.venv` is deleted and recreated.
