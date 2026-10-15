import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from zipfile import ZipFile

from scripts.build_registry import build, ROOT
from scripts.export_package import export


class RegistryAndPackageTests(unittest.TestCase):
    def test_automations_are_disabled_and_targets_are_known(self):
        records = build()["automations.yaml"]["automations"]
        names = {item["plan_name"].replace("jarvis-", "friday-", 1)
                 for item in json.loads((ROOT / "registry/roadmap.json").read_text(encoding="utf-8"))["skills"]}
        self.assertEqual(len(records), 15)
        self.assertTrue(all(not record["enabled"] and record["skill"] in names for record in records))

    def test_routing_and_dashboard_cover_registered_skills(self):
        generated = build()
        names = {item["name"] for item in json.loads((ROOT / "registry/skills.json").read_text(encoding="utf-8"))["skills"]}
        routes = generated["routing.yaml"]["routes"]
        self.assertEqual({route["skills"][0] for route in routes}, names)
        intents = [intent for route in routes for intent in route["intents"]]
        self.assertEqual(len(intents), len(set(intents)))
        self.assertTrue(all(route["intents"] for route in routes))
        self.assertEqual(set(generated["dashboard.yaml"]["skills"]), names)

    def test_zip_is_reproducible_and_omits_local_memory(self):
        with TemporaryDirectory() as folder:
            first = Path(folder) / "first.zip"
            second = Path(folder) / "second.zip"
            self.assertGreater(export(first), 0)
            export(second)
            self.assertEqual(first.read_bytes(), second.read_bytes())
            with ZipFile(first) as archive:
                names = archive.namelist()
                self.assertFalse(any("MEMORY.md" in name or "SCOPE.md" in name or ".env" in name for name in names))
                self.assertTrue(any(name.endswith("SKILL.md") for name in names))


if __name__ == "__main__":
    unittest.main()
