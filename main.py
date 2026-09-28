"""
Grab-Style Geocoding & Ride Fare Calculation CLI.

Features:
- State selection to contextualize address queries.
- Nominatim OpenStreetMap search API for geocoding human-readable addresses to coordinates.
- Interactive questionary selection with search amendment / re-query capabilities.
- Weather and Traffic multiplier adjustments.
- Distance calculation via Haversine formula.
- Final price computation: Distance * base_price * weather_multiplier * traffic_multiplier.
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
USER_AGENT = "GrabPricingCLI/1.0 (terminal_fare_calculator)"
BASE_PRICE_PER_KM = 2.50  # Base price in RM per KM

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
    r = 6371.0  # Earth's mean radius in km
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
    """Query Nominatim search API for geocoding suggestions."""
    search_q = query.strip()
    if state and state != "All / Other (Worldwide)":
        # Include state in query context if not already present
        if state.lower() not in search_q.lower():
            search_q = f"{search_q}, {state}"

    params = {
        "q": search_q,
        "format": "json",
        "addressdetails": 1,
        "limit": 6,
    }
    headers = {
        "User-Agent": USER_AGENT,
    }

    try:
        response = requests.get(NOMINATIM_URL, params=params, headers=headers, timeout=10)
        response.raise_for_status()
        results = response.json()
        return results
    except requests.RequestException as e:
        print(f"\n[!] Error connecting to Nominatim server: {e}")
        return []


def prompt_location_search(label: str, state: str) -> dict:
    """Prompt user to type address, search Nominatim, and select or amend query."""
    query = ""
    while True:
        # Prompt for query text
        default_query = query if query else ""
        query_input = questionary.text(
            f"Enter {label} location keyword/address:",
            default=default_query,
            style=CUSTOM_STYLE,
        ).ask()

        if query_input is None:
            print("\nOperation cancelled by user.")
            sys.exit(0)

        query = query_input.strip()
        if not query:
            print("Please enter a non-empty search term.")
            continue

        print(f"🔎 Polling Nominatim server for '{query}'...")
        results = query_nominatim(query, state=state)

        if not results:
            print(f"⚠️  No matching locations found for '{query}'.")
            action = questionary.select(
                "How would you like to proceed?",
                choices=[
                    "✏️  Amend search query and try again",
                    "❌ Cancel",
                ],
                style=CUSTOM_STYLE,
            ).ask()

            if action == "✏️  Amend search query and try again":
                continue
            else:
                print("\nExiting.")
                sys.exit(0)

        # Build dropdown options
        choices = []
        result_map = {}
        for idx, item in enumerate(results):
            display_name = item.get("display_name", "")
            lat = float(item.get("lat", 0.0))
            lon = float(item.get("lon", 0.0))
            # Truncate display name if too long for clean CLI rendering
            short_name = display_name if len(display_name) <= 85 else display_name[:82] + "..."
            choice_label = f"{idx + 1}. {short_name} ({lat:.4f}, {lon:.4f})"
            choices.append(choice_label)
            result_map[choice_label] = {
                "display_name": display_name,
                "lat": lat,
                "lon": lon,
            }

        choices.append("✏️  Amend query and search again")
        choices.append("❌ Cancel")

        selected = questionary.select(
            f"Select matching {label} location:",
            choices=choices,
            style=CUSTOM_STYLE,
        ).ask()

        if selected is None or selected == "❌ Cancel":
            print("\nOperation cancelled.")
            sys.exit(0)

        if selected == "✏️  Amend query and search again":
            continue

        selected_loc = result_map[selected]
        print(f"✓ Confirmed {label}: {selected_loc['display_name']} [{selected_loc['lat']:.5f}, {selected_loc['lon']:.5f}]")
        return selected_loc


def print_banner():
    """Display program header."""
    print("=" * 72)
    print("  🚗 GRAB FARE ESTIMATOR & NOMINATIM GEOCODING CLI")
    print("=" * 72)
    print("  • Reverse geocodes your address via OpenStreetMap Nominatim.")
    print("  • Computes trip distance, surge multipliers, and estimated fare.")
    print("=" * 72 + "\n")


def print_receipt(
    pickup: dict,
    dest: dict,
    distance_km: float,
    base_price: float,
    weather_name: str,
    weather_mult: float,
    traffic_name: str,
    traffic_mult: float,
    final_price: float,
):
    """Print an itemized trip summary and fare calculation."""

    # Calculate fare components for a clearer breakdown
    base_fare = distance_km * base_price

    weather_surcharge = base_fare * (weather_mult - 1)
    fare_after_weather = base_fare * weather_mult

    traffic_surcharge = fare_after_weather * (traffic_mult - 1)

    print("\n" + "=" * 72)
    print("                     TRIP SUMMARY & FARE RECEIPT                     ")
    print("=" * 72)

    print(f"📍 Pickup Location   : {pickup['display_name']}")
    print(f"   Coordinates       : {pickup['lat']:.5f}, {pickup['lon']:.5f}")

    print("-" * 72)

    print(f"🏁 Destination       : {dest['display_name']}")
    print(f"   Coordinates       : {dest['lat']:.5f}, {dest['lon']:.5f}")

    print("-" * 72)

    print(f"📏 Estimated Distance: {distance_km:.2f} km")
    print(f"💵 Base Rate         : RM {base_price:.2f} / km")
    print(f"🌦️ Weather Factor   : {weather_name} ({weather_mult:.2f}x)")
    print(f"🚦 Traffic Factor   : {traffic_name} ({traffic_mult:.2f}x)")

    print("-" * 72)

    print("                     FARE BREAKDOWN")
    print("-" * 72)

    print(f"Base Fare           : RM {base_fare:.2f}")
    print(f"Weather Surcharge   : RM {weather_surcharge:.2f}")
    print(f"Traffic Surcharge   : RM {traffic_surcharge:.2f}")

    print("-" * 72)

    print("Fare Formula: Distance * Base Price * Weather Multiplier * Traffic Multiplier")

    print(
        f"Calculation : {distance_km:.2f} km * RM {base_price:.2f} "
        f"* {weather_mult:.2f} * {traffic_mult:.2f}"
    )

    print("=" * 72)
    print(f"💰 ESTIMATED FARE   : RM {final_price:.2f}")
    print("=" * 72 + "\n")

def main():
    try:
        print_banner()

        # Step 1: Select state
        state = questionary.select(
            "Step 1: Select your State / Region for geocoding context:",
            choices=MALAYSIA_STATES,
            style=CUSTOM_STYLE,
        ).ask()

        if state is None:
            print("\nOperation cancelled.")
            sys.exit(0)

        print(f"Selected Region: {state}\n")

        # Allow the user to calculate multiple trips
        while True:

            # Step 2: Pickup location geocoding
            print("Step 2: Geocode Pickup Location")
            pickup_loc = prompt_location_search("Pickup", state)

            # Step 3: Destination location geocoding
            print("\nStep 3: Geocode Destination Location")
            dest_loc = prompt_location_search("Destination", state)

            # Step 4: Weather condition
            print("\nStep 4: Weather Condition")
            weather_choice = questionary.select(
                "Select current weather condition:",
                choices=list(WEATHER_OPTIONS.keys()),
                style=CUSTOM_STYLE,
            ).ask()

            if weather_choice is None:
                print("\nOperation cancelled.")
                sys.exit(0)

            weather_info = WEATHER_OPTIONS[weather_choice]

            # Step 5: Traffic condition
            print("\nStep 5: Traffic Condition")
            traffic_choice = questionary.select(
                "Select current traffic condition:",
                choices=list(TRAFFIC_OPTIONS.keys()),
                style=CUSTOM_STYLE,
            ).ask()

            if traffic_choice is None:
                print("\nOperation cancelled.")
                sys.exit(0)

            traffic_info = TRAFFIC_OPTIONS[traffic_choice]

            # Step 6: Calculation
            distance_km = haversine_distance(
                pickup_loc["lat"],
                pickup_loc["lon"],
                dest_loc["lat"],
                dest_loc["lon"],
            )

            final_price = (
                distance_km
                * BASE_PRICE_PER_KM
                * weather_info["multiplier"]
                * traffic_info["multiplier"]
            )

            # Step 7: Display summary receipt
            print_receipt(
                pickup=pickup_loc,
                dest=dest_loc,
                distance_km=distance_km,
                base_price=BASE_PRICE_PER_KM,
                weather_name=weather_info["name"],
                weather_mult=weather_info["multiplier"],
                traffic_name=traffic_info["name"],
                traffic_mult=traffic_info["multiplier"],
                final_price=final_price,
            )

            # Step 8: Ask whether to calculate another trip
            calculate_again = questionary.confirm(
                "Would you like to calculate another trip?",
                default=True,
                style=CUSTOM_STYLE,
            ).ask()

            if not calculate_again:
                print(
                    "\nThank you for using the Grab Fare Estimator. Goodbye!"
                )
                break

            print("\n" + "-" * 72)
            print("                     NEW TRIP CALCULATION")
            print("-" * 72 + "\n")

    except KeyboardInterrupt:
        print("\n[!] Program interrupted. Goodbye!")
        sys.exit(0)

if __name__ == "__main__":
    main()
