# uv-gmt-gdal-pygmt

This GDAL and PyGMT development environment uses two environment managers with
separate responsibilities:

- **Micromamba** installs the native GMT runtime and its DLL dependencies into `.gmt`.
- **uv** creates `.venv` and installs Python packages, including PyGMT and GDAL.

## Prerequisites

Install [uv](https://docs.astral.sh/uv/) and
[Micromamba](https://mamba.readthedocs.io/en/latest/installation/micromamba-installation.html),
then ensure both commands are available on `PATH`.

## Windows setup

Open **Command Prompt (`cmd.exe`)** in the repository root and install GMT:

```cmd
micromamba create --prefix .\.gmt --channel conda-forge gmt --yes
```

Then create/update the uv environment from either Command Prompt or PowerShell:

```console
uv sync --locked
uv run python scripts/install_gmt_startup.py
```

The committed `.vscode/settings.json` exposes GMT to new VS Code integrated
terminals by configuring:

- `GMT_LIBRARY_PATH` as `${workspaceFolder}\.gmt\Library\bin`
- `PATH` to include `.gmt\Library\bin` and `.gmt\Scripts`

After setup, **close existing terminals and open a new VS Code integrated
terminal** so these environment variables take effect. In VS Code notebooks,
select the `.venv` Python kernel and restart it after installing the startup
hook.

The second command installs a small `.pth` file into the generated `.venv`.
Python reads that hook before Jupyter starts and imports the tracked
`uv_gmt_gdal_pygmt.gmt_runtime` module. The module sets `GMT_LIBRARY_PATH`, adds
the GMT DLL directory, and preloads `gmt.dll` before Jupyter loads native
libraries. The generated `.pth` file is intentionally not committed; the
installer script and runtime module are committed and recreate it on every
computer.

## Verify the installation

```console
uv run python -c "from osgeo import gdal; import pygmt; print(gdal.VersionInfo('--version')); pygmt.show_versions()"
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
micromamba create --prefix .\.gmt --channel conda-forge gmt --yes
uv sync --locked
uv run python scripts/install_gmt_startup.py
```

Run the startup-hook installer again whenever `.venv` is deleted and recreated.
