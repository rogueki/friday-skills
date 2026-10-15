# Local archive E2E6 mock

`run_local_archive_mock` in `adapters/archive_e2e_mock.py` connects the bounded, read-only local archive reader to the E2E6 inventory, exact duplicate grouping, copy-only plan, approval boundary and in-memory integrity check. It is an **opt-in local test path**, separate from the original synthetic `run_scenario("photo_archive")`.

The caller explicitly supplies two authorized absolute local directories: source and an independent backup copy. Both are scanned with SHA-256 and identical relative file paths, sizes and hashes are required; a shared file identity (hard link) is rejected. Partial scans, unknown capacity, missing backup coverage, source changes, unsafe paths and capacity below twice the source bytes block a proposal. A second source scan must match before the proposal. The manifest's backup scan ID identifies local evidence; it is not proof that the backup can be restored or survives loss of the source volume. Capacity is caller-supplied for simulation and is not measured against a real destination filesystem.

The default returns `waiting_approval` with a tier-2, manifest-bound proposal; it creates no target directory. `simulated_approval=True` creates and consumes a **simulated-only** manifest-bound grant, rescans the source, safely rereads and hashes each file, copies bytes into an in-memory map, verifies target count, total bytes and SHA-256, and checks the source scan again. No trusted host approval or real filesystem migration occurs. Originals and backup files are never changed or deleted by the adapter.

Example with small, controlled local directories:

```python
from adapters.archive_e2e_mock import run_local_archive_mock

result = run_local_archive_mock(
    r"C:\controlled\photos", r"C:\controlled\backup-photos",
    destination_free_bytes=100_000_000,
)
assert result["status"] == "waiting_approval"
```

The caller must authorize both roots; strings emitted by a model do not grant filesystem access. The local mock caps input at 100 files, 32 MiB, 200 entries and depth 8. The scanner rejects known links, reparse points and network roots, but Windows standard-library path opens do not provide an atomic no-follow guarantee for every path component under hostile concurrent mutation. Protect test roots from untrusted writes. SHA-256 equality cannot establish that an image decodes or is uncorrupted; `media_integrity` stays `unknown_unverified`. Real migration, restoration, deletion, Hermes model routing and Dashboard publication remain untested.

Focused checks: `python -m unittest discover -s tests -p 'test_archive_e2e_mock.py' -q`.
