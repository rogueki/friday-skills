"""Hermes plugin exposing only a labelled synthetic Loxone status fixture."""

from __future__ import annotations

from datetime import datetime, timezone
import json
import os
from pathlib import Path


TOOL_NAME = "friday_loxone_status_snapshot"
SCHEMA = {
    "name": TOOL_NAME,
    "description": (
        "Read a synthetic, explicitly allowlisted Loxone status example. This plugin is fixture-only; "
        "it does not connect to a Miniserver or expose control/write commands."
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


def register(ctx) -> None:
    from adapters import loxone_status

    configured = os.environ.get("FRIDAY_SKILLS_ROOT")
    if not configured:
        raise RuntimeError("FRIDAY_SKILLS_ROOT must point to the Friday skills support directory")
    root = Path(configured).resolve(strict=True)
    if (root / "adapters" / "loxone_status.py").resolve() != Path(loxone_status.__file__).resolve():
        raise RuntimeError("Loxone status adapter was imported from outside this friday-skills package")
    fixture = root / "fixtures" / "loxone" / "adapter_status.json"
    if not fixture.is_file():
        raise RuntimeError("Friday support directory lacks the synthetic Loxone fixture")

    def status(params: dict, **_kwargs) -> str:
        if not isinstance(params, dict) or set(params) != {"control_ids"}:
            return json.dumps({
                "status": "blocked", "error": {"code": "invalid_request"},
                "capability": None, "write_effect": False,
            })
        try:
            result = loxone_status.read_status(params["control_ids"], mode="mock")
        except loxone_status.LoxoneStatusError as exc:
            return json.dumps({
                "status": "blocked", "error": {"code": exc.code, "message": str(exc)},
                "capability": None, "write_effect": False,
            }, ensure_ascii=False)
        return json.dumps({
            **result,
            "capability": {
                "name": "loxone.read", "status": "synthetic", "mode": "mock",
                "permissions": ["read"], "checked_at": datetime.now(timezone.utc).isoformat(),
                "source": result["source"], "synthetic": True, "authenticated": False,
                "rate_limited": False, "public_read": False, "adapter_id": "loxone-status-fixture",
            },
        }, ensure_ascii=False)

    ctx.register_tool(name=TOOL_NAME, toolset="friday_loxone_status", schema=SCHEMA, handler=status)
