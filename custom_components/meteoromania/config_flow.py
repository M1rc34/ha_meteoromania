"""Config flow for Meteoromania Weather integration."""
from __future__ import annotations

import voluptuous as vol
from homeassistant.config_entries import ConfigFlow
from homeassistant.const import CONF_NAME
from homeassistant.data_entry_flow import FlowResult

from .const import DOMAIN, CITIES, CONF_CITY

class MeteoRomaniaConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Meteoromania Weather."""

    VERSION = 1

    async def async_step_user(self, user_input=None):
        """Handle the initial step."""
        errors = {}

        if user_input is not None:
            # Validate the input
            if user_input[CONF_CITY] in CITIES:
                return self.async_create_entry(
                    title=f"Meteoromania Weather - {user_input[CONF_CITY]}",
                    data={
                        CONF_CITY: user_input[CONF_CITY],
                    }
                )
            else:
                errors["base"] = "invalid_city"

        data_schema = vol.Schema({
            vol.Required(CONF_CITY): vol.In(CITIES)
        })

        return self.async_show_form(
            step_id="user",
            data_schema=data_schema,
            errors=errors
        )