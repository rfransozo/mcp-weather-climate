"""
mcp-weather-climate — MCPize Server
Global weather, forecasts, historical climate, air quality and marine data
via Open-Meteo — 100% free, no API key required.
"""

import os
import sys
import logging
import types as _types
from typing import Literal, Optional

import httpx
from fastmcp import FastMCP
from dotenv import load_dotenv
from starlette.requests import Request
from starlette.responses import JSONResponse
from starlette.routing import Route

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
FLOOD_URL      = "https://flood-api.open-meteo.com/v1/flood"
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
        try:
            resp = await client.get(url, params=params)
            resp.raise_for_status()
            return resp.json()
        except httpx.HTTPStatusError as exc:
            raise RuntimeError(
                f"Upstream API returned HTTP {exc.response.status_code}. Try again later."
            ) from exc
        except httpx.RequestError as exc:
            raise RuntimeError(
                f"Network error ({type(exc).__name__}). Check your connection."
            ) from exc


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
        raise ValueError(f"No location found for '{name}'. Try a different spelling or a nearby city.")
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
# Tool 9 — pollen_forecast
# =================================================================
@mcp.tool()
async def pollen_forecast(
    latitude: float,
    longitude: float,
    forecast_days: int = 4,
) -> dict:
    """
    Get hourly pollen forecast for Europe (alder, birch, grass, mugwort,
    olive, and ragweed). Data provided by CAMS European Air Quality forecast.
    Only available for European locations during the pollen season.

    Args:
        latitude: Decimal latitude (European locations only).
        longitude: Decimal longitude.
        forecast_days: Number of forecast days (1–4, default 4).
    """
    forecast_days = max(1, min(forecast_days, 4))
    hourly_vars = ",".join([
        "alder_pollen",
        "birch_pollen",
        "grass_pollen",
        "mugwort_pollen",
        "olive_pollen",
        "ragweed_pollen",
    ])
    params = {
        "latitude": latitude,
        "longitude": longitude,
        "hourly": hourly_vars,
        "forecast_days": forecast_days,
        "domains": "cams_europe",
        "timezone": "auto",
    }
    data   = await _get(AIR_URL, params)
    hourly = data.get("hourly", {})
    units  = data.get("hourly_units", {})
    times  = hourly.get("time", [])

    # Build daily peak summaries + hourly rows
    rows = []
    for i, t in enumerate(times):
        row = {"time": t}
        for k, vals in hourly.items():
            if k == "time":
                continue
            row[k] = {"value": vals[i] if i < len(vals) else None, "unit": units.get(k)}
        rows.append(row)

    # Compute daily max for each pollen type
    daily_peaks: dict[str, dict] = {}
    for row in rows:
        day = row["time"][:10]
        if day not in daily_peaks:
            daily_peaks[day] = {}
        for k in row:
            if k == "time":
                continue
            val = row[k]["value"]
            if val is not None:
                daily_peaks[day][k] = max(daily_peaks[day].get(k, 0.0), val)

    def _pollen_level(grains: float | None) -> str:
        if grains is None:
            return "unknown"
        if grains < 10:
            return "low"
        if grains < 30:
            return "moderate"
        if grains < 80:
            return "high"
        return "very high"

    daily_summary = [
        {
            "date": day,
            **{k: {"max_grains_m3": round(v, 1), "level": _pollen_level(v)}
               for k, v in peaks.items()},
        }
        for day, peaks in sorted(daily_peaks.items())
    ]

    return {
        "location": {"latitude": latitude, "longitude": longitude},
        "timezone": data.get("timezone"),
        "note": "Pollen data available for Europe only (CAMS European AQ forecast).",
        "daily_summary": daily_summary,
        "hourly": rows,
    }


