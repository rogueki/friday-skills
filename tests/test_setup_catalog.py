import copy
import json
import unittest

from scripts.build_registry import ROOT
from scripts.build_setup_catalog import build
from scripts.validate_setup_catalog import validate


class SetupCatalogTests(unittest.TestCase):
    def setUp(self):
        self.catalog = json.loads((ROOT / "registry/integration_setup.json").read_text(encoding="utf-8"))

    def test_exact_inventory_and_capability_parity(self):
        self.assertEqual(self.catalog, build())
        self.assertEqual(len(self.catalog["skills"]), 105)
        self.assertEqual(validate(self.catalog), [])
        self.assertTrue(all(item["live_status"] == "unknown" for item in self.catalog["skills"].values()))

    def test_missing_skill_and_invalid_references_fail(self):
        changed = copy.deepcopy(self.catalog)
        del changed["skills"]["friday-weather"]
        self.assertTrue(any("registered skills" in error for error in validate(changed)))
        changed = copy.deepcopy(self.catalog)
        changed["skills"]["friday-weather"]["required_integrations"].append("made_up")
        self.assertTrue(any("required_integrations" in error for error in validate(changed)))
        changed = copy.deepcopy(self.catalog)
        changed["integrations"]["gmx"]["reference"] = "docs/missing.md"
        self.assertTrue(any("invalid reference" in error for error in validate(changed)))

    def test_status_and_secret_values_fail(self):
        changed = copy.deepcopy(self.catalog)
        changed["skills"]["friday-weather"]["live_status"] = "ready"
        self.assertTrue(any("live status" in error for error in validate(changed)))
        changed = copy.deepcopy(self.catalog)
        changed["integrations"]["gmx"]["setup_de"] += " api_key=abc12345"
        self.assertTrue(any("secret" in error for error in validate(changed)))

    def test_account_and_hermes_compatibility_semantics(self):
        self.assertEqual(self.catalog["integrations"]["control_api"]["account"], "none")
        self.assertEqual(self.catalog["integrations"]["control_api"]["auth_kind"], "local_session")
        for name in ("obsidian", "computer_use"):
            self.assertEqual(self.catalog["integrations"][name]["account"], "none")
        self.assertEqual(self.catalog["hermes_compatibility"]["telephony"]["distribution"], "not_bundled")
        self.assertTrue(all(item["installed_status"] == "unknown" for item in self.catalog["hermes_compatibility"].values()))
        changed = copy.deepcopy(self.catalog)
        changed["integrations"]["banking"]["setup_de"] = "Schnittstelle konfigurieren."
        self.assertTrue(any("generated source" in error for error in validate(changed)))


if __name__ == "__main__":
    unittest.main()
