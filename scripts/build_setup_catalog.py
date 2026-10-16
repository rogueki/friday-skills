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
    "discord_gateway", "imap_smtp_mail", "loxone", "messaging_gateway", "telegram_gateway", "telephony",
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
    "caldav": ("CalDAV-Server-URL der Kalendersammlung (mit abschließendem /), Benutzername und App-Passwort unter Friday Dashboard > Einstellungen > Adapter eintragen; der Dashboard-Kalender liest CalDAV und kann nach Vorschau und ausdrücklicher Besitzerbestätigung einen neuen Termin anlegen. Ein ICS-Feed bleibt lesend. Der Installer richtet für Hermes einen separaten lokalen Kalenderleser ein, der die im Dashboard konfigurierte Quelle ohne eigene Anbieter-Credentials liest. Er stellt keinen Schreibzugriff bereit. Der ältere separate Friday-Skills-CalDAV-Adapter benötigt weiterhin eine eigene authentifizierte Host-Bindung. Google-CalDAV mit direkter OAuth-Anmeldung und Outlook Graph sind hier nicht abgedeckt. Für Google/Outlook kann eine veröffentlichte ICS-URL lesend genutzt werden.", "docs/CALDAV_ADAPTER.md", "/settings?area=adapters#calendar-setup-title"),
    "carddav": ("Kontaktanbieter, CardDAV-URL und Konto erst wählen; ein produktiver Kontakt-Reader ist noch nicht implementiert.", "skills/executive/friday-contact-context/SKILL.md", "Host: CardDAV-Provider noch offen"),
    "control_api": ("Lokale Dashboard-Owner-Session und CSRF an den Host binden, Bridge separat aktivieren; dies ist lokale Anmeldung, kein zusätzliches externes Konto.", "docs/CONTENT_STUDIO.md", "Hermes-Prozess: FRIDAY_CONTROL_API_ORIGIN/SESSION/CSRF"),
    "document_parser": ("Freigegebene Dokumentpfade und Parser je Dateityp auswählen; der vorhandene PDF-Parser deckt nur begrenzte Rechnungsfälle ab.", "docs/INVOICE_ADAPTER.md", "Host: Dokumentleser und erlaubte Pfade"),
    "document_worker": ("Lokalen Dokument-Worker und Ausgabeordner bereitstellen; erzeugte Seiten rendern und prüfen.", "docs/CONFIGURATION.md", "Host: lokaler Dokument-Worker"),
    "energy_telemetry": ("Zählerquelle, Messgrenzen, Einheit und Zeitstempel festlegen; kein allgemeiner Live-Telemetrieadapter enthalten.", "docs/CAPABILITIES.md", "Host: Energie-Messquelle"),
    "finance": ("Finanzdatenquelle und berechtigte Konto-/Ledger-Lesewege hostseitig auswählen; hier gibt es keinen allgemeinen Live-Finanzadapter.", "docs/CAPABILITIES.md", "Host: Finanz-Ledger/Provider noch offen"),
    "finanzonline": ("FinanzOnline-Zugang und zulässigen Einreichungsweg erst separat prüfen; dieses Paket hat keinen Submit-Adapter.", "docs/CAPABILITIES.md", "Host: FinanzOnline-Anbindung noch offen"),
    "imap_smtp_mail": ("E-Mail-Postfach eines passenden Anbieters mit IMAP- und SMTP-Server, Ports/TLS, Benutzername und Passwort oder App-Passwort unter Friday Dashboard > Einstellungen > Skill-Konten einrichten. Das Owner-Panel kann über das verwaltete Himalaya-v2-Postfach lesen und nach ausdrücklicher Bestätigung eine Textmail per SMTP senden. Diese Dashboard-Konfiguration bindet die Friday-Skills-Mail-Capabilities nicht automatisch an Hermes oder einen Anbieteradapter; der Skill-Laufzeitstatus bleibt ohne separate Host-Bindung und Prüfung unbekannt.", "docs/SETUP_CATALOG.md", "/settings?area=skillAccounts#himalaya-account-title"),
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
    "telegram_gateway": ("Im Friday Dashboard unter Einstellungen > Skill-Konten > Telegram BotFather-Token und numerische erlaubte User-ID einrichten. Das installierte Hermes-Gateway kann Telegram-Nachrichten verarbeiten; gespeicherte Werte und laufender Dienst belegen noch keine erfolgreiche Bot-Verbindung oder Empfängeridentität.", "skills/communication/friday-telegram-communication/SKILL.md", "Friday Dashboard > Einstellungen > Skill-Konten > Telegram"),
    "telephony": ("Den optionalen Asterisk-SIP-Adapter im Friday Dashboard unter Einstellungen > Skill-Konten > Telefonie einrichten. Lokale Nebenstellen benötigen eigene SIP-Endpunkte; externe Nummern zusätzlich einen registrierten SIP-Trunk und bestätigte Ziele. Adapterstatus und SIP-Trunk separat prüfen.", "skills/communication/friday-phone-call-coordinator/SKILL.md", "Friday Dashboard > Einstellungen > Skill-Konten > Telefonie"),
    "weather": ("Öffentlichen Wetterleser bei Bedarf separat als Hermes-Plugin aktivieren; kein Konto nötig.", "docs/WEATHER_PLUGIN.md", "Hermes: optionales Wetter-Plugin"),
    "web_fetch": ("Erlaubte Webquellen und Host-Egress konfigurieren; Zugriff je Quelle prüfen.", "docs/WEB_EXTRACTION_ADAPTER.md", "Host: Web-Egress-Allowlist"),
    "whatsapp_gateway": ("Im Friday Dashboard unter Einstellungen > Skill-Konten > WhatsApp das lokale Hermes-Dashboard zur QR-Kopplung öffnen; danach Modus und erlaubte Telefonnummer mit Ländervorwahl ohne + einrichten. Friday zeigt die Session-Datei und Gateway-Konfiguration, keine bestätigte Verbindung oder Nachrichtenzustellung.", "skills/communication/friday-whatsapp-communication/SKILL.md", "Friday Dashboard > Einstellungen > Skill-Konten > WhatsApp"),
    "discord_gateway": ("Im Friday Dashboard unter Einstellungen > Skill-Konten > Discord Bot-Token, numerische erlaubte User-ID und optional Kanal-IDs einrichten. Discord Developer Portal: Message Content Intent aktivieren und Bot einladen. Gespeicherte Konfiguration beweist weder Verbindung noch Nachrichtenzustellung.", "skills/communication/friday-discord-communication/SKILL.md", "Friday Dashboard > Einstellungen > Skill-Konten > Discord"),
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
    "friday-phone-call-coordinator": ["cloudtalk_api"],
    "friday-executive-mail-manager": ["gmx"],
    "friday-mail-attachment-intake": ["gmx"],
    "friday-mail-draft-writer": ["gmx"],
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
    "cloudtalk_api": ("Für den optionalen CloudTalk-API-Anrufweg im Friday Dashboard unter Einstellungen > Skill-Konten > CloudTalk Desktop und API ein Admin-API-Zugangsschlüsselpaar (Access Key ID und Secret) sowie die CloudTalk Agent-ID einrichten. CloudTalk API-Zugang setzt einen dafür berechtigten Tarif (Essential oder höher) voraus. Gespeicherte Zugangsdaten bestätigen weder API-Erreichbarkeit noch Anrufannahme oder Erreichbarkeit des Ziels. Der Desktop-Handoff über ct+tel benötigt keine API-Zugangsdaten; er öffnet nur die CloudTalk-App und liefert Friday weder Gesprächsaudio noch Status oder Auflegen.", "skills/communication/friday-phone-call-coordinator/SKILL.md", "required", "/settings?area=skillAccounts#cloudtalk-setup-title"),
    "gmx": ("Den eigenständigen Friday-Skills-GMX-Adapter mit einem GMX-Postfach und authentifizierter Host-Bindung bereitstellen. Das Dashboard-Postfach richtet diesen Adapter nicht automatisch ein; Mailbox-Suche, vollständige Threads, Anhangsbytes und ein live verifizierter Versand sind damit nicht belegt.", "docs/GMX_MAIL_ADAPTER.md", "required", "Host: separater Friday-Skills-GMX-Adapter"),
    "friday_local_calendar": ("Den lokalen Kalender im Friday Dashboard mit Owner-Anmeldung ohne externes Anbieterkonto öffnen; dort lassen sich Termine lesen und verwalten. Der separate Hermes-Kalenderleser kann lokale Termine über die Dashboard-Bridge nur lesen und bleibt schreibgeschützt.", "skills/calendar/friday-calendar-manager/SKILL.md", "none", "/calendar"),
    "kie_ai": ("Kie.ai-Konto und Server-Key in den Dashboard-Einstellungen hinterlegen; kostenpflichtige Anfrage einzeln bestätigen.", "docs/CONTENT_STUDIO.md", "required", "Dashboard Settings → Content Studio → kie.ai"),
    "elevenlabs": ("ElevenLabs-Konto, Server-Key und Voice-ID in den Dashboard-Einstellungen hinterlegen; Anfrage einzeln bestätigen.", "docs/CONTENT_STUDIO.md", "required", "Dashboard Settings → Content Studio → ElevenLabs"),
    "video_editor": ("CapCut oder lokalen Videoeditor für manuellen Handoff bereitstellen; keine Editor-Automation voraussetzen.", "docs/CONTENT_STUDIO.md", "none", "lokaler Editor"),
    "obsidian": ("Optionalen lokalen Vault-Pfad freigeben; Hermes-Bundleskill nutzt Dateitools und benötigt kein Cloud-Konto.", "skills/knowledge/friday-knowledge-base-curator/SKILL.md", "none", "Hermes: OBSIDIAN_VAULT_PATH"),
    "coding_cli": ("Für Codeaufgaben optional OpenCode, Codex oder Claude Code im Hermes-Laufzeitkontext bereitstellen; CLI-Version, eigene Modell-Anmeldung und Projektzugriff vor einem Auftrag prüfen.", "docs/HERMES_WORKFLOWS.md", "conditional", "/settings?area=skillAccounts#coding-cli-setup-title"),
    "computer_use": ("Hermes-Computer-Use-Werkzeug und Desktop-Treiber im aktiven Laufzeitkontext prüfen; ein installierter Skill beweist keine benutzbare GUI-Verbindung.", "docs/HERMES_WORKFLOWS.md", "none", "Hermes: computer_use und lokaler Desktop-Treiber"),
    "powerpoint_playback": ("Zielversion von PowerPoint für Animations-Playback und Sichtprüfung bereitstellen.", "skills/office/friday-powerpoint-animation-director/SKILL.md", "none", "lokaler Windows-Office-Worker"),
}

