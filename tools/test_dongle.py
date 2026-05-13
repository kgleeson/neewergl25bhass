#!/usr/bin/env python3
"""Standalone Neewer GL25B USB HID dongle test utility."""

from __future__ import annotations

import argparse
import importlib.util
import pathlib
import sys
from types import ModuleType

REPO_ROOT = pathlib.Path(__file__).resolve().parents[1]
PACKAGE_DIR = REPO_ROOT / "custom_components" / "neewer_gl25b"


def load_controller_module() -> ModuleType:
    """Load hid_controller.py without importing the Home Assistant package."""
    # Register a minimal stand-in package so `from .const import ...` resolves
    # without executing the real __init__.py (which depends on Home Assistant).
    package_name = "neewer_gl25b_standalone"
    package = ModuleType(package_name)
    package.__path__ = [str(PACKAGE_DIR)]
    sys.modules[package_name] = package

    const_spec = importlib.util.spec_from_file_location(
        f"{package_name}.const", PACKAGE_DIR / "const.py"
    )
    if const_spec is None or const_spec.loader is None:
        raise RuntimeError("Cannot load const module")
    const_module = importlib.util.module_from_spec(const_spec)
    sys.modules[const_spec.name] = const_module
    const_spec.loader.exec_module(const_module)

    controller_spec = importlib.util.spec_from_file_location(
        f"{package_name}.hid_controller", PACKAGE_DIR / "hid_controller.py"
    )
    if controller_spec is None or controller_spec.loader is None:
        raise RuntimeError("Cannot load hid_controller module")
    controller_module = importlib.util.module_from_spec(controller_spec)
    sys.modules[controller_spec.name] = controller_module
    controller_spec.loader.exec_module(controller_module)
    return controller_module


def main() -> int:
    """Run a standalone dongle command."""
    controller_module = load_controller_module()

    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)

    subparsers.add_parser("toggle", help="Send the raw hardware toggle command")

    brightness_parser = subparsers.add_parser(
        "brightness", help="Set GL25B brightness percent"
    )
    brightness_parser.add_argument("percent", type=int, help="Brightness from 0 to 100")

    kelvin_parser = subparsers.add_parser("temp", help="Set color temperature in Kelvin")
    kelvin_parser.add_argument(
        "kelvin",
        type=int,
        help=f"Kelvin from {controller_module.MIN_KELVIN} to {controller_module.MAX_KELVIN}",
    )

    args = parser.parse_args()
    controller = controller_module.NeewerGL25BController()

    try:
        if args.command == "toggle":
            controller.toggle()
        elif args.command == "brightness":
            controller.set_brightness(args.percent)
        elif args.command == "temp":
            controller.set_kelvin(args.kelvin)
    finally:
        controller.disconnect()

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
