"""The Meteoromania integration."""
from __future__ import annotations

import logging
from datetime import timedelta
import async_timeout

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.update_coordinator import (
    DataUpdateCoordinator,
    UpdateFailed,
)
import xmltodict
import aiohttp

from .const import DOMAIN, CONF_LOCATION

_LOGGER = logging.getLogger(__name__)

PLATFORMS: list[str] = ["sensor", "weather"]
SCAN_INTERVAL = timedelta(hours=1)

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Meteoromania from a config entry."""
    location = entry.data[CONF_LOCATION]
    
    # Create coordinator
    coordinator = MeteoRomaniaDataUpdateCoordinator(hass, location)
    await coordinator.async_config_entry_first_refresh()

    # Setup platforms
    entry.async_on_unload(entry.add_update_listener(update_listener))
    
    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = coordinator
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    
    return True

async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)
    
    return unload_ok

async def update_listener(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Handle options update."""
    await hass.config_entries.async_reload(entry.entry_id)

class MeteoRomaniaDataUpdateCoordinator(DataUpdateCoordinator):
    """Class to manage fetching Meteoromania data."""

    def __init__(self, hass: HomeAssistant, location: str):
        """Initialize."""
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=SCAN_INTERVAL,
        )
        self.location = location.upper()  # Ensure uppercase for matching
        self.session = async_get_clientsession(hass)

    async def _async_update_data(self):
        """Update data via library."""
        try:
            async with async_timeout.timeout(10):
                url = "https://www.meteoromania.ro/wp-json/meteoapi/v2/prognoza-orase"
                async with self.session.get(url) as response:
                    response.raise_for_status()
                    xml_text = await response.text()
                    
                    # Convert XML to dict
                    data = xmltodict.parse(xml_text)
                    
                    return self._process_forecast_data(data)
        
        except (aiohttp.ClientError, xmltodict.ParsingInterrupted) as err:
            raise UpdateFailed(f"Error communicating with Meteoromania API: {err}") from err

    def _process_forecast_data(self, data):
        """Process raw data into usable forecast."""
        forecasts = []
        try:
            # Find the specific location's forecast
            for location in data['tara']['localitate']:
                if location['@attributes']['nume'].upper() == self.location:
                    prognoza_list = location['prognoza']
                    
                    # Ensure prognoza_list is a list
                    if not isinstance(prognoza_list, list):
                        prognoza_list = [prognoza_list]
                    
                    for prognoza in prognoza_list:
                        forecasts.append({
                            'datetime': prognoza['@attributes']['data'],
                            'temperature': float(prognoza['temp_max']),
                            'templow': float(prognoza['temp_min']),
                            'condition': self._map_condition(prognoza['fenomen_descriere']),
                        })
                    
                    return forecasts
            
            # If location not found
            _LOGGER.error(f"Location {self.location} not found in forecast data")
            return []
        
        except (KeyError, TypeError, ValueError) as err:
            _LOGGER.error(f"Error processing forecast data: {err}")
            return []

    def _map_condition(self, raw_condition):
        """Map Romanian weather descriptions to HA conditions."""
        condition_map = {
            'CER VARIABIL': 'partlycloudy',
            'CER PARTIAL NOROS': 'partlycloudy',
            'CER MAI MULT NOROS': 'cloudy',
            'NOROS': 'cloudy',
            'PLOAIE SLABA': 'rainy',
            'PLOAIE': 'rainy',
            'NINSOARE': 'snowy',
            'CEAȚĂ': 'fog',
            'CERATA': 'fog',
            'CER TEMPORAR NOROS, CEATA': 'fog',
            'VÂNT': 'windy'
        }
        return condition_map.get(raw_condition.upper(), 'unknown')