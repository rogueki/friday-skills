import json
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path

from adapters.weather import WeatherAdapterError, read_forecast


NOW = datetime(2026, 10, 15, 14, 0, tzinfo=timezone.utc)
FIXTURE = Path(__file__).resolve().parents[1] / "fixtures" / "weather" / "adapter_forecast.json"


def payload():
    return json.loads(FIXTURE.read_text(encoding="utf-8"))


class WeatherAdapterTests(unittest.TestCase):
    def test_mock_is_synthetic_and_never_calls_transport(self):
        result = read_forecast(48.2082, 16.3738, mode="mock", now=NOW)
        self.assertEqual((result["temperature_c"], result["wind_speed_m_s"]), (16.6, 2.0))
        self.assertEqual((result["mode"], result["license"]), ("mock", "synthetic"))
        with self.assertRaises(WeatherAdapterError):
            read_forecast(48.2082, 16.3738, mode="mock", now=NOW, transport=lambda *_: payload())

    def test_read_only_uses_exact_host_and_get_contract(self):
        seen = []

        def fetch(url, timeout):
            seen.append((url, timeout))
            return payload()

        result = read_forecast(48.2082, 16.3738, now=NOW, transport=fetch)
        self.assertEqual(result["status"], "completed")
        self.assertEqual(result["reference_time"], "2026-10-15T09:00:00+00:00")
        self.assertEqual(result["source"], seen[0][0])
        self.assertTrue(seen[0][0].startswith("https://dataset.api.hub.geosphere.at/v1/timeseries/forecast/nwp-v2-1h-1km?"))
        self.assertIn("lat_lon=48.20820%2C16.37380", seen[0][0])
        self.assertEqual(seen[0][1], 8.0)

    def test_live_is_still_read_only(self):
        result = read_forecast(48.2082, 16.3738, mode="live", now=NOW, transport=lambda *_: payload())
        self.assertEqual(result["status"], "completed")
        self.assertNotIn("actions_taken", result)

    def test_stale_forecast_fails_closed(self):
        with self.assertRaises(WeatherAdapterError) as context:
            read_forecast(48.2082, 16.3738, now=NOW + timedelta(hours=13), transport=lambda *_: payload())
        self.assertEqual(context.exception.code, "stale_forecast")

    def test_naive_timestamp_and_mismatched_location_fail(self):
        bad = payload()
        bad["timestamps"][0] = "2026-10-15T14:00:00"
        with self.assertRaises(WeatherAdapterError) as context:
            read_forecast(48.2082, 16.3738, now=NOW, transport=lambda *_: bad)
        self.assertEqual(context.exception.code, "invalid_time")
        bad = payload()
        bad["features"][0]["geometry"]["coordinates"] = [12.0, 46.0]
        with self.assertRaises(WeatherAdapterError) as context:
            read_forecast(48.2082, 16.3738, now=NOW, transport=lambda *_: bad)
        self.assertEqual(context.exception.code, "wrong_location")

    def test_missing_temperature_blocks_but_secondary_value_is_partial(self):
        bad = payload()
        bad["features"][0]["properties"]["parameters"]["2t"]["data"][0] = None
        with self.assertRaises(WeatherAdapterError) as context:
            read_forecast(48.2082, 16.3738, now=NOW, transport=lambda *_: bad)
        self.assertEqual(context.exception.code, "invalid_value")
        bad = payload()
        bad["features"][0]["properties"]["parameters"]["tp"]["data"][0] = None
        result = read_forecast(48.2082, 16.3738, now=NOW, transport=lambda *_: bad)
        self.assertEqual((result["status"], result["warnings"]), ("partial", ["precipitation_unavailable"]))

    def test_bad_unit_and_series_length_fail(self):
        bad = payload()
        bad["features"][0]["properties"]["parameters"]["2t"]["unit"] = "kelvin"
        with self.assertRaises(WeatherAdapterError) as context:
            read_forecast(48.2082, 16.3738, now=NOW, transport=lambda *_: bad)
        self.assertEqual(context.exception.code, "invalid_response")
        bad = payload()
        bad["features"][0]["properties"]["parameters"]["2t"]["data"].pop()
        with self.assertRaises(WeatherAdapterError):
            read_forecast(48.2082, 16.3738, now=NOW, transport=lambda *_: bad)

    def test_unavailable_and_bad_horizon_fail(self):
        def offline(*_):
            raise TimeoutError("offline")

        with self.assertRaises(WeatherAdapterError) as context:
            read_forecast(48.2082, 16.3738, now=NOW, transport=offline)
        self.assertEqual(context.exception.code, "unavailable")
        with self.assertRaises(WeatherAdapterError) as context:
            read_forecast(48.2082, 16.3738, now=NOW, at=NOW + timedelta(days=3), transport=lambda *_: payload())
        self.assertEqual(context.exception.code, "invalid_horizon")


if __name__ == "__main__":
    unittest.main()
