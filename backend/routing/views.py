from datetime import datetime, timedelta
from math import ceil
import requests
from django.shortcuts import render
from rest_framework.decorators import api_view
from rest_framework.response import Response
from geopy.geocoders import Nominatim
from geopy.extra.rate_limiter import RateLimiter
from .weather import get_weather_batch
from geopy.distance import geodesic
import os

OPENROUTESERVICE_API_KEY = os.getenv("OPENROUTESERVICE_API_KEY")


def create_checkpoints(route_geometry, interval_miles=25):
    coordinates = route_geometry.get("coordinates", [])
    if not coordinates:
        return []

    interval_km = interval_miles * 1.60934
    checkpoints = []
    cumulative_km = 0.0
    next_checkpoint_km = interval_km

    first_lon, first_lat = coordinates[0]
    checkpoints.append(
        {
            "latitude": first_lat,
            "longitude": first_lon,
            "distance_km": 0.0,
            "distance_miles": 0.0,
        }
    )

    for i in range(1, len(coordinates)):
        previous = coordinates[i - 1]
        current = coordinates[i]

        segment_km = geodesic(
            (previous[1], previous[0]),
            (current[1], current[0]),
        ).kilometers

        if segment_km == 0:
            continue

        segment_start_km = cumulative_km
        segment_end_km = cumulative_km + segment_km

        while next_checkpoint_km <= segment_end_km:
            fraction = (next_checkpoint_km - segment_start_km) / segment_km

            longitude = previous[0] + (current[0] - previous[0]) * fraction
            latitude = previous[1] + (current[1] - previous[1]) * fraction

            checkpoints.append(
                {
                    "latitude": latitude,
                    "longitude": longitude,
                    "distance_km": round(next_checkpoint_km, 2),
                    "distance_miles": round(next_checkpoint_km / 1.60934, 2),
                }
            )

            next_checkpoint_km += interval_km

        cumulative_km = segment_end_km

    last_lon, last_lat = coordinates[-1]
    total_miles = cumulative_km / 1.60934

    if total_miles > checkpoints[-1]["distance_miles"]:
        checkpoints.append(
            {
                "latitude": last_lat,
                "longitude": last_lon,
                "distance_km": round(cumulative_km, 2),
                "distance_miles": round(total_miles, 2),
            }
        )

    return checkpoints


def calculate_arrival_time(departure, distance_km, total_distance_km, duration_minutes):
    departure_time = datetime.fromisoformat(departure)

    if total_distance_km <= 0:
        return departure_time.isoformat()

    elapsed_minutes = duration_minutes * (distance_km / total_distance_km)

    arrival_time = departure_time + timedelta(minutes=elapsed_minutes)

    return arrival_time.isoformat()


def calculate_weather_risk(weather, load_weight):
    if weather is None:
        return {
            "risk_level": "unknown",
            "risk_score": None,
            "reasons": ["Weather data is unavailable for this checkpoint."],
            "no_travel": False,
        }

    reasons = []

    # Convert the user's load from kilograms to pounds.
    load_weight_lb = load_weight * 2.20462

    wind = weather.get("wind_speed_mph")
    rain = weather.get("rain_inches_per_hour")
    snow = weather.get("snow_inches_per_hour")

    # Missing weather measurements must not be treated as zero.
    if wind is None or rain is None or snow is None:
        return {
            "risk_level": "unknown",
            "risk_score": None,
            "reasons": ["One or more weather measurements are unavailable."],
            "no_travel": False,
        }

    # Wind and load rules.
    if wind >= 55:
        reasons.append("No Travel: wind is at least 55 mph.")
        level = "no_travel"
    elif wind >= 45 and load_weight_lb > 30000:
        reasons.append("No Travel: wind is 45–54 mph and load exceeds 30,000 lb.")
        level = "no_travel"
    elif wind >= 35 and load_weight_lb > 40000:
        reasons.append("Severe risk: wind is 35–44 mph and load exceeds 40,000 lb.")
        level = "severe"
    elif wind >= 45:
        reasons.append("Severe wind: 45–54 mph.")
        level = "severe"
    elif wind >= 35:
        reasons.append("High wind: 35–44 mph.")
        level = "high"
    elif wind >= 25:
        reasons.append("Moderate wind: 25–34 mph.")
        level = "moderate"
    else:
        level = "low"

    # Rain rules.
    if rain > 1.00:
        reasons.append("No Travel: rainfall exceeds 1.00 inch/hour.")
        level = "no_travel"
    elif rain >= 0.50:
        reasons.append("Severe rain: 0.50–1.00 inch/hour.")
        if level != "no_travel":
            level = "severe"
    elif rain >= 0.25:
        reasons.append("High rain: 0.25–0.50 inch/hour.")
        if level not in ("no_travel", "severe"):
            level = "high"
    elif rain >= 0.10:
        reasons.append("Moderate rain: 0.10–0.25 inch/hour.")
        if level == "low":
            level = "moderate"

    # Snow rules.
    if snow > 3.00:
        reasons.append("No Travel: snowfall exceeds 3.00 inches/hour.")
        level = "no_travel"
    elif snow >= 2.00:
        reasons.append("Severe snow: 2.00–3.00 inches/hour.")
        if level != "no_travel":
            level = "severe"
    elif snow >= 1.00:
        reasons.append("High snow: 1.00–2.00 inches/hour.")
        if level not in ("no_travel", "severe"):
            level = "high"
    elif snow >= 0.50:
        reasons.append("Moderate snow: 0.50–1.00 inches/hour.")
        if level == "low":
            level = "moderate"

    risk_scores = {
        "low": 0,
        "moderate": 1,
        "high": 2,
        "severe": 3,
        "no_travel": 4,
    }

    return {
        "risk_level": level,
        "risk_score": risk_scores[level],
        "reasons": reasons or ["No major weather risks detected."],
        "no_travel": level == "no_travel",
    }


