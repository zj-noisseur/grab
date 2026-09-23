"""
Grab-Style Geocoding & Ride Fare Calculation CLI.
Step 3: Interactive CLI experience using Questionary prompts and custom styling.
"""

import sys
import math
import requests
import questionary
from questionary import Style

# Custom prompt style for a polished CLI look
CUSTOM_STYLE = Style([
    ("qmark", "fg:#2ecc71 bold"),
    ("question", "bold"),
    ("answer", "fg:#2ecc71 bold"),
    ("pointer", "fg:#2ecc71 bold"),
    ("highlighted", "fg:#2ecc71 bold"),
    ("selected", "fg:#2ecc71"),
    ("separator", "fg:#7f8c8d"),
    ("instruction", "fg:#95a5a6"),
    ("text", ""),
])

NOMINATIM_URL = "https://nominatim.openstreetmap.org/search"
USER_AGENT = "GrabPricingCLI/1.0"
BASE_PRICE_PER_KM = 2.50

MALAYSIA_STATES = [
    "Kuala Lumpur",
    "Selangor",
    "Penang",
    "Johor",
    "Perak",
    "Melaka",
    "Kedah",
    "Pahang",
    "Negeri Sembilan",
    "Kelantan",
    "Terengganu",
    "Perlis",
    "Sabah",
    "Sarawak",
    "Putrajaya",
    "Labuan",
    "All / Other (Worldwide)",
]

WEATHER_OPTIONS = {
    "☀️ Sunny (1.0x)": {"multiplier": 1.0, "name": "Sunny"},
    "☁️ Cloudy (1.1x)": {"multiplier": 1.1, "name": "Cloudy"},
    "⛈️ Storm (1.5x)": {"multiplier": 1.5, "name": "Storm"},
}

TRAFFIC_OPTIONS = {
    "🟢 Free-flowing (1.0x)": {"multiplier": 1.0, "name": "Free-flowing"},
    "🟡 Normal (1.2x)": {"multiplier": 1.2, "name": "Normal"},
    "🔴 Congested (1.6x)": {"multiplier": 1.6, "name": "Congested"},
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


def query_nominatim(query: str, state: str = None) -> list[dict]:
    """Query Nominatim search API for geocoding coordinates with state context."""
    search_q = query.strip()
    if state and state != "All / Other (Worldwide)":
        if state.lower() not in search_q.lower():
            search_q = f"{search_q}, {state}"

    params = {
        "q": search_q,
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


def prompt_location(label: str, state: str) -> dict:
    """Prompt user using questionary text prompt and fetch top coordinate."""
    while True:
        query = questionary.text(
            f"Enter {label} location keyword/address:",
            style=CUSTOM_STYLE,
        ).ask()

        if query is None:
            print("\nOperation cancelled.")
            sys.exit(0)

        query = query.strip()
        if not query:
            print("Please enter a non-empty search term.")
            continue

        print(f"🔎 Polling Nominatim server for '{query}'...")
        results = query_nominatim(query, state=state)

        if not results:
            print(f"⚠️ No matching locations found for '{query}'. Please try again.")
            continue

        top = results[0]
        selected = {
            "display_name": top.get("display_name"),
            "lat": float(top.get("lat")),
            "lon": float(top.get("lon")),
        }
        print(f"✓ Confirmed {label}: {selected['display_name']} [{selected['lat']:.5f}, {selected['lon']:.5f}]\n")
        return selected


def main():
    print("=" * 60)
    print("  🚗 GRAB FARE ESTIMATOR (QUESTIONARY PROMPTS)")
    print("=" * 60 + "\n")

    # Step 1: State selection
    state = questionary.select(
        "Step 1: Select your State / Region for geocoding context:",
        choices=MALAYSIA_STATES,
        style=CUSTOM_STYLE,
    ).ask()

    if state is None:
        sys.exit(0)

    # Step 2 & 3: Pickup & Destination
    pickup = prompt_location("Pickup", state)
    dest = prompt_location("Destination", state)

    # Step 4: Weather selection
    weather_choice = questionary.select(
        "Step 4: Select current weather condition:",
        choices=list(WEATHER_OPTIONS.keys()),
        style=CUSTOM_STYLE,
    ).ask()

    if weather_choice is None:
        sys.exit(0)

    weather_info = WEATHER_OPTIONS[weather_choice]

    # Step 5: Traffic selection
    traffic_choice = questionary.select(
        "Step 5: Select current traffic condition:",
        choices=list(TRAFFIC_OPTIONS.keys()),
        style=CUSTOM_STYLE,
    ).ask()

    if traffic_choice is None:
        sys.exit(0)

    traffic_info = TRAFFIC_OPTIONS[traffic_choice]

    # Calculations
    distance_km = haversine_distance(pickup["lat"], pickup["lon"], dest["lat"], dest["lon"])
    final_price = distance_km * BASE_PRICE_PER_KM * weather_info["multiplier"] * traffic_info["multiplier"]

    print("\n" + "=" * 60)
    print("                 TRIP SUMMARY & FARE                     ")
    print("=" * 60)
    print(f"Pickup     : {pickup['display_name']}")
    print(f"Destination: {dest['display_name']}")
    print(f"Distance   : {distance_km:.2f} km")
    print(f"Weather    : {weather_info['name']} ({weather_info['multiplier']}x)")
    print(f"Traffic    : {traffic_info['name']} ({traffic_info['multiplier']}x)")
    print(f"Total Fare : RM {final_price:.2f}")
    print("=" * 60 + "\n")


if __name__ == "__main__":
    main()
