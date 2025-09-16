"""Options flow for DaVinci integration."""

from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol

from homeassistant import config_entries

from .const import BLOCK_GROUP

_LOGGER = logging.getLogger(__name__)

class DaVinciOptionsFlowHandler(config_entries.OptionsFlow):
    """Handle DaVinci options."""

    def __init__(self, config_entry: config_entries.ConfigEntry) -> None:
        """Initialize DaVinci options flow."""
        self.config_entry = config_entry
        self.block_group = self.config_entry.data[BLOCK_GROUP]
        self.new_data = dict(self.config_entry.data)

    async def async_step_init(self, user_input: dict[str, Any] | None = None):
        """Manage the DaVinci options."""
        if user_input is not None:
            self.new_data[BLOCK_GROUP] = user_input[BLOCK_GROUP]

            self.hass.config_entries.async_update_entry(self.config_entry, data=self.new_data)

            return self.async_create_entry(data=user_input)

        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema({
                vol.Optional(BLOCK_GROUP, default=self.block_group): vol.In({0: "All", 1: "Group 1", 2: "Group 2"})
            })
        )
