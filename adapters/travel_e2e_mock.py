"""E2E5: deterministic synthetic family travel composition, without provider access."""

from __future__ import annotations

from copy import deepcopy
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal, InvalidOperation
from typing import Any

from shared.runtime import MockRuntime, dashboard_mapping, load_fixture


SOURCE = "synthetic:fixtures/travel/cases.json"
COST_KEYS = frozenset({"baggage", "seats", "transfers", "lodging_tax", "meals", "parking",
                       "activities", "insurance", "payment_fees"})
VARIANTS = frozenset({"default", "stale_quote", "missing_source", "missing_quote_time",
                      "insufficient_capacity", "unavailable", "invalid_cost", "date_mismatch",
                      "price_changed", "bad_itinerary"})


def _time(value: Any) -> datetime:
    if not isinstance(value, str):
        raise ValueError("missing_quote_time")
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise ValueError("invalid_quote_time") from exc
    if parsed.tzinfo is None or parsed.utcoffset() != timedelta(0):
        raise ValueError("invalid_quote_time")
    return parsed.astimezone(timezone.utc)


def _money(value: Any) -> Decimal:
    if not isinstance(value, str):
        raise ValueError("invalid_cost")
    try:
        amount = Decimal(value)
    except InvalidOperation as exc:
        raise ValueError("invalid_cost") from exc
    if not amount.is_finite() or amount < 0 or amount.as_tuple().exponent < -2:
        raise ValueError("invalid_cost")
    return amount.quantize(Decimal("0.01"))


def _profile(raw: dict[str, Any], now: datetime) -> dict[str, Any]:
    try:
        if raw["source"] != "synthetic:user-request" or _time(raw["recorded_at"]) > now:
            raise ValueError("profile_source_invalid")
        adults = raw["adults"]
        ages = raw["children_ages_at_departure"]
        if type(adults) is not int or not 1 <= adults <= 8 or not isinstance(ages, list) or not ages:
            raise ValueError("party_invalid")
        if any(type(age) is not int or not 0 <= age < 18 for age in ages):
            raise ValueError("party_invalid")
        start, end = date.fromisoformat(raw["trip_start"]), date.fromisoformat(raw["trip_end"])
        if not start > now.date() or not start < end or (end - start).days > 30:
            raise ValueError("trip_dates_invalid")
        budget = _money(raw["budget_eur"])
        if budget <= 0 or raw["retention"] != "transient_mock_only":
            raise ValueError("profile_invalid")
        if not isinstance(raw["preferences"], list) or not all(isinstance(x, str) for x in raw["preferences"]):
            raise ValueError("profile_invalid")
        return {"adults": adults, "children": len(ages), "children_ages_at_departure": ages,
                "budget_eur": str(budget), "departure_area": raw["departure_area"],
                "trip_start": start.isoformat(), "trip_end": end.isoformat(),
                "preferences": raw["preferences"], "source": raw["source"],
                "recorded_at": raw["recorded_at"], "retention": raw["retention"], "saved": False}
    except (KeyError, TypeError, ValueError) as exc:
        if isinstance(exc, ValueError) and str(exc) in {"profile_source_invalid", "party_invalid",
                                                    "trip_dates_invalid", "profile_invalid", "invalid_cost"}:
            raise
        raise ValueError("profile_invalid") from exc


def _offer(raw: dict[str, Any], profile: dict[str, Any], now: datetime) -> dict[str, Any]:
    if not isinstance(raw, dict):
        raise ValueError("quote_incomplete")
    try:
        if raw.get("source") != SOURCE or raw.get("terms_source") != SOURCE:
            raise ValueError("missing_source")
        observed = _time(raw.get("quoted_at"))
        if not now - timedelta(hours=24) <= observed <= now:
            raise ValueError("no_current_quote")
        if raw.get("available") is not True:
            raise ValueError("unavailable")
        if (type(raw.get("capacity_adults")) is not int or type(raw.get("capacity_children")) is not int
                or raw["capacity_adults"] < profile["adults"] or raw["capacity_children"] < profile["children"]):
            raise ValueError("insufficient_capacity")
        if raw.get("trip_start") != profile["trip_start"] or raw.get("trip_end") != profile["trip_end"]:
            raise ValueError("date_mismatch")
        if raw.get("currency") != "EUR":
            raise ValueError("unsupported_currency")
        costs = raw["costs"]
        if not isinstance(costs, dict) or costs.keys() != COST_KEYS:
            raise ValueError("invalid_cost")
        base = _money(raw["base_price"])
        line_items = {name: str(_money(costs[name])) for name in sorted(COST_KEYS)}
        total = base + sum((Decimal(value) for value in line_items.values()), Decimal("0.00"))
        if not raw.get("id") or not raw.get("provider") or not raw.get("cancellation"):
            raise ValueError("terms_missing")
        if not isinstance(raw.get("included"), list) or not all(isinstance(x, str) for x in raw["included"]):
            raise ValueError("terms_missing")
        return {"id": raw["id"], "kind": raw["kind"], "provider": raw["provider"],
                "destination": raw["destination"], "trip_start": raw["trip_start"],
                "trip_end": raw["trip_end"], "currency": "EUR", "base_price": str(base),
                "costs": line_items, "total_eur": str(total), "included": raw["included"],
                "cancellation": raw["cancellation"], "source": SOURCE, "quoted_at": raw["quoted_at"],
                "terms_source": SOURCE, "available_in_synthetic_snapshot": True}
    except (KeyError, TypeError, InvalidOperation) as exc:
        raise ValueError("quote_incomplete") from exc


