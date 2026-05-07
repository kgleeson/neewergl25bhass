#!/usr/bin/env python3
"""Standalone Neewer GL25B USB HID dongle test utility."""

from __future__ import annotations

import argparse
import importlib.util
import pathlib
from types import ModuleType

REPO_ROOT = pathlib.Path(__file__).resolve().parents[1]
CONTROLLER_PATH = REPO_ROOT / "custom_components" / "neewer_gl25b" / "hid_controller.py"


def load_controller_module() -> ModuleType:
    """Load hid_controller.py without importing the Home Assistant package."""
    spec = importlib.util.spec_from_file_location("neewer_gl25b_hid_controller", CONTROLLER_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Cannot load controller module from {CONTROLLER_PATH}")

    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


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

    if args.command == "toggle":
        controller.toggle()
    elif args.command == "brightness":
        controller.set_brightness(args.percent)
    elif args.command == "temp":
        controller.set_kelvin(args.kelvin)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
