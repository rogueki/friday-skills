"""Build static onboarding metadata; never infer a live connection from inventory."""

from __future__ import annotations

import json

try:
    from scripts.build_registry import CAPABILITIES, ROOT
except ModuleNotFoundError:  # direct scripts/validate.py invocation
    from build_registry import CAPABILITIES, ROOT


# Account requirements describe the named service, not current authentication.
ACCOUNT_REQUIRED = {
    "banking", "caldav", "carddav", "finance", "finanzonline",
    "gmx", "loxone", "messaging_gateway", "telegram_gateway", "telephony",
    "whatsapp_gateway",
}
ACCOUNT_CONDITIONAL = {"backup", "notification_gateway", "tariff_source"}

SETUP = {
    "adapter_registry": ("Host muss installierte Adapter mit Zeitstempel und Health-Prüfung melden; Paketliste genügt dafür nicht.", "docs/CAPABILITIES.md", "Host: Adapter-Registry"),
    "alerts": ("Für echte Warnungen eine datierte Alert-Quelle anbinden; hier ist kein allgemeiner Live-Alert-Feed enthalten.", "docs/CAPABILITIES.md", "Host: Alert-Quelle"),
    "approval_store": ("Vertrauenswürdige Betreiberidentität und einmalige aktionsgebundene Freigaben hostseitig bereitstellen.", "docs/APPROVAL_LEDGER.md", "Host: Freigabe-Gateway"),
    "audit_store": ("Audit-Speicher mit unveränderlichen Ereignis-IDs und Schreibrechten des Hosts wählen; Live-Publisher fehlt.", "docs/DASHBOARD_EVENTS.md", "Host: Audit-Speicher"),
    "backup": ("Lokales oder externes Sicherungsziel, Aufbewahrung und Restore-Probe festlegen; kein allgemeiner Backup-Adapter enthalten.", "docs/CAPABILITIES.md", "Host: Backup-Ziel"),
    "banking": ("Bankanbieter und autorisierten Zahlungsweg erst nach eigener Gateway-Implementierung festlegen; hier existiert nur ein nicht ausführbarer Zahlungsentwurf.", "docs/INVOICE_ADAPTER.md", "Bank-Gateway: Anbieter noch offen"),
    "caldav": ("CalDAV-Server-URL, Benutzername und App-Passwort unter Friday Dashboard > Einstellungen > Adapter eintragen; der Dashboard-Kalender liest kompatible CalDAV-Server oder einen ICS-Feed. Der separate Friday-Skills-CalDAV-Adapter benötigt weiterhin eine eigene authentifizierte Host-Bindung. Google-CalDAV mit direkter OAuth-Anmeldung und Outlook Graph sind hier nicht abgedeckt. Für Google/Outlook kann eine veröffentlichte ICS-URL lesend genutzt werden.", "docs/CALDAV_ADAPTER.md", "/settings?area=adapters#calendar-setup-title"),
    "carddav": ("Kontaktanbieter, CardDAV-URL und Konto erst wählen; ein produktiver Kontakt-Reader ist noch nicht implementiert.", "skills/executive/friday-contact-context/SKILL.md", "Host: CardDAV-Provider noch offen"),
    "control_api": ("Lokale Dashboard-Owner-Session und CSRF an den Host binden, Bridge separat aktivieren; dies ist lokale Anmeldung, kein zusätzliches externes Konto.", "docs/CONTENT_STUDIO.md", "Hermes-Prozess: FRIDAY_CONTROL_API_ORIGIN/SESSION/CSRF"),
    "document_parser": ("Freigegebene Dokumentpfade und Parser je Dateityp auswählen; der vorhandene PDF-Parser deckt nur begrenzte Rechnungsfälle ab.", "docs/INVOICE_ADAPTER.md", "Host: Dokumentleser und erlaubte Pfade"),
    "document_worker": ("Lokalen Dokument-Worker und Ausgabeordner bereitstellen; erzeugte Seiten rendern und prüfen.", "docs/CONFIGURATION.md", "Host: lokaler Dokument-Worker"),
    "energy_telemetry": ("Zählerquelle, Messgrenzen, Einheit und Zeitstempel festlegen; kein allgemeiner Live-Telemetrieadapter enthalten.", "docs/CAPABILITIES.md", "Host: Energie-Messquelle"),
    "finance": ("Finanzdatenquelle und berechtigte Konto-/Ledger-Lesewege hostseitig auswählen; hier gibt es keinen allgemeinen Live-Finanzadapter.", "docs/CAPABILITIES.md", "Host: Finanz-Ledger/Provider noch offen"),
    "finanzonline": ("FinanzOnline-Zugang und zulässigen Einreichungsweg erst separat prüfen; dieses Paket hat keinen Submit-Adapter.", "docs/CAPABILITIES.md", "Host: FinanzOnline-Anbindung noch offen"),
    "gmx": ("E-Mail-Postfach mit IMAP- und SMTP-Server, Ports/TLS, Benutzername und Passwort oder App-Passwort unter Friday Dashboard > Einstellungen > Skill-Konten einrichten. Das Owner-Panel kann über das verwaltete Himalaya-v2-Postfach lesen und nach ausdrücklicher Bestätigung eine Textmail per SMTP senden; ein unklarer Versand wird nicht automatisch wiederholt. Der separate Friday-Skills-GMX-Adapter ist dadurch weder automatisch angebunden noch live verifiziert; kein echtes Anbieterpostfach ist verifiziert.", "docs/SETUP_CATALOG.md", "/settings?area=skillAccounts#himalaya-account-title"),
    "home_telemetry": ("Haus-Sensorquelle und erlaubte Geräte hostseitig wählen; keine allgemeine Live-Haus-Telemetrie vorhanden.", "docs/LOXONE_STATUS_ADAPTER.md", "Host: Sensor-Provider"),
    "local_voice": ("Lokale Sprachpipeline und gegebenenfalls Sprecherprüfung am Host testen.", "docs/CONFIGURATION.md", "Host: lokale Voice-Konfiguration"),
    "loxone": ("Miniserver-Zugang und erlaubte Control-IDs im Host konfigurieren; Provider-Transport gegen echte Hardware prüfen.", "docs/LOXONE_STATUS_ADAPTER.md", "Host: Miniserver und Control-Allowlist"),
    "media_worker": ("Lokales Medienwerkzeug mit freigegebenen Ein- und Ausgabepfaden bereitstellen; Renderfähigkeit je Format prüfen.", "docs/CONTENT_STUDIO.md", "Host: Medien-Worker"),
    "memory_store": ("Lokalen Memory-Speicher und zulässige Schreibpfade wählen; Projektdateien nicht als aktuellen Live-Zustand ausgeben.", "docs/CAPABILITIES.md", "Host: lokaler Memory-Speicher"),
    "messaging_gateway": ("Kanal und Anbieter für Nachrichten getrennt wählen; ein allgemeines authentifiziertes Messaging-Gateway fehlt hier.", "docs/CAPABILITIES.md", "Host: Messaging-Provider noch offen"),
    "meter": ("Konkreten Strom-/Verbrauchszähler, Einheit und Zeitquelle binden; kein universeller Meter-Reader enthalten.", "docs/CAPABILITIES.md", "Host: Zähler-Provider"),
    "model_registry": ("Installierte Modelle und Kosten aus dem laufenden Host auslesen; statische Modellnamen sind kein Verfügbarkeitsnachweis.", "docs/CAPABILITIES.md", "Host: Modell-Registry"),
    "notification_gateway": ("Für Push oder andere Zustellung Kanal, Empfänger und Berechtigung wählen; kein allgemeines Zustell-Gateway enthalten.", "docs/CAPABILITIES.md", "Host: Benachrichtigungs-Provider noch offen"),
    "official_weather": ("Amtliche Warnquelle für die Region und Aktualitätsfenster festlegen; Vorhersage-Plugin deckt Warnungen nicht automatisch ab.", "docs/WEATHER_PLUGIN.md", "Host: amtliche Warnquelle"),
    "official_web_fetch": ("Amtliche URL-Liste und Abrufzeitpunkt je Quelle prüfen; kein Provider-Konto pauschal nötig.", "docs/WEB_EXTRACTION_ADAPTER.md", "Host: erlaubte amtliche URLs"),
    "profile_store": ("Lokalen Profil-Speicher und erlaubte Felder festlegen; keine persönlichen Profile in die Skill-Dateien schreiben.", "docs/CONFIGURATION.md", "Host: lokaler Profil-Speicher"),
    "reminder_store": ("Reminder-Speicher und auslösenden Scheduler getrennt einrichten; CalDAV-Termine allein lösen keine Erinnerung aus.", "docs/CALDAV_ADAPTER.md", "Host: Reminder-Backend noch offen"),
    "scheduler": ("Zeitplan, Zeitzone und Laufzeitprozess einrichten; deklarierte Automationen sind standardmäßig deaktiviert.", "docs/OPERATIONS.md", "Host: Scheduler-Konfiguration"),
    "scoped_filesystem": ("Freigegebene lokale Pfade und Lese-/Schreibrechte im Host begrenzen.", "docs/CONFIGURATION.md", "Host: erlaubte Dateipfade"),
    "service_control": ("Erlaubte Dienst-IDs, Neustartverfahren und Rollback-Checks hostseitig definieren; kein globaler Restart-Zugriff folgt aus dem Skill.", "docs/CAPABILITIES.md", "Host: Service-Allowlist"),
    "service_probes": ("Health-Endpunkte und Frischegrenzen pro Dienst festlegen; Status erst nach echter Probe anzeigen.", "docs/CAPABILITIES.md", "Host: Health-Probes"),
    "storage_probe": ("Freigegebene Laufwerke/Volumes und Messzeitpunkt festlegen; keine Profil- oder Geheimnispfade pauschal scannen.", "docs/CAPABILITIES.md", "Host: Speicher-Probes"),
    "tariff_source": ("Region und aktuellen Tarif-/Vertragsanbieter auswählen; öffentliche Preise ersetzen keinen persönlichen Vertrag.", "docs/CAPABILITIES.md", "Host: Tarifquelle und ggf. Anbieter-Konto"),
    "task_store": ("Task-Backend und Identitätsbindung im Host einrichten; Control-API-Client ist nur mit authentifiziertem Transport nutzbar.", "docs/CONTROL_API_TASKS.md", "Host: Task-Backend/Control API"),
    "telegram_gateway": ("Telegram-Bot oder Benutzeranbindung und verifizierte Owner-ID wählen; ein operativer Friday-Gateway-Adapter fehlt.", "skills/communication/friday-telegram-communication/SKILL.md", "Host: Telegram-Kanal noch offen"),
    "telephony": ("Für echte Anrufe Telefonanbieter, eigene Rufnummer, verifizierte Ziele und Anrufberechtigung festlegen; ein Dial-Adapter fehlt. Ein Kontaktkonto allein schaltet keine Anrufe frei.", "skills/communication/friday-phone-call-coordinator/SKILL.md", "Host: Telefonie-Provider und Dial-Adapter noch offen"),
    "weather": ("Öffentlichen Wetterleser bei Bedarf separat als Hermes-Plugin aktivieren; kein Konto nötig.", "docs/WEATHER_PLUGIN.md", "Hermes: optionales Wetter-Plugin"),
    "web_fetch": ("Erlaubte Webquellen und Host-Egress konfigurieren; Zugriff je Quelle prüfen.", "docs/WEB_EXTRACTION_ADAPTER.md", "Host: Web-Egress-Allowlist"),
    "whatsapp_gateway": ("WhatsApp-Konto/Business-Kanal, Einwilligung und Empfängerbindung klären; ein operativer Friday-Gateway-Adapter fehlt.", "skills/communication/friday-whatsapp-communication/SKILL.md", "Host: WhatsApp-Provider noch offen"),
    "windows_worker": ("Lokalen Office-Renderer samt Fonts bereitstellen und Ausgabe visuell prüfen; PowerPoint-Playback gesondert testen.", "docs/PRESENTATION_MOCK_WORKER.md", "Host: lokaler Office-Renderer"),
}

