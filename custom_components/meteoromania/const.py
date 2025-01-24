"""Constants for the MeteoroMania integration."""

DOMAIN = "meteoromania"

PLATFORMS = ["weather"]

API_URL = "https://meteoromania.ro/wp-json/meteoapi/v2/prognoza-orase"

# Example condition mapping.
# You will likely want to improve or expand this to match real phenomena codes from
# 'fenomen_simbol' or 'fenomen_descriere' to Home Assistant's recognized weather conditions.
CONDITION_MAP = {
    "001": "sunny",           # CER VARIABIL
    "001-2": "partlycloudy",  # CER PARTIAL NOROS
    "008": "fog",             # CEATA
    "202-2": "rainy",         # PLOAIE SLABA
    # Add more as needed
}
