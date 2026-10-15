"""Offline CalDAV contract tests; no real calendar or credentials."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from hashlib import sha256
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from adapters.caldav_calendar import (
    CalendarAdapterError, Request, Response, list_events, parse_event, write_event,
)
from shared.policy import action_fingerprint


ROOT = Path(__file__).resolve().parents[1]
FIXTURE = (ROOT / "fixtures/calendar/adapter_multistatus.xml").read_bytes()
ENDPOINT = "https://cal.example.invalid/calendars/friday/"
NOW = datetime(2026, 10, 15, 10, 0, tzinfo=timezone.utc)
START = NOW
END = NOW + timedelta(days=1)
ICAL = "\r\n".join((
    "BEGIN:VCALENDAR", "VERSION:2.0", "BEGIN:VEVENT", "UID:friday-write@example.invalid",
    "DTSTART:20261015T120000Z", "DTEND:20261015T123000Z", "SUMMARY:Approved work",
    "END:VEVENT", "END:VCALENDAR", "",
))


def response(status=207, body=FIXTURE, headers=None):
    return Response(status, headers or {}, body)


def capability():
    return {"name": "calendar.write", "status": "healthy", "mode": "live",
            "permissions": ["write"], "checked_at": NOW.isoformat(), "authenticated": True,
            "rate_limited": False}


def approval(target, etag=None, ical=ICAL, expires=None):
    payload = {"account": "friday@example.invalid", "ical": ical, "etag": etag}
    return {"status": "approved", "target": target, "tier": 2,
            "fingerprint": action_fingerprint("calendar_write", target, payload),
            "expires_at": (expires or NOW + timedelta(minutes=5)).isoformat()}


class CalDAVAdapterTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.ledger = Path(self.directory.name) / "mutations.sqlite"

    def test_mock_read_labels_fixture_and_never_calls_transport(self):
        result = list_events(ENDPOINT, "friday@example.invalid", START, END,
                             allowed_host="cal.example.invalid")
        self.assertEqual(result["mode"], "mock")
        self.assertTrue(result["synthetic"])
        self.assertEqual(len(result["events"]), 1)
        self.assertEqual(result["events"][0]["starts_at"], "2026-10-15T12:00:00+00:00")
        self.assertEqual(result["events"][0]["etag"], '"fixture-v1"')
        with self.assertRaises(CalendarAdapterError):
            list_events(ENDPOINT, "friday@example.invalid", START, END,
                        allowed_host="cal.example.invalid", transport=lambda _: response())

    def test_report_contract_and_timezone_window(self):
        seen: list[Request] = []

        def fetch(req):
            seen.append(req)
            return response()

        result = list_events(ENDPOINT, "friday@example.invalid",
                             datetime.fromisoformat("2026-10-15T12:00:00+02:00"),
                             datetime.fromisoformat("2026-10-16T12:00:00+02:00"),
                             allowed_host="cal.example.invalid", mode="read_only", transport=fetch)
        self.assertFalse(result["synthetic"])
        self.assertEqual(seen[0].method, "REPORT")
        self.assertEqual(seen[0].headers["Depth"], "1")
        self.assertIn(b'start="20261015T100000Z"', seen[0].body)
        self.assertIn(b'end="20261016T100000Z"', seen[0].body)

    def test_invalid_xml_ics_href_and_auth_fail_closed(self):
        for body, code in ((b"<!DOCTYPE a><a/>", "invalid_xml"),
                           (b"<D:multistatus xmlns:D='DAV:'><D:response></D:multistatus>", "invalid_xml"),
                           (FIXTURE.replace(b"BEGIN:VCALENDAR", b"BEGIN:NOTCAL"), "invalid_ical"),
                           (FIXTURE.replace(b"/calendars/friday/briefing.ics", b"/other/briefing.ics"), "invalid_href")):
            with self.subTest(code=code), self.assertRaises(CalendarAdapterError) as caught:
                list_events(ENDPOINT, "friday@example.invalid", START, END,
                            allowed_host="cal.example.invalid", mode="read_only",
                            transport=lambda _, body=body: response(body=body))
            self.assertEqual(caught.exception.code, code)
        with self.assertRaises(CalendarAdapterError) as caught:
            list_events(ENDPOINT, "friday@example.invalid", START, END,
                        allowed_host="cal.example.invalid", mode="read_only",
                        transport=lambda _: response(status=401))
        self.assertEqual(caught.exception.code, "auth_failed")

    def test_rejects_unbounded_or_naive_window_and_unlisted_host(self):
        for start, end in ((datetime(2026, 10, 15), END), (START, START + timedelta(days=32))):
            with self.assertRaises(CalendarAdapterError):
                list_events(ENDPOINT, "friday@example.invalid", start, end,
                            allowed_host="cal.example.invalid")
        with self.assertRaises(CalendarAdapterError) as caught:
            list_events(ENDPOINT, "friday@example.invalid", START, END,
                        allowed_host="evil.example.invalid")
        self.assertEqual(caught.exception.code, "invalid_endpoint")

    def test_ical_timezone_and_recurrence_restrictions(self):
        local = ICAL.replace("DTSTART:20261015T120000Z", "DTSTART;TZID=Europe/Berlin:20261015T140000")
        local = local.replace("DTEND:20261015T123000Z", "DTEND;TZID=Europe/Berlin:20261015T143000")
        with patch("adapters.caldav_calendar.ZoneInfo", return_value=timezone(timedelta(hours=2))):
            self.assertEqual(parse_event(local)["starts_at"], "2026-10-15T12:00:00+00:00")
        ambiguous = local.replace("Europe/Berlin", "Invalid/Timezone")
        with self.assertRaises(CalendarAdapterError):
            parse_event(ambiguous)
        with self.assertRaises(CalendarAdapterError) as caught:
            parse_event(ICAL.replace("SUMMARY:Approved work", "RRULE:FREQ=DAILY\r\nSUMMARY:Approved work"))
        self.assertEqual(caught.exception.code, "unsupported_recurrence")

    def _write(self, *, action="create", approval_record=None, capability_record=None,
               transport=None, key="op-1", href=None, etag=None, ical=ICAL):
        return write_event(ENDPOINT, "friday@example.invalid", ical,
                           allowed_host="cal.example.invalid", action=action,
                           idempotency_key=key, approval=approval_record,
                           capability=capability_record or capability(), ledger_path=self.ledger,
                           transport=transport or (lambda _: response(status=201, body=b"", headers={"ETag": '"v2"'})),
                           href=href, etag=etag, now=NOW)

    def test_create_requires_exact_unexpired_approval_and_conditional_put(self):
        seen = []
        target = ENDPOINT + sha256(b"friday@example.invalid:op-1").hexdigest() + ".ics"
        for record in (None, approval(target, expires=NOW - timedelta(seconds=1)),
                       approval(target, ical=ICAL.replace("Approved", "Changed"))):
            with self.assertRaises(CalendarAdapterError) as caught:
                self._write(approval_record=record, transport=lambda req: seen.append(req) or response(status=201))
            self.assertEqual(caught.exception.code, "approval_blocked")
        self.assertFalse(seen)
        result = self._write(approval_record=approval(target),
                             transport=lambda req: seen.append(req) or response(status=201, body=b"", headers={"ETag": '"v2"'}))
        self.assertTrue(result["write_effect"])
        self.assertEqual(seen[0].method, "PUT")
        self.assertEqual(seen[0].headers["If-None-Match"], "*")
        self.assertEqual(seen[0].url, target)
        self.assertEqual(len(seen), 1)
        self.assertEqual(self._write(approval_record=approval(target), transport=lambda req: seen.append(req)), result)
        self.assertEqual(len(seen), 1)

    def test_update_conflict_blocks_retry_and_requires_strong_etag(self):
        href = ENDPOINT + "briefing.ics"
        with self.assertRaises(CalendarAdapterError):
            self._write(action="update", href=href, etag='W/"weak"', approval_record=approval(href, 'W/"weak"'))
        seen = []
        with self.assertRaises(CalendarAdapterError) as caught:
            self._write(action="update", href=href, etag='"v1"', approval_record=approval(href, '"v1"'),
                        transport=lambda req: seen.append(req) or response(status=412, body=b""))
        self.assertEqual(caught.exception.code, "conflict")
        self.assertEqual(seen[0].headers["If-Match"], '"v1"')
        with self.assertRaises(CalendarAdapterError) as caught:
            self._write(action="update", href=href, etag='"v1"', approval_record=approval(href, '"v1"'),
                        transport=lambda req: seen.append(req))
        self.assertEqual(caught.exception.code, "outcome_uncertain")
        self.assertEqual(len(seen), 1)

    def test_uncertain_transport_and_duplicate_key_are_never_resent(self):
        target = ENDPOINT + sha256(b"friday@example.invalid:op-1").hexdigest() + ".ics"
        calls = []

        def timeout(req):
            calls.append(req)
            raise TimeoutError("synthetic timeout")

        with self.assertRaises(CalendarAdapterError) as caught:
            self._write(approval_record=approval(target), transport=timeout)
        self.assertEqual(caught.exception.code, "outcome_uncertain")
        with self.assertRaises(CalendarAdapterError) as caught:
            self._write(approval_record=approval(target), transport=timeout)
        self.assertEqual(caught.exception.code, "outcome_uncertain")
        self.assertEqual(len(calls), 1)
        with self.assertRaises(CalendarAdapterError) as caught:
            self._write(approval_record=approval(target), ical=ICAL.replace("Approved", "Changed"), transport=timeout)
        self.assertEqual(caught.exception.code, "approval_blocked")

    def test_stale_or_unauthenticated_capability_never_reaches_transport(self):
        target = ENDPOINT + sha256(b"friday@example.invalid:op-1").hexdigest() + ".ics"
        seen = []
        for broken in ({**capability(), "authenticated": False},
                       {**capability(), "checked_at": (NOW - timedelta(minutes=6)).isoformat()}):
            with self.subTest(broken=broken), self.assertRaises(CalendarAdapterError) as caught:
                self._write(approval_record=approval(target), capability_record=broken,
                            transport=lambda req: seen.append(req) or response(status=201))
            self.assertEqual(caught.exception.code, "approval_blocked")
        self.assertFalse(seen)


if __name__ == "__main__":
    unittest.main()
