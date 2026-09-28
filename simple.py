import os
import questionary
import requests
from dotenv import load_dotenv

# Load Mapbox access token from .env file
load_dotenv()
MAPBOX_TOKEN = os.getenv("MAPBOX_ACCESS_TOKEN")

NOMINATIM_URL = "https://nominatim.openstreetmap.org/search"
HEADERS = {"User-Agent": "GrabPricingCLI/1.0 (terminal_fare_calculator)"}

base = 1  # Base rate per km

weather_multipliers = {
    1: 1.0,
    2: 1.1,
    3: 1.5,
}

traffic_multipliers = {
    1: 1.6,
    2: 1.2,
}


def search_place(query, label="location"):
    """Query Nominatim search API and let user select using questionary."""
    search_q = query.strip()
    if not search_q:
        return None, None, None

    # Restrict to Malaysia for accurate local results
    params = {
        "q": search_q,
        "format": "json",
        "countrycodes": "my",
        "limit": 5,
    }

    try:
        response = requests.get(NOMINATIM_URL, params=params, headers=HEADERS, timeout=10)
        results = response.json()

        # Fallback without country filter if nothing found locally
        if not results:
            params.pop("countrycodes", None)
            results = requests.get(NOMINATIM_URL, params=params, headers=HEADERS, timeout=10).json()

        if not results:
            print(f"No matching places found for '{query}'.")
            return None, None, None

        # Build dropdown options
        choices = [
            questionary.Choice(
                title=item.get("display_name", "")[:90],
                value=(float(item["lat"]), float(item["lon"]), item["display_name"]),
            )
            for item in results
        ]

        selected = questionary.select(
            f"Select matching {label}:",
            choices=choices,
        ).ask()

        if selected:
            lat, lon, name = selected
            return lat, lon, name
    except Exception as e:
        print(f"Error querying Nominatim: {e}")

    return None, None, None


def get_driving_distance(lon1, lat1, lon2, lat2):
    """Fetch driving road distance (km) and duration from Mapbox Directions API."""
    if not MAPBOX_TOKEN:
        print("[!] MAPBOX_ACCESS_TOKEN not found in .env file.")
        return None, None

    url = f"https://api.mapbox.com/directions/v5/mapbox/driving/{lon1},{lat1};{lon2},{lat2}"
    params = {
        "access_token": MAPBOX_TOKEN,
        "overview": "false",
    }
    try:
        response = requests.get(url, params=params).json()
        routes = response.get("routes", [])
        if routes:
            dist_km = routes[0]["distance"] / 1000.0       # meters -> km
            duration_mins = routes[0]["duration"] / 60.0   # seconds -> minutes
            return dist_km, f"{duration_mins:.0f} mins"
        else:
            print("[!] No driving route found.")
    except Exception as e:
        print(f"Error connecting to Mapbox Directions: {e}")
    return None, None


def fare(dist, duration, weather, traffic):
    total = dist * base * weather_multipliers[weather] * traffic_multipliers[traffic]
    print(f"\nEstimated Road Distance : {dist:.2f} km ({duration})")
    print(f"The trip fare is        : RM {total:.2f}\n")


while True:
    # 1. Location Inputs via Questionary Text + Nominatim Dropdown
    pickup = questionary.text("Enter pickup location:").ask()
    if not pickup:
        print("Exiting.")
        break

    lat1, lon1, addr1 = search_place(pickup, "pickup")
    if not lat1:
        print("Please try searching pickup again.\n")
        continue
    print(f"-> Selected Pickup: {addr1}\n")

    destination = questionary.text("Enter destination:").ask()
    if not destination:
        print("Exiting.")
        break

    lat2, lon2, addr2 = search_place(destination, "destination")
    if not lat2:
        print("Please try searching destination again.\n")
        continue
    print(f"-> Selected Destination: {addr2}\n")

    # 2. Road Distance via Mapbox Driving API (lon, lat)
    dist, duration = get_driving_distance(lon1, lat1, lon2, lat2)
    if dist is None:
        print("Could not compute driving route. Please try again.\n")
        continue

    # 3. Weather Selection via Questionary
    weather = questionary.select(
        "Select weather condition:",
        choices=[
            questionary.Choice("☀️ Sunny (1.0x)", value=1),
            questionary.Choice("☁️ Cloudy (1.1x)", value=2),
            questionary.Choice("⛈️ Storm (1.5x)", value=3),
        ],
    ).ask()
    if weather is None:
        break

    # 4. Traffic Selection via Questionary
    traffic = questionary.select(
        "Select traffic condition:",
        choices=[
            questionary.Choice("🔴 Peak hour (1.6x)", value=1),
            questionary.Choice("🟡 Normal (1.2x)", value=2),
        ],
    ).ask()
    if traffic is None:
        break

    # 5. Calculate and display fare
    fare(dist, duration, weather, traffic)

    # 6. Continuation Prompt via Questionary
    continue_trip = questionary.confirm("Do you wish to calculate another fare?", default=True).ask()
    if not continue_trip:
        print("Goodbye!")
        break
