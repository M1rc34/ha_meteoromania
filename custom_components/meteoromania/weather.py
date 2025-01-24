"""Weather platform for the MeteoroMania integration."""
from __future__ import annotations

import logging
from typing import List

from homeassistant.components.weather import (
    WeatherEntity,
    WeatherEntityFeature,
    Forecast,
)
from homeassistant.const import UnitOfTemperature
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
    _attr_native_temperature_unit = UnitOfTemperature.CELSIUS

    def __init__(self, coordinator: MeteoroManiaCoordinator, city: str):
        """Initialize the entity."""
        self._coordinator = coordinator
        self._city = city
        self._attr_name = city
        self._unsub_coordinator_update = None
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

    async def async_forecast_daily(self) -> list[Forecast] | None:
        """Return the daily forecast."""
        return self._forecast

    async def async_added_to_hass(self):
        """When entity is added to hass."""
        self._unsub_coordinator_update = self._coordinator.async_add_listener(self._update_weather_and_notify)
        await super().async_added_to_hass()

    async def async_will_remove_from_hass(self):
        """When entity is about to be removed."""
        if self._unsub_coordinator_update:
            self._unsub_coordinator_update()
            self._unsub_coordinator_update = None
        await super().async_will_remove_from_hass()

    @property
    def available(self) -> bool:
        return self._coordinator.last_update_success

    def _update_weather_and_notify(self):
        """Update weather and notify listeners."""
        self.update_from_latest_data()
        self.async_update_listeners()  # Notify listeners when forecast updates

    def update_from_latest_data(self):
        """Parse the data from the coordinator and update internal state."""
        data = self._coordinator.data
        prognoza = data.get("prognoza", [])
        if not prognoza:
            return

        today = prognoza[0]
        t_min = float(today.get("temp_min", 0))
        t_max = float(today.get("temp_max", 0))
        temp = (t_min + t_max) / 2.0
        self._temperature = round(temp, 1)

        fenomen_simbol = today.get("fenomen_simbol", "")
        self._condition = CONDITION_MAP.get(fenomen_simbol, "cloudy")

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
                    "datetime": f"{date}T00:00:00",  # Ensure RFC 3339 format
                    "condition": cond,
                    "native_temperature": temp_max,   # Daily high
                    "native_templow": temp_min,      # Daily low
                }
            )

        self._forecast = forecasts
        _LOGGER.debug("Built forecast data: %s", self._forecast)

    async def async_update(self):
        """Request coordinator refresh."""
        await self._coordinator.async_request_refresh()

    def async_write_ha_state(self):
        """Called when coordinator data is updated."""
        self.update_from_latest_data()
        super().async_write_ha_state()

    @property
    def extra_state_attributes(self):
        """Extra attributes."""
        data = self._coordinator.data
        return {
            "DataPrognozei": data.get("DataPrognozei"),
        }
