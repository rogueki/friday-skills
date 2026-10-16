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
        registry = json.loads((ROOT / "registry/skills.json").read_text(encoding="utf-8"))
        registered_names = {item["name"] for item in registry["skills"]}
        self.assertEqual(set(self.catalog["skills"]), registered_names)
        self.assertEqual(len(self.catalog["skills"]), len(registered_names))
        self.assertEqual(validate(self.catalog), [])
        self.assertTrue(all(item["live_status"] == "unknown" for item in self.catalog["skills"].values()))
        self.assertEqual(self.catalog["schema_version"], 2)
        referenced = {
            integration
            for skill in self.catalog["skills"].values()
            for integration in skill["required_integrations"] + skill["conditional_integrations"]
        }
        self.assertTrue(referenced <= set(self.catalog["integrations"]))
        for integration in referenced:
            setup = self.catalog["integrations"][integration]
            self.assertIn(setup["permissions"]["scope_status"], {"unknown", "not_required"})
            self.assertTrue(setup["permissions"]["scope_notice"])
            self.assertIsInstance(setup["permissions"]["required_prerequisites"], list)
            self.assertIsInstance(setup["permissions"]["optional_prerequisites"], list)
            self.assertIn(setup["cost"]["model"], {"host_resources", "provider_usage", "subscription_license", "none", "unknown"})
            self.assertTrue(setup["cost"]["notice"])

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

    def test_permission_and_cost_schema_fail_closed(self):
        changed = copy.deepcopy(self.catalog)
        del changed["integrations"]["gmx"]["permissions"]
        self.assertTrue(any("permission notice missing" in error for error in validate(changed)))
        changed = copy.deepcopy(self.catalog)
        changed["integrations"]["gmx"]["permissions"]["required_prerequisites"][0]["status"] = "optional"
        self.assertTrue(any("invalid required permission prerequisite" in error for error in validate(changed)))
        changed = copy.deepcopy(self.catalog)
        changed["integrations"]["gmx"]["cost"]["model"] = "free"
        self.assertTrue(any("invalid cost notice" in error for error in validate(changed)))

    def test_account_and_hermes_compatibility_semantics(self):
        self.assertEqual(self.catalog["integrations"]["control_api"]["account"], "none")
        self.assertEqual(self.catalog["integrations"]["control_api"]["auth_kind"], "local_session")
        self.assertIn("local_session", {item["kind"] for item in self.catalog["integrations"]["control_api"]["permissions"]["required_prerequisites"]})
        self.assertEqual(self.catalog["integrations"]["gmx"]["permissions"]["scope_status"], "unknown")
        self.assertIn("belegt keine erteilten Rechte", self.catalog["integrations"]["gmx"]["permissions"]["scope_notice"])
        self.assertEqual(self.catalog["integrations"]["weather"]["cost"]["model"], "host_resources")
        for name in ("web_fetch", "official_web_fetch"):
            self.assertEqual(self.catalog["integrations"][name]["permissions"]["scope_status"], "unknown")
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
        self.assertEqual(phone["conditional_integrations"], ["carddav", "cloudtalk_api", "telephony"])
        self.assertIn("CloudTalk-API-Konto", phone["setup_de"])
        self.assertIn("keinen autonomen Wählzugriff", phone["setup_de"])
        self.assertIn("Asterisk-SIP-Adapter", self.catalog["integrations"]["telephony"]["setup_de"])
        self.assertIn("SIP-Trunk", self.catalog["integrations"]["telephony"]["setup_de"])
        cloudtalk = self.catalog["integrations"]["cloudtalk_api"]
        self.assertEqual(cloudtalk["account"], "required")
        self.assertEqual(cloudtalk["settings_target"], "/settings?area=skillAccounts#cloudtalk-setup-title")
        self.assertIn("Access Key ID und Secret", cloudtalk["setup_de"])
        self.assertIn("Agent-ID", cloudtalk["setup_de"])
        self.assertIn("weder API-Erreichbarkeit", cloudtalk["setup_de"])
        self.assertIn("ct+tel", cloudtalk["setup_de"])
        self.assertIn("weder Gesprächsaudio noch Status oder Auflegen", cloudtalk["setup_de"])

    def test_calendar_uses_local_baseline_with_optional_caldav(self):
        calendar = self.catalog["skills"]["friday-calendar-manager"]
        self.assertEqual(calendar["required_integrations"], ["friday_local_calendar"])
        self.assertEqual(calendar["conditional_integrations"], ["caldav"])
        self.assertEqual(calendar["account"], "conditional")
        self.assertEqual(self.catalog["integrations"]["friday_local_calendar"]["account"], "none")
        self.assertIn("ohne externes Anbieterkonto", calendar["setup_de"])

    def test_dashboard_setup_links_and_mail_capability_are_precise(self):
        integrations = self.catalog["integrations"]
        self.assertEqual(integrations["caldav"]["settings_target"], "/settings?area=adapters#calendar-setup-title")
        self.assertIn("Host-Bindung", integrations["caldav"]["setup_de"])
        self.assertEqual(integrations["imap_smtp_mail"]["settings_target"], "/settings?area=skillAccounts#himalaya-account-title")
        self.assertIn("eines passenden Anbieters", integrations["imap_smtp_mail"]["setup_de"])
        self.assertIn("nicht automatisch", integrations["imap_smtp_mail"]["setup_de"])
        self.assertEqual(integrations["gmx"]["settings_target"], "Host: separater Friday-Skills-GMX-Adapter")
        self.assertIn("eigenständigen", integrations["gmx"]["setup_de"])
        self.assertEqual(integrations["coding_cli"]["settings_target"], "/settings?area=skillAccounts#coding-cli-setup-title")

    def test_mail_capabilities_use_generic_account_and_gmx_remains_optional(self):
        mail_skills = {
            name: item for name, item in self.catalog["skills"].items()
            if {"mail.read", "mail.send"} & set(item["required_capabilities"] + item["conditional_capabilities"])
        }
        self.assertEqual(len(mail_skills), 12)
        for item in mail_skills.values():
            self.assertIn("imap_smtp_mail", item["required_integrations"] + item["conditional_integrations"])
            self.assertNotIn("gmx", item["required_integrations"])
            self.assertEqual(item["live_status"], "unknown")
        for name in ("friday-executive-mail-manager", "friday-mail-attachment-intake", "friday-mail-draft-writer"):
            self.assertIn("gmx", mail_skills[name]["conditional_integrations"])


if __name__ == "__main__":
    unittest.main()
