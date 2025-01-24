"""Config flow for Meteoromania integration."""
from __future__ import annotations

import requests
import logging
from typing import Any

import voluptuous as vol
from homeassistant.config_entries import ConfigFlow, ConfigFlowResult
from homeassistant.const import CONF_NAME
from homeassistant.helpers import selector

from .const import DOMAIN, CONF_LOCATION

_LOGGER = logging.getLogger(__name__)

class MeteoRomaniaConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Meteoromania."""

    VERSION = 2

    async def async_step_user(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        """Handle the initial step."""
        errors: dict[str, str] = {}
        
        if user_input is not None:
            # Validate location
            location = user_input[CONF_LOCATION]
            
            try:
                # Fetch the XML and check if location exists
                async with aiohttp.ClientSession() as session:
                    async with session.get("https://www.meteoromania.ro/wp-json/meteoapi/v2/prognoza-orase") as response:
                        xml_text = await response.text()
                        data = xmltodict.parse(xml_text)
                        
                        # Check if location exists (case-insensitive)
                        location_exists = any(
                            loc['@attributes']['nume'].upper() == location.upper() 
                            for loc in data['tara']['localitate']
                        )
                        
                        if not location_exists:
                            errors['base'] = 'invalid_location'
                        else:
                            return self.async_create_entry(
                                title=f"Meteoromania - {location}",
                                data={
                                    CONF_LOCATION: location,
                                    CONF_NAME: f"Meteoromania {location}"
                                }
                            )
            except Exception as err:
                _LOGGER.error(f"Error validating location: {err}")
                errors['base'] = 'cannot_connect'
        
        # Create form
        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema({
                vol.Required(CONF_LOCATION, default="IASI"): str
            }),
            errors=errors
        )