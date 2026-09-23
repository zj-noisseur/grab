"""
Basic Nominatim Geocoding CLI.
Step 1: Simple API integration using requests and standard input.
"""

import sys
import requests

NOMINATIM_URL = "https://nominatim.openstreetmap.org/search"
USER_AGENT = "GrabPricingCLI/1.0"


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


def main():
    print("=== Nominatim Geocoding Tester ===")
    location = input("Enter a location to geocode: ").strip()
    if not location:
        print("Empty location entered.")
        sys.exit(0)

    print(f"Searching Nominatim for '{location}'...")
    results = query_nominatim(location)
    if not results:
        print("No results found.")
        return

    top = results[0]
    print(f"\nMatched: {top.get('display_name')}")
    print(f"Coordinates: Latitude {top.get('lat')}, Longitude {top.get('lon')}")


if __name__ == "__main__":
    main()
