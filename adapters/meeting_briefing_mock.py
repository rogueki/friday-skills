"""Synthetic E2E3 briefing assembled from parsed CalDAV, RFC822 and task snapshot data."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from email.utils import parseaddr, parsedate_to_datetime
import re
from typing import Any, Mapping

from adapters.caldav_calendar import CalendarAdapterError, list_events
from adapters.gmx_mail import MailAdapterError, read_message
from shared.policy import PolicyError, capability_available
from shared.runtime import MockRuntime, dashboard_mapping, load_fixture, untrusted_text


VARIANTS = frozenset({
    "default", "missing_event", "wrong_event_time", "missing_mail", "foreign_mail", "stale_mail", "injection_mail",
    "missing_task", "stale_task", "duplicate_task", "foreign_task", "calendar_offline", "mail_offline",
    "task_offline", "calendar_capability_stale", "window_mismatch", "timezone_window",
})
TASK_ID = re.compile(r"[a-z][a-z0-9-]{1,63}\Z")


class MeetingMockError(ValueError):
    def __init__(self, code: str, status: str = "blocked"):
        super().__init__(code)
        self.code = code
        self.status = status


def _instant(value: str) -> datetime:
    if not isinstance(value, str):
        raise MeetingMockError("invalid_timestamp")
    try:
        value = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise MeetingMockError("invalid_timestamp") from exc
    if value.tzinfo is None or value.utcoffset() is None:
        raise MeetingMockError("timezone_required")
    return value.astimezone(timezone.utc)


def read_task_snapshot(
    snapshot: Mapping[str, Any], *, event_uid: str, expected_ids: list[str], cutoff: datetime,
) -> list[dict[str, str]]:
    """Validate a local synthetic snapshot, not a Control API task read."""
    if not isinstance(snapshot, Mapping) or snapshot.get("source") != "synthetic:fixtures/tasks/meeting_snapshot.json":
        raise MeetingMockError("task_source_untrusted")
    observed = _instant(snapshot.get("observed_at"))
    if observed > cutoff or cutoff - observed > timedelta(minutes=5):
        raise MeetingMockError("task_snapshot_stale", "partial")
    rows = snapshot.get("tasks")
    if not isinstance(rows, list) or len(rows) > 50 or not isinstance(expected_ids, list) or not expected_ids:
        raise MeetingMockError("invalid_task_snapshot")
    if len(set(expected_ids)) != len(expected_ids) or any(not isinstance(x, str) or not TASK_ID.fullmatch(x) for x in expected_ids):
        raise MeetingMockError("invalid_task_ids")
    seen: set[str] = set()
    selected: dict[str, dict[str, str]] = {}
    for row in rows:
        if not isinstance(row, dict) or not isinstance(row.get("id"), str) or not TASK_ID.fullmatch(row["id"]):
            raise MeetingMockError("invalid_task_row")
        if row["id"] in seen:
            raise MeetingMockError("duplicate_task")
        seen.add(row["id"])
        if row["id"] not in expected_ids:
            continue
        if row.get("meeting_uid") != event_uid:
            raise MeetingMockError("foreign_task")
        if row.get("status") not in {"open", "in_progress"}:
            raise MeetingMockError("task_not_open", "partial")
        title = row.get("title")
        if not isinstance(title, str) or not 1 <= len(title) <= 160:
            raise MeetingMockError("invalid_task_title")
        untrusted_text(title)
        due = _instant(row.get("due_at"))
        selected[row["id"]] = {"id": row["id"], "title": title, "status": row["status"],
                               "due_at": due.isoformat(), "meeting_uid": event_uid}
    if set(selected) != set(expected_ids):
        raise MeetingMockError("missing_task", "partial")
    return [selected[task_id] for task_id in expected_ids]


def run_meeting_mock(runtime: MockRuntime, result: dict[str, Any], trace: list[str], variant: str) -> None:
    if variant not in VARIANTS:
        raise ValueError(f"unknown meeting variant: {variant}")
    context = load_fixture("meetings", "e2e_context")
    task_snapshot = load_fixture("tasks", "meeting_snapshot")
    if variant == "missing_event":
        context["event_uid"] = "absent@example.invalid"
    elif variant == "wrong_event_time":
        context["expected_start"] = "2026-10-15T13:00:00Z"
    elif variant == "missing_mail":
        context["mail_uid"] = "82"
    elif variant == "window_mismatch":
        context["window_start"] = "2026-10-15T13:00:00Z"
        context["window_end"] = "2026-10-15T13:30:00Z"
    elif variant == "timezone_window":
        context["window_start"] = "2026-10-15T11:45:00"
    elif variant == "missing_task":
        task_snapshot["tasks"].pop()
    elif variant == "stale_task":
        task_snapshot["observed_at"] = "2026-10-15T11:40:00Z"
    elif variant == "duplicate_task":
        task_snapshot["tasks"].append(dict(task_snapshot["tasks"][0]))
    elif variant == "foreign_task":
        task_snapshot["tasks"][0]["meeting_uid"] = "other@example.invalid"
    elif variant.endswith("_offline"):
        context["capabilities"][variant.removesuffix("_offline")]["status"] = "offline"
    elif variant == "calendar_capability_stale":
        context["capabilities"]["calendar"]["checked_at"] = "2026-10-15T11:40:00Z"

    runtime.event("friday-meeting-briefing", "working", "Synthetic meeting preparation started", 0,
                  task_id="mock-meeting-1")
    try:
        for feed in ("calendar", "mail", "task"):
            if not capability_available(context["capabilities"][feed], permission="read", mode="mock", now=runtime.now):
                raise MeetingMockError(f"{feed}_capability_unavailable")
        trace.append("mock_source_capabilities_checked")
        cutoff = _instant(context["preparation_cutoff"])
        if cutoff != runtime.now:
            raise MeetingMockError("cutoff_mismatch")
        calendar = list_events(
            context["calendar_endpoint"], context["calendar_account"],
            _instant(context["window_start"]), _instant(context["window_end"]),
            allowed_host=context["calendar_host"], mode="mock",
        )
        trace.append("caldav_fixture_parsed")
        matches = [event for event in calendar["events"] if event["uid"] == context["event_uid"]]
        if len(matches) != 1:
            raise MeetingMockError("event_not_found")
        event = matches[0]
        untrusted_text(event["summary"])
        start, end = _instant(event["starts_at"]), _instant(event["ends_at"])
        if start != _instant(context["expected_start"]) or not start <= cutoff < end:
            raise MeetingMockError("event_time_mismatch")

        mail_fixture = {"foreign_mail": "e2e_meeting_foreign", "stale_mail": "e2e_meeting_stale",
                        "injection_mail": "e2e_meeting_injection"}.get(variant, "e2e_meeting")
        mail = read_message(context["mailbox"], context["mail_uid"], mode="mock", mock_fixture=mail_fixture)
        trace.append("rfc822_meeting_mail_parsed")
        if mail["status"] != "completed" or mail["suspicious_instructions"] or mail["attachments"]:
            raise MeetingMockError("untrusted_mail")
        untrusted_text(mail["body_text_untrusted"])
        if mail["message_id"] != context["message_id"] or not mail["message_id"]:
            raise MeetingMockError("message_id_mismatch")
        if parseaddr(mail["from"])[1] not in context["participants"]:
            raise MeetingMockError("mail_sender_outside_context")
        try:
            mail_at = parsedate_to_datetime(mail["date"])
        except (TypeError, ValueError) as exc:
            raise MeetingMockError("invalid_mail_date") from exc
        if mail_at.tzinfo is None:
            raise MeetingMockError("invalid_mail_date")
        mail_at = mail_at.astimezone(timezone.utc)
        if mail_at > cutoff or cutoff - mail_at > timedelta(days=7):
            raise MeetingMockError("mail_outside_cutoff", "partial")
        lines = mail["body_text_untrusted"].strip().splitlines()
        if len(lines) != 2 or lines[0] != f"Meeting-UID: {event['uid']}" or not lines[1].startswith("Question: "):
            raise MeetingMockError("mail_event_link_mismatch")
        question = lines[1].removeprefix("Question: ").strip()
        if not question or len(question) > 300:
            raise MeetingMockError("invalid_meeting_question")

        tasks = read_task_snapshot(task_snapshot, event_uid=event["uid"],
                                   expected_ids=context["task_ids"], cutoff=cutoff)
        trace.append("synthetic_task_snapshot_validated")
        sources = [
            {"kind": "calendar", "id": event["uid"], "source": calendar["source"],
             "etag": event["etag"], "starts_at": event["starts_at"]},
            {"kind": "mail", "id": mail["message_id"], "source": mail["source"],
             "uid": mail["uid"], "observed_at": mail_at.isoformat()},
            {"kind": "task_snapshot", "ids": [task["id"] for task in tasks],
             "source": task_snapshot["source"], "observed_at": _instant(task_snapshot["observed_at"]).isoformat()},
        ]
        result.update(status="completed", summary=f"{event['starts_at']}: {event['summary']}",
                      briefing={"goal": context["goal"], "participants": context["participants"],
                                "context": {"event_uid": event["uid"], "starts_at": event["starts_at"],
                                            "ends_at": event["ends_at"], "mail_message_id": mail["message_id"]},
                                "open_points": tasks, "risks": [], "questions": [question],
                                "decisions_needed": [context["goal"]], "materials": [],
                                "missing_data": ["prior_meetings", "documents", "contact_verification"],
                                "sources": sources},
                      sources=sources)
        trace.extend(["meeting_briefing_composed", "related_mail", "open_tasks_checked"])
        runtime.event("friday-meeting-briefing", "completed", "Synthetic meeting briefing composed", 1,
                      task_id="mock-meeting-1")
    except (MeetingMockError, CalendarAdapterError, MailAdapterError, PolicyError) as exc:
        status = exc.status if isinstance(exc, MeetingMockError) else "blocked"
        reason = exc.code if isinstance(exc, (MeetingMockError, CalendarAdapterError, MailAdapterError)) else "untrusted_source"
        result.update(status=status, reason=reason, missing_data=[reason])
        runtime.event("friday-meeting-briefing", status, "Synthetic meeting briefing incomplete", 0,
                      task_id="mock-meeting-1")
    result["dashboard_mapping"] = [dashboard_mapping(record) for record in runtime.records]
