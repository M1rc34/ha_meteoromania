"""Sensor platform for Meteoromania integration."""
from __future__ import annotations

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.typing import StateType
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN

async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback
) -> None:
    """Set up Meteoromania sensors."""
    coordinator = hass.data[DOMAIN][config_entry.entry_id]
    
    # Create sensors based on forecast data
    sensors = [
        MeteoromaniaTempMaxSensor(coordinator, config_entry),
        MeteoromaniaTempMinSensor(coordinator, config_entry),
        MeteoromaniaCategorySensor(coordinator, config_entry)
    ]
    
    async_add_entities(sensors)

class BaseMeteoromaniaSensor(CoordinatorEntity, SensorEntity):
    """Base sensor for Meteoromania."""

    def __init__(self, coordinator, config_entry):
        """Initialize the sensor."""
        super().__init__(coordinator)
        self._config_entry = config_entry
        self._attr_unique_id = f"{DOMAIN}_{config_entry.data['location']}_{self._sensor_type}"

    @property
    def available(self) -> bool:
        """Return if weather data is available."""
        return self.coordinator.last_update_success and self.coordinator.data

    def _get_today_forecast(self):
        """Get today's forecast data."""
        from datetime import date
        today = date.today().isoformat()
        
        if not self.coordinator.data:
            return None
        
        for forecast in self.coordinator.data:
            if forecast['datetime'] == today:
                return forecast
        
        return None

class MeteoromaniaTempMaxSensor(BaseMeteoromaniaSensor):
    """Maximum temperature sensor."""
    
    _sensor_type = "temp_max"

    @property
    def name(self) -> str:
        """Sensor name."""
        return f"Meteoromania {self._config_entry.data['location']} Max Temp"

    @property
    def state(self) -> StateType:
        """Return sensor state."""
        forecast = self._get_today_forecast()
        return forecast['temperature'] if forecast else None

    @property
    def device_class(self) -> SensorDeviceClass:
        """Return device class."""
        return SensorDeviceClass.TEMPERATURE

    @property
    def unit_of_measurement(self) -> str:
        """Return unit of measurement."""
        return "°C"

class MeteoromaniaTempMinSensor(BaseMeteoromaniaSensor):
    """Minimum temperature sensor."""
    
    _sensor_type = "temp_min"

    @property
    def name(self) -> str:
        """Sensor name."""
        return f"Meteoromania {self._config_entry.data['location']} Min Temp"

    @property
    def state(self) -> StateType:
        """Return sensor state."""
        forecast = self._get_today_forecast()
        return forecast['templow'] if forecast else None

    @property
    def device_class(self) -> SensorDeviceClass:
        """Return device class."""
        return SensorDeviceClass.TEMPERATURE

    @property
    def unit_of_measurement(self) -> str:
        """Return unit of measurement."""
        return "°C"

class MeteoromaniaCategorySensor(BaseMeteoromaniaSensor):
    """Weather category sensor."""
    
    _sensor_type = "category"

    @property
    def name(self) -> str:
        """Sensor name."""
        return f"Meteoromania {self._config_entry.data['location']} Weather Category"

    @property
    def state(self) -> StateType:
        """Return sensor state."""
        forecast = self._get_today_forecast()
        return forecast['condition'] if forecast else None