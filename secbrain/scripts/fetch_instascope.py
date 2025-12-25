"""
Fetch and unpack an Immunefi Instascope bundle into targets/<protocol>/instascope.

Usage (examples):
    python secbrain/scripts/fetch_instascope.py --protocol originprotocol --source https://example.com/instascope.zip
    python secbrain/scripts/fetch_instascope.py --protocol originprotocol --source ./instascope.zip --force
    python secbrain/scripts/fetch_instascope.py --protocol originprotocol --source ./instascope.tar.gz --build

Design goals:
- Keep everything under targets/<protocol>/instascope to avoid duplicate locations.
- No new dependencies; uses stdlib (urllib + shutil.unpack_archive).
- Optional build step runs ./build.sh inside the unpacked bundle (requires forge + shell).
"""

from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from urllib.request import urlretrieve


def _repo_root() -> Path:
    # File is at <repo>/secbrain/scripts/fetch_instascope.py
    return Path(__file__).resolve().parents[2]


def download_source(source: str, download_dir: Path) -> Path:
    source_path = Path(source)
    if source_path.exists():
        return source_path

    download_dir.mkdir(parents=True, exist_ok=True)
    target = download_dir / "instascope_bundle"
    urlretrieve(source, target)
    return target


def unpack_bundle(bundle_path: Path, dest_dir: Path) -> None:
    dest_dir.mkdir(parents=True, exist_ok=True)
    shutil.unpack_archive(str(bundle_path), str(dest_dir))


def run_build(dest_dir: Path) -> None:
    build_script = dest_dir / "build.sh"
    if not build_script.exists():
        return

    try:
        subprocess.check_call(["bash", str(build_script)], cwd=dest_dir)
    except FileNotFoundError:
        pass
    except subprocess.CalledProcessError as exc:
        raise


def main() -> int:
    parser = argparse.ArgumentParser(description="Fetch and unpack an Instascope bundle.")
    parser.add_argument("--protocol", required=True, help="Protocol name (e.g., originprotocol)")
    parser.add_argument(
        "--source",
        required=True,
        help="URL or local path to Instascope archive (zip/tar.*)",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Overwrite existing targets/<protocol>/instascope directory",
    )
    parser.add_argument(
        "--build",
        action="store_true",
        help="Run build.sh inside the unpacked bundle after fetching",
    )
    args = parser.parse_args()

    root = _repo_root()
    targets_dir = root / "targets"
    dest_dir = targets_dir / args.protocol / "instascope"

    if dest_dir.exists():
        if not args.force:
            return 1
        shutil.rmtree(dest_dir)

    with tempfile.TemporaryDirectory() as tmpdir_str:
        tmpdir = Path(tmpdir_str)
        bundle_path = download_source(args.source, tmpdir)
        unpack_bundle(bundle_path, dest_dir)

    if args.build:
        run_build(dest_dir)

    return 0


if __name__ == "__main__":
    sys.exit(main())
