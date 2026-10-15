"""Bounded read-only normalizer for allowlisted Loxone status snapshots.

The provider callback is an integration boundary, not a Loxone wire-protocol
implementation. It must return the documented provider-neutral snapshot shape.
"""

from __future__ import annotations

import json
import math
import re
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Protocol


MAX_CONTROLS = 100
MAX_AGE = timedelta(minutes=5)
MAX_FUTURE_SKEW = timedelta(seconds=60)
ID_PATTERN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.:-]{0,63}$")
class AuthenticatedTransport(Protocol):
    """Injected provider attesting it established an authenticated read session."""

    authenticated: bool

    def read_snapshot(self, control_ids: tuple[str, ...], timeout: float) -> dict[str, Any]: ...

# Exact units constrain interpretation and prevent accidental unit conversion.
NUMERIC_UNITS = {
    "temperature": {"°C": (-50.0, 100.0)},
    "humidity": {"%": (0.0, 100.0)},
    "light": {"%": (0.0, 100.0)},
    "shading": {"%": (0.0, 100.0)},
    "heating": {"°C": (-10.0, 80.0)},
    "pv": {"W": (0.0, 1_000_000.0)},
    "battery": {"%": (0.0, 100.0)},
    "consumption": {"W": (0.0, 1_000_000.0)},
}
BOOLEAN_KINDS = {"window", "door", "alarm"}
KINDS = frozenset(NUMERIC_UNITS) | BOOLEAN_KINDS


class LoxoneStatusError(ValueError):
    """A stable, safe-to-report adapter error."""

    def __init__(self, code: str, detail: str):
        super().__init__(detail)
        self.code = code


def _timestamp(value: Any, field: str) -> datetime:
    if not isinstance(value, str):
        raise LoxoneStatusError("invalid_timestamp", f"{field} must be an ISO timestamp")
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise LoxoneStatusError("invalid_timestamp", f"{field} is invalid") from exc
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise LoxoneStatusError("invalid_timestamp", f"{field} must include a timezone")
    return parsed.astimezone(timezone.utc)


def _id(value: Any, field: str) -> str:
    if not isinstance(value, str) or not ID_PATTERN.fullmatch(value):
        raise LoxoneStatusError("invalid_id", f"{field} is invalid")
    return value


def _validate_fresh(timestamp: datetime, now: datetime, field: str) -> None:
    if timestamp > now + MAX_FUTURE_SKEW:
        raise LoxoneStatusError("future_status", f"{field} is future-dated")
    if now - timestamp > MAX_AGE:
        raise LoxoneStatusError("stale_status", f"{field} is older than five minutes")


def _normalize(snapshot: Any, allowlist: tuple[str, ...], now: datetime) -> dict[str, Any]:
    if not isinstance(snapshot, dict) or set(snapshot) != {"version", "observed_at", "controls"}:
        raise LoxoneStatusError("invalid_snapshot", "snapshot must match version 1 contract")
    if snapshot["version"] != 1:
        raise LoxoneStatusError("unsupported_version", "snapshot version is unsupported")
    observed = _timestamp(snapshot["observed_at"], "observed_at")
    _validate_fresh(observed, now, "observed_at")
    controls = snapshot["controls"]
    if not isinstance(controls, list) or len(controls) > MAX_CONTROLS:
        raise LoxoneStatusError("invalid_snapshot", "controls must be a bounded list")

    allowed = set(allowlist)
    seen: set[str] = set()
    output: list[dict[str, Any]] = []
    rooms: set[str] = set()
    for control in controls:
        expected = {"id", "room_id", "kind", "value", "unit", "updated_at"}
        if not isinstance(control, dict) or set(control) != expected:
            raise LoxoneStatusError("invalid_control", "control does not match the normalized contract")
        control_id = _id(control["id"], "control id")
        room_id = _id(control["room_id"], "room id")
        if control_id not in allowed:
            raise LoxoneStatusError("not_allowlisted", "provider returned a control outside the explicit allowlist")
        if control_id in seen:
            raise LoxoneStatusError("duplicate_control", "snapshot contains duplicate control IDs")
        seen.add(control_id)
        kind = control["kind"]
        if not isinstance(kind, str) or kind not in KINDS:
            raise LoxoneStatusError("unsupported_control", "control kind is not permitted")
        updated = _timestamp(control["updated_at"], "updated_at")
        _validate_fresh(updated, now, "updated_at")
        if updated > observed + MAX_FUTURE_SKEW:
            raise LoxoneStatusError("invalid_timestamp", "control timestamp exceeds snapshot time")

        unit = control["unit"]
        value = control["value"]
        if kind in BOOLEAN_KINDS:
            if unit != "boolean" or not isinstance(value, bool):
                raise LoxoneStatusError("invalid_value", "binary controls require a boolean value and unit")
            # Alarm details/text/source are never accepted or returned; only active state.
        else:
            choices = NUMERIC_UNITS[kind]
            if not isinstance(unit, str) or unit not in choices:
                raise LoxoneStatusError("invalid_unit", "unit does not match the control kind")
            if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
                raise LoxoneStatusError("invalid_value", "numeric control must have a finite number")
            lower, upper = choices[unit]
            if not lower <= value <= upper:
                raise LoxoneStatusError("out_of_range", "control value is outside its accepted range")
            value = float(value)

        rooms.add(room_id)
        output.append({
            "id": control_id,
            "room_id": room_id,
            "kind": kind,
            "value": value,
            "unit": unit,
            "updated_at": updated.isoformat(),
        })

    output.sort(key=lambda item: (item["room_id"], item["id"]))
    return {
        "observed_at": observed.isoformat(),
        "rooms": sorted(rooms),
        "controls": output,
        "control_count": len(output),
    }


