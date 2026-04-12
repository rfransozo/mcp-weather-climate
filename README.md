# mcp-weather-climate

[![MCPize](https://img.shields.io/badge/MCPize-Premium-blue)](https://mcpize.com/mcp/mcp-weather-climate)
[![Python](https://img.shields.io/badge/Python-3.11+-green)](https://python.org)
[![FastMCP](https://img.shields.io/badge/FastMCP-3.x-orange)](https://fastmcp.com)

13 tools giving AI assistants instant access to global weather, climate, and environmental
data — real-time conditions, 16-day forecasts, historical records back to 1940, air quality,
marine forecasts, pollen, flood risk, solar radiation, severe weather outlook, and agricultural
soil data. Powered by [Open-Meteo](https://open-meteo.com/) — no API key required.

## What you can do

- **`geocode_location`** — Convert any city or place name into geographic coordinates (lat/lon), timezone, elevation, and population. Supports 10+ languages.

- **`current_weather`** — Real-time weather conditions: temperature, apparent temperature, humidity, precipitation, wind speed & direction, gusts, UV index, cloud cover, surface pressure, visibility, and WMO weather description.

- **`hourly_forecast`** — Detailed hour-by-hour forecast for the next 1–16 days, including precipitation probability, snowfall, UV index, and visibility.

- **`daily_forecast`** — Day-by-day forecast with min/max temperatures, precipitation totals, max wind/gusts, UV index, sunrise/sunset, and daylight duration — up to 16 days.

- **`historical_weather`** — Access daily weather records going back to January 1, 1940 for any location. Ideal for climate research, insurance, agriculture, and retrospective analysis.

- **`climate_normals`** — Long-term monthly averages based on 1991–2020 CMIP6 climate data: mean/min/max temperature, precipitation, wind, and solar radiation. Perfect for travel planning or infrastructure design.

- **`air_quality`** — Hourly air quality forecast up to 7 days: PM2.5, PM10, carbon monoxide, nitrogen dioxide, sulphur dioxide, ozone, aerosol optical depth, dust, UV index, and European & US AQI.

- **`marine_forecast`** — Hourly ocean and wave data for coastal or offshore locations: wave height, wave period, wave direction, swell, wind waves, and ocean current velocity — up to 7 days.

- **`pollen_forecast`** *(Europe)* — Daily pollen levels (low/moderate/high/very high) for alder, birch, grass, mugwort, olive, and ragweed — powered by CAMS European Air Quality forecast.

- **`flood_risk`** — Daily river discharge forecasts via GloFAS v4 with up to 7 months of outlook and reanalysis from 1984. Returns peak discharge and risk level (normal/elevated/high/extreme).

- **`solar_radiation_forecast`** — Hourly GHI, DNI, DHI, sunshine duration, and UV index. Optional tilted-panel irradiance (GTI) for solar energy planning.

- **`severe_weather_outlook`** — Daily risk score (low/moderate/high/extreme) computed from CAPE, wind gusts, lightning potential, and precipitation probability.

- **`agricultural_conditions`** — Soil temperature and moisture at 4 depths, ET₀ FAO-56 reference evapotranspiration, and vapour pressure deficit for irrigation and crop management.

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
| `pollen_forecast` | Daily pollen levels by species (Europe, CAMS) |
| `flood_risk` | River discharge forecast and risk level via GloFAS v4 |
| `solar_radiation_forecast` | GHI, DNI, DHI, GTI panel irradiance, UV index |
| `severe_weather_outlook` | CAPE-based daily severe weather risk score |
| `agricultural_conditions` | Soil temp/moisture (4 depths), ET₀, vapour pressure deficit |

## Why use this server?

- **Zero setup** — No API keys, no accounts, no rate-limit worries for reasonable use
- **Global coverage** — Works for any latitude/longitude on Earth
- **Unique data** — Flood risk (GloFAS), CAPE-based severe outlook, and pollen — not available in any other MCP weather server
- **Historical depth** — 80+ years of daily records since 1940
- **Climate intelligence** — 30-year CMIP6 normals for long-term planning
- **Multi-domain** — Standard weather + air quality + marine + agriculture + solar energy in a single server

## Data Sources

- **Open-Meteo Forecast API** — `https://api.open-meteo.com`
- **Open-Meteo Archive API** — `https://archive-api.open-meteo.com`
- **Open-Meteo Climate API** — `https://climate-api.open-meteo.com`
- **Open-Meteo Air Quality API** — `https://air-quality-api.open-meteo.com`
- **Open-Meteo Marine API** — `https://marine-api.open-meteo.com`
- **Open-Meteo Geocoding API** — `https://geocoding-api.open-meteo.com`

All Open-Meteo APIs are free, open-source, and do not require authentication.

- **CAMS European Air Quality Forecast** — `https://air-quality-api.open-meteo.com` (pollen)
- **GloFAS v4 (Copernicus)** — via `https://flood-api.open-meteo.com` (river discharge & flood risk)

## Ideal for

✔ Travel apps and AI trip planners  
✔ Agricultural platforms and irrigation decision tools  
✔ Solar and renewable energy planning  
✔ Allergy and health apps (European pollen season)  
✔ Flood risk assessment and river logistics management  
✔ Severe weather alert systems and insurance underwriting  
✔ Academic climate research and environmental dashboards

## Use on MCPize

**[https://mcpize.com/mcp/mcp-weather-climate](https://mcpize.com/mcp/mcp-weather-climate)**

```bash
mcpize connect @rfransozo/mcp-weather-climate --client claude
```


