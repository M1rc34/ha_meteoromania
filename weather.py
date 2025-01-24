"""Weather platform for Meteoromania integration."""
from __future__ import annotations

from homeassistant.components.weather import (
    Forecast,
    WeatherEntity,
    WeatherEntityFeature,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceEntryType
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.typing import ConfigType, DiscoveryInfoType
from homeassistant.config_entries import ConfigEntry

from .const import DOMAIN
from datetime import datetime, timedelta

async def async_setup_entry(
    hass: HomeAssistant, 
    config_entry: ConfigEntry, 
    async_add_entities: AddEntitiesCallback
) -> None:
    """Set up the weather platform."""
    coordinator = hass.data[DOMAIN][config_entry.entry_id]
    async_add_entities([MeteoRomaniaWeather(coordinator, config_entry)])

class MeteoRomaniaWeather(WeatherEntity):
    """Representation of a weather entity for Meteoromania."""

    def __init__(self, coordinator, config_entry):
        """Initialize the weather entity."""
        self._coordinator = coordinator
        self._config_entry = config_entry
        self._attr_unique_id = f"{DOMAIN}_{config_entry.data['location']}"
        self._attr_name = f"Meteoromania {config_entry.data['location']}"

    @property
    def should_poll(self) -> bool:
        """No need to poll. Coordinator handles updates."""
        return False

    @property
    def available(self) -> bool:
        """Return if weather data is available."""
        return self._coordinator.last_update_success

    @property
    def forecast(self) -> list[Forecast] | None:
        """Return the forecast."""
        return self._coordinator.data

    async def async_added_to_hass(self) -> None:
        """When entity is added to hass."""
        await super().async_added_to_hass()
        self.async_on_remove(
            self._coordinator.async_add_listener(self.async_write_ha_state)
        )

    async def async_update(self) -> None:
        """Update the entity."""
        await self._coordinator.async_request_refresh()