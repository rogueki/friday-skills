"""Optional Hermes tools for the host-bound F.R.I.D.A.Y. Content Studio API."""

from __future__ import annotations

import json
import os
from pathlib import Path
import sys
from uuid import uuid4

from adapters.content_studio_control import ContentStudioClient, StudioError, StudioHostBinding


def _schema(name: str, description: str, properties: dict, required: list[str]) -> dict:
    return {"name": name, "description": description, "parameters": {
        "type": "object", "properties": properties, "required": required, "additionalProperties": False,
    }}


SCHEMAS = {
    "friday_studio_read_plan": _schema("friday_studio_read_plan", "Read the authoritative F.R.I.D.A.Y. Content Studio plan and its current revision. No publishing occurs.", {}, []),
    "friday_studio_write_plan": _schema("friday_studio_write_plan", "Replace the Content Studio plan only when expected_revision matches the current server revision. A conflict requires user review; never retry automatically. No publishing occurs.", {
        "plan": {"type": "object", "description": "Complete version 1 Content Studio plan with content and postings arrays"},
        "expected_revision": {"type": "integer", "minimum": 0, "description": "Revision returned by friday_studio_read_plan"},
    }, ["plan", "expected_revision"]),
    "friday_studio_create_media": _schema("friday_studio_create_media", "Request an approved paid kie.ai image or video through the local F.R.I.D.A.Y. Control API.", {
        "kind": {"type": "string", "enum": ["image", "video"]}, "prompt": {"type": "string", "maxLength": 2000},
        "aspect_ratio": {"type": "string", "enum": ["1:1", "16:9"]},
        "idempotency_key": {"type": "string", "description": "Stable unique key for this exact user intent, 8-128 characters"},
    }, ["kind", "prompt", "aspect_ratio", "idempotency_key"]),
    "friday_studio_media_status": _schema("friday_studio_media_status", "Read status of one existing kie.ai task created by this Control API.", {
        "task_id": {"type": "string"},
    }, ["task_id"]),
    "friday_studio_create_speech": _schema("friday_studio_create_speech", "Request approved paid ElevenLabs MP3 speech through F.R.I.D.A.Y. Control API.", {
        "text": {"type": "string", "maxLength": 2500}, "voice_id": {"type": "string"},
        "idempotency_key": {"type": "string", "description": "Stable unique key for this exact user intent, 8-128 characters"},
    }, ["text", "voice_id", "idempotency_key"]),
    "friday_studio_create_production": _schema("friday_studio_create_production", "After explicit host approval, start one paid Content Studio production job for an idea in the current server plan. Never claim the job is finished until its status says completed.", {
        "idea_id": {"type": "string", "maxLength": 100}, "plan_revision": {"type": "integer", "minimum": 1},
        "voice_id": {"type": "string", "description": "Optional configured ElevenLabs voice ID"},
        "idempotency_key": {"type": "string", "description": "Stable unique key for this exact user intent, 8-128 characters"},
    }, ["idea_id", "plan_revision", "idempotency_key"]),
    "friday_studio_production_status": _schema("friday_studio_production_status", "Read a production job state; provider_unknown and speech_unknown require operator review, not automatic retry.", {
        "job_id": {"type": "string", "description": "UUID from friday_studio_create_production"},
    }, ["job_id"]),
    "friday_studio_cancel_production": _schema("friday_studio_cancel_production", "Stop further local work and provider requests for a production job. Already submitted provider requests may have incurred charges.", {
        "job_id": {"type": "string", "description": "UUID from friday_studio_create_production"},
    }, ["job_id"]),
}


def _blocked(code: str) -> str:
    return json.dumps({"status": "blocked", "error": {"code": code}, "write_effect": False})


def _interactive_binding() -> tuple[StudioHostBinding | None, Path | None]:
    """Optional local CLI binding. Gateway/non-TTY sessions always fail closed."""
    if os.environ.get("FRIDAY_CONTENT_STUDIO_INTERACTIVE_APPROVAL") != "1":
        return None, None
    origin = os.environ.get("FRIDAY_CONTROL_API_ORIGIN", "")
    session = os.environ.get("FRIDAY_CONTROL_API_SESSION", "")
    csrf = os.environ.get("FRIDAY_CONTROL_API_CSRF", "")
    output = os.environ.get("FRIDAY_CONTENT_STUDIO_OUTPUT_DIR", "")
    if not all((origin, session, csrf, output)):
        return None, None

    def approve(action: str, payload: dict) -> bool:
        if not sys.stdin.isatty():
            return False
        try:
            print(f"\nF.R.I.D.A.Y. paid action: {action}\n{json.dumps(payload, ensure_ascii=False)}\nType YES to authorize this exact request: ", file=sys.stderr, flush=True)
            return input().strip() == "YES"
        except (EOFError, OSError):
            return False

    return StudioHostBinding(origin, session, csrf, approve, authorized=True), Path(output)


