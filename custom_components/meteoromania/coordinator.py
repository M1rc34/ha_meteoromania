import logging
import aiohttp
from datetime import timedelta

from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import API_URL_FORECAST, API_URL_CURRENT, DOMAIN

_LOGGER = logging.getLogger(__name__)

class MeteoroManiaCoordinator(DataUpdateCoordinator):
    """Class to manage fetching data from the MeteoroMania API."""
    
    def __init__(self, hass, city):
        """Initialize the coordinator."""
        self.city = city
        self.forecast_data = None
        self.current_data = None

        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=timedelta(minutes=30),
        )

    # Normalize city names for comparison
    def normalize_city_name(city_name: str) -> str:
        """Normalize city names to lowercase for consistent comparison."""
        return city_name.strip().lower()

    async def _async_update_data(self):
        """Fetch data from the MeteoroMania API."""
        async with aiohttp.ClientSession() as session:
            try:
                # Fetch forecast data
                async with session.get(API_URL_FORECAST) as response:
                    if response.status != 200:
                        raise UpdateFailed(f"Error fetching forecast: {response.status}")
                    forecast_data = await response.json()

                # Fetch current weather data
                async with session.get(API_URL_CURRENT) as response:
                    if response.status != 200:
                        raise UpdateFailed(f"Error fetching current weather: {response.status}")
                    current_data = await response.json()

                # Find relevant data for the city
                normalized_city = self.normalize_city_name(self.city)
                forecast_city = next(
                    (
                        city
                        for city in forecast_data["tara"]["localitate"]
                        if self.normalize_city_name(city["@attributes"]["nume"]) == normalized_city
                    ),
                    None,
                )
                current_city = next(
                    (
                        feature
                        for feature in current_data["features"]
                        if self.normalize_city_name(feature["properties"]["nume"]) == normalized_city
                    ),
                    None,
                )

                if not forecast_city:
                    _LOGGER.warning(f"No forecast data available for city: {self.city}")
                if not current_city:
                    _LOGGER.warning(f"No current weather data available for city: {self.city}")

                self.forecast_data = forecast_city
                self.current_data = current_city
            except Exception as err:
                raise UpdateFailed(f"Unexpected error: {err}")