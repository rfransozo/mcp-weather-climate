"""
mcp-weather-climate — MCPize Server
Global weather, forecasts, historical climate, air quality and marine data
via Open-Meteo — 100% free, no API key required.
"""

import os
import sys
import logging
from typing import Literal

import httpx
from fastmcp import FastMCP
from dotenv import load_dotenv

load_dotenv()

# -----------------------------------------------------------------
# Logging — NUNCA escrever no stdout (quebra JSON-RPC via stdio)
# -----------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    stream=sys.stderr,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
log = logging.getLogger("mcp-weather-climate")

# -----------------------------------------------------------------
# Base URLs — Open-Meteo (free, no auth)
# -----------------------------------------------------------------
FORECAST_URL   = "https://api.open-meteo.com/v1/forecast"
ARCHIVE_URL    = "https://archive-api.open-meteo.com/v1/archive"
CLIMATE_URL    = "https://climate-api.open-meteo.com/v1/climate"
AIR_URL        = "https://air-quality-api.open-meteo.com/v1/air-quality"
MARINE_URL     = "https://marine-api.open-meteo.com/v1/marine"
GEOCODING_URL  = "https://geocoding-api.open-meteo.com/v1/search"

# -----------------------------------------------------------------
# MCP Server
# ⚠️  FastMCP 3.x: construtor aceita APENAS o nome
# -----------------------------------------------------------------
mcp = FastMCP("mcp-weather-climate")

# -----------------------------------------------------------------
# HTTP helper
# -----------------------------------------------------------------
async def _get(url: str, params: dict) -> dict:
    async with httpx.AsyncClient(timeout=20) as client:
        resp = await client.get(url, params=params)
        resp.raise_for_status()
        return resp.json()


# =================================================================
# Tool 1 — geocode_location
# =================================================================
@mcp.tool()
async def geocode_location(
    name: str,
    count: int = 5,
    language: str = "en",
) -> dict:
    """
    Search for geographic coordinates by place name (city, country, etc.).
    Returns up to `count` matching locations with latitude, longitude, country,
    timezone, and elevation.

    Args:
        name: Place name to search (e.g. "London", "São Paulo", "Tokyo").
        count: Maximum number of results (1–10, default 5).
        language: Language for result names — 'en', 'pt', 'es', 'de', 'fr', etc.
    """
    count = max(1, min(count, 10))
    data = await _get(GEOCODING_URL, {"name": name, "count": count, "language": language, "format": "json"})
    results = data.get("results", [])
    if not results:
        return {"error": f"No location found for '{name}'"}
    return {
        "query": name,
        "results": [
            {
                "name": r.get("name"),
                "country": r.get("country"),
                "country_code": r.get("country_code"),
                "admin1": r.get("admin1"),
                "latitude": r.get("latitude"),
                "longitude": r.get("longitude"),
                "elevation_m": r.get("elevation"),
                "timezone": r.get("timezone"),
                "population": r.get("population"),
            }
            for r in results
        ],
    }


# =================================================================
# Tool 2 — current_weather
# =================================================================
@mcp.tool()
async def current_weather(
    latitude: float,
    longitude: float,
    temperature_unit: Literal["celsius", "fahrenheit"] = "celsius",
    wind_speed_unit: Literal["kmh", "mph", "ms", "kn"] = "kmh",
) -> dict:
    """
    Get real-time current weather conditions for any location.
    Returns temperature, apparent temperature, humidity, precipitation,
    wind speed/direction, UV index, cloud cover, and weather condition code.

    Args:
        latitude: Decimal latitude (-90 to 90).
        longitude: Decimal longitude (-180 to 180).
        temperature_unit: 'celsius' (default) or 'fahrenheit'.
        wind_speed_unit: 'kmh' (default), 'mph', 'ms', or 'kn'.
    """
    current_vars = ",".join([
        "temperature_2m",
        "apparent_temperature",
        "relative_humidity_2m",
        "precipitation",
        "weather_code",
        "cloud_cover",
        "wind_speed_10m",
        "wind_direction_10m",
        "wind_gusts_10m",
        "uv_index",
        "surface_pressure",
        "visibility",
        "is_day",
    ])
    params = {
        "latitude": latitude,
        "longitude": longitude,
        "current": current_vars,
        "temperature_unit": temperature_unit,
        "wind_speed_unit": wind_speed_unit,
        "timezone": "auto",
    }
    data = await _get(FORECAST_URL, params)
    cur  = data.get("current", {})
    units = data.get("current_units", {})
    return {
        "location": {"latitude": latitude, "longitude": longitude},
        "timezone": data.get("timezone"),
        "time": cur.get("time"),
        "current": {k: {"value": cur.get(k), "unit": units.get(k)} for k in cur if k != "time"},
        "weather_description": _wmo_description(cur.get("weather_code")),
    }