def calculate_route_summary(route):
    checkpoints = route.get("checkpoints", [])

    severe_miles = 0.0
    high_miles = 0.0
    risk_scores = []

    for checkpoint in checkpoints:
        score = checkpoint.get("risk_score")
        if score is not None:
            risk_scores.append(score)

    for index in range(1, len(checkpoints)):
        previous = checkpoints[index - 1]
        current = checkpoints[index]

        segment_miles = (current["distance_km"] - previous["distance_km"]) * 0.621371

        level = current.get("risk_level", "unknown")

        if level in ("severe", "no_travel"):
            severe_miles += segment_miles
        elif level == "high":
            high_miles += segment_miles

    average_risk = sum(risk_scores) / len(risk_scores) if risk_scores else None

    return {
        "severe_miles": round(severe_miles, 2),
        "high_miles": round(high_miles, 2),
        "average_risk_score": (
            round(average_risk, 2) if average_risk is not None else None
        ),
    }


def get_coordinates(place):
    geolocator = Nominatim(user_agent="weather_truck_routing_app")
    location = geolocator.geocode(place, timeout=10)

    if location is None:
        return None

    return {
        "latitude": location.latitude,
        "longitude": location.longitude,
        "display_name": location.address,
    }


def get_driving_routes(origin_coords, destination_coords):
    if not OPENROUTESERVICE_API_KEY:
        raise ValueError("OPENROUTESERVICE_API_KEY is missing from backend/.env")

    url = "https://api.openrouteservice.org/v2/directions/driving-hgv/geojson"

    headers = {
        "Authorization": OPENROUTESERVICE_API_KEY,
        "Content-Type": "application/json",
    }

    origin = (
        origin_coords["latitude"],
        origin_coords["longitude"],
    )
    destination = (
        destination_coords["latitude"],
        destination_coords["longitude"],
    )

    approximate_distance_km = geodesic(origin, destination).kilometers

    body = {
        "coordinates": [
            [origin_coords["longitude"], origin_coords["latitude"]],
            [destination_coords["longitude"], destination_coords["latitude"]],
        ],
        "radiuses": [2000, 2000],
    }

    if approximate_distance_km <= 100:
        body["alternative_routes"] = {
            "target_count": 3,
            "weight_factor": 1.6,
            "share_factor": 0.6,
        }

    response = requests.post(
        url,
        headers=headers,
        json=body,
        timeout=30,
    )
    response.raise_for_status()

    data = response.json()
    features = data.get("features", [])
    routes = []

    for feature in features[:3]:
        properties = feature.get("properties", {})
        summary = properties.get("summary", {})
        geometry = feature.get("geometry", {})

        if not geometry.get("coordinates") or not summary:
            continue

        routes.append(
            {
                "distance": summary["distance"],
                "duration": summary["duration"],
                "geometry": geometry,
            }
        )

    return routes


@api_view(["GET"])
def health_check(request):
    return Response(
        {"status": "success", "message": "Weather Truck Routing API is running!"}
    )

