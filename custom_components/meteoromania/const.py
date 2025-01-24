"""Constants for the Meteoromania Weather integration."""

DOMAIN = "meteoromania"
NAME = "Meteoromania"
API_URL = "https://meteoromania.ro/wp-json/meteoapi/v2/prognoza-orase"

# Configuration keys
CONF_CITY = "city"

# List of available Romanian cities
CITIES = [
    "Arad", "Botosani", "Bucuresti", "Cluj-Napoca", "Constanta", 
    "Craiova", "Iasi", "Rm. Valcea", "Sibiu", "Sulina"
]