# =================================================================
# Tool 3 — hourly_forecast
# =================================================================
@mcp.tool()
async def hourly_forecast(
    latitude: float,
    longitude: float,
    days: int = 3,
    temperature_unit: Literal["celsius", "fahrenheit"] = "celsius",
    wind_speed_unit: Literal["kmh", "mph", "ms", "kn"] = "kmh",
) -> dict:
    """
    Get hourly weather forecast for the next 1–16 days.
    Includes temperature, precipitation probability, precipitation, wind speed,
    humidity, cloud cover, UV index, visibility, and weather code per hour.

    Args:
        latitude: Decimal latitude.
        longitude: Decimal longitude.
        days: Forecast horizon in days (1–16, default 3).
        temperature_unit: 'celsius' or 'fahrenheit'.
        wind_speed_unit: 'kmh', 'mph', 'ms', or 'kn'.
    """
    days = max(1, min(days, 16))
    hourly_vars = ",".join([
        "temperature_2m",
        "apparent_temperature",
        "precipitation_probability",
        "precipitation",
        "weather_code",
        "cloud_cover",
        "wind_speed_10m",
        "wind_direction_10m",
        "relative_humidity_2m",
        "uv_index",
        "visibility",
        "snowfall",
        "snow_depth",
    ])
    params = {
        "latitude": latitude,
        "longitude": longitude,
        "hourly": hourly_vars,
        "forecast_days": days,
        "temperature_unit": temperature_unit,
        "wind_speed_unit": wind_speed_unit,
        "timezone": "auto",
    }
    data = await _get(FORECAST_URL, params)
    hourly = data.get("hourly", {})
    units  = data.get("hourly_units", {})
    times  = hourly.get("time", [])

    rows = []
    for i, t in enumerate(times):
        row = {"time": t}
        for k, vals in hourly.items():
            if k == "time":
                continue
            row[k] = {"value": vals[i] if i < len(vals) else None, "unit": units.get(k)}
        rows.append(row)

    return {
        "location": {"latitude": latitude, "longitude": longitude},
        "timezone": data.get("timezone"),
        "forecast_days": days,
        "hours": rows,
    }


# =================================================================
# Tool 4 — daily_forecast
# =================================================================
@mcp.tool()
async def daily_forecast(
    latitude: float,
    longitude: float,
    days: int = 7,
    temperature_unit: Literal["celsius", "fahrenheit"] = "celsius",
    wind_speed_unit: Literal["kmh", "mph", "ms", "kn"] = "kmh",
) -> dict:
    """
    Get daily weather forecast for the next 1–16 days.
    Returns min/max temperature, precipitation sum, max wind speed,
    UV index max, sunrise/sunset, and dominant weather code per day.

    Args:
        latitude: Decimal latitude.
        longitude: Decimal longitude.
        days: Number of days to forecast (1–16, default 7).
        temperature_unit: 'celsius' or 'fahrenheit'.
        wind_speed_unit: 'kmh', 'mph', 'ms', or 'kn'.
    """
    days = max(1, min(days, 16))
    daily_vars = ",".join([
        "weather_code",
        "temperature_2m_max",
        "temperature_2m_min",
        "apparent_temperature_max",
        "apparent_temperature_min",
        "sunrise",
        "sunset",
        "daylight_duration",
        "uv_index_max",
        "precipitation_sum",
        "precipitation_probability_max",
        "wind_speed_10m_max",
        "wind_gusts_10m_max",
        "wind_direction_10m_dominant",
        "snowfall_sum",
        "rain_sum",
        "showers_sum",
    ])
    params = {
        "latitude": latitude,
        "longitude": longitude,
        "daily": daily_vars,
        "forecast_days": days,
        "temperature_unit": temperature_unit,
        "wind_speed_unit": wind_speed_unit,
        "timezone": "auto",
    }
    data  = await _get(FORECAST_URL, params)
    daily = data.get("daily", {})
    units = data.get("daily_units", {})
    dates = daily.get("time", [])

    rows = []
    for i, d in enumerate(dates):
        row = {"date": d}
        for k, vals in daily.items():
            if k == "time":
                continue
            row[k] = {"value": vals[i] if i < len(vals) else None, "unit": units.get(k)}
        if "weather_code" in daily:
            row["description"] = _wmo_description(daily["weather_code"][i])
        rows.append(row)

    return {
        "location": {"latitude": latitude, "longitude": longitude},
        "timezone": data.get("timezone"),
        "forecast_days": days,
        "days": rows,
    }


