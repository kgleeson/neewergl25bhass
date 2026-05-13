"""Config flow for the Neewer GL25B integration."""

from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError

from .const import CONF_NAME, DEFAULT_NAME, DOMAIN
from .hid_controller import PID, VID, NeewerGL25BController

_LOGGER = logging.getLogger(__name__)

STEP_USER_DATA_SCHEMA = vol.Schema(
    {
        vol.Optional(CONF_NAME, default=DEFAULT_NAME): str,
    }
)


async def validate_input(hass: HomeAssistant) -> None:
    """Validate that the Neewer GL25B dongle can be opened."""
    controller = NeewerGL25BController()
    try:
        available = await hass.async_add_executor_job(controller.connect)
        if not available:
            raise CannotConnect
    finally:
        await hass.async_add_executor_job(controller.disconnect)


class NeewerGL25BConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Neewer GL25B."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> config_entries.ConfigFlowResult:
        """Handle the initial step."""
        await self.async_set_unique_id(f"{VID:04x}:{PID:04x}")
        self._abort_if_unique_id_configured()

        errors: dict[str, str] = {}

        if user_input is not None:
            try:
                await validate_input(self.hass)
            except CannotConnect:
                errors["base"] = "cannot_connect"
            except Exception:  # noqa: BLE001
                _LOGGER.exception("Unexpected exception during Neewer GL25B setup")
                errors["base"] = "unknown"
            else:
                name = user_input.get(CONF_NAME, DEFAULT_NAME)
                return self.async_create_entry(title=name, data={CONF_NAME: name})

        return self.async_show_form(
            step_id="user",
            data_schema=STEP_USER_DATA_SCHEMA,
            errors=errors,
        )


class CannotConnect(HomeAssistantError):
    """Error to indicate the dongle cannot be opened."""
