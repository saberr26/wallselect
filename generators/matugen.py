#!/usr/bin/env python3
"""
Matugen Generator Script for Wallselect

This script handles generating color schemes using matugen with all available options.
It reads settings from the config file and applies them correctly.
"""

import os
import sys
import subprocess
import json
import argparse

def parse_arguments():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description="Generate color schemes using matugen")
    parser.add_argument("--image", "-i", required=True, help="Path to the wallpaper image")
    parser.add_argument("--config", "-c", help="Path to config file (optional)")
    parser.add_argument("--mode", "-m", choices=["dark", "light"], default="dark", help="Color scheme mode")
    parser.add_argument("--type", "-t", default="scheme-tonal-spot",
                      help="Color scheme type (scheme-content, scheme-expressive, scheme-fidelity, scheme-fruit-salad, scheme-monochrome, scheme-neutral, scheme-rainbow, scheme-tonal-spot)")
    parser.add_argument("--contrast", type=float, default=0, help="Contrast value from -1 to 1")
    parser.add_argument("--dry-run", action="store_true", help="Will not generate templates, reload apps, set wallpaper or run any commands")
    parser.add_argument("--show-colors", action="store_true", help="Whether to show colors or not")
    parser.add_argument("--json", "-j", choices=["hex", "rgb", "rgba", "hsl", "hsla", "strip"], help="Whether to dump json of colors")
    parser.add_argument("--quiet", "-q", action="store_true", help="Whether to show no output")
    parser.add_argument("--debug", "-d", action="store_true", help="Whether to show debug output")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose mode")
    return parser.parse_args()

def load_config(config_path):
    """Load settings from config file."""
    settings = {
        "mode": "dark",
        "type": "scheme-tonal-spot",
        "contrast": "0",
        "dry_run": "false",
        "show_colors": "false",
        "json": "",
        "quiet": "false",
        "debug": "false"
    }

    if not config_path or not os.path.exists(config_path):
        return settings

    try:
        with open(config_path, "r") as f:
            in_matugen_section = False
            for line in f:
                line = line.strip()
                if not line or line.startswith("#"):
                    continue

                if line == "[Matugen]":
                    in_matugen_section = True
                    continue
                elif line.startswith("[") and line.endswith("]"):
                    in_matugen_section = False
                    continue

                if in_matugen_section and "=" in line:
                    key, value = line.split("=", 1)
                    key = key.strip().lower()
                    value = value.strip()

                    # Map config file keys to settings keys
                    if key == "mode":
                        settings["mode"] = value
                    elif key == "type":
                        settings["type"] = value
                    elif key == "contrast":
                        settings["contrast"] = value
                    elif key == "json":
                        settings["json"] = value
                    elif key == "show_colors":
                        settings["show_colors"] = value
                    elif key == "verbose":
                        settings["verbose"] = value
                    elif key == "quiet":
                        settings["quiet"] = value
                    elif key == "debug":
                        settings["debug"] = value
                    elif key == "dry_run":
                        settings["dry_run"] = value
    except Exception as e:
        print(f"Error loading config: {e}", file=sys.stderr)

    return settings

def build_matugen_command(args, settings):
    """Build the matugen command with all options."""
    # Start with the base command
    cmd = ["matugen", "image"]

    # Add the image path
    cmd.append(args.image)

    # Add mode (light/dark)
    mode = args.mode if args.mode else settings["mode"]
    cmd.extend(["--mode", mode])

    # Add type
    scheme_type = args.type if args.type else settings["type"]
    cmd.extend(["--type", scheme_type])

    # Add contrast
    contrast = args.contrast if args.contrast is not None else float(settings["contrast"])
    cmd.extend(["--contrast", str(contrast)])

    # Add dry-run option
    if args.dry_run or settings["dry_run"].lower() == "true":
        cmd.append("--dry-run")

    # Add show-colors option
    if args.show_colors or settings["show_colors"].lower() == "true":
        cmd.append("--show-colors")

    # Add json option
    json_format = args.json if args.json else settings["json"]
    if json_format:
        cmd.extend(["--json", json_format])

    # Add quiet mode if specified
    if args.quiet or settings["quiet"].lower() == "true":
        cmd.append("--quiet")

    # Add debug mode if specified
    if args.debug or settings["debug"].lower() == "true":
        cmd.append("--debug")

    return cmd

def run_matugen(cmd):
    """Run the matugen command and return the output."""
    try:
        # Print the command for debugging
        print(f"Running: {' '.join(cmd)}")

        # Run the command
        result = subprocess.run(cmd, capture_output=True, text=True)

        # Print the output
        if result.stdout:
            print(result.stdout)

        # Print any errors
        if result.stderr:
            print(result.stderr, file=sys.stderr)

        return result.returncode == 0
    except Exception as e:
        print(f"Error running matugen: {e}", file=sys.stderr)
        return False

def main():
    """Main function."""
    # Parse arguments
    args = parse_arguments()

    # Load config
    config_path = args.config or os.path.expanduser("~/.config/wallselect/config.ini")
    settings = load_config(config_path)

    # Print loaded settings for debugging
    print("Loaded matugen settings from config:")
    for key, value in settings.items():
        print(f"  {key}: {value}")

    # Build and run the matugen command
    cmd = build_matugen_command(args, settings)
    success = run_matugen(cmd)

    # Exit with appropriate code
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()
