"""Config flow for Meteoromania integration."""
from __future__ import annotations

import logging
from typing import Any

import aiohttp
import voluptuous as vol
import xmltodict

from homeassistant.config_entries import ConfigFlow, ConfigFlowResult
from homeassistant.const import CONF_NAME
from homeassistant.helpers import selector
from homeassistant.exceptions import HomeAssistantError

from .const import DOMAIN, CONF_LOCATION

_LOGGER = logging.getLogger(__name__)

class MeteoRomaniaConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Meteoromania."""

    VERSION = 1

    async def _validate_location(self, location: str):
        """Validate the location by fetching data from the API."""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get("https://www.meteoromania.ro/wp-json/meteoapi/v2/prognoza-orase") as response:
                    if response.status != 200:
                        _LOGGER.error(f"API returned status code {response.status}")
                        raise HomeAssistantError(f"API returned status code {response.status}")
                    
                    xml_text = await response.text()
                    data = xmltodict.parse(xml_text)
                    
                    # Check if location exists (case-insensitive)
                    location_exists = any(
                        loc['@attributes']['nume'].upper() == location.upper() 
                        for loc in data['tara']['localitate']
                    )
                    
                    if not location_exists:
                        _LOGGER.error(f"Location {location} not found in available locations")
                        raise HomeAssistantError(f"Location {location} not found. Available locations: {', '.join(loc['@attributes']['nume'] for loc in data['tara']['localitate'])}")
                    
                    return True
        except aiohttp.ClientError as err:
            _LOGGER.error(f"Connection error: {err}")
            raise HomeAssistantError("Cannot connect to Meteoromania API") from err
        except xmltodict.ParsingInterrupted as err:
            _LOGGER.error(f"XML parsing error: {err}")
            raise HomeAssistantError("Error parsing XML response") from err
        except Exception as err:
            _LOGGER.error(f"Unexpected error: {err}")
            raise HomeAssistantError("Unexpected error occurred") from err

    async def async_step_user(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        """Handle the initial step."""
        errors: dict[str, str] = {}
        
        if user_input is not None:
            try:
                # Validate location
                location = user_input[CONF_LOCATION]
                await self._validate_location(location)
                
                return self.async_create_entry(
                    title=f"Meteoromania - {location}",
                    data={
                        CONF_LOCATION: location,
                        CONF_NAME: f"Meteoromania {location}"
                    }
                )
            except HomeAssistantError as err:
                errors['base'] = 'cannot_connect'
                _LOGGER.error(f"Configuration error: {err}")
        
        # Fetch available locations for potential user guidance
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get("https://www.meteoromania.ro/wp-json/meteoapi/v2/prognoza-orase") as response:
                    if response.status == 200:
                        xml_text = await response.text()
                        data = xmltodict.parse(xml_text)
                        available_locations = [loc['@attributes']['nome'] for loc in data['tara']['localitate']]
                        _LOGGER.info(f"Available locations: {available_locations}")
                    else:
                        available_locations = ["IASI", "BUCURESTI", "CLUJ-NAPOCA"]  # Fallback list
        except Exception:
            available_locations = ["IASI", "BUCURESTI", "CLUJ-NAPOCA"]  # Fallback list
        
        # Create form
        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema({
                vol.Required(CONF_LOCATION, default="IASI"): str
            }),
            errors=errors
        )

    async def async_step_import(self, config: dict[str, Any]) -> ConfigFlowResult:
        """Import a config entry."""
        return await self.async_step_user(config)