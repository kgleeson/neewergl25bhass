"""Light entity for the Neewer GL25B integration."""

from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.light import (
    ATTR_BRIGHTNESS,
    ATTR_COLOR_TEMP_KELVIN,
    ColorMode,
    LightEntity,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import (
    CONF_NAME,
    DEFAULT_BRIGHTNESS,
    DEFAULT_COLOR_TEMP_KELVIN,
    DEFAULT_NAME,
    DOMAIN,
    MAX_COLOR_TEMP_KELVIN,
    MIN_COLOR_TEMP_KELVIN,
)
from .hid_controller import PID, VID, NeewerGL25BController, NeewerGL25BError

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the Neewer GL25B light entity."""
    controller: NeewerGL25BController = hass.data[DOMAIN][entry.entry_id]
    name = entry.data.get(CONF_NAME, DEFAULT_NAME)
    async_add_entities([NeewerGL25BLight(hass, controller, name)])


class NeewerGL25BLight(LightEntity):
    """Representation of a Neewer GL25B light."""

    _attr_supported_color_modes = {ColorMode.COLOR_TEMP}
    _attr_color_mode = ColorMode.COLOR_TEMP
    _attr_min_color_temp_kelvin = MIN_COLOR_TEMP_KELVIN
    _attr_max_color_temp_kelvin = MAX_COLOR_TEMP_KELVIN
    _attr_assumed_state = True
    _attr_should_poll = True

    def __init__(
        self,
        hass: HomeAssistant,
        controller: NeewerGL25BController,
        name: str,
    ) -> None:
        """Initialize the Neewer GL25B light."""
        self.hass = hass
        self._controller = controller

        self._attr_name = name
        self._attr_unique_id = f"{DOMAIN}_{VID:04x}_{PID:04x}"
        self._attr_is_on = False
        self._attr_available = True
        self._attr_brightness = DEFAULT_BRIGHTNESS
        self._attr_color_temp_kelvin = DEFAULT_COLOR_TEMP_KELVIN
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, f"{VID:04x}:{PID:04x}")},
            manufacturer="Neewer",
            model="GL25B",
            name=DEFAULT_NAME,
        )

    async def async_update(self) -> None:
        """Refresh dongle availability."""
        self._attr_available = await self.hass.async_add_executor_job(
            self._controller.is_available
        )

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Turn on the light and apply requested state."""
        requested_brightness = kwargs.get(ATTR_BRIGHTNESS)
        requested_kelvin = kwargs.get(ATTR_COLOR_TEMP_KELVIN)

        target_brightness = (
            requested_brightness
            if requested_brightness is not None
            else self._attr_brightness
        )
        target_brightness = max(1, min(255, int(target_brightness)))

        target_kelvin = (
            requested_kelvin
            if requested_kelvin is not None
            else self._attr_color_temp_kelvin
        )
        target_kelvin = max(
            MIN_COLOR_TEMP_KELVIN, min(MAX_COLOR_TEMP_KELVIN, int(target_kelvin))
        )

        try:
            if requested_kelvin is not None and target_kelvin != self._attr_color_temp_kelvin:
                await self.hass.async_add_executor_job(
                    self._controller.set_kelvin, target_kelvin
                )

            if not self._attr_is_on or target_brightness != self._attr_brightness:
                await self.hass.async_add_executor_job(
                    self._controller.set_brightness,
                    self._ha_brightness_to_percent(target_brightness),
                )
        except NeewerGL25BError:
            _LOGGER.exception("Failed to turn on Neewer GL25B")
            self._attr_available = False
            self.async_write_ha_state()
            return

        self._attr_is_on = True
        self._attr_available = True
        self._attr_brightness = target_brightness
        self._attr_color_temp_kelvin = target_kelvin
        self.async_write_ha_state()

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Turn off the light by setting brightness to zero."""
        if not self._attr_is_on:
            return

        try:
            await self.hass.async_add_executor_job(self._controller.set_brightness, 0)
        except NeewerGL25BError:
            _LOGGER.exception("Failed to turn off Neewer GL25B")
            self._attr_available = False
            self.async_write_ha_state()
            return

        self._attr_is_on = False
        self._attr_available = True
        self.async_write_ha_state()

    @staticmethod
    def _ha_brightness_to_percent(brightness: int) -> int:
        """Convert Home Assistant brightness 1-255 to GL25B brightness 1-100."""
        return max(1, min(100, round((brightness / 255) * 100)))
