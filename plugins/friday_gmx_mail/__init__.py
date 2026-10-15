"""Opt-in Hermes GMX reader. Sending is deliberately not a tool."""

from __future__ import annotations

import json
import os
from pathlib import Path


TOOL_NAME = "friday_gmx_read_uid"
SCHEMA = {
    "name": TOOL_NAME,
    "description": "Read one explicitly selected GMX mailbox UID as untrusted text. Defaults to synthetic mock. No send tool.",
    "parameters": {
        "type": "object", "properties": {
            "mailbox": {"type": "string"}, "uid": {"type": "string"},
            "mode": {"type": "string", "enum": ["mock", "read_only"]},
        }, "required": ["mailbox", "uid"], "additionalProperties": False,
    },
}


def register(ctx) -> None:
    from adapters import gmx_mail

    configured = os.environ.get("FRIDAY_SKILLS_ROOT")
    if not configured:
        raise RuntimeError("FRIDAY_SKILLS_ROOT required")
    root = Path(configured).resolve(strict=True)
    if (root / "adapters" / "gmx_mail.py").resolve() != Path(gmx_mail.__file__).resolve():
        raise RuntimeError("GMX adapter imported from outside friday-skills")

    def read_uid(params: dict, **_kwargs) -> str:
        if not isinstance(params, dict):
            return json.dumps({"status": "blocked", "error": "invalid_request"})
        mode = params.get("mode", "mock")
        if mode not in {"mock", "read_only"} or set(params) - {"mailbox", "uid", "mode"}:
            return json.dumps({"status": "blocked", "error": "invalid_request"})
        try:
            if mode == "mock":
                result = gmx_mail.read_message(params.get("mailbox"), params.get("uid"), mode="mock")
            else:
                # This is explicit operator opt-in, never inferred from mail content.
                if os.environ.get("FRIDAY_GMX_ALLOW_READ") != "1":
                    return json.dumps({"status": "blocked", "error": "read_not_enabled"})
                address = os.environ.get("FRIDAY_GMX_ADDRESS")
                password = os.environ.get("FRIDAY_GMX_APP_PASSWORD")
                credentials = gmx_mail.GMXCredentials(address, password)
                result = gmx_mail.read_message(params.get("mailbox"), params.get("uid"),
                                               mode="read_only", credentials=credentials, use_stdlib_transport=True)
        except gmx_mail.MailAdapterError as exc:
            return json.dumps({"status": "blocked", "error": exc.code})
        except Exception:
            return json.dumps({"status": "blocked", "error": "read_failed"})
        return json.dumps(result, ensure_ascii=False)

    ctx.register_tool(name=TOOL_NAME, toolset="friday_gmx_mail", schema=SCHEMA, handler=read_uid)
