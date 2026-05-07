# Neewer GL25B Home Assistant Integration

Home Assistant custom integration for controlling a Neewer GL25B key light through its official USB HID dongle.

This integration is local-only. It does not use cloud access, Bluetooth, shell commands from the integration, or a Home Assistant add-on.

## Features

- Adds one light entity named `Neewer GL25B` by default.
- Supports turn on, turn off, brightness, and color temperature.
- Uses the official USB HID dongle directly through Python `hidapi`.
- Runs blocking HID writes in Home Assistant executor jobs.
- Avoids duplicate writes when the requested state is already the current in-memory state.

## Requirements

- Home Assistant Core with custom integrations enabled.
- The Neewer GL25B official USB HID dongle visible inside Home Assistant Core.
- USB VID/PID: `0581:011d`.
- Python package `hidapi`; Home Assistant should install this automatically from `manifest.json`.

## Known Limitations

No true discrete hardware on/off command is currently known. The integration handles power state as follows:

- Turn off sends brightness `0` and marks the entity off internally.
- Turn on restores the last known brightness, or uses the brightness provided by Home Assistant.
- The raw hardware toggle command exists in the controller and test script, but normal Home Assistant light on/off handling does not use it.

State is assumed because the dongle/light does not provide known readable state feedback.

## Installation Through HACS

1. In HACS, add this repository as a custom repository.
2. Select category `Integration`.
3. Install `Neewer GL25B`.
4. Restart Home Assistant.
5. Go to Settings -> Devices & services -> Add integration.
6. Search for `Neewer GL25B`.
7. Connect the USB HID dongle and complete the config flow.

## Home Assistant OS Note

The USB dongle must be visible inside the Home Assistant Core environment, not just attached to the host machine. If Home Assistant runs in a VM, container, or supervised environment, pass the USB HID device through to the environment running Home Assistant Core.

## HID Details

The confirmed working method is:

- Import `hidapi` as `hid`.
- Open using `dev.open(0x0581, 0x011D)`.
- Write exactly 64 bytes with `dev.write(packet)`.
- Do not use `open_path`.
- Do not use `send_feature_report`.
- Do not prepend a report ID byte.
- Do not use 45-byte packets.

Packet format:

```text
ba 70 24 00 00 00 00 + command body + zero padding to 64 bytes
```

Brightness command body:

```text
77 58 01 82 <brightness_byte> 8c
```

Color temperature command body:

```text
77 58 01 83 <kelvin_div_100_byte> 8c
```

Raw toggle command body:

```text
77 58 01 85 01 56
```

## Troubleshooting

List visible HID devices from the same Python environment Home Assistant uses:

```bash
python3 -c "import hid; print(hid.enumerate())"
```

Check for `vendor_id` `0x0581` and `product_id` `0x011d`.

On Linux, permission errors usually mean Home Assistant cannot access `/dev/hidraw*`. Configure USB passthrough and, if needed, udev rules so the Home Assistant process can open the dongle.

If installation fails because `hidapi` cannot build or install, check the Home Assistant logs for package installation errors. Home Assistant Core should install `hidapi` automatically from this integration's manifest requirements.

## Credits

This integration’s USB HID packet handling is derived from AugusDogus’ reverse-engineering of the Neewer 2.4 GHz USB dongle in [`neweer-tray`](https://github.com/AugusDogus/neweer-tray) and the related write-up, [“Reverse Engineering My Studio Lights in an Afternoon”](https://www.augie.gg/blog/reverse-engineering-neewer-lights). GL25B-specific brightness and colour-temperature packet examples are credited to @4noxx in [`taburineagle/NeewerLite-Python` issue #105](https://github.com/taburineagle/NeewerLite-Python/issues/105).