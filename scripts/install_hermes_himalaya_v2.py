#!/usr/bin/env python3
"""Install reviewed Himalaya 2.2.1 instructions over Hermes' local v1 copy."""

import argparse
import hashlib
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile


REVIEWED_V1 = {
    "SKILL.md": "0f6c9bb4c0a5c4f4627e139b6beb2b1ba0addd7145895196528b8125929e3837",
    "references/configuration.md": "ccd540fa964f843903b17400a5f45ef610a16f23fe1e0ca3e625f717fa951b89",
    "references/message-composition.md": "84d889972f5f4243d891405b83e67bddc7e835b2c4e434efd77fdc6bca9fe307",
}
SOURCE = Path(__file__).resolve().parents[1] / "compat" / "hermes" / "himalaya-v2"
OVERLAY = {
    "SKILL.md": SOURCE / "SKILL.md",
    "references/himalaya-v2.md": SOURCE / "references" / "himalaya-v2.md",
}


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def safe_file(path: Path) -> bool:
    return path.is_file() and not path.is_symlink() and not path.parent.is_symlink()


def replace_file(target: Path, data: bytes) -> None:
    target.parent.mkdir(parents=True, exist_ok=True)
    fd, staging = tempfile.mkstemp(prefix=".friday-himalaya-", dir=target.parent)
    try:
        os.fchmod(fd, 0o644)
        with os.fdopen(fd, "wb") as stream:
            stream.write(data)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(staging, target)
    finally:
        if os.path.exists(staging):
            os.unlink(staging)


def run() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--hermes-home", type=Path, default=Path.home() / ".hermes")
    parser.add_argument("--himalaya-bin", type=Path, default=Path.home() / ".local/bin/himalaya")
    parser.add_argument("--apply", action="store_true", help="back up and install reviewed overlay")
    args = parser.parse_args()

    binary = args.himalaya_bin
    if not safe_file(binary):
        print("Himalaya binary is missing or unsafe", file=sys.stderr)
        return 2
    version = subprocess.run([str(binary), "--version"], capture_output=True, text=True, timeout=5, check=False)
    if version.returncode != 0 or not version.stdout.startswith("himalaya v2.2.1 "):
        print("Requires reviewed Himalaya 2.2.1", file=sys.stderr)
        return 2

    home = args.hermes_home
    skill = home / "skills/email/himalaya"
    if home.is_symlink() or skill.is_symlink() or skill.parent.is_symlink() or not skill.is_dir():
        print("Hermes Himalaya skill is missing or unsafe", file=sys.stderr)
        return 2
    for relative in set(REVIEWED_V1) | set(OVERLAY):
        path = skill / relative
        if path.exists() and not safe_file(path):
            print(f"Refusing unsafe skill file: {relative}", file=sys.stderr)
            return 2

    if all(safe_file(skill / name) and digest(skill / name) == digest(source)
           for name, source in OVERLAY.items()):
        print("Himalaya v2 overlay already installed")
        return 0
    if not all(safe_file(skill / name) and digest(skill / name) == expected
               for name, expected in REVIEWED_V1.items()):
        print("Bundled Himalaya skill differs from reviewed v1.1.0; leaving it untouched", file=sys.stderr)
        return 3
    if not args.apply:
        print("Reviewed v1.1.0 skill found; run with --apply to install v2 overlay")
        return 0

    backup = home / "backups/friday-himalaya-v1" / REVIEWED_V1["SKILL.md"]
    if backup.is_symlink() or backup.parent.is_symlink():
        print("Unsafe backup location", file=sys.stderr)
        return 2
    backup.mkdir(parents=True, mode=0o700, exist_ok=True)
    for relative, expected in REVIEWED_V1.items():
        dest = backup / relative
        if dest.exists():
            if not safe_file(dest) or digest(dest) != expected:
                print(f"Existing backup differs: {relative}", file=sys.stderr)
                return 3
        else:
            dest.parent.mkdir(parents=True, exist_ok=True)
            replace_file(dest, (skill / relative).read_bytes())

    for relative, source in OVERLAY.items():
        replace_file(skill / relative, source.read_bytes())
    print(f"Himalaya v2 overlay installed; original backed up at {backup}")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(run())
    except (OSError, subprocess.TimeoutExpired) as exc:
        print(f"Himalaya compatibility check failed: {type(exc).__name__}", file=sys.stderr)
        raise SystemExit(2)