# Diese Hinweise beschreiben Einrichtungsvoraussetzungen und mögliche Kosten,
# keine aktuelle Berechtigung oder Anbieterpreise. Scopes werden nie aus einem
# Konto oder Zugangsschlüssel abgeleitet.
COST_PROFILES = {
    "weather": ("host_resources", "Der mitgelieferte öffentliche Wetterleser benötigt kein Anbieter-Konto. Friday nutzt weiterhin Netzwerk- und Hostressourcen; mögliche Hostingkosten hängen von der Umgebung ab."),
    "official_web_fetch": ("host_resources", "Der Abruf nutzt Netzwerk- und Hostressourcen. Kosten für ausgewählte Quellen oder Hosting hängen vom Anbieter und der Umgebung ab."),
    "web_fetch": ("host_resources", "Der Abruf nutzt Netzwerk- und Hostressourcen. Kosten für ausgewählte Quellen oder Hosting hängen vom Anbieter und der Umgebung ab."),
    "friday_local_calendar": ("host_resources", "Der lokale Friday-Kalender nutzt Host- und Speicherressourcen; für diesen Pfad ist kein externes Kalenderkonto erforderlich."),
    "obsidian": ("host_resources", "Der lokale Vault nutzt Datei- und Speicherressourcen des Hosts; für diesen Ablauf ist kein Obsidian-Cloud-Abo erforderlich."),
    "computer_use": ("unknown", "Kosten für Desktop-Software, Betriebssystemlizenz und Hostressourcen hängen von der gewählten Laufzeitumgebung ab."),
    "powerpoint_playback": ("unknown", "PowerPoint-Lizenz und Hostressourcen hängen von der installierten Office-Version und deren Lizenz ab."),
    "video_editor": ("unknown", "Der gewählte Editor kann ein Abo oder eine Lizenz erfordern; die konkrete Ausgabe ist hier nicht festgelegt."),
    "coding_cli": ("unknown", "CLI-Lizenz, Modellnutzung und Hostressourcen hängen von OpenCode, Codex oder Claude Code und deren Einrichtung ab."),
    "cloudtalk_api": ("unknown", "Tarifberechtigung und Gesprächskosten hängen vom CloudTalk-Konto und Ziel ab; konkrete Preise werden hier nicht angegeben."),
    "kie_ai": ("provider_usage", "Für Anfragen können nutzungsabhängige Anbietergebühren anfallen. Aktuelle Kontopreise und Guthaben wurden hier nicht geprüft."),
    "elevenlabs": ("provider_usage", "Es können nutzungsabhängige Anbietergebühren oder Tarifgrenzen gelten. Aktuelle Kontopreise und Guthaben wurden hier nicht geprüft."),
}