HERMES_COMPATIBILITY = {
    "powerpoint": ("bundled", "https://hermes-agent.nousresearch.com/docs/user-guide/skills/bundled/productivity/productivity-powerpoint", "PPTX-Arbeit; Render-Abhängigkeiten separat prüfen"),
    "computer-use": ("bundled", "https://hermes-agent.nousresearch.com/docs/user-guide/features/computer-use", "Desktop-Werkzeug; lokalen Treiber und Rechte separat prüfen"),
    "obsidian": ("bundled", "https://hermes-agent.nousresearch.com/docs/user-guide/skills/bundled/note-taking/note-taking-obsidian", "Lokaler Vault-Pfad; kein Obsidian-Cloud-Konto nötig"),
    "opencode": ("bundled", "https://hermes-agent.nousresearch.com/docs/reference/skills-catalog", "Optionale Coding-CLI; CLI und eigene Modell-Anmeldung separat prüfen"),
    "codex": ("bundled", "https://hermes-agent.nousresearch.com/docs/reference/skills-catalog", "Optionale Coding-CLI; CLI und eigene Modell-Anmeldung separat prüfen"),
    "claude-code": ("bundled", "https://hermes-agent.nousresearch.com/docs/reference/skills-catalog", "Optionale Coding-CLI; CLI und eigene Modell-Anmeldung separat prüfen"),
    "telephony": ("not_bundled", "https://hermes-agent.nousresearch.com/docs/reference/toolsets-reference", "Kein hier belegtes eingebautes Dial-Tool; Provider und Adapter separat nötig"),
}

