import requests
from datetime import datetime


def get_weather(latitude, longitude, arrival_time):
    url = "https://api.open-meteo.com/v1/forecast"

    params = {
        "latitude": latitude,
        "longitude": longitude,
        "hourly": "temperature_2m,precipitation,rain,snowfall,wind_speed_10m",
        "forecast_days": 3,
        "timezone": "auto",
    }

    
    try:
        response = requests.get(url, params=params, timeout=20)
        print("OPEN-METEO STATUS:", response.status_code)
        print("OPEN-METEO URL:", response.url)
        response.raise_for_status()
    except requests.RequestException as exc:
        print("OPEN-METEO ERROR:", repr(exc))
        raise

    data = response.json()

    hourly = data.get("hourly", {})
    times = hourly.get("time", [])

    if not times:
        print("OPEN-METEO RESPONSE:", data)
        return None

    target_time = datetime.fromisoformat(arrival_time)

    forecast_times = [datetime.fromisoformat(time) for time in times]

    index = min(
        range(len(forecast_times)),
        key=lambda i: abs((forecast_times[i] - target_time).total_seconds()),
    )

    if abs((forecast_times[index] - target_time).total_seconds()) > 90 * 60:
        return None

    def value(name):
        values = hourly.get(name, [])
        return values[index] if index < len(values) else None

    return {
        "time": times[index],
        "temperature_c": value("temperature_2m"),
        "precipitation_mm": value("precipitation"),
        "rain_mm": value("rain"),
        "snowfall_cm": value("snowfall"),
        "wind_speed_mph": (
            value("wind_speed_10m") * 0.621371
            if value("wind_speed_10m") is not None
            else None
        ),
        "rain_inches_per_hour": (
            value("rain") / 25.4 if value("rain") is not None else None
        ),
        "snow_inches_per_hour": (
            value("snowfall") / 2.54 if value("snowfall") is not None else None
        ),
    }
