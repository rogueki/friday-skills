"""Isolated installer checks; no mailbox or provider is contacted."""

import hashlib
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


SCRIPT = Path(__file__).resolve().parents[1] / "scripts/install_hermes_himalaya_v2.py"


class HimalayaOverlayTests(unittest.TestCase):
    def test_reviewed_v1_backed_up_once_and_unknown_version_refused(self):
        if os.name == "nt":
            self.skipTest("POSIX installer and executable fixture")
        with tempfile.TemporaryDirectory() as root:
            root = Path(root)
            home = root / ".hermes"
            skill = home / "skills/email/himalaya"
            skill.joinpath("references").mkdir(parents=True)
            original = {
                "SKILL.md": b"reviewed v1 main",
                "references/configuration.md": b"reviewed v1 config",
                "references/message-composition.md": b"reviewed v1 composition",
            }
            for relative, content in original.items():
                (skill / relative).write_bytes(content)
            binary = root / "himalaya"
            binary.write_text("#!/bin/sh\nprintf 'himalaya v2.2.1 +imap +smtp\\n'\n", encoding="utf-8")
            binary.chmod(0o700)

            # A copied module allows the pinned v1 fingerprint to be replaced
            # with this synthetic fixture without changing the production guard.
            source = SCRIPT.read_text(encoding="utf-8")
            for relative, content in original.items():
                old = {
                    "SKILL.md": "0f6c9bb4c0a5c4f4627e139b6beb2b1ba0addd7145895196528b8125929e3837",
                    "references/configuration.md": "ccd540fa964f843903b17400a5f45ef610a16f23fe1e0ca3e625f717fa951b89",
                    "references/message-composition.md": "84d889972f5f4243d891405b83e67bddc7e835b2c4e434efd77fdc6bca9fe307",
                }[relative]
                source = source.replace(old, hashlib.sha256(content).hexdigest())
            fixture = root / "fixture.py"
            fixture.write_text(source.replace(
                'SOURCE = Path(__file__).resolve().parents[1] / "compat" / "hermes" / "himalaya-v2"',
                f'SOURCE = Path({str(SCRIPT.parents[1] / "compat/hermes/himalaya-v2")!r})'), encoding="utf-8")
            command = [sys.executable, str(fixture), "--hermes-home", str(home),
                       "--himalaya-bin", str(binary)]
            first = subprocess.run([*command, "--apply"], capture_output=True, text=True)
            self.assertEqual(first.returncode, 0, first.stderr)
            self.assertIn("--no-save", (skill / "SKILL.md").read_text(encoding="utf-8"))
            backup = home / "backups/friday-himalaya-v1" / hashlib.sha256(original["SKILL.md"]).hexdigest()
            self.assertEqual((backup / "SKILL.md").read_bytes(), original["SKILL.md"])
            again = subprocess.run([*command, "--apply"], capture_output=True, text=True)
            self.assertEqual(again.returncode, 0, again.stderr)
            self.assertIn("already installed", again.stdout)
            (skill / "SKILL.md").write_text("upstream changed", encoding="utf-8")
            unknown = subprocess.run([*command, "--apply"], capture_output=True, text=True)
            self.assertEqual(unknown.returncode, 3)
            self.assertEqual((skill / "SKILL.md").read_text(encoding="utf-8"), "upstream changed")


if __name__ == "__main__":
    unittest.main()
