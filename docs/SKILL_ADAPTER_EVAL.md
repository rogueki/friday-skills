# Offline-Adapter-Evaluation

Der Evaluator fuehrt 18 positive und negative Varianten aus neun bestehenden synthetischen E2E-Ablaeufen aus. Die Zuordnung der jeweils betroffenen F.R.I.D.A.Y.-Skills steht explizit in `registry/skill_adapter_bindings.json`. Diese Zuordnung ist Kontext fuer die Fehlersuche, keine Behauptung, dass Hermes die `SKILL.md` geladen oder befolgt hat.

```powershell
python scripts/evaluate_skill_adapters.py
python scripts/evaluate_skill_adapters.py --json
```

Jeder Fall laeuft durch `shared.scenarios.run_scenario` und prueft Status, entscheidende Trace-Schritte, Artefakte, lokalen Event-Endzustand und eine unveroeffentlichbare Dashboard-Abbildung. Audit-Eintraege duerfen keine ausgefuehrte externe Aktion melden. Der Bericht enthaelt SHA-256-Hashes des Manifests sowie der zugeordneten `SKILL.md`, Adapterquellen, Szenarioquelle und Fixtures. Ein unerwarteter Fehler ergibt `ERROR`, eine gebrochene Assertion `FAIL`; beides erzeugt einen Exitcode 1. Nur der explizite fehlende optionale PDF-Parser ergibt fuer die zwei PDF-Faelle `SKIP`.

Diese Evidenz heisst ausschliesslich `offline_adapter_execution`. Die 404 Hermes-Modell-Routingfaelle und 1616 individuellen Skill-Laufzeitfaelle bleiben `NOT_RUN`. Auch ein `PASS` hier beweist keine Providerverbindung, echte Host-Freigabe, reale Dateimigration, Buchung, Steuerabgabe, Geraeteschaltung oder Dashboard-Publikation. Der PowerPoint-Renderpfad gehoert wegen der optionalen Office-Laufzeit nicht zu dieser deterministischen Matrix und wird separat geprueft.
