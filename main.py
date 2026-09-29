"""
Grab-Style Geocoding & Ride Fare Calculation CLI.

Features:
- State selection to contextualize address queries.
- Nominatim OpenStreetMap search API for geocoding human-readable addresses.
- Interactive location selection with search amendment.
- Recent location history.
- Weather and traffic multiplier adjustments.
- Distance calculation using the Haversine formula.
- Minimum fare rule.
- Detailed fare breakdown.
- Trip history.
- Repeat trip calculation.
"""

import sys
import math
import json
from datetime import datetime
from pathlib import Path

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

BASE_PRICE_PER_KM = 2.50
MINIMUM_FARE = 4.00

MAX_RECENT_LOCATIONS = 5
MAX_TRIP_HISTORY = 10

RECENT_LOCATIONS_FILE = (
    Path(__file__).resolve().parent / "recent_locations.json"
)

TRIP_HISTORY_FILE = (
    Path(__file__).resolve().parent / "trip_history.json"
)


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
    "☀️ Sunny (1.0x)": {
        "multiplier": 1.0,
        "name": "Sunny",
    },
    "☁️ Cloudy (1.1x)": {
        "multiplier": 1.1,
        "name": "Cloudy",
    },
    "⛈️ Storm (1.5x)": {
        "multiplier": 1.5,
        "name": "Storm",
    },
}


TRAFFIC_OPTIONS = {
    "🟢 Free-flowing (1.0x)": {
        "multiplier": 1.0,
        "name": "Free-flowing",
    },
    "🟡 Normal (1.2x)": {
        "multiplier": 1.2,
        "name": "Normal",
    },
    "🔴 Congested (1.6x)": {
        "multiplier": 1.6,
        "name": "Congested",
    },
}


def load_recent_locations() -> list[dict]:
    """Load saved recent locations."""

    if not RECENT_LOCATIONS_FILE.exists():
        return []

    try:
        with RECENT_LOCATIONS_FILE.open(
            "r",
            encoding="utf-8",
        ) as file:
            data = json.load(file)

        if isinstance(data, list):
            return data

    except (json.JSONDecodeError, OSError):
        print(
            "\n[!] Could not read recent locations."
        )

    return []


def save_recent_locations(
    locations: list[dict],
) -> None:
    """Save recent locations."""

    try:
        with RECENT_LOCATIONS_FILE.open(
            "w",
            encoding="utf-8",
        ) as file:
            json.dump(
                locations[:MAX_RECENT_LOCATIONS],
                file,
                indent=4,
                ensure_ascii=False,
            )

    except OSError as e:
        print(
            f"\n[!] Could not save recent locations: {e}"
        )


def add_recent_location(
    location: dict,
) -> None:
    """Add a selected location to recent history."""

    locations = load_recent_locations()

    locations = [
        saved_location
        for saved_location in locations
        if not (
            saved_location.get("lat") == location.get("lat")
            and saved_location.get("lon") == location.get("lon")
        )
    ]

    locations.insert(
        0,
        {
            "display_name": location["display_name"],
            "lat": location["lat"],
            "lon": location["lon"],
        },
    )

    save_recent_locations(locations)


def load_trip_history() -> list[dict]:
    """Load saved trip history."""

    if not TRIP_HISTORY_FILE.exists():
        return []

    try:
        with TRIP_HISTORY_FILE.open(
            "r",
            encoding="utf-8",
        ) as file:
            data = json.load(file)

        if isinstance(data, list):
            return data

    except (json.JSONDecodeError, OSError):
        print(
            "\n[!] Could not read trip history."
        )

    return []


def save_trip_history(
    history: list[dict],
) -> None:
    """Save trip history."""

    try:
        with TRIP_HISTORY_FILE.open(
            "w",
            encoding="utf-8",
        ) as file:
            json.dump(
                history[:MAX_TRIP_HISTORY],
                file,
                indent=4,
                ensure_ascii=False,
            )

    except OSError as e:
        print(
            f"\n[!] Could not save trip history: {e}"
        )


