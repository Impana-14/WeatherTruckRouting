import os
import requests
from datetime import datetime
from functools import lru_cache

WEATHERAPI_URL = "https://api.weatherapi.com/v1/forecast.json"


def _parse_weather(data, arrival_time):
    forecast_days = data.get("forecast", {}).get("forecastday", [])

    if not forecast_days:
        return None

    target_time = datetime.fromisoformat(arrival_time)
    hours = [
        hour
        for day in forecast_days
        for hour in day.get("hour", [])
    ]

    if not hours:
        return None

    def parse_time(hour):
        return datetime.fromisoformat(hour["time"])

    # Match the forecast hour closest to the checkpoint's arrival.
    target = min(hours, key=lambda hour: abs(
        (parse_time(hour) - target_time).total_seconds()
    ))

    if abs((parse_time(target) - target_time).total_seconds()) > 90 * 60:
        return None

    rain_inches = target.get("precip_in")
    snow_cm = target.get("snow_cm")
    wind_mph = target.get("wind_mph")

    return {
        "time": target.get("time"),
        "temperature_c": target.get("temp_c"),
        "precipitation_mm": (
            target.get("precip_mm")
        ),
        "rain_mm": (
            rain_inches * 25.4 if rain_inches is not None else None
        ),
        "snowfall_cm": snow_cm,
        "wind_speed_mph": wind_mph,
        "rain_inches_per_hour": rain_inches,
        "snow_inches_per_hour": (
            snow_cm / 2.54 if snow_cm is not None else None
        ),
    }


@lru_cache(maxsize=256)
def _get_weather_cached(latitude, longitude, arrival_hour):
    api_key = os.getenv("WEATHERAPI_API_KEY")

    if not api_key:
        raise RuntimeError("WEATHERAPI_API_KEY is not configured")

    response = requests.get(
        WEATHERAPI_URL,
        params={
            "key": api_key,
            "q": f"{latitude},{longitude}",
            "days": 3,
            "aqi": "no",
            "alerts": "no",
        },
        timeout=20,
    )
    response.raise_for_status()

    return _parse_weather(response.json(), arrival_hour)


def get_weather(latitude, longitude, arrival_time):
    target = datetime.fromisoformat(arrival_time)
    return _get_weather_cached(
        round(latitude, 2),
        round(longitude, 2),
        target.isoformat(),
    )


def get_weather_batch(checkpoints):
    results = []

    for checkpoint in checkpoints:
        try:
            weather = get_weather(
                checkpoint["latitude"],
                checkpoint["longitude"],
                checkpoint["arrival_time"],
            )
        except (requests.RequestException, ValueError) as exc:
            print("WEATHERAPI ERROR:", repr(exc))
            weather = None

        results.append(weather)

    return results