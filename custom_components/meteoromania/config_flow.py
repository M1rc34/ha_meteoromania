"""Config flow for MeteoroMania integration."""
import logging
import aiohttp
import asyncio

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResult

from .const import DOMAIN, API_URL

_LOGGER = logging.getLogger(__name__)

async def fetch_available_cities(hass: HomeAssistant) -> list[str]:
    """Fetch the list of all available cities from the meteoromania API."""
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(API_URL) as resp:
                if resp.status != 200:
                    _LOGGER.warning("Failed to fetch city list, status: %s", resp.status)
                    return []
                data = await resp.json()
        return [item["@attributes"]["nume"] for item in data["tara"]["localitate"]]
    except asyncio.TimeoutError:
        _LOGGER.warning("Timeout while fetching city list from meteoromania.")
        return []
    except Exception as ex:
        _LOGGER.warning("Error fetching city list from meteoromania: %s", ex)
        return []


class MeteoroManiaConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for MeteoroMania."""

    VERSION = 1

    async def async_step_user(self, user_input=None) -> FlowResult:
        """Handle the initial step."""
        errors = {}

        if user_input is not None:
            city = user_input["city"]
            # We create an entry right away
            await self.async_set_unique_id(city.lower())
            self._abort_if_unique_id_configured()

            return self.async_create_entry(title=city, data={"city": city})

        # If no user_input, present form
        all_cities = await fetch_available_cities(self.hass)
        if not all_cities:
            # fallback to manual text input if we cannot fetch anything
            schema = vol.Schema({vol.Required("city"): str})
        else:
            # let user select from the dropdown
            all_cities.sort()
            schema = vol.Schema({vol.Required("city"): vol.In(all_cities)})

        return self.async_show_form(
            step_id="user",
            data_schema=schema,
            errors=errors
        )