def _itinerary(offer: dict[str, Any], profile: dict[str, Any], *, bad: bool) -> dict[str, Any]:
    start, end = date.fromisoformat(profile["trip_start"]), date.fromisoformat(profile["trip_end"])
    days = []
    for offset in range((end - start).days + 1):
        day = (start + timedelta(days=offset)).isoformat()
        phase = "arrival" if offset == 0 else "departure" if offset == (end - start).days else "stay"
        days.append({"date": day, "phase": phase,
                     "main_activity": "arrival and check-in" if phase == "arrival" else
                                      "departure and transfer" if phase == "departure" else
                                      "optional age-appropriate local activity",
                     "meals_and_rest": True, "rain_fallback": "indoor rest or flexible activity",
                     "timings": "to_verify", "opening_hours": "unverified",
                     "reservation": "none_confirmed"})
    itinerary = {"destination": offer["destination"], "trip_start": profile["trip_start"],
                 "trip_end": profile["trip_end"], "arrival_buffer_minutes": 90,
                 "departure_buffer_minutes": 120, "days": days,
                 "transport_times": "unverified", "status": "draft_only"}
    if bad:
        itinerary["arrival_buffer_minutes"] = 0
    if (itinerary["arrival_buffer_minutes"] < 60 or itinerary["departure_buffer_minutes"] < 60
            or len(days) != (end - start).days + 1 or any(day["reservation"] != "none_confirmed" for day in days)):
        raise ValueError("itinerary_invalid")
    return itinerary


def _flexible_cancellation(value: Any, now: datetime, departure: str) -> bool:
    if not isinstance(value, str) or not value.startswith("refundable_until_"):
        return False
    try:
        cutoff = date.fromisoformat(value.removeprefix("refundable_until_"))
    except ValueError:
        return False
    return now.date() < cutoff < date.fromisoformat(departure)


