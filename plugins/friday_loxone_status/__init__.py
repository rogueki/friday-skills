"""Hermes Loxone status tool with an optional host-injected read boundary."""

from __future__ import annotations

from datetime import datetime, timezone
import json
import os
from pathlib import Path


TOOL_NAME = "friday_loxone_status_snapshot"
SCHEMA = {
    "name": TOOL_NAME,
    "description": (
        "Read an allowlisted Loxone status snapshot. The host may inject an authenticated "
        "read provider; otherwise the result is an explicitly labelled synthetic fixture."
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "control_ids": {
                "type": "array", "items": {"type": "string", "minLength": 1, "maxLength": 64},
                "minItems": 1, "maxItems": 100,
            },
        },
        "required": ["control_ids"],
        "additionalProperties": False,
    },
}


def register(ctx, *, transport=None, allowed_control_ids=None) -> None:
    """Register one read tool; only the host can inject transport and its fixed ID ceiling."""
    from adapters import loxone_status

    configured = os.environ.get("FRIDAY_SKILLS_ROOT")
    if not configured:
        raise RuntimeError("FRIDAY_SKILLS_ROOT must point to the Friday skills support directory")
    root = Path(configured).resolve(strict=True)
    if (root / "adapters" / "loxone_status.py").resolve() != Path(loxone_status.__file__).resolve():
        raise RuntimeError("Loxone status adapter was imported from outside this friday-skills package")
    if (transport is None) != (allowed_control_ids is None):
        raise RuntimeError("read provider and host control allowlist must be configured together")
    if transport is not None:
        ids = allowed_control_ids
        if (not isinstance(ids, (list, tuple, frozenset)) or
                not 1 <= len(ids) <= loxone_status.MAX_CONTROLS or
                any(not isinstance(item, str) or not loxone_status.ID_PATTERN.fullmatch(item) for item in ids) or
                len(set(ids)) != len(ids)):
            raise RuntimeError("host control allowlist is invalid")
        host_ids = frozenset(ids)
    else:
        host_ids = None
    fixture = root / "fixtures" / "loxone" / "adapter_status.json"
    if transport is None and not fixture.is_file():
        raise RuntimeError("Friday support directory lacks the synthetic Loxone fixture")

    def blocked(code: str) -> str:
        return json.dumps({
            "status": "blocked", "error": {"code": code},
            "capability": None, "write_effect": False,
        })

    def status(params: dict, **_kwargs) -> str:
        if not isinstance(params, dict) or set(params) != {"control_ids"}:
            return blocked("invalid_request")
        requested = params["control_ids"]
        if host_ids is not None and (
            not isinstance(requested, list)
            or any(not isinstance(item, str) or item not in host_ids for item in requested)
        ):
            return blocked("not_allowlisted")
        try:
            mode = "read_only" if host_ids is not None else "mock"
            result = loxone_status.read_status(requested, mode=mode, transport=transport)
        except loxone_status.LoxoneStatusError as exc:
            return blocked(exc.code)
        except Exception:
            return blocked("adapter_unavailable")
        if host_ids is not None:
            try:
                authenticated = getattr(transport, "authenticated", False) is True
            except Exception:
                authenticated = False
            if not authenticated:
                return blocked("transport_required")
        return json.dumps({
            **result,
            "capability": {
                "name": "loxone.read", "status": "available" if host_ids is not None else "synthetic",
                "mode": mode,
                "permissions": ["read"], "checked_at": datetime.now(timezone.utc).isoformat(),
                "source": result["source"], "synthetic": host_ids is None,
                "authenticated": host_ids is not None,
                "rate_limited": False, "public_read": False,
                "adapter_id": "loxone-status-provider" if host_ids is not None else "loxone-status-fixture",
            },
        }, ensure_ascii=False)

    ctx.register_tool(name=TOOL_NAME, toolset="friday_loxone_status", schema=SCHEMA, handler=status)
