"""Constants for the MeteoroMania integration."""

DOMAIN = "meteoromania"

PLATFORMS = ["weather"]

API_URL_FORECAST = "https://meteoromania.ro/wp-json/meteoapi/v2/prognoza-orase"
API_URL_CURRENT = "https://meteoromania.ro/wp-json/meteoapi/v2/starea-vremii"

CONDITION_MAP = {
    "001": "sunny",            # Clear sky
    "001-2": "partlycloudy",   # Partly cloudy
    "008": "fog",              # Foggy
    "202-2": "rainy",          # Light rain
    "18": "rainy",             # Rain (specific for "ploaie")
    # Add any additional mappings here
}