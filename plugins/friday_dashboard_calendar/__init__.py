"""Read-only bridge to Friday's configured ICS or CalDAV calendar."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
import json
from pathlib import Path
from urllib.parse import urlencode
from urllib.request import HTTPRedirectHandler, ProxyHandler, Request, build_opener


TOOL_NAME = "friday_calendar_events"
SCHEMA = {"name": TOOL_NAME, "description": "Read up to 100 events in a maximum 31-day window from the calendar configured in Friday Dashboard. Reports whether the source is live, synthetic or unknown. Never creates or changes events.",
          "parameters": {"type": "object", "properties": {
              "start": {"type": "string", "description": "Timezone-aware ISO start time"},
              "end": {"type": "string", "description": "Timezone-aware ISO end time, at most 31 days after start"}},
              "required": ["start", "end"], "additionalProperties": False}}
MAX_BODY = 512_000
MAX_EVENTS = 100
MAX_PAGES = 2


def _blocked(code: str) -> str:
    return json.dumps({"status": "blocked", "events": None, "source_status": "unknown", "fetched_at": None, "write_effect": False,
                       "error": {"code": code}}, ensure_ascii=False)


class _NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, request, fp, code, msg, headers, newurl):
        return None


def _setting(home: Path):
    config = home / ".hermes/friday-calendar-bridge.json"
    key_file = home / ".hermes/friday-calendar-bridge.key"
    if config.is_symlink() or key_file.is_symlink() or config.stat().st_mode & 0o077 or key_file.stat().st_mode & 0o077:
        raise ValueError("bridge configuration is not private")
    data = json.loads(config.read_text(encoding="utf-8"))
    if not isinstance(data, dict) or set(data) != {"port"} or type(data["port"]) is not int or not 1024 <= data["port"] <= 65535:
        raise ValueError("invalid bridge configuration")
    key = key_file.read_text(encoding="ascii").strip()
    if len(key) != 44 or not key.endswith("="):
        raise ValueError("invalid bridge key")
    return data["port"], key


def _time(value):
    if not isinstance(value, str) or len(value) > 40:
        raise ValueError("invalid time")
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise ValueError("timezone required")
    return parsed


def _source_status(page):
    if page.get("freshness", {}).get("state") != "fresh":
        raise ValueError("stale calendar response")
    sources = [item.get("source", {}) for item in page["items"] if isinstance(item, dict)]
    if sources and all(source.get("adapterId") == "caldav-calendar" for source in sources):
        return "live"
    if sources and all(str(source.get("adapterId", "")).startswith("mock-") for source in sources):
        return "synthetic"
    return "unknown"


def _fetched_at(page):
    freshness = page.get("freshness")
    value = freshness.get("asOf") if isinstance(freshness, dict) else None
    if not isinstance(value, str) or len(value) > 40:
        raise ValueError("missing calendar fetch time")
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise ValueError("calendar fetch time has no timezone")
    return parsed


def register(ctx):
    def events(params: dict, **_kwargs) -> str:
        if not isinstance(params, dict) or set(params) != {"start", "end"}:
            return _blocked("invalid_request")
        try:
            start, end = _time(params["start"]), _time(params["end"])
            if end <= start or end - start > timedelta(days=31):
                return _blocked("invalid_window")
        except (ValueError, TypeError, OverflowError):
            return _blocked("invalid_time")
        try:
            port, key = _setting(Path.home())
            opener = build_opener(ProxyHandler({}), _NoRedirect())
            items, cursor, statuses, fetch_times = [], None, [], []
            for _ in range(MAX_PAGES):
                query = {"from": start.isoformat(), "to": end.isoformat(), "limit": "50"}
                if cursor:
                    query["cursor"] = cursor
                url = f"http://127.0.0.1:{port}/api/v1/calendar/events?{urlencode(query)}"
                request = Request(url, method="GET", headers={"Authorization": f"Bearer {key}", "Accept": "application/json"})
                with opener.open(request, timeout=6) as response:
                    if response.status != 200 or response.geturl() != url:
                        return _blocked("bridge_unavailable")
                    payload = response.read(MAX_BODY + 1)
                    if len(payload) > MAX_BODY:
                        return _blocked("response_too_large")
                    page = json.loads(payload)
                if not isinstance(page, dict) or not isinstance(page.get("items"), list) or not isinstance(page.get("pageInfo"), dict):
                    return _blocked("invalid_response")
                items.extend(page["items"])
                if len(items) > MAX_EVENTS:
                    return _blocked("response_too_large")
                statuses.append(_source_status(page))
                fetch_times.append(_fetched_at(page))
                cursor = page["pageInfo"].get("nextCursor")
                if cursor is None:
                    break
                if not isinstance(cursor, str) or len(cursor) > 512:
                    return _blocked("invalid_response")
            else:
                return _blocked("page_limit")
            source_status = "synthetic" if "synthetic" in statuses else "live" if statuses and all(s == "live" for s in statuses) else "unknown"
            fetched_at = min(fetch_times).astimezone(timezone.utc).isoformat().replace("+00:00", "Z")
            public_items = [{field: item[field] for field in ("id", "title", "start", "end", "allDay", "timeZone", "status")
                             if field in item} for item in items if isinstance(item, dict)]
            return json.dumps({"status": "completed", "events": public_items, "source_status": source_status,
                               "fetched_at": fetched_at,
                               "write_effect": False}, ensure_ascii=False)
        except Exception:
            return _blocked("bridge_unavailable")

    ctx.register_tool(name=TOOL_NAME, toolset="friday_dashboard_calendar", schema=SCHEMA, handler=events)
