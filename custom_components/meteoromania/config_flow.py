"""Config flow for Meteoromania integration."""
from __future__ import annotations

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

    VERSION = 1

    async def async_step_user(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        """Handle the initial step."""
        errors: dict[str, str] = {}
        
        if user_input is not None:
            # Validate input
            location = user_input[CONF_LOCATION]
            
            # Optional: Add validation logic to check if location is valid
            return self.async_create_entry(
                title=f"Meteoromania - {location}",
                data={
                    CONF_LOCATION: location,
                    CONF_NAME: f"Meteoromania {location}"
                }
            )
        
        # Create form
        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema({
                vol.Required(CONF_LOCATION, default="IASI"): str
            }),
            errors=errors
        )