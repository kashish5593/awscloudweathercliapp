#!/usr/bin/env python3
"""Fetch current weather for a city using the free Open-Meteo API."""

import argparse
import sys

import requests

GEO_URL = "https://geocoding-api.open-meteo.com/v1/search"
FORECAST_URL = "https://api.open-meteo.com/v1/forecast"

# Weather code -> human readable description
WEATHER_CODES = {
    0: "Clear sky",
    1: "Mainly clear",
    2: "Partly cloudy",
    3: "Overcast",
    45: "Fog",
    48: "Depositing rime fog",
    51: "Light drizzle",
    53: "Moderate drizzle",
    55: "Dense drizzle",
    56: "Light freezing drizzle",
    57: "Dense freezing drizzle",
    61: "Slight rain",
    63: "Moderate rain",
    65: "Heavy rain",
    66: "Light freezing rain",
    67: "Heavy freezing rain",
    71: "Slight snowfall",
    73: "Moderate snowfall",
    75: "Heavy snowfall",
    77: "Snow grains",
    80: "Slight rain showers",
    81: "Moderate rain showers",
    82: "Violent rain showers",
    85: "Slight snow showers",
    86: "Heavy snow showers",
    95: "Thunderstorm",
    96: "Thunderstorm with slight hail",
    99: "Thunderstorm with heavy hail",
}


def parse_args():
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description="Fetch the current weather for a city using Open-Meteo."
    )
    parser.add_argument("city", help="Name of the city (e.g. \"New York\")")
    parser.add_argument(
        "--units",
        choices=["metric", "imperial"],
        default="metric",
        help="Units: metric (Celsius, km/h) or imperial (Fahrenheit, mph)",
    )
    return parser.parse_args()


def geocode(city):
    """Resolve a city name to latitude/longitude via the geocoding API."""
    params = {"name": city, "count": 1, "language": "en", "format": "json"}
    resp = requests.get(GEO_URL, params=params, timeout=10)
    resp.raise_for_status()
    data = resp.json()
    results = data.get("results")
    if not results:
        sys.exit("Error: city not found: {}".format(city))
    return results[0]


def fetch_weather(lat, lon, units):
    """Fetch current weather for the given coordinates."""
    unit_map = {"metric": "celsius", "imperial": "fahrenheit"}
    params = {
        "latitude": lat,
        "longitude": lon,
        "current_weather": "true",
        "temperature_unit": unit_map[units],
        "windspeed_unit": "kmh" if units == "metric" else "mph",
        "timezone": "auto",
    }
    resp = requests.get(FORECAST_URL, params=params, timeout=10)
    resp.raise_for_status()
    return resp.json()


def build_table(rows):
    """Build a simple ASCII table from a list of (label, value) pairs."""
    label_width = max(len(label) for label, _ in rows)
    value_width = max(len(value) for _, value in rows)
    total = label_width + value_width + 7  # 3 spaces + 2 pipes + 2 padding
    border = "+" + "-" * (total - 2) + "+"

    lines = [border]
    for label, value in rows:
        lines.append(
            "| {:<{}} | {:<{}} |".format(label, label_width, value, value_width)
        )
    lines.append(border)
    return "\n".join(lines)


def main():
    """Main entry point."""
    args = parse_args()

    try:
        location = geocode(args.city)
        weather = fetch_weather(
            location["latitude"], location["longitude"], args.units
        )
    except requests.RequestException as exc:
        sys.exit("Error: could not reach Open-Meteo API: {}".format(exc))

    current = weather["current_weather"]
    temp_unit = "deg C" if args.units == "metric" else "deg F"
    wind_unit = "km/h" if args.units == "metric" else "mph"
    condition = WEATHER_CODES.get(current["weathercode"], "Unknown")

    rows = [
        ("City", location.get("name", args.city)),
        ("Region", "{}, {}".format(
            location.get("admin1", ""), location.get("country", "")
        ).strip(", ")),
        ("Latitude", "{:.5f}".format(location["latitude"])),
        ("Longitude", "{:.5f}".format(location["longitude"])),
        ("Temperature", "{} {}".format(current["temperature"], temp_unit)),
        ("Wind Speed", "{} {}".format(current["windspeed"], wind_unit)),
        ("Wind Direction", "{} deg".format(current["winddirection"])),
        ("Conditions", condition),
        ("Observed At", current["time"]),
    ]

    print()
    print("Weather for {}".format(args.city))
    print()
    print(build_table(rows))
    print()


if __name__ == "__main__":
    main()