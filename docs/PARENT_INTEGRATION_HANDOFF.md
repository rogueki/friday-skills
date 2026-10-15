# F.R.I.D.A.Y. Skills → `rogue-friday` Integrations-Handoff

**Zweck:** Dieser Handoff benennt die kleinsten Parent-Änderungen und Vertragsentscheidungen, die für die Control-API-Integration der Skillsuite nötig sind. Er ist als Arbeitsauftrag für den parallel am Parent arbeitenden Agenten gedacht.

**Prüfstand:** Parent-Checkout `dashboard`, Branch `main`, Commit [`d2432d623ad6ea541467f322cbbbfbbc9ba2f542`](https://github.com/rogueki/rogue-friday/tree/d2432d623ad6ea541467f322cbbbfbbc9ba2f542). `git status` war sauber (`main...origin/main`). Die Prüfung war lokal und ausschließlich lesend. Quellenlinks sind auf diesen Commit festgelegt; spätere Parent-Änderungen können sie überholen.

## Kurzbefund

Der Parent hat bereits ein umfangreiches Control-API-Vertragsmodell: Cookie-Session-Auth, CSRF-Schutz, Aufgaben-CRUD, Activity-/Audit-Lesezugriffe, eine globale WebSocket-Sequenz und append-only Audit-Aufzeichnung serverseitig. Die Skillintegration scheitert an drei konkreten Vertragsgrenzen:

1. **Es gibt keine dokumentierte Maschinenidentität.** OpenAPI verlangt global `cookieAuth`. Ein Hermes-Prozess kann den Browser-Login nicht sicher als langlebige Maschinenanmeldung verwenden.
2. **Activity und Audit sind für Clients read-only.** Es gibt `GET /api/v1/activity` und `GET /api/v1/audit/events`, aber keinen Append-Endpunkt. Der Server schreibt zwar Audit-Einträge für mutierende API-Aufrufe, Skills können damit aber keine Laufzeit-/Tool-Aktivitäten melden.
3. **Der bekannte Login-Fehler ist im Snapshot weiterhin sichtbar.** `AuthService` erzeugt `user_owner` und Dev-IDs wie `dev-owner`; die Session-User-Schema-Validierung erwartet IDs im Format `usr_` plus 26 alphanumerische Zeichen. `docs/PROJECT_STATUS.md` nennt den Login deshalb als blockierenden Response-Validierungsfehler.

Der Aufgabenvertrag ist grundsätzlich nutzbar: `POST /api/v1/tasks` erstellt, `PATCH /api/v1/tasks/{id}` aktualisiert und `GET` liest zurück. Er erfordert allerdings CSRF bzw. Optimistic Concurrency und der Ereignisstream besitzt derzeit kein Server-ACK-Protokoll. Siehe die konkreten Vorschläge unten.

## Vorhandener Vertrag im Snapshot

| Bereich | Belegter Ist-Stand | Quellen |
|---|---|---|
| Auth | OpenAPI global `cookieAuth`; `POST /api/v1/auth/login` liefert Session-Cookie. Session-Antwort enthält `csrfToken`, der auf mutierenden Requests als `X-CSRF-Token` gesendet werden muss. Auth-Service authentifiziert anhand des Session-Cookies. | [`openapi/jarvis-api.yaml` L57–58, L299–325](https://github.com/rogueki/rogue-friday/blob/d2432d623ad6ea541467f322cbbbfbbc9ba2f542/packages/contracts/openapi/jarvis-api.yaml#L57-L58), [`session.schema.json`](https://github.com/rogueki/rogue-friday/blob/d2432d623ad6ea541467f322cbbbfbbc9ba2f542/packages/contracts/schemas/auth/session.schema.json), [`auth-service.ts` L76–83](https://github.com/rogueki/rogue-friday/blob/d2432d623ad6ea541467f322cbbbfbbc9ba2f542/apps/control-api/src/security/auth-service.ts#L76-L83), [`csrf.ts`](https://github.com/rogueki/rogue-friday/blob/d2432d623ad6ea541467f322cbbbfbbc9ba2f542/packages/auth/src/csrf.ts) |
| Login-Mismatch | `OWNER_USER_ID = "user_owner"`, Dev-IDs `dev-owner`/`dev-operator`/`dev-viewer`; Project Status hält den Fehler fest: Response-Validierung erwartet `^usr_[0-9A-Za-z]{26}$`. | [`auth-service.ts` L51–59](https://github.com/rogueki/rogue-friday/blob/d2432d623ad6ea541467f322cbbbfbbc9ba2f542/apps/control-api/src/security/auth-service.ts#L51-L59), [`PROJECT_STATUS.md`](https://github.com/rogueki/rogue-friday/blob/d2432d623ad6ea541467f322cbbbfbbc9ba2f542/docs/PROJECT_STATUS.md) |
| Tasks | `POST /api/v1/tasks` (`createTask`) nimmt `TaskCreateRequest`, liefert `TaskResponse`, verlangt CSRF + `Idempotency-Key`, Rolle `operator`. `PATCH /api/v1/tasks/{id}` (`updateTask`) verlangt CSRF + `If-Match`, liefert die aktualisierte Task. `GET /api/v1/tasks/{id}` liefert Task zum Read-after-write. | [`openapi/jarvis-api.yaml` L560–604, L605–680](https://github.com/rogueki/rogue-friday/blob/d2432d623ad6ea541467f322cbbbfbbc9ba2f542/packages/contracts/openapi/jarvis-api.yaml#L560-L604), [`task.schema.json`](https://github.com/rogueki/rogue-friday/blob/d2432d623ad6ea541467f322cbbbfbbc9ba2f542/packages/contracts/schemas/tasks/task.schema.json) |
| Idempotenz / Revision | Idempotenzschlüssel muss 8–128 Zeichen lang sein; Schlüssel wird pro Actor/Route/Key gebunden. Gleicher Key mit anderem Body ergibt Conflict; erfolgreiche Antwort wird wiederholt und als Replay markiert. `If-Match` akzeptiert numerische Resource-Version. Task-Schema definiert `version` als monotone Revision. | [`pipeline.ts` L130–139, L185–239, L339–349](https://github.com/rogueki/rogue-friday/blob/d2432d623ad6ea541467f322cbbbfbbc9ba2f542/apps/control-api/src/http/pipeline.ts#L130-L139), [`task.schema.json` L12–16](https://github.com/rogueki/rogue-friday/blob/d2432d623ad6ea541467f322cbbbfbbc9ba2f542/packages/contracts/schemas/tasks/task.schema.json#L12-L16) |
| Activity | Öffentliche Operationen sind nur `listActivity`/`getActivityEvent`. Contract erlaubt Backfill per `sinceSequence`; Adapter-Port-Spezifikation führt ausschließlich `listActivity` und `getActivityEvent`. | [`openapi/jarvis-api.yaml` L866–905](https://github.com/rogueki/rogue-friday/blob/d2432d623ad6ea541467f322cbbbfbbc9ba2f542/packages/contracts/openapi/jarvis-api.yaml#L866-L905), [`port-spec.ts` Activity](https://github.com/rogueki/rogue-friday/blob/d2432d623ad6ea541467f322cbbbfbbc9ba2f542/packages/adapter-core/src/port-spec.ts#L64-L72) |
| Audit | Öffentliche API bietet `GET /api/v1/audit/events`. Pipeline zeichnet mutierende, authentifizierte Requests serverseitig auf; das ist Control-Plane-Audit und kein Skill-Activity-Append. | [`openapi/jarvis-api.yaml` L3468–3500](https://github.com/rogueki/rogue-friday/blob/d2432d623ad6ea541467f322cbbbfbbc9ba2f542/packages/contracts/openapi/jarvis-api.yaml#L3468-L3500), [`pipeline.ts` Audit-Aufzeichnung](https://github.com/rogueki/rogue-friday/blob/d2432d623ad6ea541467f322cbbbfbbc9ba2f542/apps/control-api/src/http/pipeline.ts#L263-L275) |
| Realtime | `GET /api/v1/events` ist ein WebSocket-Stream mit strikt steigender globaler `sequence`, Replay über `?since=`, Resync-Event bei abgelaufenem Puffer und Ping/Pong. Die Task- und Activity-Events sind Server-zu-Client-Nachrichten. Es gibt kein Client-ACK, keinen dokumentierten Consumer-Cursor und keine Event-Acknowledge-Operation. | [`jarvis-events.yaml` L1–28, L247–379](https://github.com/rogueki/rogue-friday/blob/d2432d623ad6ea541467f322cbbbfbbc9ba2f542/packages/contracts/asyncapi/jarvis-events.yaml#L1-L28), [AsyncAPI channel](https://github.com/rogueki/rogue-friday/blob/d2432d623ad6ea541467f322cbbbfbbc9ba2f542/packages/contracts/asyncapi/jarvis-events.yaml#L361-L379) |
| Hermes-Mapping | Parent-Doku kennzeichnet Task-/Activity-/Agent-Endpunkte von Hermes explizit als nicht verifiziert; die genannten Mappingtabellen sind Zielmodell, keine bestätigte Hermes-API. | [`docs/MAPPING/hermes.md`](https://github.com/rogueki/rogue-friday/blob/d2432d623ad6ea541467f322cbbbfbbc9ba2f542/docs/MAPPING/hermes.md) |

## Erforderliche Parent-Arbeit, priorisiert

### P0 — Login-Vertrag reparieren

`POST /api/v1/auth/login` muss die eigene Antwort gegen OpenAPI validieren lassen und erfolgreich sein. IDs für reale und Dev-Identitäten müssen das aktuelle User-Schema erfüllen; interne Test- und Mock-Fixtures, SDK-Beispiele und Assertions entsprechend mitziehen. Regressionstest: Login → Session-Cookie → `GET /auth/session` → gültiger User + CSRF-Token. Keine Sonderbehandlung, die Response-Validierung für Login abschaltet.

### P0 — Authentisierung für einen lokalen Skill-Prozess festlegen

Der Parent soll eine explizite, dokumentierte Service-Principal-Variante oder einen gleichwertigen Session-Flow definieren. Empfehlung für Hermes: kurzlebige, widerrufbare Service-Credentials mit minimalen Scopes und eindeutiger `service/friday-skills`-Identität. Token-Rotation und Speicherung gehören in lokalen Secret Store/Dateirechte; niemals in Skilldateien, Task-Text, Activity, Audit-Details oder Logs. Keine Annahme eines Browser-Cookies als Maschinen-Credential.

Der Vertrag muss Auth-Verfahren, Scope-/Rollenbindung, Ablauf/Widerruf, `actor`-Attribution und Loopback-/Origin-Verhalten festlegen. Für Session-Auth stattdessen muss ein offizieller maschinengeeigneter Session-Bootstrap mit Cookie-Jar und CSRF-Token-Lifecycle dokumentiert werden; der CSRF-Schutz darf nicht für Hermes deaktiviert werden. Zugangsdaten bleiben außerhalb des Skills-Repositories.

### P0 — Task-Lifecycle Ende-zu-Ende nachweisen

Mit dem obigen Principal müssen `createTask` und `updateTask` erreichbar und autorisiert sein. Der Aufrufer muss:

1. für `POST` einen stabilen Idempotency-Key (8–128 Zeichen) pro logischem Create-Versuch erzeugen und bei Netzwerk-Retry wiederverwenden;
2. die erfolgreiche Antwort validieren, `taskId`/Version speichern und per `GET /tasks/{id}` den persistierten Zustand lesen;
3. für `PATCH` die aktuelle Task-Version als `If-Match` senden, `409` als Konflikt behandeln, erneut lesen und nur nach Policy neu entscheiden;
4. Fehler, Replay, Retry und doppelte Requests testen, ohne Tasks mehrfach anzulegen;
5. Task-Ereignisse mit derselben `taskId`/`correlationId` und gültigen Zustandsübergängen abbilden.

Der Parent sollte im Vertrag die erwarteten Idempotenz- und `If-Match`-Semantiken präzisieren (insbesondere fehlender Header, stale Version, Wildcard, gleiche Idempotency-Key/Body-Kombination, Speicher-/TTL-Lebensdauer). Der aktuelle Parser behandelt `If-Match: *` wie „keine Version“; das muss explizit als Policy entschieden und getestet werden, bevor ein Worker es nutzt.

### P1 — Activity-Publish-Schnittstelle definieren

Plan §§7.2, 9.6 und 38 erwarten Skill-Start/Progress/Approval/Completion/Failure sowie Tool-/Task-Aktivität. Dafür ist im Parent aktuell kein Write-Contract belegt. Ergänzt einen append-only Activity-Eingang oder einen anderen dokumentierten Ingest-Vertrag. Vorschlag: versioniertes `ActivityAppendRequest` mit Typ/Kind, Summary, Status, UTC-Zeit, `correlationId`, optional `taskId`/`parentId`, Herkunft (`service/friday-skills`) und redigierten Metadaten. Der Server setzt Activity-ID, globale Sequenz, Actor, Zeitnormalisierung und Validierung. Schreiben muss `jarvis.activity.appended` in denselben Persistenz-/Realtime-Pfad einspeisen, den GET/Backfill nutzt.

Den Client nicht selbst `sequence`, `hash`, Actor-Adminfelder oder Serverzeit setzen lassen. Content-Limits und Allowlist für Details definieren; Nachrichteninhalte, E-Mail-/Dokumentkörper, Zugangsdaten, Rohprompts und vollständige Tool-Argumente grundsätzlich nicht übernehmen. Append muss idempotent sein (Request-Id/Idempotency-Key) und Replay nach Timeout erlauben.

### P1 — Audit und Activity getrennt halten

Der vorhandene Audit-Writer protokolliert mutierende API-Aufrufe. Das genügt als Nachweis für `POST`/`PATCH`-Vorgänge, aber nicht für Skillinterne Schritte. Bevor ein öffentlicher Audit-Append-Endpunkt entsteht, festlegen, ob Skillereignisse als vertrauenswürdige serverseitige Auditdaten oder lediglich als Activity gelten. Empfehlung: Activity-Ingest für Laufzeit-/Fortschrittsdaten; Audit ausschließlich serverseitig aus authentifizierter Principal, validiertem Request und Policy-Entscheidung erzeugen. Nie einen vom Skill gelieferten Audit-Eintrag ungeprüft in die Hashkette schreiben.

### P1 — Event-Wiedergabe und ACK-Entscheidung

Der bestehende Stream arbeitet bereits mit globaler Sequenz und `?since=`-Replay. Für einen Skill-Publisher ist kein eingehender Event-ACK erforderlich. Für den Kanban-/Task-Observer soll der Parent entscheiden, ob persistierter Client-Cursor plus Replay ausreicht (empfohlen) oder ein expliziter ACK-/Consumer-Offset nötig ist. Falls ACK hinzugefügt wird, muss er getrennt von Ping/Pong und von Task-Erfolg definiert sein: Consumer-ID, monotone bestätigte Sequenz, Wiederholung, Cursorablauf, Reconnect, Lücken-/Resync-Verhalten und AuthZ. Ein ACK bestätigt nur Verarbeitung bis zu einer Sequenz; er darf Task-Zustand nicht mutieren. Vorhandene Stream-Semantik nicht stillschweigend ändern.

### P1 — Task-Zustände und Events festschreiben

Der Task-Statusenum ist `triage`, `todo`, `ready`, `running`, `waiting`, `review`, `done`, `failed`, `cancelled`; ein `paused`-Status existiert nicht. Hermes-Status müssen in diesem Enum abgebildet werden (z. B. menschliche Freigabe → `waiting`, „Review“ → `review`); Pausieren darf nicht als `paused` geschrieben werden. Task-Events sind `jarvis.task.created`, `.updated`, `.progress`, `.completed`, `.failed`, `.cancelled`. Vertrag/Tests sollen festlegen, welche Statusänderungen welche Events emittieren und dass Create/Update-Antwort, GET-Readback und Event denselben Task plus Version referenzieren.

## Parent-Akzeptanztests

1. Contract-Test, dass ein gültiger Service-Principal auf erlaubte Reads/Task-Operationen zugreifen kann und ohne Auth bzw. mit falschem Scope `401`/`403` erhält.
2. Login-Regression wie oben; Response-Validation bleibt aktiv.
3. `POST createTask`: einmalig persistiert, gleicher Idempotency-Key + gleicher Body liefert Replay derselben Task; gleicher Key + anderer Body `409`.
4. `PATCH updateTask`: gültige Version erfolgreich; stale Version `409`; Readback liefert aktualisierte Version.
5. Integrationstest mit echtem In-Memory/Mock-Event-Hub: Task-Write erzeugt erwartetes Event mit monotoner Sequenz; Reconnect mit `since` liefert es erneut bzw. `resync_required` bei Cursor außerhalb des Puffers.
6. Wenn Activity-Ingest umgesetzt wird: Append → GET-Backfill → Stream-Event mit gleicher ID/Correlation; Replay doppelt erzeugt keinen zweiten Datensatz; sensible Felder werden abgewiesen oder redigiert.
7. Wenn ACK eingeführt wird: Cursor wird pro authentisiertem Consumer persistiert, ist monoton und kann nur Sequenzen bestätigen, die der Server tatsächlich ausgegeben hat; ACK beeinflusst keine Task-/Approval-Policy.
8. Security-/Privacy-Tests: Cookie/CSRF bleiben aktiv für Session-Clients; keine Secrets oder vollständigen untrusted Inhalte in Logs/Activity/Audit; Service-Credential lässt sich widerrufen.

## Umsetzungsreihenfolge

1. Login-ID-/Response-Validierungsfehler beheben und regressionssichern.
2. Service-Auth Vertrag samt minimaler Scopes und actor attribution entscheiden und implementieren.
3. Task Create/Update inkl. Idempotenz, Versionierung, Readback und AsyncAPI-Verifikation end-to-end testen.
4. Festlegen, ob Status-/Progress-Meldungen einen Activity-Ingest benötigen; falls ja OpenAPI + Schema + Handler + Speicher + AsyncAPI + Tests gemeinsam ergänzen.
5. Cursor-Replay verwenden oder ACK-Contract bewusst ergänzen; kein implizites ACK-Verhalten voraussetzen.
6. Hermes-Adapter erst gegen verifizierte und versionierte Endpunkte bauen; `docs/MAPPING/hermes.md` aktuell als unbestätigte Zielabbildung behandeln.

## Bezug zur Skill-Plan-Abnahme

- Plan §§7.1–7.3 definieren Result, `jarvis.skill.*`-Event-Beispiele und den einzigen API-Client als Integrationsgrenze.
- Plan §8 setzt Tier 0/1 autonom, Tier 2 mit Bestätigung und Tier 3 mit harter Freigabe plus zweitem Faktor.
- Plan §9.3 erwartet Task-Erstellung und verifizierten Abschluss; §9.6 den Activity-Publisher; §9.7 Audit/Lineage mit Secret-Redaktion.
- Plan §38 verlangt funktionierende Dashboard-Events, korrekt erstellte/abgeschlossene Kanban-Tasks und Audit-Events. Diese Handoff-Datei ist keine Abnahme dieser Punkte; sie beschreibt den Parent-Vertrag, der dafür noch fehlt bzw. zu verifizieren ist.
- Plan §39 verlangt am Ende Repository, Skills, Policies, Mocks, Plugins, Registry, Tests, Fixtures, Installer, Dokumentation, Testbericht, Abnahmematrix, ZIP und Tag `v1.0.0`.

**Grenze dieses Handoffs:** keine Änderung am Parent, keine Live-Anmeldung, keine Credentials und keine Aussage, dass Parent-Fixes oder Laufzeittests bereits erfolgt sind. Der Parallel-Agent soll `HEAD` vor einer Umsetzung erneut prüfen und diesen Snapshot als Referenz aktualisieren.
