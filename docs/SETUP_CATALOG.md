# Integrations- und Einrichtungskatalog

`registry/integration_setup.json` ist die maschinenlesbare Grundlage für Dashboard-Onboarding. Sie enthält alle derzeit 105 IDs aus `registry/skills.json`. Pro Skill stehen erforderliche und bedingte Capability-IDs, Integrationen, Account-Bedarf (`none`, `conditional`, `required`), eine deutsche Einrichtungshilfe und `live_status` bereit. Eine Integration enthält den Einrichtungsschritt, das Einstellungsziel, eine Dokumentationsreferenz und `auth_kind`. `local_session` bezeichnet die Anmeldung am lokalen Control API; das ist kein weiteres externes Konto.

`required` beschreibt den adaptergestützten Hauptpfad. Verifizierte vom Nutzer bereitgestellte Daten können je nach Skill einen begrenzten Analysepfad erlauben. `conditional` gilt nur für die jeweilige optionale Aktion. Ein Account ist `required`, wenn der Hauptpfad ein Dienstkonto benötigt; ein Konto für eine optionale Aktion führt zu `conditional`. `none` bedeutet, dass für die aufgeführten Integrationen kein externes Konto erforderlich ist, nicht dass die Fähigkeit bereits funktioniert.

Der Katalog ist **Paketmetadatenbestand**. Sein `live_status` ist durchgehend `unknown`. Auch `mock_ready` und `live_adapter_ready` in `registry/skills.json` sind keine aktuelle Hermes- oder Providerdiagnose. Das Dashboard muss Discovery, Plugin-Registrierung, Host-Bindung, Anmeldung, Capability-Frische und End-to-End-Verifikation als getrennte Laufzeitdaten erheben und mit Zeitstempel anzeigen. Ohne diese Daten bleibt der Live-Zustand unbekannt.

## Wichtige Einrichtungen

| Bereich | Einrichtung | Grenze |
| --- | --- | --- |
| GMX | IMAP und gegebenenfalls App-Passwort im Host einrichten; [GMX-Anleitung](GMX_MAIL_ADAPTER.md). | Python-Lese-/Schreibpfade und optionales Lesetool; kein verbundenes Konto nachgewiesen. |
| CalDAV | HTTPS-Kalender-URL, Account und authentifizierten Transport hostseitig binden; [CalDAV-Anleitung](CALDAV_ADAPTER.md). | Optionales Hermes-Lesetool, kein Hermes-Schreibtool. |
| Kie.ai / ElevenLabs | Anbieter-Keys nur serverseitig in Dashboard Settings → Content Studio setzen; lokale Owner-Session und CSRF für die [optionale Bridge](CONTENT_STUDIO.md) binden. | Kostenpflichtige Anfragen brauchen Einzelbestätigung; kein bezahlter Live-Aufruf belegt. |
| Loxone | Miniserver-Zugang und erlaubte Control-IDs hostseitig konfigurieren; [Statusvertrag](LOXONE_STATUS_ADAPTER.md). | Kein nativer Miniserver-Client oder Schreibadapter in diesem Paket. |
| Telefonie | Für echte Anrufe Anbieter, eigene Rufnummer, Dial-Adapter, verifizierte Ziele und Anrufberechtigung konfigurieren. CardDAV ist nur eine optionale Kontaktquelle. | Der [Telefon-Skill](../skills/communication/friday-phone-call-coordinator/SKILL.md) kann ohne Konto einen Plan erstellen, aber keinen Anruf auslösen. |
| Obsidian | Optional einen autorisierten lokalen Vault-Pfad freigeben; ein Cloud-Konto ist für Dateizugriff nicht nötig. | Allgemeiner KB-Merge-/Indexadapter fehlt; Vault ist kein Live-Statusbeleg. |
| PowerPoint | Lokalen Renderer, Fonts und für Animationen Ziel-PowerPoint bereitstellen; [Rendervertrag](PRESENTATION_MOCK_WORKER.md). | Synthetischer PPTX-/PDF-Test ersetzt keine visuelle QA oder Playback. |
| Computer Use / Coding-CLIs | Optionale Hostwerkzeuge und Projekt-/UI-Berechtigungen lokal konfigurieren. Computer Use benötigt kein externes Konto; Coding-CLIs können eine eigene Modell-Anmeldung brauchen. | Hierfür sind keine eigenständigen Friday-Adapter fertiggestellt. |

## Hermes-Kompatibilität

Hermes dokumentiert [gebündelte Skills](https://hermes-agent.nousresearch.com/docs/reference/skills-catalog) für [PowerPoint](https://hermes-agent.nousresearch.com/docs/user-guide/skills/bundled/productivity/productivity-powerpoint), [Obsidian](https://hermes-agent.nousresearch.com/docs/user-guide/skills/bundled/note-taking/note-taking-obsidian), OpenCode, Codex und Claude Code. [Computer Use](https://hermes-agent.nousresearch.com/docs/user-guide/features/computer-use) ist als Hermes-Werkzeug dokumentiert. Am 2026-10-16 wurden die sechs SKILL.md in der lokalen Hermes-v0.22.2-Installation gesehen. `installed_status: unknown` im statischen Katalog bleibt korrekt, da der Katalog keine Laufzeitprüfung vornimmt; CLI-Anmeldung, Treiber, Abhängigkeiten und tatsächliche Ausführung sind gesondert zu prüfen. Die Friday-Skills können diese Werkzeuge optional nutzen, erfordern sie aber nicht als Paketvoraussetzung. Konkrete Übergaben stehen in [Friday mit Hermes](HERMES_WORKFLOWS.md). Der [Hermes-Toolset-Katalog](https://hermes-agent.nousresearch.com/docs/reference/toolsets-reference) belegt keinen allgemeinen Telefon-Dial-Adapter für Friday; die Telefonieintegration bleibt offen.

Neue oder geänderte Skill-IDs erfordern `python -m scripts.build_setup_catalog`, danach `python scripts/validate.py` und `python -m unittest discover -s tests -p 'test_setup_catalog.py' -v`. Der Validator prüft exakte Registry-Parität, Generator-Gleichheit, bekannte Capability-/Integrationsreferenzen, Dokumentationsreferenzen, Statuswerte und mögliche versehentlich eingetragene Geheimniswerte. Kein Schritt stellt Live-Verbindungen her.