def run_travel_mock(runtime: MockRuntime, result: dict[str, Any], trace: list[str], *,
                    variant: str = "default", context: dict[str, Any] | None = None) -> None:
    if variant not in VARIANTS:
        raise ValueError(f"unknown family_travel variant: {variant}")
    fixture = "stale_quote" if variant == "stale_quote" else "cases"
    data = deepcopy(context if context is not None else load_fixture("travel", fixture))
    if variant == "missing_source":
        for quote in data["options"]:
            quote.pop("source", None)
    elif variant == "missing_quote_time":
        for quote in data["options"]:
            quote.pop("quoted_at", None)
    elif variant == "insufficient_capacity":
        for quote in data["options"]:
            quote["capacity_children"] = 1
    elif variant == "unavailable":
        for quote in data["options"]:
            quote["available"] = False
    elif variant == "invalid_cost":
        for quote in data["options"]:
            quote["costs"]["transfers"] = "-1.00"
    elif variant == "date_mismatch":
        for quote in data["options"]:
            quote["trip_start"] = "2026-11-03"

    runtime.event("friday-family-travel-profile", "working", "Synthetic travel request received", 0)
    trace.append("travel_request")
    try:
        if not isinstance(data.get("request"), str) or not data["request"].strip():
            raise ValueError("request_missing")
        profile = _profile(data["profile"], runtime.now)
        result["profile"] = profile
        result["party"] = {"adults": profile["adults"], "children": profile["children"]}
        trace.append("transient_family_profile")
        runtime.event("friday-family-travel-profile", "completed", "Transient synthetic profile checked", 1)
        runtime.event("friday-family-destination-research", "working", "Synthetic quote snapshot reviewed", 0)
        raw_options = data["options"]
        if not isinstance(raw_options, list) or not raw_options:
            raise ValueError("quote_incomplete")
        compared, rejected = [], []
        for raw in raw_options:
            try:
                compared.append(_offer(raw, profile, runtime.now))
            except ValueError as exc:
                rejected.append({"id": raw.get("id") if isinstance(raw, dict) else None,
                                 "reason": str(exc)})
        trace.append("synthetic_quote_research")
        result["research"] = {"source": SOURCE, "kind": "synthetic_fixture_only",
                              "provider_verified": False, "observed_at": runtime.now.isoformat(),
                              "rejected": rejected}
        if not compared:
            reasons = {item["reason"] for item in rejected}
            reason = "no_current_quote" if reasons == {"no_current_quote", "unavailable"} else sorted(reasons)[0]
            result.update(status="partial" if reason == "no_current_quote" else "blocked", reason=reason)
            return
        runtime.event("friday-family-destination-research", "completed", "Synthetic offers sourced", 1)
        eligible = []
        for offer in compared:
            offer["within_budget"] = Decimal(offer["total_eur"]) <= Decimal(profile["budget_eur"])
            offer["family_room"] = "family_room" in offer["included"]
            offer["flexible_cancel"] = _flexible_cancellation(
                offer["cancellation"], runtime.now, profile["trip_start"])
            if offer["within_budget"] and offer["family_room"] and offer["flexible_cancel"]:
                eligible.append(offer)
        result["comparison"] = {"currency": "EUR", "offers": compared,
                                "criteria": ["capacity", "dates", "full_cost", "budget", "family_room", "flexible_cancel"]}
        trace.append("family_fit_full_cost_comparison")
        if not eligible:
            result.update(status="partial", reason="no_family_fit_offer")
            return
        selected = min(eligible, key=lambda offer: (Decimal(offer["total_eur"]), offer["id"]))
        itinerary = _itinerary(selected, profile, bad=variant == "bad_itinerary")
        result["itinerary"] = itinerary
        trace.append("flexible_unverified_itinerary")
        bound_total = selected["total_eur"]
        if variant == "price_changed":
            bound_total = str(Decimal(bound_total) + Decimal("1.00"))
        draft = {"type": "non_executable_booking_draft", "quote_id": selected["id"],
                 "provider": selected["provider"], "source": selected["source"],
                 "quoted_at": selected["quoted_at"], "destination": selected["destination"],
                 "trip_start": selected["trip_start"], "trip_end": selected["trip_end"],
                 "travelers": {"adults": profile["adults"], "children": profile["children"],
                               "names": "REDACTED_NOT_COLLECTED"},
                 "currency": "EUR", "total_eur": bound_total,
                 "costs": selected["costs"], "cancellation": selected["cancellation"],
                 "payment_details": "NOT_COLLECTED", "provider_verified": False,
                 "reservation_status": "NOT_RESERVED"}
        if (draft["total_eur"] != selected["total_eur"] or draft["quote_id"] != selected["id"]
                or draft["trip_start"] != profile["trip_start"] or draft["trip_end"] != profile["trip_end"]):
            raise ValueError("draft_quote_mismatch")
        result["booking_draft"] = draft
        trace.append("redacted_booking_draft")
        proposal_payload = {"kind": selected["kind"], "quote_id": selected["id"],
                            "provider": selected["provider"], "trip_start": selected["trip_start"],
                            "trip_end": selected["trip_end"], "currency": "EUR",
                            "total_eur": selected["total_eur"], "draft_type": draft["type"],
                            "source": selected["source"], "quoted_at": selected["quoted_at"],
                            "terms_source": selected["terms_source"],
                            "cancellation": selected["cancellation"], "costs": selected["costs"]}
        result["proposal"] = runtime.propose("booking", "synthetic-trip", proposal_payload, tier=3)
        result["approval"] = {"status": "required", "tier": 3, "hard_approval": True,
                              "second_factor_required": True, "granted": False,
                              "real_provider_recheck_required": True}
        result["status"] = "waiting_approval"
        trace.append("hard_approval_required_no_booking")
    except (KeyError, TypeError, ValueError) as exc:
        result.update(status="blocked", reason=str(exc) if isinstance(exc, ValueError) else "travel_data_incomplete")
        result.pop("booking_draft", None)
    finally:
        runtime.event("friday-booking-preparation", result["status"],
                      "Synthetic travel flow " + result["status"],
                      0.9 if result["status"] == "waiting_approval" else 0)
        result["dashboard_mapping"] = [dashboard_mapping(record) for record in runtime.records]
