# GeoSphere weather read adapter

`adapters/weather.py` is an opt-in forecast reader for `friday-weather` and the `weather.read` capability. It does **not** register a Hermes tool, enable `weather.read` in the capability registry, send alerts, or write to another service. `mock` reads only the synthetic fixture; `read_only` and `live` make the same public HTTPS GET. The mode named `live` grants no mutation path.

## Provider contract

GeoSphere Austria documents the Dataset API [endpoint structure and metadata](https://dataset.api.hub.geosphere.at/v1/docs/user-guide/endpoints.html), the [timeseries `lat_lon` coordinate parameter](https://dataset.api.hub.geosphere.at/v1/docs/user-guide/type.html), and the [forecast reference time, latest run, and forecast offset](https://dataset.api.hub.geosphere.at/v1/docs/user-guide/mode.html). The selected resource is [`nwp-v2-1h-1km`](https://dataset.api.hub.geosphere.at/v1/docs/user-guide/resource.html), queried at `https://dataset.api.hub.geosphere.at/v1/timeseries/forecast/nwp-v2-1h-1km` with `parameters=2t,tp,10u,10v`, `lat_lon=<latitude>,<longitude>`, and `output_format=geojson`. Its [live metadata](https://dataset.api.hub.geosphere.at/v1/timeseries/forecast/nwp-v2-1h-1km/metadata) defines the parameter names and units: `2t` in degrees Celsius, `tp` in `kg m-2` per forecast interval, `10u` and `10v` in `m s-1`. Wind speed is the magnitude of the two components. This is a **model forecast**, not a station observation or official warning.

The [API documentation](https://dataset.api.hub.geosphere.at/v1/docs/) licenses public unauthenticated data under CC BY 4.0. Attribute GeoSphere Austria when showing its values. [Forecast endpoints are prerelease](https://dataset.api.hub.geosphere.at/v1/docs/user-guide/mode.html); changed response contracts should fail validation until updated deliberately.

## Use

```python
from adapters.weather import read_forecast

forecast = read_forecast(48.2082, 16.3738, mode="read_only")
```

Pass explicit EPSG:4326 latitude and longitude. This adapter does not geocode place names or assume a user's location. It accepts the provider model bounding box, uses one nearest grid cell, and reports both requested and returned coordinates. `at` selects a forecast hour from now through 48 hours; pass timezone-aware `datetime` values. The result includes reference, valid, and retrieval times, URL, units encoded in field names, provider, license, and `completed` or `partial`. Secondary missing rain or wind returns `partial`; missing temperature, stale model run, mismatched grid location, malformed data, timeout, and missing requested hour raise `WeatherAdapterError(code, detail)`. Callers should convert errors to a blocked result without inventing weather.

The URL and host are fixed. The HTTP client uses GET, rejects redirects, allows JSON only, caps the response at 1 MB and timeout at 15 seconds. No credentials are stored or sent. Automated tests inject a transport and never make network calls.

## Verification and limits

On 2026-10-15 at 14:06 UTC, one read-only adapter call for Vienna (`48.2082, 16.3738`) returned `completed` from the 09:00 UTC model run, valid at 15:00 UTC, with 16.6 °C, 0 `kg m-2` precipitation and 1.7 `m s-1` wind. This verifies one real response at one time; it does not prove future uptime, other coordinates, or integration with Hermes. Forecast freshness uses a 12-hour run-age ceiling. The adapter does not obtain warnings; `friday-weather-alerts` still requires a separate warning source. No `weather.read` registry availability flag is changed by this standalone module.
