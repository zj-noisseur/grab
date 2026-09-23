import requests
import questionary
from prompt_toolkit.completion import Completer, Completion

class reverseGeoencode(Completer):
    def __init__(self):
        self.url = "https://nominatim.openstreetmap.org/search"
        self.headers = {
            "User-Agent": "FareEst/1.0"
        }

        def get_com