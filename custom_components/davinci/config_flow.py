"""Config flow for DaVinci integration."""

from __future__ import annotations

import logging
from typing import Any

import aiohttp
import voluptuous as vol

from homeassistant import config_entries
from homeassistant.data_entry_flow import FlowResult

from .const import DOMAIN, HOST, PASS, USER
from .sensor import async_get_davinci_data

_LOGGER = logging.getLogger(__name__)


class DaVinciConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for DaVinci."""

    VERSION = 1

    async def async_step_user(self, user_input: dict[str, Any] | None = None) -> FlowResult:
        """Handle the initial step."""
        if self._async_current_entries():
            return self.async_abort(reason="You already have a DaVinci Timetable Setup!")

        if user_input is not None:
            try:
                await async_get_davinci_data(user_input[HOST], user_input[USER], user_input[PASS])
                return self.async_create_entry(title="DaVinci Integration", data=user_input)
            except aiohttp.ClientResponseError as err:
                if err.status == 900:
                    _LOGGER.debug("Incorrect Username or Password!")
                    return self.async_abort(reason="Incorrect Username or Password!", )
                _LOGGER.debug("HTTP error connecting to DaVinci server: %s", err)
                return self.async_abort(reason=f"HTTP error connecting to DaVinci server: {err}")
            except (aiohttp.ClientError, TimeoutError):
                _LOGGER.debug("Connection to DaVinci Server Timed out! ", user_input[HOST])  # noqa: PLE1205
                return self.async_abort(reason=f"Connection to DaVinci Server Timed out! {user_input[HOST]}")
            except Exception:
                _LOGGER.exception("Unexpected error occurred")
                return self.async_abort(reason="Unexpected error occurred")

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema({
                vol.Required(HOST): str,
                vol.Required(USER): str,
                vol.Required(PASS): str,
            }),
        )
