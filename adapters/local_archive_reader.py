"""Bounded, read-only local file inventory and exact duplicate evidence.

This is a best-effort local scanner, not a race-proof sandbox or media decoder.
"""

from __future__ import annotations

from collections import defaultdict
import ctypes
from datetime import datetime, timezone
from hashlib import sha256
from itertools import islice
import os
from pathlib import Path
import stat
from typing import Any
from uuid import uuid4


REPARSE_POINT = getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0x400)


class ArchiveScanError(ValueError):
    """Invalid root or scan configuration; no scan was started."""

    def __init__(self, code: str, *, bytes_consumed: int = 0):
        super().__init__(code)
        self.bytes_consumed = bytes_consumed


def _identity(info: os.stat_result) -> tuple[int, int, int, int, int]:
    return (info.st_dev, info.st_ino, info.st_size, info.st_mtime_ns, info.st_ctime_ns)


def _is_link_or_reparse(info: os.stat_result) -> bool:
    return stat.S_ISLNK(info.st_mode) or bool(getattr(info, "st_file_attributes", 0) & REPARSE_POINT)


def _hash_fd(fd: int, byte_limit: int) -> tuple[str, int]:
    digest = sha256()
    count = 0
    while True:
        chunk = os.read(fd, min(1024 * 1024, byte_limit - count + 1))
        if not chunk:
            return digest.hexdigest(), count
        count += len(chunk)
        if count > byte_limit:
            raise ArchiveScanError("byte_limit_during_read", bytes_consumed=count)
        digest.update(chunk)