def add_trip_history(
    pickup: dict,
    destination: dict,
    distance_km: float,
    weather_name: str,
    traffic_name: str,
    final_price: float,
) -> None:
    """Save a completed trip to history."""

    history = load_trip_history()

    new_trip = {
        "timestamp": datetime.now().strftime(
            "%Y-%m-%d %H:%M"
        ),
        "pickup": pickup["display_name"],
        "destination": destination["display_name"],
        "distance_km": round(distance_km, 2),
        "weather": weather_name,
        "traffic": traffic_name,
        "fare": round(final_price, 2),
    }

    history.insert(
        0,
        new_trip,
    )

    save_trip_history(history)


def display_trip_history() -> None:
    """Display previous fare estimates."""

    history = load_trip_history()

    print("\n" + "=" * 72)
    print(
        "                         TRIP HISTORY"
    )
    print("=" * 72)

    if not history:
        print(
            "\nNo previous trips have been recorded yet."
        )

        print("=" * 72 + "\n")
        return

    for index, trip in enumerate(
        history,
        start=1,
    ):
        print(
            f"\n#{index}  {trip['timestamp']}"
        )

        print(
            f"📍 Pickup      : {trip['pickup']}"
        )

        print(
            f"🏁 Destination : {trip['destination']}"
        )

        print(
            f"📏 Distance    : "
            f"{trip['distance_km']:.2f} km"
        )

        print(
            f"🌦️ Weather    : "
            f"{trip['weather']}"
        )

        print(
            f"🚦 Traffic     : "
            f"{trip['traffic']}"
        )

        print(
            f"💰 Fare        : "
            f"RM {trip['fare']:.2f}"
        )

        print("-" * 72)

    input(
        "\nPress Enter to return to the main menu..."
    )


def haversine_distance(
    lat1: float,
    lon1: float,
    lat2: float,
    lon2: float,
) -> float:
    """Compute great-circle distance in kilometers."""

    r = 6371.0

    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)

    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lon2 - lon1)

    a = (
        math.sin(delta_phi / 2.0) ** 2
        + math.cos(phi1)
        * math.cos(phi2)
        * math.sin(delta_lambda / 2.0) ** 2
    )

    c = 2.0 * math.atan2(
        math.sqrt(a),
        math.sqrt(1.0 - a),
    )

    return r * c


def query_nominatim(
    query: str,
    state: str = None,
) -> list[dict]:
    """Query Nominatim search API."""

    search_q = query.strip()

    if state and state != "All / Other (Worldwide)":
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
        response = requests.get(
            NOMINATIM_URL,
            params=params,
            headers=headers,
            timeout=10,
        )

        response.raise_for_status()

        return response.json()

    except requests.RequestException as e:
        print(
            f"\n[!] Error connecting to Nominatim server: {e}"
        )

        return []


