"""Bounded, read-only GeoSphere Austria forecast client."""

from __future__ import annotations

import json
import math
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Callable
from urllib.parse import urlencode, urlsplit
from urllib.request import HTTPRedirectHandler, Request, build_opener


HOST = "dataset.api.hub.geosphere.at"
ENDPOINT = f"https://{HOST}/v1/timeseries/forecast/nwp-v2-1h-1km"
PARAMETERS = ("2t", "tp", "10u", "10v")
UNITS = {"2t": "degree Celsius", "tp": "kg m-2", "10u": "m s-1", "10v": "m s-1"}
MAX_BYTES = 1_000_000
Transport = Callable[[str, float], dict[str, Any]]


class WeatherAdapterError(ValueError):
    def __init__(self, code: str, detail: str):
        super().__init__(detail)
        self.code = code


class _NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, request: Request, fp: Any, code: int, msg: str, headers: Any, newurl: str) -> None:
        raise WeatherAdapterError("redirect_blocked", "GeoSphere request redirected")


def _fetch_json(url: str, timeout: float) -> dict[str, Any]:
    parsed = urlsplit(url)
    if parsed.scheme != "https" or parsed.hostname != HOST or parsed.port is not None or parsed.path != urlsplit(ENDPOINT).path:
        raise WeatherAdapterError("host_blocked", "unexpected forecast endpoint")
    request = Request(url, headers={"Accept": "application/json", "User-Agent": "RogueKI-Friday-Skills/0.2"}, method="GET")
    try:
        with build_opener(_NoRedirect()).open(request, timeout=timeout) as response:
            if response.headers.get_content_type() != "application/json":
                raise WeatherAdapterError("invalid_response", "expected JSON response")
            raw = response.read(MAX_BYTES + 1)
    except WeatherAdapterError:
        raise
    except OSError as exc:
        raise WeatherAdapterError("unavailable", "GeoSphere request failed") from exc
    if len(raw) > MAX_BYTES:
        raise WeatherAdapterError("response_too_large", "forecast response exceeds limit")
    try:
        payload = json.loads(raw)
    except (UnicodeError, json.JSONDecodeError) as exc:
        raise WeatherAdapterError("invalid_response", "forecast is not JSON") from exc
    if not isinstance(payload, dict):
        raise WeatherAdapterError("invalid_response", "forecast JSON must be an object")
    return payload


def _instant(value: Any) -> datetime:
    if not isinstance(value, str):
        raise WeatherAdapterError("invalid_time", "time must be an ISO timestamp")
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise WeatherAdapterError("invalid_time", "invalid ISO timestamp") from exc
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise WeatherAdapterError("invalid_time", "time must include a timezone")
    return parsed.astimezone(timezone.utc)


