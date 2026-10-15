# Local archive reader

`adapters/local_archive_reader.py` provides an opt-in, standard-library, read-only scan of one explicitly supplied absolute local directory. Each accepted run returns a random `scan_id`, UTC `started_at`/`completed_at`, the applied `limits`, relative paths, byte counts, filesystem `mtime_ns`/`ctime_ns`, observed device/inode where supplied by the OS, SHA-256 and exact duplicate groups. The ID contains no path or content and is a correlation label, not a content fingerprint. Empty accessible roots return `complete` with zero files. The caller must authorize the root and decide whether the results may be disclosed or stored; this adapter writes no report.

Example from the repository root:

```python
from adapters.local_archive_reader import scan_archive

result = scan_archive(r"C:\Users\ByteNinja\Pictures", max_files=5000,
                      max_bytes=20 * 1024**3, max_entries=10000, max_depth=16)
if result["status"] != "complete":
    print(result["errors"])
```

`status=partial` means at least one path was skipped, unreadable, changed or stopped by a limit. The `files` list then covers only successfully hashed files; it must not be treated as a complete archive or as proof that ungrouped files are unique. Compare the scan window, ID, root and limits when reusing results; a new run gets a new ID even if files did not change. The scan checks root and directory identity before opening each file, then path, file identity and timestamps around hashing. It excludes detected symlinks, Windows reparse points and device crossings. It rejects UNC roots and Windows mapped network drives; portable detection of every network-mounted directory is unavailable. On Windows the Python standard library does not guarantee an atomic no-follow open through every component; an adversarial concurrent path swap may evade these checks. Protect the root from untrusted concurrent modification before relying on the inventory for consequential decisions.

`exact_duplicates` means equal byte count and SHA-256 among successfully scanned files. Hashes are evidence, not approval to delete. The adapter does not parse EXIF or media, evaluate perceptual similarity or corruption, check backups, migrate files, create dashboard events, or execute a Hermes skill. `adapters/archive_e2e_mock.py` remains a separate three-record, in-memory E2E6 composition; its simulated approval and copy are not part of this adapter.

Focused tests in `tests/test_local_archive_reader.py` use real temporary files, independent SHA-256 expectations and controlled error/race cases. The tested read-only boundary does not prove resistance to an adversarial time-of-check/time-of-use race on every platform.