def prompt_location_search(
    label: str,
    state: str,
) -> dict:
    """Select a recent location or search for a new one."""

    recent_locations = load_recent_locations()

    if recent_locations:
        recent_choices = [
            "🔎 Search for a new location"
        ]

        recent_map = {}

        for index, location in enumerate(
            recent_locations,
            start=1,
        ):
            display_name = location["display_name"]

            short_name = (
                display_name
                if len(display_name) <= 80
                else display_name[:77] + "..."
            )

            choice = (
                f"🕘 {index}. {short_name}"
            )

            recent_choices.append(choice)

            recent_map[choice] = location

        recent_choices.append(
            "❌ Cancel"
        )

        selected_recent = questionary.select(
            f"{label} location:",
            choices=recent_choices,
            style=CUSTOM_STYLE,
        ).ask()

        if selected_recent is None:
            print("\nOperation cancelled.")
            sys.exit(0)

        if selected_recent == "❌ Cancel":
            print("\nOperation cancelled.")
            sys.exit(0)

        if selected_recent != (
            "🔎 Search for a new location"
        ):
            selected_location = recent_map[
                selected_recent
            ]

            print(
                f"✓ Using recent {label}: "
                f"{selected_location['display_name']} "
                f"[{selected_location['lat']:.5f}, "
                f"{selected_location['lon']:.5f}]"
            )

            add_recent_location(
                selected_location
            )

            return selected_location

    query = ""

    while True:
        default_query = query if query else ""

        query_input = questionary.text(
            f"Enter {label} location keyword/address:",
            default=default_query,
            style=CUSTOM_STYLE,
        ).ask()

        if query_input is None:
            print("\nOperation cancelled.")
            sys.exit(0)

        query = query_input.strip()

        if not query:
            print(
                "Please enter a non-empty search term."
            )
            continue

        print(
            f"🔎 Polling Nominatim server "
            f"for '{query}'..."
        )

        results = query_nominatim(
            query,
            state=state,
        )

        if not results:
            print(
                f"⚠️  No matching locations found "
                f"for '{query}'."
            )

            action = questionary.select(
                "How would you like to proceed?",
                choices=[
                    "✏️  Amend search query and try again",
                    "❌ Cancel",
                ],
                style=CUSTOM_STYLE,
            ).ask()

            if action == (
                "✏️  Amend search query and try again"
            ):
                continue

            print("\nExiting.")
            sys.exit(0)

        choices = []
        result_map = {}

        for index, item in enumerate(results):
            display_name = item.get(
                "display_name",
                "",
            )

            lat = float(
                item.get("lat", 0.0)
            )

            lon = float(
                item.get("lon", 0.0)
            )

            short_name = (
                display_name
                if len(display_name) <= 85
                else display_name[:82] + "..."
            )

            choice_label = (
                f"{index + 1}. "
                f"{short_name} "
                f"({lat:.4f}, {lon:.4f})"
            )

            choices.append(choice_label)

            result_map[choice_label] = {
                "display_name": display_name,
                "lat": lat,
                "lon": lon,
            }

        choices.append(
            "✏️  Amend query and search again"
        )

        choices.append(
            "❌ Cancel"
        )

        selected = questionary.select(
            f"Select matching {label} location:",
            choices=choices,
            style=CUSTOM_STYLE,
        ).ask()

        if selected is None:
            print("\nOperation cancelled.")
            sys.exit(0)

        if selected == "❌ Cancel":
            print("\nOperation cancelled.")
            sys.exit(0)

        if selected == (
            "✏️  Amend query and search again"
        ):
            continue

        selected_loc = result_map[selected]

        print(
            f"✓ Confirmed {label}: "
            f"{selected_loc['display_name']} "
            f"[{selected_loc['lat']:.5f}, "
            f"{selected_loc['lon']:.5f}]"
        )

        add_recent_location(
            selected_loc
        )

        return selected_loc


def print_banner():
    """Display program header."""

    print("=" * 72)
    print(
        "  🚗 GRAB FARE ESTIMATOR "
        "& NOMINATIM GEOCODING CLI"
    )
    print("=" * 72)

    print(
        "  • Reverse geocodes your address "
        "via OpenStreetMap Nominatim."
    )

    print(
        "  • Computes trip distance, surge "
        "multipliers, and estimated fare."
    )

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
    """Print an itemized trip summary."""

    base_fare = (
        distance_km * base_price
    )

    weather_surcharge = (
        base_fare * (weather_mult - 1)
    )

    fare_after_weather = (
        base_fare * weather_mult
    )

    traffic_surcharge = (
        fare_after_weather
        * (traffic_mult - 1)
    )

    print("\n" + "=" * 72)
    print(
        "                     TRIP SUMMARY & FARE RECEIPT"
    )
    print("=" * 72)

    print(
        f"📍 Pickup Location   : "
        f"{pickup['display_name']}"
    )

    print(
        f"   Coordinates       : "
        f"{pickup['lat']:.5f}, "
        f"{pickup['lon']:.5f}"
    )

    print("-" * 72)

    print(
        f"🏁 Destination       : "
        f"{dest['display_name']}"
    )

    print(
        f"   Coordinates       : "
        f"{dest['lat']:.5f}, "
        f"{dest['lon']:.5f}"
    )

    print("-" * 72)

    print(
        f"📏 Estimated Distance: "
        f"{distance_km:.2f} km"
    )

    print(
        f"💵 Base Rate         : "
        f"RM {base_price:.2f} / km"
    )

    print(
        f"🌦️ Weather Factor   : "
        f"{weather_name} ({weather_mult:.2f}x)"
    )

    print(
        f"🚦 Traffic Factor   : "
        f"{traffic_name} ({traffic_mult:.2f}x)"
    )

    print("-" * 72)

    print(
        "                     FARE BREAKDOWN"
    )

    print("-" * 72)

    print(
        f"Base Fare           : "
        f"RM {base_fare:.2f}"
    )

    print(
        f"Weather Surcharge   : "
        f"RM {weather_surcharge:.2f}"
    )

    print(
        f"Traffic Surcharge   : "
        f"RM {traffic_surcharge:.2f}"
    )

    print("-" * 72)

    print(
        "Fare Formula: Distance * Base Price * "
        "Weather Multiplier * Traffic Multiplier"
    )

    print(
        f"Calculation : "
        f"{distance_km:.2f} km * "
        f"RM {base_price:.2f} * "
        f"{weather_mult:.2f} * "
        f"{traffic_mult:.2f}"
    )

    print("=" * 72)

    print(
        f"💰 ESTIMATED FARE   : "
        f"RM {final_price:.2f}"
    )

    print("=" * 72 + "\n")


