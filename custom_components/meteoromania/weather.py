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
        self._humidity = None
        self._pressure = None
        self._wind_speed = None
        self._forecast: List[Forecast] = []

    @property
    def native_temperature(self):
        """Return the current temperature."""
        return self._temperature

    @property
    def condition(self):
        """Return the current weather condition."""
        return self._condition

    @property
    def humidity(self):
        """Return the current humidity."""
        return self._humidity

    @property
    def native_pressure(self):
        """Return the current air pressure."""
        return self._pressure

    @property
    def native_wind_speed(self):
        """Return the current wind speed."""
        return self._wind_speed

    async def async_forecast_daily(self) -> list[Forecast] | None:
        """Return the daily forecast."""
        return self._forecast

    def update_from_latest_data(self):
        """Parse the data from the coordinator and update internal state."""
        # Update current weather
        if self._coordinator.current_data:
            current = self._coordinator.current_data["properties"]
            self._temperature = float(current.get("tempe", 0))
            self._condition = CONDITION_MAP.get(current.get("icon", ""), "cloudy")
            self._humidity = current.get("umezeala", None)
            self._pressure = float(current.get("presiunetext", "0").split()[0])
            self._wind_speed = float(current.get("vant", "0").split()[0])
        else:
            _LOGGER.warning("No current weather data available to update entity")
            self._temperature = None
            self._condition = None
            self._humidity = None
            self._pressure = None
            self._wind_speed = None

        # Update forecast
        if self._coordinator.forecast_data:
            forecast_data = self._coordinator.forecast_data.get("prognoza", [])
            forecasts: list[Forecast] = []
            for day_data in forecast_data:
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
                        "datetime": f"{date}T00:00:00",
                        "condition": cond,
                        "native_temperature": temp_max,
                        "native_templow": temp_min,
                    }
                )

            self._forecast = forecasts
        else:
            _LOGGER.warning("No forecast data available to update entity")
            self._forecast = None

    def _update_weather_and_notify(self):
        """Update weather and notify listeners."""
        self.update_from_latest_data()
        self.async_update_listeners()
