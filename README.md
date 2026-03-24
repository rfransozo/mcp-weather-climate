# mcp-weather-climate

Global weather, climate, air quality and marine MCP server — powered by
[Open-Meteo](https://open-meteo.com/) (free, open-source, no API key required).

## Tools

| Tool | Description |
|---|---|
| `geocode_location` | Search lat/lon for any city or place name |
| `current_weather` | Real-time conditions (temp, wind, UV, humidity…) |
| `hourly_forecast` | Hourly forecast up to 16 days ahead |
| `daily_forecast` | Daily forecast up to 16 days (min/max/precip/wind) |
| `historical_weather` | Daily weather archive going back to 1940 |
| `climate_normals` | 1991–2020 monthly climate averages (CMIP6) |
| `air_quality` | PM2.5, PM10, NO₂, SO₂, ozone, EU/US AQI |
| `marine_forecast` | Wave height/period/direction, swell, ocean currents |

## Deploying on MCPize

```bash
cd mcp-weather-climate
mcpize deploy
```

## Local Development

```bash
python -m venv .venv
.venv\Scripts\activate          # Windows
pip install -r requirements.txt
python src/server.py            # stdio mode
```

## Data Sources

- **Open-Meteo Forecast API** — `https://api.open-meteo.com`
- **Open-Meteo Archive API** — `https://archive-api.open-meteo.com`
- **Open-Meteo Climate API** — `https://climate-api.open-meteo.com`
- **Open-Meteo Air Quality API** — `https://air-quality-api.open-meteo.com`
- **Open-Meteo Marine API** — `https://marine-api.open-meteo.com`
- **Open-Meteo Geocoding API** — `https://geocoding-api.open-meteo.com`

All APIs are free, open-source and do not require authentication.