# =================================================================
# Tool 5 — historical_weather
# =================================================================
@mcp.tool()
async def historical_weather(
    latitude: float,
    longitude: float,
    start_date: str,
    end_date: str,
    temperature_unit: Literal["celsius", "fahrenheit"] = "celsius",
    wind_speed_unit: Literal["kmh", "mph", "ms", "kn"] = "kmh",
) -> dict:
    """
    Retrieve historical daily weather data going back to 1940.
    Returns temperature (min/max/mean), precipitation, wind, and weather codes
    for each day in the requested period.

    Args:
        latitude: Decimal latitude.
        longitude: Decimal longitude.
        start_date: Start date in YYYY-MM-DD format (earliest: 1940-01-01).
        end_date: End date in YYYY-MM-DD format.
        temperature_unit: 'celsius' or 'fahrenheit'.
        wind_speed_unit: 'kmh', 'mph', 'ms', or 'kn'.
    """
    daily_vars = ",".join([
        "weather_code",
        "temperature_2m_max",
        "temperature_2m_min",
        "temperature_2m_mean",
        "apparent_temperature_max",
        "apparent_temperature_min",
        "apparent_temperature_mean",
        "sunrise",
        "sunset",
        "daylight_duration",
        "precipitation_sum",
        "rain_sum",
        "snowfall_sum",
        "wind_speed_10m_max",
        "wind_gusts_10m_max",
        "wind_direction_10m_dominant",
    ])
    params = {
        "latitude": latitude,
        "longitude": longitude,
        "start_date": start_date,
        "end_date": end_date,
        "daily": daily_vars,
        "temperature_unit": temperature_unit,
        "wind_speed_unit": wind_speed_unit,
        "timezone": "auto",
    }
    data  = await _get(ARCHIVE_URL, params)
    daily = data.get("daily", {})
    units = data.get("daily_units", {})
    dates = daily.get("time", [])

    rows = []
    for i, d in enumerate(dates):
        row = {"date": d}
        for k, vals in daily.items():
            if k == "time":
                continue
            row[k] = {"value": vals[i] if i < len(vals) else None, "unit": units.get(k)}
        if "weather_code" in daily:
            row["description"] = _wmo_description(daily["weather_code"][i])
        rows.append(row)

    return {
        "location": {"latitude": latitude, "longitude": longitude},
        "period": {"start": start_date, "end": end_date},
        "days_returned": len(rows),
        "days": rows,
    }


# =================================================================
# Tool 6 — climate_normals
# =================================================================
@mcp.tool()
async def climate_normals(
    latitude: float,
    longitude: float,
    temperature_unit: Literal["celsius", "fahrenheit"] = "celsius",
    wind_speed_unit: Literal["kmh", "mph", "ms", "kn"] = "kmh",
) -> dict:
    """
    Get long-term climate normals (1991–2020 CMIP6 averages) for any location.
    Returns monthly averages of temperature, precipitation, wind, and sunshine
    — ideal for understanding typical climate patterns of a place.

    Args:
        latitude: Decimal latitude.
        longitude: Decimal longitude.
        temperature_unit: 'celsius' or 'fahrenheit'.
        wind_speed_unit: 'kmh', 'mph', 'ms', or 'kn'.
    """
    daily_vars = ",".join([
        "temperature_2m_max",
        "temperature_2m_min",
        "temperature_2m_mean",
        "precipitation_sum",
        "wind_speed_10m_mean",
        "shortwave_radiation_sum",
    ])
    params = {
        "latitude": latitude,
        "longitude": longitude,
        "start_date": "1991-01-01",
        "end_date": "2020-12-31",
        "daily": daily_vars,
        "temperature_unit": temperature_unit,
        "wind_speed_unit": wind_speed_unit,
        "models": "CMIP6",
    }
    data  = await _get(CLIMATE_URL, params)
    daily = data.get("daily", {})
    units = data.get("daily_units", {})
    dates = daily.get("time", [])

    # Aggregate into monthly averages
    monthly: dict[str, dict] = {}
    for i, d in enumerate(dates):
        month_key = d[:7]  # YYYY-MM
        if month_key not in monthly:
            monthly[month_key] = {k: [] for k in daily if k != "time"}
        for k in daily:
            if k == "time":
                continue
            val = daily[k][i]
            if val is not None:
                monthly[month_key][k].append(val)

    month_summaries = []
    for month_key in sorted(monthly.keys()):
        row = {"month": month_key}
        for k, vals in monthly[month_key].items():
            if vals:
                row[k] = {"avg": round(sum(vals) / len(vals), 2), "unit": units.get(k)}
        month_summaries.append(row)

    return {
        "location": {"latitude": latitude, "longitude": longitude},
        "period": "1991–2020 (CMIP6 climate normals)",
        "months": month_summaries,
    }


