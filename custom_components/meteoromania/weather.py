"""Weather platform for Meteoromania Weather integration."""
from __future__ import annotations

import logging
from datetime import datetime, timedelta

import aiohttp
import async_timeout

from homeassistant.components.weather import (
    WeatherEntity,
    WeatherEntityFeature,
    Forecast,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.typing import ConfigType
from homeassistant.util import dt as dt_util

from .const import DOMAIN, API_URL, CONF_CITY

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the Meteoromania weather platform."""
    city = config_entry.data[CONF_CITY]
    async_add_entities([MeteoRomaniaWeatherEntity(city)])

class MeteoRomaniaWeatherEntity(WeatherEntity):
    """Representation of a Meteoromania Weather entity."""

    _attr_has_entity_name = True
    _attr_supported_features = WeatherEntityFeature.FORECAST_DAILY
    _attr_attribution = "Data from Meteoromania.ro"

    def __init__(self, city: str) -> None:
        """Initialize the weather entity."""
        self._city = city
        self._weather_data = None

    @property
    def name(self) -> str:
        """Return the name of the entity."""
        return f"{self._city} Weather"

    @property
    def unique_id(self) -> str:
        """Return a unique identifier for this weather entity."""
        return f"{DOMAIN}_{self._city}"

    async def async_update(self) -> None:
        """Update weather data."""
        try:
            async with async_timeout.timeout(10):
                async with aiohttp.ClientSession() as session:
                    async with session.get(API_URL) as response:
                        data = await response.json()
                        
                        # Find city's forecast
                        for location in data.get('tara', {}).get('localitate', []):
                            if location['@attributes']['nume'] == self._city:
                                self._weather_data = location
                                break
        except Exception as err:
            _LOGGER.error(f"Error fetching weather data: {err}")
            self._weather_data = None

    @property
    def condition(self) -> str | None:
        """Return the current condition."""
        if not self._weather_data:
            return None
        
        # Map Romanian weather descriptions to Home Assistant conditions
        condition_map = {
            'CER TEMPORAR NOROS': 'cloudy',
            'CER PARTIAL NOROS': 'partlycloudy',
            'CER VARIABIL': 'partlycloudy',
            'CER MAI MULT NOROS': 'cloudy',
            'PLOAIE SLABA': 'rainy'
        }
        
        return condition_map.get(
            self._weather_data['prognoza'][0]['fenomen_descriere'], 
            'unknown'
        )

    @property
    def temperature(self) -> float | None:
        """Return the current temperature."""
        if not self._weather_data:
            return None
        
        try:
            return float(self._weather_data['prognoza'][0]['temp_max'])
        except (TypeError, IndexError):
            return None

    @property
    def temperature_unit(self) -> str:
        """Return the temperature unit."""
        return "°C"

    def get_forecast(self, forecast_type: str) -> list[Forecast] | None:
        """Return a forecast of temperature and condition."""
        if not self._weather_data or forecast_type != 'daily':
            return None

        forecasts = []
        for forecast in self._weather_data['prognoza']:
            try:
                date_str = forecast['@attributes']['data']
                forecasts.append({
                    'datetime': date_str,
                    'temperature': float(forecast['temp_max']),
                    'templow': float(forecast['temp_min']),
                    'condition': self._map_condition(forecast['fenomen_descriere'])
                })
            except (KeyError, TypeError):
                continue

        return forecasts

    def _map_condition(self, description: str) -> str:
        """Map Meteoromania description to Home Assistant condition."""
        condition_map = {
            'CER TEMPORAR NOROS': 'cloudy',
            'CER PARTIAL NOROS': 'partlycloudy',
            'CER VARIABIL': 'partlycloudy',
            'CER MAI MULT NOROS': 'cloudy',
            'PLOAIE SLABA': 'rainy'
        }
        return condition_map.get(description, 'unknown')