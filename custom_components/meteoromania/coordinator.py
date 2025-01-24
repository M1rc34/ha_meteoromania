"""Coordinator to fetch data from meteoromania.ro API."""

import asyncio
import logging
import aiohttp

from datetime import timedelta

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import API_URL

_LOGGER = logging.getLogger(__name__)

class MeteoroManiaCoordinator(DataUpdateCoordinator):
    """Class to manage fetching data from MeteoroMania API."""

    def __init__(self, hass: HomeAssistant, city: str) -> None:
        """Initialize."""
        self.hass = hass
        self.city = city

        # We'll refresh every 6 hours by default
        super().__init__(
            hass,
            _LOGGER,
            name="MeteoroManiaCoordinator",
            update_interval=timedelta(hours=6),
        )

    async def _async_update_data(self):
        """Fetch data from the meteoromania API and return the relevant city's data."""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(API_URL) as response:
                    if response.status != 200:
                        raise UpdateFailed(f"API error: {response.status}")
                    data = await response.json()

            # The structure is data["tara"]["localitate"] -> list of city entries
            # Each city entry: { "@attributes": {"nume": "Arad"}, "DataPrognozei": ..., "prognoza": [...] }
            # We must filter for the city name matching self.city
            # city attribute is data["@attributes"]["nume"]
            all_cities = data["tara"]["localitate"]
            result = None
            for city_data in all_cities:
                if city_data["@attributes"]["nume"].lower() == self.city.lower():
                    result = city_data
                    break

            if result is None:
                # We did not find the city in the response
                raise UpdateFailed(f"City {self.city} not found in API data.")

            return result

        except asyncio.TimeoutError as err:
            raise UpdateFailed("Timeout fetching meteoromania data") from err
        except Exception as err:
            raise UpdateFailed(f"Unexpected error: {err}") from err
