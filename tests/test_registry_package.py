import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch
from zipfile import ZipFile

from scripts.build_registry import build, load_skill_capabilities, CAPABILITIES, ROOT
from scripts.export_package import export
from shared.policy import capability_available


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

    def test_capability_manifest_covers_every_skill_and_references_known_ids(self):
        generated = build()["capabilities.yaml"]
        names = {item["name"] for item in json.loads((ROOT / "registry/skills.json").read_text(encoding="utf-8"))["skills"]}
        self.assertEqual(set(generated["skill_requirements"]), names)
        self.assertEqual(set(generated["capabilities"]), set(CAPABILITIES))
        self.assertTrue(all(not item["live_available"] and not item["mock_available"]
                            for item in generated["capabilities"].values()))
        self.assertEqual(generated["status"], "logical_contract_only")
        for record in generated["skill_requirements"].values():
            self.assertEqual(set(record), {"required", "conditional"})
            self.assertTrue(set(record["required"] + record["conditional"]) <= set(CAPABILITIES))

    def test_malformed_capability_manifest_fails_closed(self):
        source = json.loads((ROOT / "registry/skill_capabilities.json").read_text(encoding="utf-8"))
        entries = json.loads((ROOT / "registry/skills.json").read_text(encoding="utf-8"))["skills"]
        names = {entry["name"] for entry in entries}
        with TemporaryDirectory() as folder:
            temporary_registry = Path(folder)
            manifest_file = temporary_registry / "skill_capabilities.json"
            with patch("scripts.build_registry.REGISTRY", temporary_registry):
                missing = json.loads(json.dumps(source))
                del missing["skills"]["friday-weather"]
                manifest_file.write_text(json.dumps(missing), encoding="utf-8")
                with self.assertRaisesRegex(ValueError, "cover exactly"):
                    load_skill_capabilities(names, entries)
                typo = json.loads(json.dumps(source))
                typo["skills"]["friday-weather"]["conditional"].append("weather.reed")
                manifest_file.write_text(json.dumps(typo), encoding="utf-8")
                with self.assertRaisesRegex(ValueError, "unknown or duplicate"):
                    load_skill_capabilities(names, entries)
                unsafe = json.loads(json.dumps(source))
                unsafe["skills"]["friday-loxone-control"]["conditional"].remove("loxone.write")
                unsafe["skills"]["friday-loxone-control"]["required"].append("loxone.write")
                manifest_file.write_text(json.dumps(unsafe), encoding="utf-8")
                with self.assertRaisesRegex(ValueError, "side-effect capability"):
                    load_skill_capabilities(names, entries)
                manifest_file.write_text(json.dumps(source), encoding="utf-8")
                fake_skill = temporary_registry / "SKILL.md"
                fake_skill.write_text("Required capability: bogus.read for current data.\n", encoding="utf-8")
                with self.assertRaisesRegex(ValueError, "unknown capability IDs in procedure"):
                    load_skill_capabilities(names, [{"name": "friday-weather", "path": str(fake_skill)}])

    def test_live_action_capabilities_are_explicitly_conditional_and_unavailable(self):
        generated = build()["capabilities.yaml"]
        requirements = generated["skill_requirements"]
        expected = {
            "friday-loxone-control": "loxone.write",
            "friday-home-scene-manager": "loxone.write",
            "friday-calendar-manager": "calendar.write",
            "friday-executive-mail-manager": "mail.send",
            "friday-telegram-communication": "telegram.send",
            "friday-whatsapp-communication": "whatsapp.send",
            "friday-phone-call-coordinator": "telephony.call",
            "friday-service-recovery": "service.restart",
            "friday-archive-migrator": "file.write",
        }
        for skill, capability_id in expected.items():
            self.assertIn(capability_id, requirements[skill]["conditional"])
            self.assertNotIn(capability_id, requirements[skill]["required"])
            self.assertFalse(capability_available(generated["capabilities"][capability_id], permission="write", mode="live"))
        self.assertEqual(generated["capabilities"]["payment.execute"]["mode"], "hard_approval")
        self.assertNotIn("payment.execute", requirements["friday-payment-preparation"]["conditional"])
        self.assertFalse(capability_available(generated["capabilities"]["mail.read"], permission="read", mode="read_only"))

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
                self.assertIn("friday-skills/pyproject.toml", names)
                self.assertIn("friday-skills/.github/workflows/ci.yml", names)


if __name__ == "__main__":
    unittest.main()
