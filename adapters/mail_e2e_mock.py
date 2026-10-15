"""Synthetic E2E1 composition: parsed mail, calendar context, approval, local simulation."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from email.utils import parseaddr, parsedate_to_datetime
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Any

from adapters.caldav_calendar import CalendarAdapterError, list_events
from adapters.gmx_mail import MailAdapterError, read_message
from shared.approval_ledger import ApprovalLedger, ApprovalLedgerError
from shared.policy import PolicyError, action_fingerprint, capability_available
from shared.runtime import MockRuntime, dashboard_mapping, load_fixture, untrusted_text


VARIANTS = frozenset({"default", "approved", "injection", "forged_approval", "expired_approval",
                      "changed_recipient", "changed_draft", "calendar_unavailable"})


def _instant(value: str) -> datetime:
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        raise ValueError("UTC timestamp required")
    return parsed.astimezone(timezone.utc)


def _map(runtime: MockRuntime, result: dict[str, Any]) -> None:
    result["dashboard_mapping"] = [dashboard_mapping(record) for record in runtime.records]


def run_important_mail_e2e(runtime: MockRuntime, result: dict[str, Any], trace: list[str], variant: str) -> None:
    """Run one pinned mock thread. Only the test harness issues a synthetic grant."""
    if variant not in VARIANTS:
        raise ValueError(f"unknown important_mail_e2e variant: {variant}")
    fixture_name, uid = ("e2e_injection", "72") if variant == "injection" else ("e2e_important", "71")
    context = load_fixture("mail", "e2e_context")
    runtime.event("friday-executive-mail-manager", "working", "Synthetic mail review started", 0, task_id="mock-mail-71")
    try:
        message = read_message("INBOX", uid, mode="mock", mock_fixture=fixture_name)
        trace.append("rfc822_parsed_by_gmx_adapter")
        if message["status"] != "completed" or message["suspicious_instructions"] or message["attachments"]:
            raise PolicyError("untrusted_mail")
        untrusted_text(message["body_text_untrusted"])
        sender = parseaddr(message["from"])[1]
        if sender != context["expected_sender"] or message["subject"] != "Urgent synthetic briefing request":
            raise PolicyError("sender_or_subject_mismatch")
        if not message["message_id"] or message["message_id"] != context["expected_message_id"]:
            raise PolicyError("message_id_mismatch")
        request_text = message["body_text_untrusted"].strip()
        if request_text != "Please confirm whether you can attend the briefing today at 12:00 UTC.":
            raise PolicyError("thread_content_mismatch")
        try:
            received_at = parsedate_to_datetime(message["date"])
        except (TypeError, ValueError) as exc:
            raise PolicyError("invalid_message_date") from exc
        if received_at.tzinfo is None or received_at.astimezone(timezone.utc).date() != runtime.now.date():
            raise PolicyError("invalid_message_date")
        result["classification"] = {"priority": "P1", "reason": "expected synthetic From field and exact urgent subject; sender unauthenticated",
                                     "source_uid": message["uid"], "source": message["source"]}
        result["thread_summary"] = {"thread_id": message["message_id"], "source_uid": message["uid"],
                                    "request": request_text,
                                    "received_at": received_at.astimezone(timezone.utc).isoformat()}
        trace.extend(["classified_P1", "thread_summary_from_parsed_fields"])
        capability = dict(context["calendar_capability"])
        if variant == "calendar_unavailable":
            capability["status"] = "offline"
        available = capability_available(capability, permission="read", mode="mock", now=runtime.now)
        result["calendar_capability"] = {"mode": "mock", "permission": "read", "available": available,
                                         "synthetic": True}
        trace.append("calendar_mock_capability_checked")
        if not available:
            raise CalendarAdapterError("capability_unavailable", "synthetic calendar capability unavailable")
        calendar = list_events(context["calendar_endpoint"], context["calendar_account"],
                               _instant(context["window_start"]), _instant(context["window_end"]),
                               allowed_host=context["calendar_host"], mode="mock")
        matching = [event for event in calendar["events"] if event["uid"] == "friday-briefing@example.invalid"]
        if len(matching) != 1 or matching[0]["starts_at"] != "2026-10-15T12:00:00+00:00":
            raise CalendarAdapterError("context_mismatch", "briefing calendar context unavailable")
        event = matching[0]
        result["calendar_context"] = {"source": calendar["source"], "uid": event["uid"],
                                      "starts_at": event["starts_at"], "ends_at": event["ends_at"],
                                      "summary": event["summary"]}
        trace.append("caldav_fixture_lookup_utc_window")
    except (MailAdapterError, CalendarAdapterError, PolicyError) as exc:
        reason = exc.code if isinstance(exc, (MailAdapterError, CalendarAdapterError)) else "untrusted_mail"
        result.update(status="blocked", reason=reason)
        runtime.audit.append({"kind": "local_decision", "reason": reason, "executed": False})
        runtime.event("friday-executive-mail-manager", "blocked", "Synthetic mail review blocked", 0,
                      task_id="mock-mail-71")
        _map(runtime, result)
        return

    runtime.event("friday-executive-mail-manager", "completed", "Synthetic P1 alert prepared locally", 1,
                  task_id="mock-mail-71")
    draft = {"sender": "friday@example.invalid", "recipient": context["recipient"],
             "subject": "Re: Urgent synthetic briefing request",
             "body": "Guten Tag,\n\ndanke für die Anfrage. Im Kalender steht ein Briefing heute von 12:00 bis 12:30 UTC. Bitte bestätigen Sie den vorgesehenen Termin.\n\nF.R.I.D.A.Y."}
    result["draft"] = draft
    fingerprint = action_fingerprint("send_message", draft["recipient"], draft)
    result["proposal"] = runtime.propose("send_message", draft["recipient"], draft, tier=2)
    result["approval_preview"] = {"action": "send_message", "recipient": draft["recipient"],
                                  "draft": draft, "fingerprint": fingerprint, "tier": 2,
                                  "approval_source": "synthetic operator fixture only"}
    trace.extend(["dashboard_alert_local", "reply_draft", "action_bound_approval_preview"])
    if variant == "default":
        result.update(status="waiting_approval", reason="synthetic_approval_required")
        runtime.event("friday-mail-draft-writer", "waiting_approval", "Synthetic reply awaits mock approval", 0.8,
                      task_id="mock-mail-71")
        _map(runtime, result)
        return

    key = "synthetic-mail-71-reply"
    with TemporaryDirectory(prefix="friday-mail-e2e-") as temp:
        ledger = ApprovalLedger(Path(temp) / "approvals.sqlite")
        if variant == "forged_approval":
            grant = "0" * 64
        else:
            expiry = runtime.now + timedelta(minutes=5)
            if variant == "expired_approval":
                # Issue during a synthetic prior decision, then consume after expiry.
                issued_at = runtime.now - timedelta(minutes=10)
                expiry = runtime.now - timedelta(minutes=5)
            else:
                issued_at = runtime.now
            grant = ledger.issue(action="send_message", target=draft["recipient"], payload=draft,
                                 idempotency_key=key, expires_at=expiry, decision_id="synthetic-operator-71",
                                 now=issued_at)
        recipient = "changed@example.invalid" if variant == "changed_recipient" else draft["recipient"]
        payload = {**draft, "body": draft["body"] + " changed"} if variant == "changed_draft" else draft
        try:
            ledger.consume(grant, action="send_message", target=recipient, payload=payload,
                           idempotency_key=key, now=runtime.now)
        except ApprovalLedgerError:
            result.update(status="blocked", reason="mock_approval_invalid")
            runtime.audit.append({"kind": "synthetic_approval_denied", "fingerprint": fingerprint,
                                  "executed": False})
            runtime.event("friday-approval-policy", "blocked", "Synthetic approval invalid", 0.8,
                          task_id="mock-mail-71")
            _map(runtime, result)
            return
        # Deliberately separate from adapters.gmx_mail.send_message and any SMTP transport.
        result["mock_send"] = {"kind": "local_simulation", "delivered": False, "transport": "none",
                               "recipient": recipient, "fingerprint": fingerprint, "source_uid": message["uid"]}
        result["status"] = "completed"
        runtime.audit.append({"kind": "synthetic_approval_consumed", "fingerprint": fingerprint,
                              "decision": "synthetic-operator-71", "executed": False})
        runtime.audit.append({"kind": "mock_delivery_record", "transport": "none", "delivered": False,
                              "executed": False})
        trace.extend(["synthetic_grant_consumed", "mock_delivery_simulated", "local_audit_recorded"])
        runtime.event("friday-mail-draft-writer", "completed", "Synthetic reply simulated locally", 1,
                      task_id="mock-mail-71")
        _map(runtime, result)
