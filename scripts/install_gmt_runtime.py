"""Install the prebuilt GMT and ESMF runtime into this repository."""

from __future__ import annotations

import argparse
import hashlib
import shutil
import sys
import tempfile
import urllib.request
import zipfile
from pathlib import Path, PurePosixPath

DEFAULT_URL = (
    "https://github.com/danhamill/gmt_builder/releases/download/v.0.3/gmt-windows.zip"
)
DEFAULT_SHA256 = "d01effe253830b2b2240923355d49ae424e5cdf1cee05170955267e1e48aea96"
DOWNLOAD_CHUNK_SIZE = 1024 * 1024


def download_archive(url: str, destination: Path) -> str:
    """Download *url* to *destination* and return its SHA-256 digest."""
    digest = hashlib.sha256()
    request = urllib.request.Request(
        url, headers={"User-Agent": "uv-gmt-runtime-installer"}
    )

    with urllib.request.urlopen(request) as response, destination.open("wb") as output:
        total = int(response.headers.get("Content-Length", 0))
        downloaded = 0
        while chunk := response.read(DOWNLOAD_CHUNK_SIZE):
            output.write(chunk)
            digest.update(chunk)
            downloaded += len(chunk)
            if total:
                print(
                    f"\rDownloading GMT and ESMF runtimes: {downloaded / 1024**2:.0f} / "
                    f"{total / 1024**2:.0f} MiB",
                    end="",
                    flush=True,
                )
        if total:
            print()

    return digest.hexdigest()


def extract_archive(archive: Path, destination: Path) -> None:
    """Safely extract the archive, removing its single top-level directory."""
    with zipfile.ZipFile(archive) as source:
        files = [member for member in source.infolist() if not member.is_dir()]
        if not files:
            raise ValueError("The downloaded archive is empty.")

        paths = [PurePosixPath(member.filename.replace("\\", "/")) for member in files]
        roots = {path.parts[0] for path in paths if path.parts}
        strip_root = len(roots) == 1 and all(len(path.parts) > 1 for path in paths)

        for member, path in zip(files, paths, strict=True):
            parts = path.parts[1:] if strip_root else path.parts
            if not parts or path.is_absolute() or ".." in parts:
                raise ValueError(f"Unsafe archive member: {member.filename}")

            target = destination.joinpath(*parts)
            target.parent.mkdir(parents=True, exist_ok=True)
            with source.open(member) as input_file, target.open("wb") as output_file:
                shutil.copyfileobj(input_file, output_file)


def validate_runtime(runtime: Path) -> None:
    """Confirm that the extracted tree contains the required native runtime."""
    required = (
        runtime / "Library" / "bin" / "gmt.dll",
        runtime / "Library" / "lib" / "esmf.mk",
        runtime / "Library" / "lib" / "esmf_fullylinked.dll",
    )
    missing = [path.relative_to(runtime) for path in required if not path.is_file()]
    if missing:
        formatted = ", ".join(str(path) for path in missing)
        raise ValueError(f"The archive is missing required runtime files: {formatted}")


def install_runtime(
    project_root: Path, url: str, expected_sha256: str, force: bool
) -> None:
    """Download and install the runtime under ``.gmt``."""
    runtime = project_root / ".gmt"

    if runtime.exists() and not force:
        raise FileExistsError(f"{runtime} already exists; use --force to replace it.")

    installation_started = False
    try:
        with tempfile.TemporaryDirectory(prefix="gmt-download-") as temporary:
            archive = Path(temporary) / "gmt-windows.zip"
            actual_sha256 = download_archive(url, archive)
            if actual_sha256.lower() != expected_sha256.lower():
                raise ValueError(
                    "GMT archive checksum mismatch: "
                    f"expected {expected_sha256}, received {actual_sha256}"
                )

            if runtime.exists():
                shutil.rmtree(runtime)
            runtime.mkdir()
            installation_started = True
            print("Extracting GMT runtime...")
            extract_archive(archive, runtime)

        validate_runtime(runtime)
    except BaseException:
        if installation_started and runtime.exists():
            shutil.rmtree(runtime)
        raise

    print(f"Installed GMT and ESMF runtime: {runtime}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Download the prebuilt GMT/ESMF Windows runtime into .gmt."
    )
    parser.add_argument("--force", action="store_true", help="replace an existing .gmt")
    parser.add_argument("--url", default=DEFAULT_URL, help=argparse.SUPPRESS)
    parser.add_argument("--sha256", default=DEFAULT_SHA256, help=argparse.SUPPRESS)
    return parser.parse_args()


def main() -> None:
    if sys.platform != "win32":
        raise SystemExit("This prebuilt runtime supports Windows only.")

    args = parse_args()
    project_root = Path(__file__).resolve().parents[1]
    try:
        install_runtime(project_root, args.url, args.sha256, args.force)
    except (OSError, ValueError, zipfile.BadZipFile) as error:
        raise SystemExit(f"Runtime installation failed: {error}") from error


if __name__ == "__main__":
    main()
