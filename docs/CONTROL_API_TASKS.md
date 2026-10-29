# Control API: Task-Client

Dieser optionale Python-3.11-Client bildet die Task-Operationen der F.R.I.D.A.Y.-Control-API ab. Vertragsgrundlage ist der **read-only gelesene** Stand `rogueki/rogue-friday`, Commit `d2432d623ad6ea541467f322cbbbfbbc9ba2f542`, insbesondere `dashboard/packages/contracts/openapi/jarvis-api.yaml` und die referenzierten Task-Schemas. Vor Live-Nutzung den dann aktuellen Vertrag erneut vergleichen.

## Umfang

- `POST /api/v1/tasks`: Operator, `friday_session`, `X-CSRF-Token`, `Idempotency-Key` (8 bis 128 Zeichen), `TaskCreateRequest`, Antwort 201 mit `TaskResponse`.
- `PATCH /api/v1/tasks/{id}`: Operator, Session, CSRF, `If-Match` als positive Task-Version, nicht als ETag. `TaskUpdateRequest` enthält den Kanban-Status; Antwort 200.
- `GET /api/v1/tasks/{id}`: Viewer, Session, Antwort 200. Der Client bietet aktuell keine Listen-, Cancel-, Retry-, Pause- oder Resume-Methode.
- Ein Transport wird **explizit** injiziert. Ohne Transport gibt es keinen Netzwerkzugriff. Origin ist auf `localhost`, `127.0.0.0/8` oder `::1` beschränkt; URL-Pfade und Userinfo werden abgelehnt. Keine automatische Anmeldung, Credential-Ermittlung, Redirects oder Retries.

```python
from shared.control_task_client import ControlTaskClient

# transport(method, url, headers, body, timeout) -> Response
client = ControlTaskClient("http://127.0.0.1:8384", transport=my_reviewed_transport)
task = client.create(
    {"title": "Rechnung prüfen", "priority": "P3"},
    session=session_cookie_value,
    csrf=csrf_token,
    idempotency_key=stable_request_id,
)
updated = client.update(
    task.id, {"status": "review"},
    session=session_cookie_value, csrf=csrf_token, if_match=task.if_match,
)
```

`session_cookie_value` ist nur der Wert des `friday_session`-Cookies, kein gesamter Cookie-Header. Der CSRF-Wert stammt laut Vertrag aus `GET /auth/session`. Die Bereitstellung von Session und CSRF ist Sache des aufrufenden, autorisierten Hosts. Dieser Client speichert sie nicht und schreibt sie nicht in Fehlermeldungen.

## Fehler und Abgleich

`TaskClientError.code` ordnet 401/403/404/409/422/429/503 und andere Antworten ein. Eine 409 ist eine Versions- oder Idempotenzkollision; die Ursache muss anhand der Operation und eines frischen GET geklärt werden. Bei Transportausfall, 5xx oder nicht verifizierbarer Erfolgsantwort **nach einer Mutation** meldet `UnknownMutationOutcome`: Task-Status mit derselben Task-ID lesen oder bei CREATE den Idempotenzschlüssel kontrolliert abgleichen. Eine neue Mutation mit einem neuen Schlüssel darf nicht blind folgen. Die lokale Schlüssel-Fingerprint-Sperre gilt nur für eine Client-Instanz und ersetzt kein persistentes Operationsjournal. Fehler enthalten weder Response-Body noch Session/CSRF.

Die Antwortprüfung kontrolliert Envelope, erforderliche Task-Felder, Identität, Version, Status, Priorität und einige Typen. Sie ist kein vollständiger JSON-Schema-Validator für alle verschachtelten Task-Strukturen. Tests nutzen ausschließlich einen injizierten In-Memory-Transport:

```powershell
python -m unittest discover -s tests -p test_control_task_client.py -q
```

Es gab **keinen Live-Request**. Der bekannte Login-Response-Defekt des Parent-Projekts verhindert derzeit eine belastbare End-to-End-Abnahme. Dieser Client erzeugt keine `jarvis.task.*`-Events selbst und publiziert keine `jarvis.activity.appended`-Events; das bleibt Verantwortung der Control API. Das Parent-Repository, Dashboard und der Installer wurden für diese Arbeit nicht verändert.
