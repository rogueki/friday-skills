"""Opt-in Hermes forecast tool backed by the bounded GeoSphere adapter."""

from __future__ import annotations

from datetime import datetime, timezone
import json
import os
from pathlib import Path
from typing import Any


MOCK_NOW = datetime(2026, 10, 15, 14, 0, tzinfo=timezone.utc)
TOOL_NAME = "friday_weather_forecast"
SCHEMA = {
    "name": TOOL_NAME,
    "description": (
        "Read one GeoSphere Austria forecast hour at explicit latitude and longitude. "
        "Default mock returns labelled synthetic data; read_only and live perform a "
        "public HTTPS GET. No geocoding, warning source, notification, or write action."
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "latitude": {"type": "number", "minimum": 43, "maximum": 51.5},
            "longitude": {"type": "number", "minimum": 5, "maximum": 22.6},
            "mode": {"type": "string", "enum": ["mock", "read_only", "live"]},
            "at": {"type": "string", "description": "Optional timezone-aware ISO timestamp within 48 hours"},
        },
        "required": ["latitude", "longitude"],
        "additionalProperties": False,
    },
}


def _forecast_time(value: Any) -> datetime | None:
    if value is None:
        return None
    if not isinstance(value, str):
        raise ValueError("at must be a timezone-aware ISO timestamp")
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise ValueError("at must be a timezone-aware ISO timestamp") from exc
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise ValueError("at must be a timezone-aware ISO timestamp")
    return parsed


def _blocked(mode: Any, code: str, message: str) -> str:
    return json.dumps({
        "status": "blocked", "mode": mode if isinstance(mode, str) else None, "forecast": None,
        "capability": None, "error": {"code": code, "message": message},
        "write_effect": False,
    }, ensure_ascii=False)


def register(ctx) -> None:
    """Register only when an operator explicitly enables this standalone plugin."""
    from adapters import weather

    configured = os.environ.get("FRIDAY_SKILLS_ROOT")
    if not configured:
        raise RuntimeError("FRIDAY_SKILLS_ROOT must point to the Friday weather support directory")
    root = Path(configured).resolve(strict=True)
    if (root / "adapters" / "weather.py").resolve() != Path(weather.__file__).resolve():
        raise RuntimeError("weather adapter was imported from outside this friday-skills package")
    if not (root / "fixtures" / "weather" / "adapter_forecast.json").is_file():
        raise RuntimeError("Friday weather support directory lacks the synthetic fixture")

    def forecast(params: dict, **_kwargs) -> str:
        if not isinstance(params, dict):
            return _blocked(None, "invalid_request", "parameters must be an object")
        mode = params.get("mode", "mock")
        if mode not in ("mock", "read_only", "live"):
            return _blocked(mode, "invalid_mode", "unsupported weather mode")
        if set(params) - {"latitude", "longitude", "mode", "at"}:
            return _blocked(mode, "invalid_request", "unexpected weather parameters")
        if "latitude" not in params or "longitude" not in params:
            return _blocked(mode, "invalid_location", "explicit latitude and longitude required")
        try:
            at = _forecast_time(params.get("at"))
        except ValueError as exc:
            return _blocked(mode, "invalid_time", str(exc))
        try:
            result = weather.read_forecast(
                params["latitude"], params["longitude"], mode=mode, at=at,
                **({"now": MOCK_NOW} if mode == "mock" else {}),
            )
        except weather.WeatherAdapterError as exc:
            return _blocked(mode, exc.code, str(exc))
        except Exception:
            return _blocked(mode, "adapter_failure", "forecast adapter failed")
        checked_at = datetime.now(timezone.utc).isoformat()
        return json.dumps({
            "status": result["status"], "mode": mode, "forecast": result,
            "capability": {
                "name": "weather.read", "status": "healthy", "mode": mode,
                "permissions": ["read"], "checked_at": checked_at,
                "source": result["source"],
                "synthetic": mode == "mock", "authenticated": mode == "mock",
                "rate_limited": False, "public_read": mode != "mock",
                "adapter_id": "geosphere-weather",
            },
            "write_effect": False,
        }, ensure_ascii=False)

    ctx.register_tool(name=TOOL_NAME, toolset="friday_weather", schema=SCHEMA, handler=forecast)
