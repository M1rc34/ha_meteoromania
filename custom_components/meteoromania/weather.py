"""Weather platform for the MeteoroMania integration."""
from __future__ import annotations

import logging
from typing import List

from homeassistant.components.weather import (
    WeatherEntity,
    WeatherEntityFeature,
    Forecast,
)
from homeassistant.const import TEMP_CELSIUS
from homeassistant.core import HomeAssistant

from .const import DOMAIN, CONDITION_MAP
from .coordinator import MeteoroManiaCoordinator

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass: HomeAssistant, entry, async_add_entities):
    """Set up the MeteoroMania weather entity."""
    coordinator: MeteoroManiaCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([MeteoroManiaWeather(coordinator, entry.data["city"])])


class MeteoroManiaWeather(WeatherEntity):
    """Representation of the weather entity for a chosen city."""

    _attr_has_entity_name = True
    _attr_attribution = "Data provided by meteoromania.ro"
    _attr_supported_features = WeatherEntityFeature.FORECAST_DAILY
    _attr_native_temperature_unit = TEMP_CELSIUS

    def __init__(self, coordinator: MeteoroManiaCoordinator, city: str):
        """Initialize the entity."""
        self._coordinator = coordinator
        self._city = city
        # This name will show in the frontend. 
        # If you want it to be city-specific, something like f"Weather {city}"
        self._attr_name = city
        self._attr_unique_id = f"meteoromania_{city.lower()}"
        self._condition = None
        self._temperature = None
        self._forecast: List[Forecast] = []

    @property
    def should_poll(self) -> bool:
        """Disable polling because we use the coordinator."""
        return False

    @property
    def native_temperature(self):
        """Return the temperature for the 'current' day (approx)."""
        return self._temperature

    @property
    def condition(self):
        """Return the weather condition."""
        return self._condition

    @property
    def forecast(self) -> list[Forecast] | None:
        """Return the daily forecast array."""
        return self._forecast

    async def async_added_to_hass(self):
        """When entity is added to hass."""
        self._coordinator.async_add_listener(self.async_write_ha_state)
        await super().async_added_to_hass()

    async def async_will_remove_from_hass(self):
        """When entity is about to be removed."""
        self._coordinator.async_remove_listener(self.async_write_ha_state)
        await super().async_will_remove_from_hass()

    @property
    def available(self) -> bool:
        """Return if entity is available."""
        return not self._coordinator.last_update_failed

    def update_from_latest_data(self):
        """Parse the data from the coordinator and update internal state."""
        data = self._coordinator.data
        # `data` is the dictionary for a single city:
        # {
        #   "@attributes": {"nume": "Bucuresti"},
        #   "DataPrognozei": "2025-01-24",
        #   "prognoza": [
        #       {
        #         "@attributes": { "data":"2025-01-25"},
        #         "temp_min":"4",
        #         "temp_max":"11",
        #         "fenomen_descriere":"CER VARIABIL",
        #         "fenomen_simbol":"001",
        #         ...
        #       }, ...
        #    ]
        # }
        prognoza = data.get("prognoza", [])
        if not prognoza:
            return

        # We'll treat the first item in `prognoza` as "today" (i.e. current).
        today = prognoza[0]
        # Some integrators average min and max or pick max as "current" temperature.
        # We'll choose to do a midpoint for example:
        t_min = float(today.get("temp_min", 0))
        t_max = float(today.get("temp_max", 0))
        temp = (t_min + t_max) / 2.0
        self._temperature = round(temp, 1)

        fenomen_simbol = today.get("fenomen_simbol", "")
        # Map phenomenon symbol to an internal condition
        self._condition = CONDITION_MAP.get(fenomen_simbol, "cloudy")

        # Build the forecast for all days (including day 1)
        forecasts: list[Forecast] = []
        for day_data in prognoza:
            attributes = day_data.get("@attributes", {})
            date = attributes.get("data")
            if not date:
                continue

            temp_min = float(day_data.get("temp_min", 0))
            temp_max = float(day_data.get("temp_max", 0))
            fenomen_code = day_data.get("fenomen_simbol", "")
            cond = CONDITION_MAP.get(fenomen_code, "cloudy")

            forecasts.append(
                {
                    "datetime": date,
                    "condition": cond,
                    "temperature": temp_max,       # daily high
                    "templow": temp_min,           # daily low
                }
            )

        self._forecast = forecasts

    async def async_update(self):
        """Update the entity by asking the coordinator for new data."""
        await self._coordinator.async_request_refresh()

    def async_write_ha_state(self):
        """Call when coordinator data is updated."""
        self.update_from_latest_data()
        super().async_write_ha_state()

    @property
    def extra_state_attributes(self):
        """Add any additional attributes you want."""
        data = self._coordinator.data
        return {
            "DataPrognozei": data.get("DataPrognozei"),
        }