def _number(value: Any, key: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
        raise WeatherAdapterError("invalid_value", f"{key} must be a finite number")
    return float(value)


def _series(payload: dict[str, Any], timestamps: list[datetime], key: str) -> list[Any]:
    try:
        part = payload["features"][0]["properties"]["parameters"][key]
        if part["unit"] != UNITS[key] or not isinstance(part["data"], list) or len(part["data"]) != len(timestamps):
            raise WeatherAdapterError("invalid_response", f"bad {key} unit or series length")
        return part["data"]
    except (KeyError, IndexError, TypeError) as exc:
        raise WeatherAdapterError("invalid_response", f"missing {key} forecast series") from exc


def read_forecast(
    latitude: float,
    longitude: float,
    *,
    mode: str = "read_only",
    at: datetime | None = None,
    now: datetime | None = None,
    timeout: float = 8.0,
    transport: Transport | None = None,
) -> dict[str, Any]:
    """Read one forecast hour. Mock data is labelled synthetic; network is GET only."""
    if mode not in {"mock", "read_only", "live"}:
        raise WeatherAdapterError("invalid_mode", "unsupported adapter mode")
    lat, lon = _number(latitude, "latitude"), _number(longitude, "longitude")
    if not 43 <= lat <= 51.5 or not 5 <= lon <= 22.6:
        raise WeatherAdapterError("invalid_location", "coordinates outside model bounding box")
    if isinstance(timeout, bool) or not isinstance(timeout, (int, float)) or not 0 < timeout <= 15:
        raise WeatherAdapterError("invalid_timeout", "timeout must be between 0 and 15 seconds")
    current = (now or datetime.now(timezone.utc))
    target = at or current
    if current.tzinfo is None or target.tzinfo is None:
        raise WeatherAdapterError("invalid_time", "now and at need timezones")
    current, target = current.astimezone(timezone.utc), target.astimezone(timezone.utc)
    if not current - timedelta(hours=1) <= target <= current + timedelta(hours=48):
        raise WeatherAdapterError("invalid_horizon", "requested hour outside 48-hour forecast window")

    url = ENDPOINT + "?" + urlencode({"parameters": ",".join(PARAMETERS), "lat_lon": f"{lat:.5f},{lon:.5f}", "output_format": "geojson"})
    if mode == "mock":
        if transport is not None:
            raise WeatherAdapterError("invalid_transport", "mock mode cannot use an external transport")
        fixture = Path(__file__).resolve().parents[1] / "fixtures" / "weather" / "adapter_forecast.json"
        payload = json.loads(fixture.read_text(encoding="utf-8"))
        source = "synthetic:fixtures/weather/adapter_forecast.json"
    else:
        try:
            payload = (transport or _fetch_json)(url, float(timeout))
        except WeatherAdapterError:
            raise
        except Exception as exc:
            raise WeatherAdapterError("unavailable", "forecast transport failed") from exc
        source = url
    retrieved = current if now is not None or mode == "mock" else datetime.now(timezone.utc)
    if not isinstance(payload, dict) or payload.get("type") != "FeatureCollection":
        raise WeatherAdapterError("invalid_response", "forecast must be a FeatureCollection")
    raw_times = payload.get("timestamps")
    if not isinstance(raw_times, list) or not 1 <= len(raw_times) <= 96:
        raise WeatherAdapterError("invalid_response", "invalid forecast time series")
    timestamps = [_instant(t) for t in raw_times]
    if any(a >= b for a, b in zip(timestamps, timestamps[1:])):
        raise WeatherAdapterError("invalid_response", "forecast times are not strictly increasing")
    reference = _instant(payload.get("reference_time"))
    if mode != "mock" and not retrieved - timedelta(hours=12) <= reference <= retrieved + timedelta(minutes=5):
        raise WeatherAdapterError("stale_forecast", "model reference time is stale or future dated")
    features = payload.get("features")
    if not isinstance(features, list) or len(features) != 1 or not isinstance(features[0], dict):
        raise WeatherAdapterError("invalid_response", "expected exactly one forecast point")
    geometry = features[0].get("geometry")
    if not isinstance(geometry, dict):
        raise WeatherAdapterError("invalid_response", "missing forecast grid point")
    coords = geometry.get("coordinates")
    if geometry.get("type") != "Point" or not isinstance(coords, list) or len(coords) != 2:
        raise WeatherAdapterError("invalid_response", "missing forecast grid point")
    point_lon, point_lat = _number(coords[0], "point longitude"), _number(coords[1], "point latitude")
    if abs(point_lat - lat) > 0.05 or abs(point_lon - lon) > 0.05:
        raise WeatherAdapterError("wrong_location", "forecast grid point does not match request")
    index = next((i for i, stamp in enumerate(timestamps) if target <= stamp <= target + timedelta(hours=1)), None)
    if index is None:
        raise WeatherAdapterError("no_forecast_hour", "no matching forecast hour")
    values = {key: _series(payload, timestamps, key)[index] for key in PARAMETERS}
    temperature = _number(values["2t"], "temperature")
    warnings: list[str] = []
    precipitation: float | None = None
    wind: float | None = None
    try:
        precipitation = _number(values["tp"], "precipitation")
        if precipitation < 0:
            raise WeatherAdapterError("invalid_value", "negative precipitation")
    except WeatherAdapterError:
        warnings.append("precipitation_unavailable")
    try:
        wind = round(math.hypot(_number(values["10u"], "wind u"), _number(values["10v"], "wind v")), 2)
    except WeatherAdapterError:
        warnings.append("wind_unavailable")
    return {
        "status": "partial" if warnings else "completed",
        "mode": mode,
        "provider": "GeoSphere Austria" if mode != "mock" else "synthetic fixture",
        "model": "nwp-v2-1h-1km" if mode != "mock" else "synthetic",
        "requested_coordinates": {"latitude": lat, "longitude": lon},
        "grid_coordinates": {"latitude": point_lat, "longitude": point_lon},
        "reference_time": reference.isoformat(),
        "valid_time": timestamps[index].isoformat(),
        "retrieved_at": retrieved.isoformat(),
        "temperature_c": temperature,
        "precipitation_kg_m2": precipitation,
        "wind_speed_m_s": wind,
        "warnings": warnings,
        "source": source,
        "license": "CC BY 4.0" if mode != "mock" else "synthetic",
    }
