"""Neewer GL25B Home Assistant integration."""

from __future__ import annotations

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant

from .const import DOMAIN
from .hid_controller import NeewerGL25BController

PLATFORMS: list[Platform] = [Platform.LIGHT]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Neewer GL25B from a config entry."""
    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = NeewerGL25BController()

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a Neewer GL25B config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)

    if unload_ok:
        controller: NeewerGL25BController = hass.data[DOMAIN].pop(entry.entry_id)
        await hass.async_add_executor_job(controller.disconnect)

    return unload_ok
