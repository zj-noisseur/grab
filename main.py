"""
Grab-Style Geocoding & Ride Fare Calculation CLI.
Step 2: Distance calculation via Haversine and fare estimation with standard input.
"""

import sys
import math
import requests

NOMINATIM_URL = "https://nominatim.openstreetmap.org/search"
USER_AGENT = "GrabPricingCLI/1.0"
BASE_PRICE_PER_KM = 2.50

WEATHER_MULTIPLIERS = {
    "sunny": 1.0,
    "cloudy": 1.1,
    "storm": 1.5,
}

TRAFFIC_MULTIPLIERS = {
    "free-flowing": 1.0,
    "normal": 1.2,
    "congested": 1.6,
}


def haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Compute great-circle distance between two points on Earth in kilometers."""
    r = 6371.0
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lon2 - lon1)

    a = (
        math.sin(delta_phi / 2.0) ** 2
        + math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda / 2.0) ** 2
    )
    c = 2.0 * math.atan2(math.sqrt(a), math.sqrt(1.0 - a))
    return r * c


def query_nominatim(query: str) -> list[dict]:
    """Query Nominatim search API for geocoding coordinates."""
    params = {
        "q": query.strip(),
        "format": "json",
        "addressdetails": 1,
        "limit": 5,
    }
    headers = {"User-Agent": USER_AGENT}

    try:
        response = requests.get(NOMINATIM_URL, params=params, headers=headers, timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        print(f"Error querying Nominatim: {e}")
        return []


def geocode_location(label: str) -> dict:
    """Prompt user for a location and resolve coordinates via Nominatim."""
    while True:
        addr = input(f"Enter {label} location: ").strip()
        if not addr:
            print("Please enter a valid location name.")
            continue

        print(f"Searching Nominatim for '{addr}'...")
        results = query_nominatim(addr)
        if not results:
            print(f"No results found for '{addr}'. Please try again.")
            continue

        top = results[0]
        return {
            "display_name": top.get("display_name"),
            "lat": float(top.get("lat")),
            "lon": float(top.get("lon")),
        }


def main():
    print("=== Grab Fare Estimator (Console Input) ===")

    pickup = geocode_location("Pickup")
    print(f"✓ Pickup set: {pickup['display_name']} ({pickup['lat']:.4f}, {pickup['lon']:.4f})\n")

    dest = geocode_location("Destination")
    print(f"✓ Destination set: {dest['display_name']} ({dest['lat']:.4f}, {dest['lon']:.4f})\n")

    # Multipliers via simple console input
    weather = input("Select weather (sunny, cloudy, storm) [sunny]: ").strip().lower() or "sunny"
    traffic = input("Select traffic (free-flowing, normal, congested) [normal]: ").strip().lower() or "normal"

    weather_mult = WEATHER_MULTIPLIERS.get(weather, 1.0)
    traffic_mult = TRAFFIC_MULTIPLIERS.get(traffic, 1.2)

    dist_km = haversine_distance(pickup["lat"], pickup["lon"], dest["lat"], dest["lon"])
    fare = dist_km * BASE_PRICE_PER_KM * weather_mult * traffic_mult

    print("\n" + "=" * 50)
    print("                 TRIP SUMMARY                     ")
    print("=" * 50)
    print(f"Pickup     : {pickup['display_name']}")
    print(f"Destination: {dest['display_name']}")
    print(f"Distance   : {dist_km:.2f} km")
    print(f"Weather    : {weather} ({weather_mult}x)")
    print(f"Traffic    : {traffic} ({traffic_mult}x)")
    print(f"Total Fare : RM {fare:.2f}")
    print("=" * 50)


if __name__ == "__main__":
    main()