def permission_and_cost(adapter: str, account: str, auth_kind: str) -> dict:
    """Erzeugt statische Hinweise, ohne einem Konto API-Scopes zuzuschreiben."""
    required = [{"kind": "host_access", "status": "required",
                 "notice": "Bei Aktivierung muss der Host nur die lokalen Ressourcen oder ausgehenden Netzwerkzugriffe bereitstellen, die diese Integration benötigt. Die genauen Freigaben hängen von der gewählten Implementierung ab."}]
    optional = []
    if auth_kind == "local_session":
        required.append({"kind": "local_session", "status": "required",
                         "notice": "Erforderlich sind eine vom Host authentifizierte Owner-Sitzung und deren CSRF-Schutz."})
    elif account == "required":
        required.append({"kind": "provider_account", "status": "required",
                         "notice": "Bei Nutzung dieser Integration muss das oben beschriebene Konto beim gewählten Anbieter eingerichtet sein."})
    elif account == "conditional":
        optional.append({"kind": "provider_account", "status": "optional",
                         "notice": "Nur erforderlich, wenn diese optionale Integration verwendet wird."})

    # Bei den meisten Einträgen sind Anbieter und Host nicht festgelegt. Auch
    # mit Zugangsdaten müssen die tatsächlich gewährten Rechte separat geprüft werden.
    scope_status = "unknown"
    scope_notice = ("Die konkreten Anbieter-/API-Scopes und Host-Freigaben sind in diesem Katalog nicht festgelegt. Nur die vom gewählten Anbieter und Host unterstützten Mindestberechtigungen einrichten und prüfen. Ein Konto oder Zugangsschlüssel belegt keine erteilten Rechte.")
    if adapter in {"weather", "friday_local_calendar", "obsidian"}:
        scope_status = "not_required"
        scope_notice = "Für diesen beschriebenen Ablauf ist kein externer Anbieter-OAuth-/API-Scope erforderlich. Hostzugriff und Einschränkungen der gewählten Quellen gelten weiterhin."

    profile = COST_PROFILES.get(adapter)
    if profile:
        cost_model, cost_notices = profile
    elif account != "none":
        cost_model = "unknown"
        cost_notices = "Anbietergebühren, Abos/Lizenzen und enthaltene Kontingente hängen vom gewählten Anbieter und Konto ab. Dieser Katalog behauptet weder konkrete Preise noch Tarifansprüche."
    else:
        cost_model = "unknown"
        cost_notices = "Zusätzliche Kosten für Ressourcen, Softwarelizenzen oder Dienste hängen von der gewählten Implementierung und dem Host ab."

    return {
        "permissions": {
            "required_prerequisites": required,
            "optional_prerequisites": optional,
            "scope_status": scope_status,
            "scope_notice": scope_notice,
        },
        "cost": {"model": cost_model, "notice": cost_notices},
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
        auth_kind = "local_session" if adapter == "control_api" else "provider_account" if account == "required" else "none_or_optional"
        integrations[adapter] = {"account": account, "setup_de": instruction, "reference": reference,
                                 "settings_target": target, "auth_kind": auth_kind,
                                 **permission_and_cost(adapter, account, auth_kind)}
    for name, (instruction, reference, account, target) in EXTRA_SETUP.items():
        auth_kind = "provider_account" if account == "required" else "none_or_optional"
        integrations[name] = {"account": account, "setup_de": instruction, "reference": reference,
                              "settings_target": target, "auth_kind": auth_kind,
                              **permission_and_cost(name, account, auth_kind)}
    records = {}
    for entry in skills:
        name = entry["name"]
        record = capabilities[name]
        required = sorted({CAPABILITIES[cap][0] for cap in record["required"]})
        conditional = sorted(({CAPABILITIES[cap][0] for cap in record["conditional"]} | set(EXTRA.get(name, []))) - set(required))
        if name == "friday-calendar-manager":
            # The default calendar capability points to CalDAV for other skills;
            # this manager can start with Friday's local calendar instead.
            required = ["friday_local_calendar"]
            conditional = sorted(set(conditional) | {"caldav"})
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
            setup = ("Gesprächsplan ohne Konto möglich. Anrufe erfordern einen separat eingerichteten Telefonieweg: optional CloudTalk-API-Konto "
                     "(Admin-API-Schlüsselpaar und Agent-ID, berechtigter Tarif) oder Asterisk/SIP-Adapter mit registriertem SIP-Trunk. "
                     "CloudTalk-Desktop-Handoff benötigt keine API-Zugangsdaten, übergibt nur die Nummer an die App und liefert Friday kein Audio oder Anrufstatus. "
                     "Eingerichtete Zugangsdaten beweisen weder Provider-Verbindung noch Zielannahme. CardDAV ist nur eine optionale Kontaktquelle; "
                     "der Skill selbst führt keine Gespräche und erhält keinen autonomen Wählzugriff.")
        records[name] = {"required_capabilities": record["required"], "conditional_capabilities": record["conditional"],
                         "required_integrations": required, "conditional_integrations": conditional,
                         "account": account, "setup_de": setup.strip(),
                         "live_status": "unknown"}
    compatibility = {name: {"distribution": distribution, "official_url": url, "setup_de": guidance,
                            "installed_status": "unknown", "friday_requirement": "optional"}
                     for name, (distribution, url, guidance) in HERMES_COMPATIBILITY.items()}
    return {"schema_version": 2, "inventory_source": "registry/skills.json", "inventory_count": len(skills),
            "status_semantics": "unknown bedeutet: keine aktuelle Hermes- oder Anbieterprüfung durch diesen Katalog.",
            "integrations": integrations, "hermes_compatibility": compatibility, "skills": records}


if __name__ == "__main__":
    path = ROOT / "registry/integration_setup.json"
    path.write_text(json.dumps(build(), ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"wrote {path}")
