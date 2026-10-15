# Optional Hermes weather plugin

`plugins/friday_weather` is a standalone, opt-in plugin authored by RogueKI for F.R.I.D.A.Y. It registers one Hermes v0.20.5 tool, `friday_weather_forecast`. Installing this plugin is a separate operator action; this repository does not enable it in an active Hermes profile. It does not change the static `registry/capabilities.yaml` availability flags.

## Tool contract

Input: explicit EPSG:4326 `latitude` and `longitude`, optional `mode` (`mock`, `read_only`, `live`; default `mock`) and optional timezone-aware ISO `at`. The GeoSphere model covers the adapter's documented coordinate bounds and a 48-hour forecast window. There is no implicit location, place-name lookup or location storage. The mock uses a fixed dated synthetic fixture for deterministic examples. Its weather values are not current observations.

`read_only` and `live` both call the bounded public GET reader in `adapters/weather.py`; `live` does not enable writes. A successful call returns `status`, `mode`, `forecast`, `write_effect: false`, and per-call `capability` evidence containing `weather.read`, source, mode and the fresh `checked_at` timestamp. Because the public API needs no credentials, the record uses the narrowly allowlisted `public_read` policy path instead of claiming an authenticated session. The forecast itself includes provider/model, requested and grid coordinates, model reference time, valid time, retrieval time, units in value keys and attribution. On any validation, stale-source or transport error, the tool returns `status: blocked`, a structured `error`, and null `forecast` and `capability`. A partial forecast has a usable temperature plus warnings for missing secondary values. This tool cannot issue warnings, send notifications or publish dashboard events.

## Opt-in installation

Stage `adapters/` and `fixtures/weather/adapter_forecast.json` together in a separate support directory outside the Hermes profile, then place or link `plugins/friday_weather` in `<HERMES_HOME>/plugins/friday_weather/`. Set both `FRIDAY_SKILLS_ROOT` and `PYTHONPATH` to the support directory and start Hermes outside the repository checkout. The support directory must contain `adapters/weather.py` and the synthetic fixture, but should not contain this repository's top-level `plugins` package, which can shadow Hermes' own Python package. Keep the plugin folder intact with `plugin.yaml` and `__init__.py`, and explicitly enable `friday-weather` in that profile's `plugins.enabled` list. The registration function verifies that `adapters.weather` was imported from the configured support directory. Hermes source v0.20.5 declares `register_tool(name, toolset, schema, handler, ...)`; this plugin uses those four required arguments. No credentials are required for the public forecast endpoint. See `docs/WEATHER_ADAPTER.md` for the provider and network limits.

## Verification

`python -m unittest discover -s tests -p test_hermes_weather_plugin.py -v` uses a fake Hermes context and injected adapter transport. It verifies registration, labelled mock data, read-only/live forwarding, blocked validation and stale-source errors without network access or active-profile changes. Provider availability and future API compatibility are not established by these tests; the adapter has a separately recorded one-time live response in `docs/WEATHER_ADAPTER.md`.
