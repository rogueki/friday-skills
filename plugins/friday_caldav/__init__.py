"""Opt-in Hermes calendar reader with a host-bound read-only transport."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import json
import os
from pathlib import Path
from typing import Any


TOOL_NAME = "friday_caldav_events"
MOCK_ENDPOINT = "https://calendar.example.invalid/"
MOCK_ACCOUNT = "synthetic@example.invalid"
MOCK_HOST = "calendar.example.invalid"
SCHEMA = {
    "name": TOOL_NAME,
    "description": (
        "Read bounded CalDAV events for the host-selected source. Without host configuration this reads "
        "synthetic data. Real reads require host authorization and an authenticated read-only transport."
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "start": {"type": "string", "description": "Timezone-aware ISO timestamp"},
            "end": {"type": "string", "description": "Timezone-aware ISO timestamp, max 31 days"},
        },
        "required": ["start", "end"],
        "additionalProperties": False,
    },
}


@dataclass(frozen=True)
class HostCalDAVReadConfig:
    """Trusted host's fixed account binding; never populated from tool arguments."""

    endpoint: str
    account: str
    allowed_host: str
    transport: Any
    authorized: bool


def _blocked(code: str, message: str) -> str:
    return json.dumps({"status": "blocked", "events": None, "capability": None,
                       "write_effect": False, "error": {"code": code, "message": message}},
                      ensure_ascii=False)


def register(ctx, *, host_read: HostCalDAVReadConfig | None = None) -> None:
    """Register one read tool. Supplying host_read opts in to a fixed real account."""
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
        if not isinstance(params, dict) or set(params) != {"start", "end"}:
            return _blocked("invalid_request", "only a start and end time range may be supplied")
        try:
            start = datetime.fromisoformat(params["start"].replace("Z", "+00:00"))
            end = datetime.fromisoformat(params["end"].replace("Z", "+00:00"))
        except (TypeError, AttributeError, ValueError):
            return _blocked("invalid_time", "invalid timezone-aware time range")

        if host_read is None:
            endpoint, account, allowed_host = MOCK_ENDPOINT, MOCK_ACCOUNT, MOCK_HOST
            mode, transport = "mock", None
        else:
            if not isinstance(host_read, HostCalDAVReadConfig):
                return _blocked("host_config_invalid", "host calendar configuration is invalid")
            if host_read.authorized is not True:
                return _blocked("host_authorization_required", "host authorization is required")
            try:
                authenticated = (callable(host_read.transport)
                                 and getattr(host_read.transport, "authenticated", None) is True)
            except Exception:
                authenticated = False
            if not authenticated:
                return _blocked("authenticated_transport_required", "an authenticated read transport is required")
            endpoint, account, allowed_host = host_read.endpoint, host_read.account, host_read.allowed_host
            mode, transport = "read_only", host_read.transport

        try:
            result = caldav_calendar.list_events(
                endpoint, account, start, end, allowed_host=allowed_host,
                mode=mode, transport=transport,
            )
        except caldav_calendar.CalendarAdapterError as exc:
            return _blocked(exc.code, str(exc))
        except Exception:
            return _blocked("adapter_failure", "calendar adapter failed")
        if mode == "read_only":
            try:
                still_authenticated = getattr(host_read.transport, "authenticated", None) is True
            except Exception:
                still_authenticated = False
            if not still_authenticated:
                return _blocked("authenticated_transport_required", "calendar transport authentication was lost")
            result["capability"] = {
                "name": "caldav.read", "status": "authorized", "mode": "read_only",
                "permissions": ["read"], "checked_at": datetime.now(timezone.utc).isoformat(),
                "source": endpoint, "account": account, "synthetic": False,
                "authenticated": True, "write_effect": False,
            }
        return json.dumps(result, ensure_ascii=False)

    ctx.register_tool(name=TOOL_NAME, toolset="friday_caldav", schema=SCHEMA, handler=events)
