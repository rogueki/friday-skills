"""E2E4: local forecast-to-text composition with no audio or network effects."""

from __future__ import annotations

import math
from datetime import datetime, timedelta, timezone
from typing import Any, Callable, Mapping

from adapters.weather import WeatherAdapterError, read_forecast
from shared.policy import capability_available
from shared.runtime import MockRuntime, dashboard_mapping, load_fixture, route_request, untrusted_text

ForecastReader = Callable[..., dict[str, Any]]
SOURCE = "synthetic:fixtures/weather/adapter_forecast.json"


def _instant(value: Any) -> datetime:
    if not isinstance(value, str):
        raise ValueError("invalid_time")
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise ValueError("invalid_time") from exc
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise ValueError("invalid_time")
    return parsed.astimezone(timezone.utc)


def _location(value: Any) -> dict[str, Any]:
    if not isinstance(value, Mapping):
        raise ValueError("invalid_location")
    name, lat, lon = value.get("name"), value.get("latitude"), value.get("longitude")
    if not isinstance(name, str) or not 1 <= len(name.strip()) <= 80:
        raise ValueError("invalid_location")
    if not all(isinstance(v, (int, float)) and not isinstance(v, bool) and math.isfinite(v) for v in (lat, lon)):
        raise ValueError("invalid_location")
    if not 43 <= lat <= 51.5 or not 5 <= lon <= 22.6:
        raise ValueError("invalid_location")
    return {"name": untrusted_text(name.strip()), "latitude": float(lat), "longitude": float(lon)}


def run_weather_mock(
    runtime: MockRuntime, result: dict[str, Any], trace: list[str], *, variant: str = "default",
    request: str | None = None, location_override: Mapping[str, Any] | None = None,
    forecast_reader: ForecastReader = read_forecast, context: dict[str, Any] | None = None,
) -> None:
    """Compose a validated one-hour synthetic forecast; injected readers are test-only."""
    variants = {"default", "stale", "missing_location", "invalid_location", "adapter_offline",
                "capability_offline", "weather_briefing", "morning_briefing"}
    if variant not in variants:
        raise ValueError(f"unknown weather variant: {variant}")
    setup = context if context is not None else load_fixture("weather", "e2e_context")
    if variant == "missing_location":
        setup["default_location"] = None
    elif variant == "invalid_location":
        setup["default_location"] = {"name": "Wien", "latitude": "bad", "longitude": 16.3738}
    elif variant == "capability_offline":
        setup["capability"]["status"] = "offline"
    elif variant == "weather_briefing":
        request = "Wetter im Briefing"
    elif variant == "morning_briefing":
        request = "Gib mir mein Morgenbriefing"

    runtime.event("friday-weather", "working", "Synthetic forecast request started", 0)
    route = route_request(request or setup["request"])
    result["route"] = route
    result["voice_playback"] = {"status": "NOT_RUN", "played": False}
    if route.get("status") != "selected" or route.get("skill") != "friday-weather":
        result.update(status="blocked", reason="weather_route_unavailable")
    else:
        trace.append("weather_route")
        try:
            selected = _location(location_override if location_override is not None else setup.get("default_location"))
            trace.append("explicit_location" if location_override is not None else "configured_default_location")
            if not capability_available(setup["capability"], permission="read", mode="mock", now=runtime.now):
                raise ValueError("weather_capability_unavailable")
            target = _instant(setup["forecast_at"])
            if not runtime.now <= target <= runtime.now + timedelta(hours=48):
                raise ValueError("invalid_forecast_horizon")
            if variant == "adapter_offline":
                raise WeatherAdapterError("unavailable", "synthetic adapter offline")
            forecast = forecast_reader(selected["latitude"], selected["longitude"], mode="mock",
                                       at=target, now=runtime.now)
            trace.append("forecast_adapter_called")
            if variant == "stale":
                forecast = {**forecast, "reference_time": (runtime.now - timedelta(hours=13)).isoformat()}
            if not isinstance(forecast, dict) or forecast.get("status") != "completed":
                raise ValueError("forecast_incomplete")
            if forecast.get("mode") != "mock" or forecast.get("source") != SOURCE or forecast.get("provider") != "synthetic fixture":
                raise ValueError("forecast_source_invalid")
            coords = forecast.get("requested_coordinates")
            if not isinstance(coords, dict) or coords.get("latitude") != selected["latitude"] or coords.get("longitude") != selected["longitude"]:
                raise ValueError("forecast_location_mismatch")
            reference, valid, retrieved = (_instant(forecast.get(key)) for key in
                                           ("reference_time", "valid_time", "retrieved_at"))
            if not runtime.now - timedelta(hours=12) <= reference <= runtime.now + timedelta(minutes=5):
                raise ValueError("stale_weather")
            if retrieved != runtime.now or not target <= valid <= target + timedelta(hours=1):
                raise ValueError("forecast_time_invalid")
            temperature = forecast.get("temperature_c")
            if not isinstance(temperature, (int, float)) or isinstance(temperature, bool) or not math.isfinite(temperature):
                raise ValueError("forecast_temperature_invalid")
            answer = f"Synthetische Prognose für {selected['name']} um {valid:%H:%M} UTC: {temperature:g} °C."
            result.update(status="completed", location=selected, forecast=forecast,
                          voice_answer_text=answer, answer=answer)
            trace.extend(["forecast_source_and_times_checked", "local_voice_text"])
        except WeatherAdapterError as exc:
            result.update(status="blocked", reason=f"weather_adapter_{exc.code}")
        except (ValueError, KeyError, TypeError) as exc:
            reason = str(exc) if isinstance(exc, ValueError) else "forecast_incomplete"
            result.update(status="partial" if reason == "stale_weather" else "blocked", reason=reason)
    runtime.event("friday-weather", result["status"], "Synthetic forecast flow " + result["status"],
                  1 if result["status"] == "completed" else 0)
    result["dashboard_mapping"] = [dashboard_mapping(record) for record in runtime.records]