EXTRA = {
    "friday-content-planning": ["control_api"],
    "friday-kie-media": ["control_api", "kie_ai"],
    "friday-elevenlabs-voice": ["control_api", "elevenlabs"],
    "friday-video-editing": ["video_editor"],
    "friday-knowledge-base-curator": ["obsidian"],
    "friday-project-context-builder": ["obsidian", "coding_cli"],
    "friday-file-classifier": ["computer_use"],
    "friday-powerpoint-animation-director": ["powerpoint_playback"],
    "friday-presentation-qa": ["powerpoint_playback"],
}

EXTRA_SETUP = {
    "kie_ai": ("Kie.ai-Konto und Server-Key in den Dashboard-Einstellungen hinterlegen; kostenpflichtige Anfrage einzeln bestätigen.", "docs/CONTENT_STUDIO.md", "required", "Dashboard Settings → Content Studio → kie.ai"),
    "elevenlabs": ("ElevenLabs-Konto, Server-Key und Voice-ID in den Dashboard-Einstellungen hinterlegen; Anfrage einzeln bestätigen.", "docs/CONTENT_STUDIO.md", "required", "Dashboard Settings → Content Studio → ElevenLabs"),
    "video_editor": ("CapCut oder lokalen Videoeditor für manuellen Handoff bereitstellen; keine Editor-Automation voraussetzen.", "docs/CONTENT_STUDIO.md", "none", "lokaler Editor"),
    "obsidian": ("Optionalen lokalen Vault-Pfad freigeben; Hermes-Bundleskill nutzt Dateitools und benötigt kein Cloud-Konto.", "skills/knowledge/friday-knowledge-base-curator/SKILL.md", "none", "Hermes: OBSIDIAN_VAULT_PATH"),
    "coding_cli": ("Für Codeaufgaben optional OpenCode, Codex oder Claude Code im Hermes-Laufzeitkontext bereitstellen; CLI-Version, eigene Modell-Anmeldung und Projektzugriff vor einem Auftrag prüfen.", "docs/HERMES_WORKFLOWS.md", "conditional", "/settings?area=skillAccounts#coding-cli-setup-title"),
    "computer_use": ("Hermes-Computer-Use-Werkzeug und Desktop-Treiber im aktiven Laufzeitkontext prüfen; ein installierter Skill beweist keine benutzbare GUI-Verbindung.", "docs/HERMES_WORKFLOWS.md", "none", "Hermes: computer_use und lokaler Desktop-Treiber"),
    "powerpoint_playback": ("Zielversion von PowerPoint für Animations-Playback und Sichtprüfung bereitstellen.", "skills/office/friday-powerpoint-animation-director/SKILL.md", "none", "lokaler Windows-Office-Worker"),
}