def calculate_trip(state: str) -> None:
    """Run one complete fare estimation."""

    # Step 2: Pickup location
    print(
        "Step 2: Geocode Pickup Location"
    )

    pickup_loc = prompt_location_search(
        "Pickup",
        state,
    )

    # Step 3: Destination location
    print(
        "\nStep 3: Geocode Destination Location"
    )

    dest_loc = prompt_location_search(
        "Destination",
        state,
    )

    # Step 4: Weather
    print(
        "\nStep 4: Weather Condition"
    )

    weather_choice = questionary.select(
        "Select current weather condition:",
        choices=list(
            WEATHER_OPTIONS.keys()
        ),
        style=CUSTOM_STYLE,
    ).ask()

    if weather_choice is None:
        print("\nOperation cancelled.")
        return

    weather_info = WEATHER_OPTIONS[
        weather_choice
    ]

    # Step 5: Traffic
    print(
        "\nStep 5: Traffic Condition"
    )

    traffic_choice = questionary.select(
        "Select current traffic condition:",
        choices=list(
            TRAFFIC_OPTIONS.keys()
        ),
        style=CUSTOM_STYLE,
    ).ask()

    if traffic_choice is None:
        print("\nOperation cancelled.")
        return

    traffic_info = TRAFFIC_OPTIONS[
        traffic_choice
    ]

    # Step 6: Calculate distance
    distance_km = haversine_distance(
        pickup_loc["lat"],
        pickup_loc["lon"],
        dest_loc["lat"],
        dest_loc["lon"],
    )

    calculated_price = (
        distance_km
        * BASE_PRICE_PER_KM
        * weather_info["multiplier"]
        * traffic_info["multiplier"]
    )

    final_price = max(
        calculated_price,
        MINIMUM_FARE,
    )

    if calculated_price < MINIMUM_FARE:
        print(
            f"\nℹ️ Minimum fare applied: "
            f"RM {MINIMUM_FARE:.2f}"
        )

    # Step 7: Receipt
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

    # Save completed trip
    add_trip_history(
        pickup=pickup_loc,
        destination=dest_loc,
        distance_km=distance_km,
        weather_name=weather_info["name"],
        traffic_name=traffic_info["name"],
        final_price=final_price,
    )


def main():
    try:
        print_banner()

        while True:

            # Main menu
            menu_choice = questionary.select(
                "What would you like to do?",
                choices=[
                    "🚗 Calculate fare",
                    "📜 View trip history",
                    "❌ Exit",
                ],
                style=CUSTOM_STYLE,
            ).ask()

            if menu_choice == "❌ Exit":
                print(
                    "\nThank you for using the "
                    "Grab Fare Estimator. Goodbye!"
                )
                break

            if menu_choice == "📜 View trip history":
                display_trip_history()
                continue

            # Step 1: Select state
            state = questionary.select(
                "Step 1: Select your State / Region for geocoding context:",
                choices=MALAYSIA_STATES,
                style=CUSTOM_STYLE,
            ).ask()

            if state is None:
                print("\nOperation cancelled.")
                continue

            print(
                f"Selected Region: {state}\n"
            )

            calculate_trip(state)

            # Ask about another trip
            calculate_again = questionary.confirm(
                "\nWould you like to calculate another trip?",
                default=True,
                style=CUSTOM_STYLE,
            ).ask()

            if not calculate_again:
                print(
                    "\nReturning to the main menu..."
                )

    except KeyboardInterrupt:
        print(
            "\n[!] Program interrupted. Goodbye!"
        )

        sys.exit(0)


if __name__ == "__main__":
    main()