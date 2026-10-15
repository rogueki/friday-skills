"""Hermes weather plugin contracts without network or active-profile changes."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
import json
import os
from pathlib import Path
import unittest
from unittest.mock import patch

from adapters import weather
from plugins.friday_weather import SCHEMA, TOOL_NAME, register
from shared.policy import capability_available


ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / "fixtures" / "weather" / "adapter_forecast.json"
NOW = datetime(2026, 10, 15, 14, 0, tzinfo=timezone.utc)


class Context:
    def __init__(self):
        self.tools = {}

    def register_tool(self, *, name, toolset, schema, handler):
        self.tools[name] = (toolset, schema, handler)


class HermesWeatherPluginTests(unittest.TestCase):
    def setUp(self):
        self.ctx = Context()
        self.root_env = patch.dict(os.environ, {"FRIDAY_SKILLS_ROOT": str(ROOT)})
        self.root_env.start()
        self.addCleanup(self.root_env.stop)
        register(self.ctx)

    def call(self, **params):
        return json.loads(self.ctx.tools[TOOL_NAME][2](params))

    def test_registers_exact_manifest_and_schema(self):
        manifest = (ROOT / "plugins" / "friday_weather" / "plugin.yaml").read_text(encoding="utf-8")
        self.assertIn("  - friday_weather_forecast\n", manifest)
        self.assertEqual(set(self.ctx.tools), {TOOL_NAME})
        self.assertEqual(self.ctx.tools[TOOL_NAME][:2], ("friday_weather", SCHEMA))
        self.assertEqual(SCHEMA["parameters"]["required"], ["latitude", "longitude"])

    def test_registration_requires_matching_support_root(self):
        with patch.dict(os.environ, {"FRIDAY_SKILLS_ROOT": ""}):
            with self.assertRaises(RuntimeError):
                register(Context())
        with patch.dict(os.environ, {"FRIDAY_SKILLS_ROOT": str(ROOT / "fixtures")}):
            with self.assertRaises(RuntimeError):
                register(Context())

    def test_mock_is_labelled_and_only_grants_call_evidence_after_success(self):
        result = self.call(latitude=48.2082, longitude=16.3738)
        self.assertEqual(result["status"], "completed")
        self.assertEqual(result["mode"], "mock")
        self.assertEqual(result["forecast"]["temperature_c"], 16.6)
        self.assertTrue(result["capability"]["synthetic"])
        self.assertEqual(result["capability"]["name"], "weather.read")
        self.assertEqual(result["capability"]["source"], result["forecast"]["source"])
        self.assertFalse(result["write_effect"])

    def test_read_only_and_live_pass_through_adapter_without_network(self):
        with patch.object(weather, "read_forecast", return_value={
            "status": "completed", "source": weather.ENDPOINT + "?parameters=2t",
            "provider": "GeoSphere Austria", "retrieved_at": NOW.isoformat(),
        }) as reader:
            for mode in ("read_only", "live"):
                result = self.call(latitude=48.2082, longitude=16.3738, mode=mode,
                                   at="2026-10-15T15:00:00+00:00")
                self.assertEqual(result["status"], "completed")
                self.assertFalse(result["capability"]["synthetic"])
                self.assertEqual(result["capability"]["mode"], mode)
                self.assertFalse(result["capability"]["authenticated"])
                self.assertTrue(capability_available(result["capability"], permission="read", mode=mode))
                self.assertEqual(reader.call_args.kwargs["mode"], mode)
                self.assertEqual(reader.call_args.kwargs["at"], NOW + timedelta(hours=1))
            self.assertEqual(reader.call_count, 2)

    def test_injected_live_transport_at_adapter_boundary(self):
        payload = json.loads(FIXTURE.read_text(encoding="utf-8"))
        original = weather.read_forecast

        def injected(*args, **kwargs):
            return original(*args, **kwargs, now=NOW, transport=lambda *_: payload)

        with patch.object(weather, "read_forecast", side_effect=injected):
            result = self.call(latitude=48.2082, longitude=16.3738, mode="read_only")
        self.assertEqual(result["status"], "completed")
        self.assertEqual(result["forecast"]["provider"], "GeoSphere Austria")
        self.assertIn("lat_lon=48.20820%2C16.37380", result["capability"]["source"])

    def test_validation_and_stale_source_block_without_capability(self):
        for params, code in (
            ({"latitude": 0, "longitude": 0}, "invalid_location"),
            ({"latitude": 48.2}, "invalid_location"),
            ({"latitude": 48.2, "longitude": 16.3, "mode": "write"}, "invalid_mode"),
            ({"latitude": 48.2, "longitude": 16.3, "at": "2026-10-15"}, "invalid_time"),
            ({"latitude": 48.2, "longitude": 16.3, "extra": 1}, "invalid_request"),
        ):
            with self.subTest(params=params):
                result = self.call(**params)
                self.assertEqual(result["status"], "blocked")
                self.assertEqual(result["error"]["code"], code)
                self.assertIsNone(result["capability"])
                self.assertIsNone(result["forecast"])

        with patch.object(weather, "read_forecast", side_effect=weather.WeatherAdapterError(
            "stale_forecast", "model reference time is stale")):
            result = self.call(latitude=48.2082, longitude=16.3738, mode="live")
        self.assertEqual(result["error"]["code"], "stale_forecast")
        self.assertIsNone(result["capability"])


if __name__ == "__main__":
    unittest.main()
