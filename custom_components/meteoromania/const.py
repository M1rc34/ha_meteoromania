"""Constants for the MeteoroMania integration."""

DOMAIN = "meteoromania"

PLATFORMS = ["weather"]

API_URL_FORECAST = "https://meteoromania.ro/wp-json/meteoapi/v2/prognoza-orase"
API_URL_CURRENT = "https://meteoromania.ro/wp-json/meteoapi/v2/starea-vremii"

CONDITION_MAP = {
    "001": "sunny",
    "001-2": "partlycloudy",
    "008": "fog",
    "202-2": "rainy",
    # Add additional mappings as needed
}
