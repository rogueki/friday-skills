# Weather E2E4 local mock

`run_scenario("weather")` routes a stand-alone weather question to `friday-weather`, loads the explicitly configured synthetic Vienna location from `fixtures/weather/e2e_context.json`, checks a synthetic `weather.read` capability, and calls the actual `adapters.weather.read_forecast(mode="mock")` function. The adapter reads the local forecast fixture. The flow validates requested coordinates, exact synthetic source, model reference age (at most 12 hours), retrieval timestamp and forecast valid hour before producing a brief German text answer.

`run_weather_mock(..., location_override=...)` supports a request-local explicit location without changing the default. The mock fixture represents one Vienna grid point; another city's coordinates fail rather than receiving Vienna's forecast. A live location needs a verified geocoding/source workflow outside this mock.

`variant="stale"` injects an old reference timestamp into the adapter's already parsed synthetic response to exercise the freshness gate. Missing/invalid location, offline capability or adapter, incomplete/invalid adapter response, and weather-plus-briefing or morning-briefing requests yield no weather claim. The fixture describes a **forecast** for 14:00 UTC, never a current observation.

The result contains `voice_answer_text` only after successful validation. `voice_playback` is always `NOT_RUN` with `played=false`. Activity records and `dashboard_mapping` are local, `publishable=false`; `external_effects=0`. No voice hardware, actual Dashboard publisher, GeoSphere network request or Hermes model choice is tested here. `tests/test_weather_e2e_mock.py` exercises the positive and negative contracts.

[GitHub Actions run 38772145653](https://github.com/rogueki/friday-skills/actions/runs/38772145653) passed Windows and Ubuntu. It verifies the offline mock composition, not a weather-provider or audio session.