@api_view(["POST"])
def plan_route(request):
    origin = request.data.get("origin")
    destination = request.data.get("destination")
    departure = request.data.get("departure")
    load_weight = request.data.get("loadWeight")
    interval_miles = request.data.get("intervalMiles", 25)

    try:
        interval_miles = int(interval_miles)
        if interval_miles not in (10, 25, 50):
            return Response(
                {"error": "Checkpoint interval must be 10, 25, or 50 miles."},
                status=400,
            )
    except (TypeError, ValueError):
        return Response(
            {"error": "Checkpoint interval must be 10, 25, or 50 miles."},
            status=400,
        )

    if not origin or not destination or not departure or load_weight is None:
        return Response({"error": "All route fields are required."}, status=400)

    try:
        load_weight = float(load_weight)
        if load_weight < 0:
            return Response(
                {"error": "Load weight cannot be negative."}, status=400
            )
    except (TypeError, ValueError):
        return Response(
            {"error": "Load weight must be a valid number."}, status=400
        )

    try:
        origin_coords = get_coordinates(origin)
        destination_coords = get_coordinates(destination)
        print("Origin coordinates:", origin_coords)
        print("Destination coordinates:", destination_coords)
    except Exception:
        return Response(
            {"error": "Location lookup failed. Please try again."}, status=502
        )

    if origin_coords is None or destination_coords is None:
        return Response(
            {
                "error": (
                    "Could not find the origin or destination. "
                    "Add the city and country."
                )
            },
            status=400,
        )

    try:
        routes = get_driving_routes(origin_coords, destination_coords)
    except requests.RequestException as exc:
        if exc.response is not None:
            print("Routing API status:", exc.response.status_code)
            print("Routing API response:", exc.response.text[:1000])
        else:
            print("Routing API connection error:", str(exc))

        return Response(
            {"error": "The routing service is unavailable. Please try again."},
            status=502,
        )

    if not routes:
        return Response(
            {"error": "No driving routes were found for these locations."},
            status=404,
        )

    # First prepare checkpoints for every route.
    route_data = []
    all_checkpoints = []

    for index, route in enumerate(routes):
        distance_km = route["distance"] / 1000
        duration_minutes = route["duration"] / 60

        checkpoints = create_checkpoints(
            route["geometry"],
            interval_miles=interval_miles,
        )

        for checkpoint in checkpoints:
            checkpoint["arrival_time"] = calculate_arrival_time(
                departure,
                checkpoint["distance_km"],
                distance_km,
                duration_minutes,
            )

        start_index = len(all_checkpoints)
        all_checkpoints.extend(checkpoints)
        end_index = len(all_checkpoints)

        route_data.append(
            {
                "route_number": index + 1,
                "route": route,
                "distance_km": distance_km,
                "duration_minutes": duration_minutes,
                "checkpoint_start": start_index,
                "checkpoint_end": end_index,
            }
        )

    # Fetch weather once for all candidate routes.
    try:
        weather_results = get_weather_batch(all_checkpoints)
    except requests.RequestException as exc:
        print("BATCH WEATHER ERROR:", repr(exc))
        weather_results = [None] * len(all_checkpoints)

    # Ensure every checkpoint has a corresponding result.
    if len(weather_results) < len(all_checkpoints):
        weather_results.extend(
            [None] * (len(all_checkpoints) - len(weather_results))
        )
    elif len(weather_results) > len(all_checkpoints):
        weather_results = weather_results[:len(all_checkpoints)]

    enriched_routes = []

    for item in route_data:
        route = item["route"]
        distance_km = item["distance_km"]
        duration_minutes = item["duration_minutes"]

        start = item["checkpoint_start"]
        end = item["checkpoint_end"]

        enriched_checkpoints = []

        for checkpoint, weather in zip(
            all_checkpoints[start:end],
            weather_results[start:end],
        ):
            risk = calculate_weather_risk(weather, load_weight)

            if risk["risk_level"] == "unknown":
                print(
                    "UNKNOWN CHECKPOINT:",
                    checkpoint["distance_miles"],
                    "miles | WEATHER:",
                    weather,
                    "| RISK:",
                    risk,
                )

            enriched_checkpoints.append(
                {
                    **checkpoint,
                    "weather": weather,
                    **risk,
                }
            )

        enriched_routes.append(
            {
                "route_number": item["route_number"],
                "distance_km": round(distance_km, 2),
                "duration_minutes": round(duration_minutes, 1),
                "geometry": route["geometry"],
                "checkpoints": enriched_checkpoints,
                "summary": calculate_route_summary(
                    {
                        "checkpoints": enriched_checkpoints,
                        "distance_km": round(distance_km, 2),
                        "duration_minutes": round(duration_minutes, 1),
                    }
                ),
            }
        )

    # Recommend only routes with complete weather data and no No Travel points.
    for route in enriched_routes:
        checkpoints = route["checkpoints"]
        route["weather_data_complete"] = bool(checkpoints) and all(
            checkpoint.get("risk_score") is not None
            for checkpoint in checkpoints
        )

    ranked_routes = sorted(
        enriched_routes,
        key=lambda route: (
            route["summary"]["severe_miles"],
            route["summary"]["high_miles"],
            (
                route["summary"]["average_risk_score"]
                if route["summary"]["average_risk_score"] is not None
                else float("inf")
            ),
            route["duration_minutes"],
        ),
    )

    eligible_routes = [
        route
        for route in ranked_routes
        if route["weather_data_complete"]
        and not any(
            checkpoint.get("no_travel", False)
            for checkpoint in route["checkpoints"]
        )
    ]

    recommended_route_number = (
        eligible_routes[0]["route_number"] if eligible_routes else None
    )

    for route in enriched_routes:
        route["recommended"] = (
            route["route_number"] == recommended_route_number
        )

    return Response(
        {
            "status": "success",
            "message": "Driving routes and checkpoint analysis completed.",
            "route_request": {
                "origin": origin,
                "destination": destination,
                "departure": departure,
                "load_weight_kg": load_weight,
            },
            "coordinates": {
                "origin": origin_coords,
                "destination": destination_coords,
            },
            "routes": enriched_routes,
        }
    )