def build() -> dict:
    skills = json.loads((ROOT / "registry/skills.json").read_text(encoding="utf-8"))["skills"]
    capabilities = json.loads((ROOT / "registry/skill_capabilities.json").read_text(encoding="utf-8"))["skills"]
    adapters = {value[0] for value in CAPABILITIES.values()}
    if set(SETUP) != adapters:
        raise ValueError(f"setup definitions differ from capability adapters: {sorted(set(SETUP) ^ adapters)}")
    integrations = {}
    for adapter in sorted(adapters):
        instruction, reference, target = SETUP[adapter]
        account = "required" if adapter in ACCOUNT_REQUIRED else "conditional" if adapter in ACCOUNT_CONDITIONAL else "none"
        integrations[adapter] = {"account": account, "setup_de": instruction, "reference": reference,
                                 "settings_target": target, "auth_kind": "local_session" if adapter == "control_api" else "provider_account" if account == "required" else "none_or_optional"}
    for name, (instruction, reference, account, target) in EXTRA_SETUP.items():
        integrations[name] = {"account": account, "setup_de": instruction, "reference": reference,
                              "settings_target": target, "auth_kind": "provider_account" if account == "required" else "none_or_optional"}
    records = {}
    for entry in skills:
        name = entry["name"]
        record = capabilities[name]
        required = sorted({CAPABILITIES[cap][0] for cap in record["required"]})
        conditional = sorted(({CAPABILITIES[cap][0] for cap in record["conditional"]} | set(EXTRA.get(name, []))) - set(required))
        account = "required" if any(integrations[item]["account"] == "required" for item in required) else (
            "conditional" if any(integrations[item]["account"] != "none" for item in required + conditional) else "none")
        def first_step(item: str) -> str:
            return integrations[item]["setup_de"].split(";", 1)[0].rstrip(". ")

        if required:
            setup = "Für den Grundablauf: " + first_step(required[0]) + "."
            if len(required) > 1:
                setup += " Weitere benötigte Quellen stehen in der Integrationsliste."
        else:
            setup = "Der Grundablauf kann mit bereitgestellten oder lokalen Daten beginnen."
        if conditional:
            setup += " Optional: " + first_step(conditional[0]) + "."
            if len(conditional) > 1:
                setup += " Weitere optionale Aktionen stehen in der Integrationsliste."
        if name == "friday-phone-call-coordinator":
            setup = ("Gesprächsplan ohne Konto möglich. Für einen echten Anruf zuerst Telefonie-Provider, "
                     "Rufnummer, Dial-Adapter und Anrufberechtigung einrichten; CardDAV ist nur eine optionale Kontaktquelle.")
        records[name] = {"required_capabilities": record["required"], "conditional_capabilities": record["conditional"],
                         "required_integrations": required, "conditional_integrations": conditional,
                         "account": account, "setup_de": setup.strip(),
                         "live_status": "unknown"}
    compatibility = {name: {"distribution": distribution, "official_url": url, "setup_de": guidance,
                            "installed_status": "unknown", "friday_requirement": "optional"}
                     for name, (distribution, url, guidance) in HERMES_COMPATIBILITY.items()}
    return {"schema_version": 1, "inventory_source": "registry/skills.json", "inventory_count": len(skills),
            "status_semantics": "unknown bedeutet: keine aktuelle Hermes- oder Anbieterprüfung durch diesen Katalog.",
            "integrations": integrations, "hermes_compatibility": compatibility, "skills": records}


if __name__ == "__main__":
    path = ROOT / "registry/integration_setup.json"
    path.write_text(json.dumps(build(), ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"wrote {path}")
