import requests
from datetime import datetime
from functools import lru_cache


def _parse_weather(data, arrival_time):
    hourly = data.get("hourly", {})
    times = hourly.get("time", [])

    if not times:
        return None

    target_time = datetime.fromisoformat(arrival_time)
    forecast_times = [datetime.fromisoformat(t) for t in times]

    index = min(
        range(len(forecast_times)),
        key=lambda i: abs(
            (forecast_times[i] - target_time).total_seconds()
        ),
    )

    if abs(
        (forecast_times[index] - target_time).total_seconds()
    ) > 90 * 60:
        return None

    def value(name):
        values = hourly.get(name, [])
        return values[index] if index < len(values) else None

    wind = value("wind_speed_10m")
    rain = value("rain")
    snow = value("snowfall")

    return {
        "time": times[index],
        "temperature_c": value("temperature_2m"),
        "precipitation_mm": value("precipitation"),
        "rain_mm": rain,
        "snowfall_cm": snow,
        "wind_speed_mph": (
            wind * 0.621371 if wind is not None else None
        ),
        "rain_inches_per_hour": (
            rain / 25.4 if rain is not None else None
        ),
        "snow_inches_per_hour": (
            snow / 2.54 if snow is not None else None
        ),
    }


@lru_cache(maxsize=512)
def _get_weather_cached(latitude, longitude, arrival_time):
    url = "https://api.open-meteo.com/v1/forecast"
    params = {
        "latitude": latitude,
        "longitude": longitude,
        "hourly": (
            "temperature_2m,precipitation,rain,"
            "snowfall,wind_speed_10m"
        ),
        "forecast_days": 3,
        "timezone": "auto",
    }

    response = requests.get(url, params=params, timeout=20)
    response.raise_for_status()

    return _parse_weather(response.json(), arrival_time)


def get_weather(latitude, longitude, arrival_time):
    target = datetime.fromisoformat(arrival_time)
    forecast_hour = target.replace(
        minute=0, second=0, microsecond=0
    )

    return _get_weather_cached(
        round(latitude, 2),
        round(longitude, 2),
        forecast_hour.isoformat(),
    )


def get_weather_batch(checkpoints):
    if not checkpoints:
        return []

    url = "https://api.open-meteo.com/v1/forecast"

    params = {
        "latitude": ",".join(
            str(round(c["latitude"], 2)) for c in checkpoints
        ),
        "longitude": ",".join(
            str(round(c["longitude"], 2)) for c in checkpoints
        ),
        "hourly": (
            "temperature_2m,precipitation,rain,"
            "snowfall,wind_speed_10m"
        ),
        "forecast_days": 3,
        "timezone": "auto",
    }

    response = requests.get(url, params=params, timeout=30)
    response.raise_for_status()

    data = response.json()

    # Open-Meteo returns a list for multiple locations.
    if isinstance(data, dict):
        data = [data]

    results = []

    for index, checkpoint in enumerate(checkpoints):
        if index >= len(data):
            results.append(None)
            continue

        results.append(
            _parse_weather(
                data[index],
                checkpoint["arrival_time"],
            )
        )

    return results