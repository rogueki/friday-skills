"""Real local-file inventory, with independent file/hash oracles."""

from hashlib import sha256
from datetime import datetime, timezone
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from adapters import local_archive_reader as archive


class LocalArchiveReaderTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)

    def test_empty_root_is_complete(self):
        before = datetime.now(timezone.utc)
        result = archive.scan_archive(self.root)
        after = datetime.now(timezone.utc)
        self.assertEqual((result["status"], result["file_count"], result["errors"]), ("complete", 0, []))
        self.assertEqual(list(self.root.iterdir()), [])
        self.assertRegex(result["scan_id"], r"^local-[0-9a-f]{32}$")
        self.assertLessEqual(before, datetime.fromisoformat(result["started_at"]))
        self.assertLessEqual(datetime.fromisoformat(result["started_at"]),
                             datetime.fromisoformat(result["completed_at"]))
        self.assertLessEqual(datetime.fromisoformat(result["completed_at"]), after)
        self.assertEqual(result["limits"], {"max_files": 10000, "max_bytes": 10 * 1024**3,
                                             "max_entries": 20000, "max_depth": 32})

    def test_exact_duplicates_use_bytes_and_preserve_sources(self):
        (self.root / "sub").mkdir()
        payloads = {"a.jpg": b"same bytes", "sub/b.bin": b"same bytes", "c.jpg": b"other text"}
        for name, data in payloads.items():
            (self.root / name).write_bytes(data)
        original = {name: (self.root / name).read_bytes() for name in payloads}
        result = archive.scan_archive(self.root)
        self.assertEqual(result["status"], "complete")
        self.assertEqual(result["file_count"], 3)
        self.assertEqual(result["bytes_read"], sum(map(len, payloads.values())))
        self.assertEqual([item["relative_path"] for item in result["files"]], sorted(payloads))
        for item in result["files"]:
            expected = payloads[item["relative_path"]]
            self.assertEqual((item["size"], item["sha256"]), (len(expected), sha256(expected).hexdigest()))
            self.assertGreaterEqual(item["mtime_ns"], 0)
        self.assertEqual(result["exact_duplicates"], [{"size": len(b"same bytes"),
            "sha256": sha256(b"same bytes").hexdigest(), "paths": ["a.jpg", "sub/b.bin"],
            "method": "byte_sha256"}])
        self.assertEqual({name: (self.root / name).read_bytes() for name in payloads}, original)
        self.assertEqual(sorted(p.relative_to(self.root).as_posix() for p in self.root.rglob("*") if p.is_file()),
                         sorted(payloads))

    def test_limits_report_partial_not_false_complete(self):
        (self.root / "a").write_bytes(b"abc")
        (self.root / "b").write_bytes(b"def")
        for kw, code in (({"max_files": 1}, "file_limit"), ({"max_bytes": 2}, "byte_limit"),
                         ({"max_entries": 1}, "entry_limit")):
            with self.subTest(kw=kw):
                result = archive.scan_archive(self.root, **kw)
                self.assertEqual(result["status"], "partial")
                self.assertIn(code, [error["code"] for error in result["errors"]])
                self.assertEqual(result["limits"][next(iter(kw))], next(iter(kw.values())))
        self.assertEqual(((self.root / "a").read_bytes(), (self.root / "b").read_bytes()), (b"abc", b"def"))

    def test_symlink_escape_is_never_hashed(self):
        outside = self.root.parent / (self.root.name + "-outside")
        outside.write_bytes(b"secret")
        self.addCleanup(outside.unlink)
        try:
            (self.root / "link").symlink_to(outside)
        except (OSError, NotImplementedError):
            self.skipTest("symlink creation unavailable")
        result = archive.scan_archive(self.root)
        self.assertEqual(result["status"], "partial")
        self.assertEqual(result["files"], [])
        self.assertIn("link_or_mount_skipped", [error["code"] for error in result["errors"]])
        self.assertEqual(outside.read_bytes(), b"secret")

    def test_directory_link_boundary_and_depth_limit(self):
        outside = self.root.parent / (self.root.name + "-dir")
        outside.mkdir()
        (outside / "outside.txt").write_bytes(b"outside")
        self.addCleanup(outside.rmdir)
        self.addCleanup(lambda: (outside / "outside.txt").unlink())
        try:
            (self.root / "shortcut").symlink_to(outside, target_is_directory=True)
        except (OSError, NotImplementedError):
            self.skipTest("directory symlink creation unavailable")
        (self.root / "deep").mkdir()
        (self.root / "deep" / "nested.txt").write_bytes(b"nested")
        result = archive.scan_archive(self.root, max_depth=0)
        self.assertEqual(result["status"], "partial")
        self.assertEqual(result["files"], [])
        self.assertEqual({error["code"] for error in result["errors"]},
                         {"link_or_mount_skipped", "depth_limit"})
        self.assertEqual((outside / "outside.txt").read_bytes(), b"outside")

    def test_changed_during_read_does_not_emit_hash(self):
        target = self.root / "changing"
        target.write_bytes(b"before")
        original_hash = archive._hash_fd

        def mutate_after_hash(fd, limit):
            result = original_hash(fd, limit)
            target.write_bytes(b"after-more")
            return result

        with patch.object(archive, "_hash_fd", side_effect=mutate_after_hash):
            result = archive.scan_archive(self.root)
        self.assertEqual(result["status"], "partial")
        self.assertEqual(result["files"], [])
        self.assertIn("source_changed", [error["code"] for error in result["errors"]])
        self.assertEqual(target.read_bytes(), b"after-more")

    def test_unreadable_file_is_coverage_gap(self):
        target = self.root / "unreadable"
        target.write_bytes(b"content")
        real_open = archive.os.open

        def deny(path, flags):
            if os.fspath(path) == str(target):
                raise PermissionError("controlled denial")
            return real_open(path, flags)

        with patch.object(archive.os, "open", side_effect=deny):
            result = archive.scan_archive(self.root)
        self.assertEqual(result["status"], "partial")
        self.assertEqual(result["files"], [])
        self.assertIn("unreadable_or_changed", [error["code"] for error in result["errors"]])

    def test_rejects_unsafe_roots_and_bad_limits(self):
        for raw in ("relative", "../relative", "//server/share", "\\\\server\\share", str(self.root / ".." / "other")):
            with self.subTest(raw=raw), self.assertRaises(archive.ArchiveScanError):
                archive.scan_archive(raw)
        with self.assertRaises(archive.ArchiveScanError):
            archive.scan_archive(self.root, max_files=-1)


if __name__ == "__main__":
    unittest.main()
