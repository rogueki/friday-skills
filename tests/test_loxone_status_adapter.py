from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from pathlib import Path
import unittest

from adapters.loxone_status import LoxoneStatusError, read_status


NOW = datetime(2026, 10, 15, 12, 0, tzinfo=timezone.utc)
FIXTURE = Path(__file__).resolve().parents[1] / "fixtures" / "loxone" / "adapter_status.json"
IDS = ["ctrl-living-temp", "ctrl-living-humidity", "ctrl-window-kitchen", "ctrl-pv-power", "ctrl-battery-level", "ctrl-alarm-summary"]


def snapshot():
    data = json.loads(FIXTURE.read_text(encoding="utf-8"))
    data["observed_at"] = NOW.isoformat()
    for row in data["controls"]:
        row["updated_at"] = NOW.isoformat()
    return data


class SnapshotProvider:
    authenticated = True

    def __init__(self, callback):
        self.callback = callback

    def read_snapshot(self, ids, timeout):
        return self.callback(ids, timeout)


class LoxoneStatusAdapterTests(unittest.TestCase):
    def test_injected_mock_snapshot_is_normalized_without_provider_or_timestamp_rewrite(self):
        synthetic = snapshot()
        synthetic["controls"] = [synthetic["controls"][0]]
        synthetic["observed_at"] = (NOW - timedelta(seconds=35)).isoformat()
        result = read_status([IDS[0]], now=NOW, mock_snapshot=synthetic)
        self.assertEqual(result["source"], "synthetic:injected-mock-snapshot")
        self.assertEqual(result["observed_at"], synthetic["observed_at"])
        self.assertTrue(result["synthetic"])
        with self.assertRaises(LoxoneStatusError) as context:
            read_status([IDS[0]], mode="read_only", now=NOW, mock_snapshot=synthetic)
        self.assertEqual(context.exception.code, "invalid_snapshot")

    def test_mock_is_labelled_and_returns_only_allowlisted_controls(self):
        result = read_status(IDS, now=NOW)
        self.assertTrue(result["synthetic"])
        self.assertEqual(result["mode"], "mock")
        self.assertEqual(result["control_count"], 6)
        self.assertEqual(result["source"], "synthetic:fixtures/loxone/adapter_status.json")
        self.assertFalse(result["write_effect"])
        result = read_status(["ctrl-living-temp"], now=NOW)
        self.assertEqual([item["id"] for item in result["controls"]], ["ctrl-living-temp"])

    def test_mock_cannot_use_external_transport_and_real_read_needs_explicit_transport(self):
        with self.assertRaises(LoxoneStatusError):
            read_status(IDS, mode="mock", now=NOW, transport=lambda *_: snapshot())
        with self.assertRaises(LoxoneStatusError) as context:
            read_status(IDS, mode="read_only", now=NOW)
        self.assertEqual(context.exception.code, "transport_required")

    def test_read_only_rejects_transport_without_authentication_attestation(self):
        class Provider:
            authenticated = False

            def read_snapshot(self, *_):
                return snapshot()

        with self.assertRaises(LoxoneStatusError) as context:
            read_status(IDS, mode="read_only", now=NOW, transport=Provider())
        self.assertEqual(context.exception.code, "transport_required")

    def test_injected_read_only_transport_receives_allowlist_and_timeout(self):
        calls = []

        class Provider:
            authenticated = True

            def read_snapshot(self, ids, timeout):
                calls.append((ids, timeout))
                return snapshot()

        result = read_status(IDS, mode="read_only", now=NOW, transport=Provider())
        self.assertEqual(calls, [(tuple(IDS), 5.0)])
        self.assertFalse(result["synthetic"])
        self.assertEqual(result["provider"], "injected provider")
        self.assertFalse(result["write_effect"])

    def test_rejects_unallowlisted_duplicate_or_invalid_ids(self):
        bad = snapshot()
        bad["controls"][0]["id"] = "not-allowlisted"
        with self.assertRaises(LoxoneStatusError) as context:
            read_status(IDS, mode="read_only", now=NOW, transport=SnapshotProvider(lambda *_: bad))
        self.assertEqual(context.exception.code, "not_allowlisted")
        with self.assertRaises(LoxoneStatusError):
            read_status(["../secret"], now=NOW)

    def test_rejects_stale_or_future_snapshot(self):
        for observed in ((NOW - timedelta(minutes=6)), (NOW + timedelta(minutes=2))):
            bad = snapshot()
            bad["observed_at"] = observed.isoformat()
            with self.subTest(observed=observed), self.assertRaises(LoxoneStatusError):
                read_status(IDS, mode="read_only", now=NOW, transport=SnapshotProvider(lambda *_: bad))

    def test_unit_range_shape_and_sensitive_fields_fail_closed(self):
        cases = []
        bad = snapshot()
        bad["controls"][0]["unit"] = "K"
        cases.append(bad)
        bad = snapshot()
        bad["controls"][0]["value"] = 500
        cases.append(bad)
        bad = snapshot()
        bad["controls"][0]["label"] = "Personal room"
        cases.append(bad)
        bad = snapshot()
        bad["controls"][-1]["alarm_text"] = "intruder details"
        cases.append(bad)
        for bad in cases:
            with self.subTest(snapshot=bad), self.assertRaises(LoxoneStatusError):
                read_status(IDS, mode="read_only", now=NOW, transport=SnapshotProvider(lambda *_: bad))

    def test_provider_errors_are_redacted(self):
        with self.assertRaises(LoxoneStatusError) as context:
            read_status(
                IDS,
                mode="read_only",
                now=NOW,
                transport=SnapshotProvider(lambda *_: (_ for _ in ()).throw(RuntimeError("password=secret"))),
            )
        self.assertEqual(context.exception.code, "provider_unavailable")
        self.assertNotIn("secret", str(context.exception))


if __name__ == "__main__":
    unittest.main()