def read_status(
    allowed_control_ids: list[str] | tuple[str, ...],
    *,
    mode: str = "mock",
    now: datetime | None = None,
    timeout: float = 5.0,
    transport: AuthenticatedTransport | None = None,
) -> dict[str, Any]:
    """Read a normalized, allowlisted snapshot. No direct Loxone protocol is used.

    ``mock`` reads a labelled local fixture. ``read_only`` requires an explicitly
    injected authenticated transport. The adapter exposes no mutation operation.
    """
    if mode not in {"mock", "read_only", "live"}:
        raise LoxoneStatusError("invalid_mode", "mode must be mock, read_only or live")
    if not isinstance(allowed_control_ids, (list, tuple)) or not 1 <= len(allowed_control_ids) <= MAX_CONTROLS:
        raise LoxoneStatusError("invalid_allowlist", "one to 100 control IDs must be explicitly allowlisted")
    allowlist = tuple(_id(item, "control id") for item in allowed_control_ids)
    if len(set(allowlist)) != len(allowlist):
        raise LoxoneStatusError("invalid_allowlist", "control IDs must be unique")
    if isinstance(timeout, bool) or not isinstance(timeout, (int, float)) or not 0 < timeout <= 15:
        raise LoxoneStatusError("invalid_timeout", "timeout must be between 0 and 15 seconds")
    current = now or datetime.now(timezone.utc)
    if current.tzinfo is None or current.utcoffset() is None:
        raise LoxoneStatusError("invalid_timestamp", "now must include a timezone")
    current = current.astimezone(timezone.utc)

    if mode == "mock":
        if transport is not None:
            raise LoxoneStatusError("invalid_transport", "mock mode cannot use an external transport")
        path = Path(__file__).resolve().parents[1] / "fixtures" / "loxone" / "adapter_status.json"
        snapshot = json.loads(path.read_text(encoding="utf-8"))
        snapshot["controls"] = [row for row in snapshot["controls"] if row["id"] in set(allowlist)]
        # Keep the fixture deterministic while exercising freshness checks.
        snapshot["observed_at"] = (current - timedelta(seconds=20)).isoformat()
        for record in snapshot["controls"]:
            record["updated_at"] = (current - timedelta(seconds=20)).isoformat()
        source = "synthetic:fixtures/loxone/adapter_status.json"
    else:
        if transport is None or getattr(transport, "authenticated", False) is not True:
            raise LoxoneStatusError("transport_required", "read_only mode requires an explicitly authenticated transport")
        try:
            snapshot = transport.read_snapshot(allowlist, float(timeout))
        except Exception as exc:
            # Avoid forwarding provider details which can contain secrets or host information.
            raise LoxoneStatusError("provider_unavailable", "status provider did not return a snapshot") from exc
        source = "injected-provider-snapshot"

    normalized = _normalize(snapshot, allowlist, current)
    return {
        "status": "completed",
        "mode": mode,
        "provider": "synthetic fixture" if mode == "mock" else "injected provider",
        "source": source,
        "synthetic": mode == "mock",
        "write_effect": False,
        **normalized,
    }
