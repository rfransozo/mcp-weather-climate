# mcp-weather-climate

[![MCPize](https://img.shields.io/badge/MCPize-Premium-blue)](https://mcpize.com/mcp/mcp-weather-climate)
[![Python](https://img.shields.io/badge/Python-3.11+-green)](https://python.org)
[![FastMCP](https://img.shields.io/badge/FastMCP-3.x-orange)](https://fastmcp.com)

Global weather & climate data directly from your AI assistant — real-time conditions,
16-day forecasts, historical records back to 1940, climate normals, air quality, and
marine/wave forecasts. Powered by [Open-Meteo](https://open-meteo.com/) — no API key required.

## What you can do

- **`geocode_location`** — Convert any city or place name into geographic coordinates (lat/lon), timezone, elevation, and population. Supports 10+ languages.

- **`current_weather`** — Real-time weather conditions: temperature, apparent temperature, humidity, precipitation, wind speed & direction, gusts, UV index, cloud cover, surface pressure, visibility, and WMO weather description.

- **`hourly_forecast`** — Detailed hour-by-hour forecast for the next 1–16 days, including precipitation probability, snowfall, UV index, and visibility.

- **`daily_forecast`** — Day-by-day forecast with min/max temperatures, precipitation totals, max wind/gusts, UV index, sunrise/sunset, and daylight duration — up to 16 days.

- **`historical_weather`** — Access daily weather records going back to January 1, 1940 for any location. Ideal for climate research, insurance, agriculture, and retrospective analysis.

- **`climate_normals`** — Long-term monthly averages based on 1991–2020 CMIP6 climate data: mean/min/max temperature, precipitation, wind, and solar radiation. Perfect for travel planning or infrastructure design.

- **`air_quality`** — Hourly air quality forecast up to 7 days: PM2.5, PM10, carbon monoxide, nitrogen dioxide, sulphur dioxide, ozone, aerosol optical depth, dust, UV index, and European & US AQI.

- **`marine_forecast`** — Hourly ocean and wave data for coastal or offshore locations: wave height, wave period, wave direction, swell, wind waves, and ocean current velocity — up to 7 days.

## Tools

| Tool | Description |
|---|---|
| `geocode_location` | Place name → lat/lon, timezone, elevation, population |
| `current_weather` | Real-time conditions (temp, wind, UV, humidity, visibility…) |
| `hourly_forecast` | Hourly forecast up to 16 days |
| `daily_forecast` | Daily forecast with min/max, precip, wind — up to 16 days |
| `historical_weather` | Daily weather archive going back to 1940 |
| `climate_normals` | 1991–2020 monthly climate averages (CMIP6) |
| `air_quality` | PM2.5, PM10, NO₂, SO₂, ozone, EU/US AQI — up to 7 days |
| `marine_forecast` | Wave height/period/direction, swell, ocean currents — up to 7 days |

## Why use this server?

- **Zero setup** — No API keys, no accounts, no rate-limit worries for reasonable use
- **Global coverage** — Works for any latitude/longitude on Earth
- **Historical depth** — 80+ years of historical records since 1940
- **Climate intelligence** — 30-year CMIP6 normals for long-term planning
- **Multi-domain** — Standard weather + air quality + marine in a single server

## Data Sources

- **Open-Meteo Forecast API** — `https://api.open-meteo.com`
- **Open-Meteo Archive API** — `https://archive-api.open-meteo.com`
- **Open-Meteo Climate API** — `https://climate-api.open-meteo.com`
- **Open-Meteo Air Quality API** — `https://air-quality-api.open-meteo.com`
- **Open-Meteo Marine API** — `https://marine-api.open-meteo.com`
- **Open-Meteo Geocoding API** — `https://geocoding-api.open-meteo.com`

All APIs are free, open-source, and do not require authentication.

## Ideal for

✔ Travel apps and AI trip planners  
✔ Agricultural and logistics decision support  
✔ Real estate and infrastructure analysis  
✔ Academic and environmental research  
✔ Embedding climate context into LLM workflows

## Use on MCPize

**[https://mcpize.com/mcp/mcp-weather-climate](https://mcpize.com/mcp/mcp-weather-climate)**

```bash
mcpize connect @rfransozo/mcp-weather-climate --client claude
```

## Local Development

```bash
git clone https://github.com/rfransozo/mcp-weather-climate.git
cd mcp-weather-climate
python -m venv .venv
.venv\Scripts\activate          # Windows
pip install -r requirements.txt
python src/server.py            # stdio mode
```

## Deploying on MCPize

```bash
mcpize deploy
mcpize publish
```

