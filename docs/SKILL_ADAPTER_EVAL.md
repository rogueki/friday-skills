# Offline-Adapter-Evaluation

Der Evaluator fuehrt 106 positive, negative und Wiederherstellungsvarianten aus neun bestehenden synthetischen E2E-Ablaeufen aus. Die Zuordnung der jeweils betroffenen F.R.I.D.A.Y.-Skills steht explizit in `registry/skill_adapter_bindings.json`. Diese Zuordnung ist Kontext fuer die Fehlersuche, keine Behauptung, dass Hermes die `SKILL.md` geladen oder befolgt hat.

```powershell
python scripts/evaluate_skill_adapters.py
python scripts/evaluate_skill_adapters.py --json
```

Jeder Fall laeuft durch `shared.scenarios.run_scenario` und prueft Status, entscheidende Trace-Schritte, verbotene Schritte und Artefakte, Ablehnungsgrund, lokalen Event-Endzustand und eine unveroeffentlichbare Dashboard-Abbildung. Bereichsspezifische Orakel pruefen unter anderem den Rechnungsbetrag nach Skontofrist, den unveraenderten Archivursprung mit Hash-/Byte-/Anzahl-Abgleich, Freigabe-Fingerprints, den ausbleibenden Buchungs-/Sende-/Steuer-/Geraeteeffekt und geordnete Recovery-Probes. Audit-Eintraege duerfen keine ausgefuehrte externe Aktion melden. Der Bericht enthaelt SHA-256-Hashes des Manifests sowie der zugeordneten `SKILL.md`, Adapterquellen, Szenarioquelle und Fixtures. Ein unerwarteter Fehler ergibt `ERROR`, eine gebrochene Assertion `FAIL`; beides erzeugt einen Exitcode 1. Nur der explizite fehlende optionale PDF-Parser ergibt fuer die sieben PDF-Faelle `SKIP`.

Die Quellvarianten werden aus den aktuellen Adapter-Deklarationen gelesen und mit den expliziten Manifestfaellen abgeglichen. Der Bericht zeigt je Szenario deklarierte, bestandene, fehlende und unbekannte Varianten. Eine Abdeckungsluecke erzeugt Exitcode 1. Der aktuelle Umfang: Mail 8, Rechnungs-PDF 7, Meeting 17, Wetter 8, Reise 10, Archiv 15, Loxone 18, Steuer 10 und Ausfall/Recovery 13 Varianten. Alle 106 sind offline gebunden; weitere Eingabekombinationen innerhalb dieser Varianten, echte Provider und Hermes-Modellverhalten bleiben ungeprueft.

Diese Evidenz heisst ausschliesslich `offline_adapter_execution`. Die 404 Hermes-Modell-Routingfaelle und 1616 individuellen Skill-Laufzeitfaelle bleiben `NOT_RUN`. Auch ein `PASS` hier beweist keine Providerverbindung, echte Host-Freigabe, reale Dateimigration, Buchung, Steuerabgabe, Geraeteschaltung oder Dashboard-Publikation. Der PowerPoint-Renderpfad gehoert wegen der optionalen Office-Laufzeit nicht zu dieser deterministischen Matrix und wird separat geprueft.