# =================================================================
# Tool 7 — air_quality
# =================================================================
@mcp.tool()
async def air_quality(
    latitude: float,
    longitude: float,
    forecast_days: int = 1,
) -> dict:
    """
    Get current and forecast air quality data including PM2.5, PM10, CO, NO2,
    SO2, ozone, European and US AQI, and dust concentration.

    Args:
        latitude: Decimal latitude.
        longitude: Decimal longitude.
        forecast_days: Number of days of hourly forecast (1–7, default 1).
    """
    forecast_days = max(1, min(forecast_days, 7))
    hourly_vars = ",".join([
        "pm10",
        "pm2_5",
        "carbon_monoxide",
        "nitrogen_dioxide",
        "sulphur_dioxide",
        "ozone",
        "aerosol_optical_depth",
        "dust",
        "uv_index",
        "european_aqi",
        "us_aqi",
    ])
    params = {
        "latitude": latitude,
        "longitude": longitude,
        "hourly": hourly_vars,
        "forecast_days": forecast_days,
        "timezone": "auto",
    }
    data   = await _get(AIR_URL, params)
    hourly = data.get("hourly", {})
    units  = data.get("hourly_units", {})
    times  = hourly.get("time", [])

    rows = []
    for i, t in enumerate(times):
        row = {"time": t}
        for k, vals in hourly.items():
            if k == "time":
                continue
            row[k] = {"value": vals[i] if i < len(vals) else None, "unit": units.get(k)}
        rows.append(row)

    return {
        "location": {"latitude": latitude, "longitude": longitude},
        "timezone": data.get("timezone"),
        "forecast_days": forecast_days,
        "hours": rows,
    }


# =================================================================
# Tool 8 — marine_forecast
# =================================================================
@mcp.tool()
async def marine_forecast(
    latitude: float,
    longitude: float,
    days: int = 5,
) -> dict:
    """
    Get hourly marine/ocean forecast including wave height, wave direction,
    wave period, swell height, swell direction, wind wave height, and
    sea surface temperature.  Best for coastal and open-ocean locations.

    Args:
        latitude: Decimal latitude (must be over ocean/sea).
        longitude: Decimal longitude.
        days: Number of forecast days (1–7, default 5).
    """
    days = max(1, min(days, 7))
    hourly_vars = ",".join([
        "wave_height",
        "wave_direction",
        "wave_period",
        "wind_wave_height",
        "wind_wave_direction",
        "wind_wave_period",
        "swell_wave_height",
        "swell_wave_direction",
        "swell_wave_period",
        "ocean_current_velocity",
        "ocean_current_direction",
    ])
    params = {
        "latitude": latitude,
        "longitude": longitude,
        "hourly": hourly_vars,
        "forecast_days": days,
        "timezone": "auto",
    }
    data   = await _get(MARINE_URL, params)
    hourly = data.get("hourly", {})
    units  = data.get("hourly_units", {})
    times  = hourly.get("time", [])

    rows = []
    for i, t in enumerate(times):
        row = {"time": t}
        for k, vals in hourly.items():
            if k == "time":
                continue
            row[k] = {"value": vals[i] if i < len(vals) else None, "unit": units.get(k)}
        rows.append(row)

    return {
        "location": {"latitude": latitude, "longitude": longitude},
        "timezone": data.get("timezone"),
        "forecast_days": days,
        "hours": rows,
    }


# =================================================================
# WMO Weather Interpretation Code → human description
# =================================================================
_WMO_CODES: dict[int, str] = {
    0:  "Clear sky",
    1:  "Mainly clear", 2: "Partly cloudy", 3: "Overcast",
    45: "Fog", 48: "Depositing rime fog",
    51: "Light drizzle", 53: "Moderate drizzle", 55: "Dense drizzle",
    56: "Light freezing drizzle", 57: "Heavy freezing drizzle",
    61: "Slight rain", 63: "Moderate rain", 65: "Heavy rain",
    66: "Light freezing rain", 67: "Heavy freezing rain",
    71: "Slight snow fall", 73: "Moderate snow fall", 75: "Heavy snow fall",
    77: "Snow grains",
    80: "Slight rain showers", 81: "Moderate rain showers", 82: "Violent rain showers",
    85: "Slight snow showers", 86: "Heavy snow showers",
    95: "Thunderstorm",
    96: "Thunderstorm with slight hail", 99: "Thunderstorm with heavy hail",
}

def _wmo_description(code) -> str | None:
    if code is None:
        return None
    return _WMO_CODES.get(int(code), f"Unknown weather code {code}")


# =================================================================
# Entrypoint — detecta modo stdio (MCPize) vs HTTP local
# =================================================================
if __name__ == "__main__":
    port_start = os.getenv("UPSTREAM_PORT_START")
    if port_start:
        port = int(port_start)
        log.info("Starting HTTP/SSE transport on port %d", port)
        mcp.run(transport="streamable-http", host="0.0.0.0", port=port, path="/mcp")
    else:
        log.info("Starting stdio transport")
        mcp.run(transport="stdio")
