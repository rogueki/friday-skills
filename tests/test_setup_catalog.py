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

    def test_phone_setup_keeps_dial_provider_separate_from_contacts(self):
        phone = self.catalog["skills"]["friday-phone-call-coordinator"]
        self.assertEqual(phone["account"], "conditional")
        self.assertEqual(phone["conditional_integrations"], ["carddav", "telephony"])
        self.assertLess(phone["setup_de"].index("Telefonie-Provider"), phone["setup_de"].index("CardDAV"))
        self.assertIn("Dial-Adapter", self.catalog["integrations"]["telephony"]["setup_de"])

    def test_dashboard_setup_links_and_mail_capability_are_precise(self):
        integrations = self.catalog["integrations"]
        self.assertEqual(integrations["caldav"]["settings_target"], "/settings?area=adapters#calendar-setup-title")
        self.assertIn("Host-Bindung", integrations["caldav"]["setup_de"])
        self.assertEqual(integrations["gmx"]["settings_target"], "/settings?area=skillAccounts#himalaya-account-title")
        self.assertIn("ausdrücklicher Bestätigung", integrations["gmx"]["setup_de"])
        self.assertIn("weder automatisch angebunden noch live verifiziert", integrations["gmx"]["setup_de"])
        self.assertEqual(integrations["coding_cli"]["settings_target"], "/settings?area=skillAccounts#coding-cli-setup-title")


if __name__ == "__main__":
    unittest.main()
