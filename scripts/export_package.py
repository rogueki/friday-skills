"""Build a deterministic source ZIP without local memory, credentials, or Git data."""

from __future__ import annotations

from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile, ZipInfo
import argparse

ROOT = Path(__file__).resolve().parents[1]
INCLUDE_DIRS = ("skills", "shared", "registry", "plugins", "tools", "fixtures", "scripts", "tests", "docs")
INCLUDE_FILES = ("README.md", "CHANGELOG.md", "LICENSE", ".gitignore")
EXCLUDED_PARTS = {"__pycache__", ".git", "artifacts", "secrets", ".venv"}


def package_files() -> list[Path]:
    paths = [ROOT / name for name in INCLUDE_FILES if (ROOT / name).is_file()]
    for directory in INCLUDE_DIRS:
        base = ROOT / directory
        if not base.exists():
            continue
        paths.extend(path for path in base.rglob("*") if path.is_file()
                     and not any(part in EXCLUDED_PARTS for part in path.relative_to(ROOT).parts)
                     and path.suffix not in {".pyc", ".pyo", ".zip"})
    return sorted(paths, key=lambda p: p.relative_to(ROOT).as_posix())


def export(destination: Path) -> int:
    destination = destination.resolve()
    if destination.exists():
        raise FileExistsError(f"refusing to overwrite: {destination}")
    destination.parent.mkdir(parents=True, exist_ok=True)
    with ZipFile(destination, "w", compression=ZIP_DEFLATED, compresslevel=9) as archive:
        for path in package_files():
            relative = path.relative_to(ROOT).as_posix()
            info = ZipInfo(f"friday-skills/{relative}", date_time=(2026, 1, 1, 0, 0, 0))
            info.compress_type = ZIP_DEFLATED
            info.external_attr = 0o644 << 16
            archive.writestr(info, path.read_bytes(), compress_type=ZIP_DEFLATED, compresslevel=9)
    return len(archive.namelist())


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("destination", type=Path)
    args = parser.parse_args()
    print(f"exported {export(args.destination)} files to {args.destination}")