def register(ctx, *, host: StudioHostBinding | None = None, output_dir: Path | None = None) -> None:
    configured = os.environ.get("FRIDAY_SKILLS_ROOT")
    if not configured:
        raise RuntimeError("FRIDAY_SKILLS_ROOT must point to the Friday skill package")
    root = Path(configured).resolve(strict=True)
    import adapters.content_studio_control as adapter
    if (root / "adapters" / "content_studio_control.py").resolve() != Path(adapter.__file__).resolve():
        raise RuntimeError("Content Studio adapter imported from outside Friday skills")
    if host is None:
        host, configured_output = _interactive_binding()
        output_dir = output_dir or configured_output

    def client() -> ContentStudioClient:
        if host is None:
            raise StudioError("host_binding_required")
        return ContentStudioClient(host)

    def create_media(params: dict, **_kwargs) -> str:
        if not isinstance(params, dict) or set(params) != {"kind", "prompt", "aspect_ratio", "idempotency_key"}:
            return _blocked("invalid_request")
        try:
            result = client().create_kie(kind=params["kind"], prompt=params["prompt"], aspect_ratio=params["aspect_ratio"], idempotency_key=params["idempotency_key"])
            return json.dumps({"status": "accepted", "task": result, "write_effect": True}, ensure_ascii=False)
        except StudioError as exc:
            return _blocked(exc.code)
        except Exception:
            return _blocked("bridge_failure")

    def read_plan(params: dict, **_kwargs) -> str:
        if not isinstance(params, dict) or params:
            return _blocked("invalid_request")
        try:
            return json.dumps({"status": "completed", "state": client().get_plan(), "write_effect": False}, ensure_ascii=False)
        except StudioError as exc:
            return _blocked(exc.code)
        except Exception:
            return _blocked("bridge_failure")

    def write_plan(params: dict, **_kwargs) -> str:
        if not isinstance(params, dict) or set(params) != {"plan", "expected_revision"}:
            return _blocked("invalid_request")
        try:
            return json.dumps({"status": "completed", "state": client().put_plan(plan=params["plan"], expected_revision=params["expected_revision"]), "write_effect": True}, ensure_ascii=False)
        except StudioError as exc:
            return _blocked(exc.code)
        except Exception:
            return _blocked("bridge_failure")

    def media_status(params: dict, **_kwargs) -> str:
        if not isinstance(params, dict) or set(params) != {"task_id"}:
            return _blocked("invalid_request")
        try:
            return json.dumps({"status": "completed", "task": client().get_kie(params["task_id"]), "write_effect": False}, ensure_ascii=False)
        except StudioError as exc:
            return _blocked(exc.code)
        except Exception:
            return _blocked("bridge_failure")

    def create_speech(params: dict, **_kwargs) -> str:
        if not isinstance(params, dict) or set(params) != {"text", "voice_id", "idempotency_key"}:
            return _blocked("invalid_request")
        if output_dir is None:
            return _blocked("output_dir_required")
        try:
            audio = client().create_speech(text=params["text"], voice_id=params["voice_id"], idempotency_key=params["idempotency_key"])
            target_dir = output_dir.resolve(strict=True)
            if not target_dir.is_dir():
                raise StudioError("output_dir_invalid")
            target = target_dir / f"friday-speech-{uuid4().hex}.mp3"
            with target.open("xb") as file:
                file.write(audio)
            return json.dumps({"status": "completed", "path": str(target), "bytes": len(audio), "write_effect": True}, ensure_ascii=False)
        except StudioError as exc:
            return _blocked(exc.code)
        except Exception:
            return _blocked("bridge_failure")

    def create_production(params: dict, **_kwargs) -> str:
        if not isinstance(params, dict) or not {"idea_id", "plan_revision", "idempotency_key"} <= set(params) or set(params) - {"idea_id", "plan_revision", "voice_id", "idempotency_key"}:
            return _blocked("invalid_request")
        try:
            job = client().create_production(idea_id=params["idea_id"], plan_revision=params["plan_revision"], voice_id=params.get("voice_id"), idempotency_key=params["idempotency_key"])
            return json.dumps({"status": "accepted", "job": job, "write_effect": True}, ensure_ascii=False)
        except StudioError as exc:
            return _blocked(exc.code)
        except Exception:
            return _blocked("bridge_failure")

    def production_status(params: dict, **_kwargs) -> str:
        if not isinstance(params, dict) or set(params) != {"job_id"}:
            return _blocked("invalid_request")
        try:
            return json.dumps({"status": "completed", "job": client().get_production(params["job_id"]), "write_effect": False}, ensure_ascii=False)
        except StudioError as exc:
            return _blocked(exc.code)
        except Exception:
            return _blocked("bridge_failure")

    def cancel_production(params: dict, **_kwargs) -> str:
        if not isinstance(params, dict) or set(params) != {"job_id"}:
            return _blocked("invalid_request")
        try:
            return json.dumps({"status": "completed", "job": client().cancel_production(params["job_id"]), "write_effect": True}, ensure_ascii=False)
        except StudioError as exc:
            return _blocked(exc.code)
        except Exception:
            return _blocked("bridge_failure")

    for name, handler in (("friday_studio_read_plan", read_plan), ("friday_studio_write_plan", write_plan), ("friday_studio_create_media", create_media), ("friday_studio_media_status", media_status), ("friday_studio_create_speech", create_speech), ("friday_studio_create_production", create_production), ("friday_studio_production_status", production_status), ("friday_studio_cancel_production", cancel_production)):
        ctx.register_tool(name=name, toolset="friday_content_studio", schema=SCHEMAS[name], handler=handler)