# =================================================================
# Tool 10 — flood_risk
# =================================================================
@mcp.tool()
async def flood_risk(
    latitude: float,
    longitude: float,
    forecast_days: int = 30,
    past_days: int = 0,
) -> dict:
    """
    Get daily river discharge (m³/s) for the nearest river using GloFAS v4.
    Includes up to 7 months of forecast (210 days) and historical data from 1984.
    Useful for flood risk assessment, river logistics, and climate research.

    Args:
        latitude: Decimal latitude.
        longitude: Decimal longitude.
        forecast_days: Days of forecast to return (1–210, default 30).
        past_days: Days of past reanalysis to prepend (0–92, default 0).
    """
    forecast_days = max(1, min(forecast_days, 210))
    past_days = max(0, min(past_days, 92))
    params = {
        "latitude": latitude,
        "longitude": longitude,
        "daily": "river_discharge,river_discharge_mean,river_discharge_median,river_discharge_max,river_discharge_min",
        "forecast_days": forecast_days,
        "past_days": past_days,
    }
    data  = await _get(FLOOD_URL, params)
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
        rows.append(row)

    # Simple risk classification based on discharge
    discharges = [r["river_discharge"]["value"] for r in rows if r.get("river_discharge", {}).get("value") is not None]
    peak = max(discharges) if discharges else None
    baseline = sorted(discharges)[len(discharges) // 2] if discharges else None

    def _flood_level(current, base) -> str:
        if current is None or base is None or base == 0:
            return "unknown"
        ratio = current / base
        if ratio < 1.5:
            return "normal"
        if ratio < 2.5:
            return "elevated"
        if ratio < 4.0:
            return "high"
        return "extreme"

    return {
        "location": {"latitude": latitude, "longitude": longitude},
        "data_source": "GloFAS v4 (Global Flood Awareness System)",
        "note": "Nearest river within 5 km. Adjust coordinates by ±0.1° if discharge is zero.",
        "forecast_days": forecast_days,
        "peak_discharge_m3s": peak,
        "median_discharge_m3s": baseline,
        "peak_risk_level": _flood_level(peak, baseline),
        "days": rows,
    }


# =================================================================
# Tool 11 — solar_radiation_forecast
# =================================================================
@mcp.tool()
async def solar_radiation_forecast(
    latitude: float,
    longitude: float,
    days: int = 7,
    tilt: Optional[float] = None,
    azimuth: Optional[float] = None,
) -> dict:
    """
    Get hourly solar radiation forecast for solar energy planning and research.
    Returns global horizontal irradiance (GHI), direct normal irradiance (DNI),
    diffuse irradiance (DHI), sunshine duration, and UV index.
    Optionally compute irradiance on a tilted panel (global_tilted_irradiance).

    Args:
        latitude: Decimal latitude.
        longitude: Decimal longitude.
        days: Forecast horizon in days (1–16, default 7).
        tilt: Panel tilt angle in degrees (0–90). If omitted, GHI only.
        azimuth: Panel azimuth in degrees (0=south, -90=east, 90=west). Required with tilt.
    """
    days = max(1, min(days, 16))
    hourly_vars = [
        "shortwave_radiation",
        "direct_radiation",
        "direct_normal_irradiance",
        "diffuse_radiation",
        "sunshine_duration",
        "uv_index",
    ]
    if tilt is not None:
        hourly_vars.append("global_tilted_irradiance")

    params: dict = {
        "latitude": latitude,
        "longitude": longitude,
        "hourly": ",".join(hourly_vars),
        "forecast_days": days,
        "timezone": "auto",
    }
    if tilt is not None:
        params["tilt"] = tilt
    if azimuth is not None:
        params["azimuth"] = azimuth

    data   = await _get(FORECAST_URL, params)
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

    # Daily totals for shortwave_radiation (MJ/m²)
    daily_sums: dict[str, float] = {}
    for row in rows:
        day = row["time"][:10]
        val = row.get("shortwave_radiation", {}).get("value")
        if val is not None:
            daily_sums[day] = round(daily_sums.get(day, 0.0) + val / 1000, 3)  # W/m² → kWh/m²

    return {
        "location": {"latitude": latitude, "longitude": longitude},
        "timezone": data.get("timezone"),
        "panel_tilt": tilt,
        "panel_azimuth": azimuth,
        "daily_ghi_kwh_m2": [{"date": d, "kwh_m2": v} for d, v in sorted(daily_sums.items())],
        "hourly": rows,
    }


# =================================================================
# Tool 12 — severe_weather_outlook
# =================================================================
@mcp.tool()
async def severe_weather_outlook(
    latitude: float,
    longitude: float,
    days: int = 3,
) -> dict:
    """
    Compute a severe weather risk outlook using CAPE, lightning potential,
    freezing level, wind gusts, and precipitation probability.
    Returns a daily risk level (low / moderate / high / extreme) plus the
    raw instability variables per hour.

    Args:
        latitude: Decimal latitude.
        longitude: Decimal longitude.
        days: Forecast horizon in days (1–7, default 3).
    """
    days = max(1, min(days, 7))
    hourly_vars = ",".join([
        "cape",
        "wind_gusts_10m",
        "precipitation_probability",
        "precipitation",
        "freezing_level_height",
        "weather_code",
        "temperature_2m",
        "snowfall",
    ])
    params = {
        "latitude": latitude,
        "longitude": longitude,
        "hourly": hourly_vars,
        "forecast_days": days,
        "timezone": "auto",
    }
    data   = await _get(FORECAST_URL, params)
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

    # Score each hour: CAPE + gusts + lightning-like WMO codes
    SEVERE_WMO = {95, 96, 99}  # thunderstorms

    def _hour_score(row: dict) -> int:
        score = 0
        cape = (row.get("cape") or {}).get("value") or 0
        gusts = (row.get("wind_gusts_10m") or {}).get("value") or 0
        precip_prob = (row.get("precipitation_probability") or {}).get("value") or 0
        wmo = (row.get("weather_code") or {}).get("value")

        if cape > 1000:
            score += 3
        elif cape > 500:
            score += 2
        elif cape > 100:
            score += 1

        if gusts > 80:
            score += 3
        elif gusts > 60:
            score += 2
        elif gusts > 40:
            score += 1

        if precip_prob > 80:
            score += 1

        if wmo and int(wmo) in SEVERE_WMO:
            score += 3

        return score

    def _score_to_level(s: int) -> str:
        if s >= 7:
            return "extreme"
        if s >= 4:
            return "high"
        if s >= 2:
            return "moderate"
        return "low"

    # Aggregate to daily
    daily_scores: dict[str, list[int]] = {}
    for row in rows:
        day = row["time"][:10]
        daily_scores.setdefault(day, []).append(_hour_score(row))

    daily_outlook = [
        {
            "date": day,
            "risk_level": _score_to_level(max(scores)),
            "max_hour_score": max(scores),
        }
        for day, scores in sorted(daily_scores.items())
    ]

    return {
        "location": {"latitude": latitude, "longitude": longitude},
        "timezone": data.get("timezone"),
        "daily_outlook": daily_outlook,
        "hourly_instability": rows,
    }


# =================================================================
# Tool 13 — agricultural_conditions
# =================================================================
@mcp.tool()
async def agricultural_conditions(
    latitude: float,
    longitude: float,
    days: int = 7,
    temperature_unit: Literal["celsius", "fahrenheit"] = "celsius",
) -> dict:
    """
    Get agricultural weather conditions: soil temperature and moisture
    at four depths, reference evapotranspiration (ET₀ FAO-56), vapour
    pressure deficit, and evapotranspiration. Useful for irrigation planning,
    crop management, and agri-insurance workflows.

    Args:
        latitude: Decimal latitude.
        longitude: Decimal longitude.
        days: Forecast horizon in days (1–16, default 7).
        temperature_unit: 'celsius' or 'fahrenheit'.
    """
    days = max(1, min(days, 16))
    hourly_vars = ",".join([
        # Soil temperature (4 depths)
        "soil_temperature_0cm",
        "soil_temperature_6cm",
        "soil_temperature_18cm",
        "soil_temperature_54cm",
        # Soil moisture (4 depths)
        "soil_moisture_0_to_1cm",
        "soil_moisture_1_to_3cm",
        "soil_moisture_3_to_9cm",
        "soil_moisture_9_to_27cm",
        # Evapotranspiration
        "et0_fao_evapotranspiration",
        "evapotranspiration",
        # Atmospheric
        "vapour_pressure_deficit",
        "relative_humidity_2m",
        "temperature_2m",
        "precipitation",
        "wind_speed_10m",
    ])
    daily_vars = ",".join([
        "et0_fao_evapotranspiration",
        "precipitation_sum",
        "temperature_2m_max",
        "temperature_2m_min",
        "wind_speed_10m_max",
    ])
    params = {
        "latitude": latitude,
        "longitude": longitude,
        "hourly": hourly_vars,
        "daily": daily_vars,
        "forecast_days": days,
        "temperature_unit": temperature_unit,
        "timezone": "auto",
    }
    data   = await _get(FORECAST_URL, params)
    hourly = data.get("hourly", {})
    h_units = data.get("hourly_units", {})
    daily  = data.get("daily", {})
    d_units = data.get("daily_units", {})
    times  = hourly.get("time", [])
    dates  = daily.get("time", [])

    hourly_rows = []
    for i, t in enumerate(times):
        row = {"time": t}
        for k, vals in hourly.items():
            if k == "time":
                continue
            row[k] = {"value": vals[i] if i < len(vals) else None, "unit": h_units.get(k)}
        hourly_rows.append(row)

    daily_rows = []
    for i, d in enumerate(dates):
        row = {"date": d}
        for k, vals in daily.items():
            if k == "time":
                continue
            row[k] = {"value": vals[i] if i < len(vals) else None, "unit": d_units.get(k)}
        daily_rows.append(row)

    return {
        "location": {"latitude": latitude, "longitude": longitude},
        "timezone": data.get("timezone"),
        "temperature_unit": temperature_unit,
        "daily_summary": daily_rows,
        "hourly_soil_and_evapo": hourly_rows,
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
async def _health(request: Request) -> JSONResponse:
    """Health check endpoint for MCPize probes."""
    return JSONResponse({"status": "ok", "service": "mcp-weather-climate"})


# Inject /health into FastMCP's internal Starlette app — avoids
# wrapping the app in another Starlette layer (which breaks lifespan).
def _extra_routes(self) -> list:
    return [Route("/health", _health, methods=["GET", "HEAD"])]

mcp._get_additional_http_routes = _types.MethodType(_extra_routes, mcp)


if __name__ == "__main__":
    port_start = os.getenv("UPSTREAM_PORT_START")
    if port_start:
        port = int(port_start)
        log.info("Starting streamable-HTTP transport on port %d", port)
        # json_response=True: respond with application/json instead of text/event-stream.
        # Fixes 406 on MCPize health probes that don't send Accept: text/event-stream.
        # Valid per MCP Streamable HTTP spec — servers may respond with either SSE or JSON.
        mcp.run(transport="streamable-http", host="0.0.0.0", port=port, path="/mcp", json_response=True)
    else:
        log.info("Starting stdio transport")
        mcp.run(transport="stdio")