def scan_archive(
    root: str | os.PathLike[str], *, max_files: int = 10000,
    max_bytes: int = 10 * 1024**3, max_entries: int = 20000,
    max_depth: int = 32,
) -> dict[str, Any]:
    """Scan one explicit local root without writing or following known links.

    A result is partial when any entry is skipped or fails. On Windows, Python's
    standard library cannot guarantee an atomic no-follow open for every path
    component; path swaps by an adversarial concurrent process remain possible.
    """
    if not all(type(n) is int and n >= 0 for n in (max_files, max_bytes, max_entries, max_depth)):
        raise ArchiveScanError("invalid_limits")
    raw = os.fspath(root)
    if not isinstance(raw, str) or not raw or "\x00" in raw:
        raise ArchiveScanError("invalid_root")
    if raw.startswith(("\\\\", "//")) or any(part == ".." for part in raw.replace("\\", "/").split("/")):
        raise ArchiveScanError("unsafe_root")
    path = Path(raw)
    if not path.is_absolute():
        raise ArchiveScanError("root_must_be_absolute")
    try:
        root_info = path.lstat()
        if _is_link_or_reparse(root_info) or not stat.S_ISDIR(root_info.st_mode):
            raise ArchiveScanError("root_not_plain_directory")
        root_real = path.resolve(strict=True)
    except OSError as exc:
        raise ArchiveScanError("root_unavailable") from exc
    if os.name == "nt" and str(root_real).startswith("\\\\"):
        raise ArchiveScanError("network_root")
    if os.name == "nt" and ctypes.windll.kernel32.GetDriveTypeW(str(root_real.anchor)) == 4:
        raise ArchiveScanError("network_root")

    scan_id = f"local-{uuid4().hex}"
    started_at = datetime.now(timezone.utc)
    limits = {"max_files": max_files, "max_bytes": max_bytes,
              "max_entries": max_entries, "max_depth": max_depth}
    rows: list[dict[str, Any]] = []
    errors: list[dict[str, str]] = []
    entries_seen = 0
    bytes_read = 0
    bytes_examined = 0
    stop = False
    stack = [(path, 0)]
    while stack and not stop:
        directory, depth = stack.pop()
        relative_directory = directory.relative_to(path).as_posix()
        try:
            before_directory = directory.lstat()
            if (_is_link_or_reparse(before_directory) or not stat.S_ISDIR(before_directory.st_mode)
                    or before_directory.st_dev != root_info.st_dev):
                errors.append({"path": relative_directory, "code": "directory_boundary"})
                continue
            if os.path.commonpath((root_real, directory.resolve(strict=True))) != str(root_real):
                errors.append({"path": relative_directory, "code": "directory_boundary"})
                continue
            with os.scandir(directory) as iterator:
                children = sorted(islice(iterator, max_entries - entries_seen + 1), key=lambda item: item.name)
        except OSError:
            errors.append({"path": relative_directory, "code": "directory_unreadable"})
            continue
        next_directories = []
        for entry in children:
            relative = Path(entry.path).relative_to(path).as_posix()
            if entries_seen >= max_entries:
                errors.append({"path": relative, "code": "entry_limit"})
                stop = True
                break
            entries_seen += 1
            try:
                # Windows DirEntry.stat can report st_dev=0 while Path.lstat
                # reports the actual volume; use one source for comparisons.
                info = Path(entry.path).lstat()
                if _is_link_or_reparse(info) or info.st_dev != root_info.st_dev:
                    errors.append({"path": relative, "code": "link_or_mount_skipped"})
                    continue
                if stat.S_ISDIR(info.st_mode):
                    if depth >= max_depth:
                        errors.append({"path": relative, "code": "depth_limit"})
                    else:
                        next_directories.append((Path(entry.path), depth + 1))
                    continue
                if not stat.S_ISREG(info.st_mode):
                    errors.append({"path": relative, "code": "non_regular_skipped"})
                    continue
                if len(rows) >= max_files:
                    errors.append({"path": relative, "code": "file_limit"})
                    stop = True
                    break
                if info.st_size > max_bytes - bytes_examined:
                    errors.append({"path": relative, "code": "byte_limit"})
                    stop = True
                    break
                if os.path.commonpath((root_real, Path(entry.path).resolve(strict=True))) != str(root_real):
                    errors.append({"path": relative, "code": "path_escape"})
                    continue
                if (_identity(path.lstat()) != _identity(root_info)
                        or _identity(directory.lstat()) != _identity(before_directory)):
                    errors.append({"path": relative, "code": "parent_changed"})
                    continue
                flags = os.O_RDONLY | getattr(os, "O_BINARY", 0) | getattr(os, "O_NOFOLLOW", 0)
                fd = os.open(entry.path, flags)
                try:
                    opened = os.fstat(fd)
                    if (_is_link_or_reparse(opened) or not stat.S_ISREG(opened.st_mode)
                            or _identity(opened) != _identity(info)):
                        errors.append({"path": relative, "code": "source_changed"})
                        continue
                    digest, count = _hash_fd(fd, max_bytes - bytes_examined)
                    bytes_examined += count
                    after = os.fstat(fd)
                finally:
                    os.close(fd)
                current = Path(entry.path).lstat()
                if (count != info.st_size or _identity(after) != _identity(info)
                        or _identity(current) != _identity(info) or _is_link_or_reparse(current)
                        or os.path.commonpath((root_real, Path(entry.path).resolve(strict=True))) != str(root_real)):
                    errors.append({"path": relative, "code": "source_changed"})
                    continue
                rows.append({"relative_path": relative, "size": count, "sha256": digest,
                             "mtime_ns": info.st_mtime_ns, "ctime_ns": info.st_ctime_ns,
                             "device": info.st_dev, "inode": info.st_ino})
                bytes_read += count
            except ArchiveScanError as exc:
                errors.append({"path": relative, "code": str(exc)})
                bytes_examined += exc.bytes_consumed
                if str(exc) == "byte_limit_during_read":
                    stop = True
                    break
            except OSError:
                errors.append({"path": relative, "code": "unreadable_or_changed"})
        stack.extend(reversed(next_directories))
        try:
            if _identity(directory.lstat()) != _identity(before_directory):
                errors.append({"path": relative_directory, "code": "directory_changed"})
        except OSError:
            errors.append({"path": relative_directory, "code": "directory_changed"})
    try:
        if _identity(path.lstat()) != _identity(root_info) or path.resolve(strict=True) != root_real:
            errors.append({"path": ".", "code": "root_changed"})
    except OSError:
        errors.append({"path": ".", "code": "root_changed"})
    rows.sort(key=lambda row: row["relative_path"])
    groups: dict[tuple[int, str], list[str]] = defaultdict(list)
    for row in rows:
        groups[(row["size"], row["sha256"])].append(row["relative_path"])
    duplicates = [{"size": size, "sha256": digest, "paths": sorted(paths), "method": "byte_sha256"}
                  for (size, digest), paths in sorted(groups.items()) if len(paths) > 1]
    return {"scan_id": scan_id, "started_at": started_at.isoformat(),
            "completed_at": datetime.now(timezone.utc).isoformat(), "limits": limits,
            "root": str(path), "status": "partial" if errors else "complete", "files": rows,
            "file_count": len(rows), "bytes_read": bytes_read, "bytes_examined": bytes_examined,
            "entries_seen": entries_seen,
            "exact_duplicates": duplicates, "errors": errors, "read_only": True}
