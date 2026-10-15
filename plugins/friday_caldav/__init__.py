"""Opt-in Hermes calendar reader. This plugin intentionally exposes no write tool."""

from __future__ import annotations

from datetime import datetime
import json
import os
from pathlib import Path


TOOL_NAME = "friday_caldav_events"
SCHEMA = {
    "name": TOOL_NAME,
    "description": "Read bounded CalDAV VEVENTs. Defaults to labelled synthetic data. Explicit transport wiring is required for external reads; no write tool is exposed.",
    "parameters": {
        "type": "object",
        "properties": {
            "endpoint": {"type": "string", "description": "Explicit HTTPS CalDAV calendar collection URL"},
            "account": {"type": "string"},
            "allowed_host": {"type": "string"},
            "start": {"type": "string", "description": "Timezone-aware ISO timestamp"},
            "end": {"type": "string", "description": "Timezone-aware ISO timestamp, max 31 days"},
            "mode": {"type": "string", "enum": ["mock", "read_only", "live"]},
        },
        "required": ["endpoint", "account", "allowed_host", "start", "end"],
        "additionalProperties": False,
    },
}


def _blocked(code: str, message: str) -> str:
    return json.dumps({"status": "blocked", "events": None, "write_effect": False,
                       "error": {"code": code, "message": message}}, ensure_ascii=False)


def register(ctx) -> None:
    from adapters import caldav_calendar

    configured = os.environ.get("FRIDAY_SKILLS_ROOT")
    if not configured:
        raise RuntimeError("FRIDAY_SKILLS_ROOT must point to the Friday skill package")
    root = Path(configured).resolve(strict=True)
    if (root / "adapters" / "caldav_calendar.py").resolve() != Path(caldav_calendar.__file__).resolve():
        raise RuntimeError("CalDAV adapter was imported from outside Friday skills")
    if not (root / "fixtures" / "calendar" / "adapter_multistatus.xml").is_file():
        raise RuntimeError("Friday calendar support directory lacks the synthetic fixture")

    def events(params: dict, **_kwargs) -> str:
        if not isinstance(params, dict):
            return _blocked("invalid_request", "parameters must be an object")
        if set(params) - {"endpoint", "account", "allowed_host", "start", "end", "mode"}:
            return _blocked("invalid_request", "unexpected calendar parameter")
        if not all(key in params for key in SCHEMA["parameters"]["required"]):
            return _blocked("invalid_request", "explicit endpoint, account, host and time range required")
        try:
            start = datetime.fromisoformat(params["start"].replace("Z", "+00:00"))
            end = datetime.fromisoformat(params["end"].replace("Z", "+00:00"))
        except (TypeError, AttributeError, ValueError):
            return _blocked("invalid_time", "invalid timezone-aware time range")
        try:
            result = caldav_calendar.list_events(
                params["endpoint"], params["account"], start, end,
                allowed_host=params["allowed_host"], mode=params.get("mode", "mock"),
            )
        except caldav_calendar.CalendarAdapterError as exc:
            return _blocked(exc.code, str(exc))
        except Exception:
            return _blocked("adapter_failure", "calendar adapter failed")
        return json.dumps(result, ensure_ascii=False)

    ctx.register_tool(name=TOOL_NAME, toolset="friday_caldav", schema=SCHEMA, handler=events)
