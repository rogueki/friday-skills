"""Forecast-to-text E2E4 contract, entirely offline."""

import unittest
from unittest.mock import patch

from adapters import weather
from adapters.weather_e2e_mock import run_weather_mock
from shared.runtime import MockRuntime, load_fixture
from shared.scenarios import run_scenario


class WeatherE2EMockTests(unittest.TestCase):
    def run_flow(self, **kwargs):
        runtime, result, trace = MockRuntime(), {"mode": "mock", "external_effects": 0}, []
        run_weather_mock(runtime, result, trace, **kwargs)
        return result, trace

    def test_default_route_calls_real_mock_adapter_and_produces_text_only(self):
        with patch("adapters.weather_e2e_mock.read_forecast", wraps=weather.read_forecast) as reader:
            # The default argument is bound at definition time, so inject the spy explicitly.
            result, trace = self.run_flow(forecast_reader=reader)
        self.assertEqual(reader.call_count, 1)
        self.assertEqual(reader.call_args.kwargs["mode"], "mock")
        self.assertEqual((result["status"], result["route"]["skill"]), ("completed", "friday-weather"))
        self.assertEqual(result["forecast"]["source"], "synthetic:fixtures/weather/adapter_forecast.json")
        self.assertEqual(result["forecast"]["valid_time"], "2026-10-15T14:00:00+00:00")
        self.assertIn("Synthetische Prognose", result["voice_answer_text"])
        self.assertEqual(result["voice_playback"], {"status": "NOT_RUN", "played": False})
        self.assertEqual([mapping["status"] for mapping in result["dashboard_mapping"]], ["working", "completed"])
        self.assertTrue(all(not row["publishable"] for row in result["dashboard_mapping"]))
        self.assertEqual(result["external_effects"], 0)
        self.assertIn("forecast_adapter_called", trace)

    def test_override_is_request_local_and_must_match_returned_grid(self):
        selected = {"name": "Wien Innenstadt", "latitude": 48.2082, "longitude": 16.3738}
        result, trace = self.run_flow(location_override=selected)
        self.assertEqual((result["status"], result["location"]["name"]), ("completed", "Wien Innenstadt"))
        self.assertIn("explicit_location", trace)
        self.assertEqual(load_fixture("weather", "e2e_context")["default_location"]["name"], "Wien")
        foreign, _ = self.run_flow(location_override={"name": "Graz", "latitude": 47.0707, "longitude": 15.4395})
        self.assertEqual((foreign["status"], foreign["reason"]), ("blocked", "weather_adapter_wrong_location"))
        self.assertNotIn("voice_answer_text", foreign)

    def test_missing_invalid_offline_and_misrouted_queries_have_no_answer(self):
        for variant in ("missing_location", "invalid_location", "adapter_offline", "capability_offline",
                        "weather_briefing", "morning_briefing"):
            with self.subTest(variant=variant):
                result = run_scenario("weather", variant=variant)
                self.assertEqual(result["status"], "blocked")
                self.assertNotIn("answer", result)
                self.assertNotIn("forecast", result)
                self.assertFalse(result["voice_playback"]["played"])
                self.assertEqual(result["external_effects"], 0)
        self.assertEqual(run_scenario("weather", variant="weather_briefing")["route"]["status"], "waiting")
        self.assertEqual(run_scenario("weather", variant="morning_briefing")["route"]["skill"],
                         "friday-morning-briefing")

    def test_stale_and_invalid_adapter_result_fail_without_claim(self):
        stale = run_scenario("weather", variant="stale")
        self.assertEqual((stale["status"], stale["reason"]), ("partial", "stale_weather"))
        self.assertNotIn("answer", stale)
        base = weather.read_forecast(48.2082, 16.3738, mode="mock", now=MockRuntime().now,
                                     at=weather._instant("2026-10-15T14:00:00Z"))
        for change in ({"status": "partial"}, {"source": "https://unknown.invalid/forecast"},
                       {"valid_time": "2026-10-16T14:00:00Z"}, {"temperature_c": None}):
            with self.subTest(change=change):
                result, _ = self.run_flow(forecast_reader=lambda *args, **kwargs: {**base, **change})
                self.assertEqual(result["status"], "blocked")
                self.assertNotIn("voice_answer_text", result)


if __name__ == "__main__":
    unittest.main()
