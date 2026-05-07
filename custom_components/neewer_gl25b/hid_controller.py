"""USB HID controller for the Neewer GL25B dongle."""

from __future__ import annotations

import logging
import time
from typing import Any

try:
    import hid
except ImportError:  # pragma: no cover - Home Assistant installs this from manifest.json.
    hid = None  # type: ignore[assignment]

_LOGGER = logging.getLogger(__name__)

VID = 0x0581
PID = 0x011D
HEADER = bytes.fromhex("ba 70 24 00 00 00 00")
PACKET_LENGTH = 64
WRITE_DELAY_SECONDS = 0.2

BRIGHTNESS_COMMAND = bytes.fromhex("77 58 01 82")
KELVIN_COMMAND = bytes.fromhex("77 58 01 83")
TOGGLE_COMMAND = bytes.fromhex("77 58 01 85 01 56")

MIN_BRIGHTNESS_PERCENT = 0
MAX_BRIGHTNESS_PERCENT = 100
MIN_KELVIN = 2900
MAX_KELVIN = 7000


class NeewerGL25BError(Exception):
    """Raised when the Neewer GL25B dongle cannot be controlled."""


class NeewerGL25BController:
    """Synchronous controller for the official Neewer GL25B USB HID dongle.

    Keeps the HID device open for the lifetime of the integration to avoid
    USB re-enumeration on every command (which causes udev initialisation failures).
    """

    def __init__(self) -> None:
        """Initialise without opening the device."""
        self._dev: Any | None = None

    def connect(self) -> bool:
        """Open the HID device. Returns True on success."""
        if hid is None:
            _LOGGER.error("hidapi is not installed")
            return False

        if self._dev is not None:
            return True

        try:
            dev = hid.device()
            dev.open(VID, PID)
            self._dev = dev
            _LOGGER.debug("Neewer GL25B dongle connected")
            return True
        except Exception as err:  # noqa: BLE001
            _LOGGER.debug("Neewer GL25B dongle not available: %s", err)
            self._dev = None
            return False

    def disconnect(self) -> None:
        """Close the HID device."""
        if self._dev is not None:
            try:
                self._dev.close()
            except Exception:  # noqa: BLE001
                _LOGGER.debug("Failed to close Neewer GL25B HID device", exc_info=True)
            finally:
                self._dev = None

    def is_connected(self) -> bool:
        """Return True if the device is currently open."""
        return self._dev is not None

    def send_command(self, command: bytes) -> None:
        """Send a command body to the dongle as one 64-byte output report."""
        if hid is None:
            raise NeewerGL25BError("hidapi is not installed")

        packet = HEADER + command
        if len(packet) > PACKET_LENGTH:
            raise NeewerGL25BError(
                f"Command is too long: {len(packet)} bytes, expected at most {PACKET_LENGTH}"
            )

        packet = packet.ljust(PACKET_LENGTH, b"\x00")

        # Reconnect if the device was lost (e.g. unplugged and re-plugged).
        if self._dev is None and not self.connect():
            raise NeewerGL25BError("Neewer GL25B dongle is not available")

        try:
            written = self._dev.write(packet)  # type: ignore[union-attr]
            if written is not None and written < 0:
                raise NeewerGL25BError("hidapi reported a failed write")
            time.sleep(WRITE_DELAY_SECONDS)
        except NeewerGL25BError:
            raise
        except Exception as err:  # noqa: BLE001 - hidapi can raise backend-specific errors.
            _LOGGER.error("Failed to write to Neewer GL25B dongle: %s", err)
            # Device may have been unplugged; drop the handle so the next call reconnects.
            self.disconnect()
            raise NeewerGL25BError("Neewer GL25B dongle is not available") from err

    def set_brightness(self, percent: int) -> None:
        """Set GL25B brightness in the 0-100 percent range."""
        brightness = max(MIN_BRIGHTNESS_PERCENT, min(MAX_BRIGHTNESS_PERCENT, percent))
        command = BRIGHTNESS_COMMAND + bytes([brightness]) + bytes.fromhex("8c")
        self.send_command(command)

    def set_kelvin(self, kelvin: int) -> None:
        """Set GL25B color temperature in Kelvin."""
        clamped_kelvin = max(MIN_KELVIN, min(MAX_KELVIN, kelvin))
        command = KELVIN_COMMAND + bytes([clamped_kelvin // 100]) + bytes.fromhex("8c")
        self.send_command(command)

    def toggle(self) -> None:
        """Send the raw hardware toggle command."""
        self.send_command(TOGGLE_COMMAND)
