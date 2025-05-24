#!/usr/bin/env python3
"""
Pywal Generator Script for Wallselect

This script handles generating color schemes using pywal with all available options.
It reads settings from the config file and applies them correctly.
"""

import os
import sys
import subprocess
import json
import argparse

def parse_arguments():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description="Generate color schemes using pywal")
    parser.add_argument("--image", "-i", required=True, help="Path to the wallpaper image")
    parser.add_argument("--config", "-c", help="Path to config file (optional)")
    parser.add_argument("--mode", "-m", choices=["dark", "light"], default="dark", help="Color scheme mode")
    parser.add_argument("--cols16", action="store_true", help="Enable 16 colors mode")
    parser.add_argument("--cols16-method", choices=["darken", "lighten"], default="darken", help="16 colors method")
    parser.add_argument("--saturate", "-s", type=float, default=0.6, help="Color saturation (0.0-1.0)")
    parser.add_argument("--backend", "-b", default="wal", help="Color backend to use")
    parser.add_argument("--contrast", type=float, default=1.0, help="Contrast ratio (1.0-21.0)")
    parser.add_argument("--skip-wallpaper", "-n", action="store_true", help="Skip setting the wallpaper")
    parser.add_argument("--skip-terminals", action="store_true", help="Skip changing colors in terminals")
    parser.add_argument("--skip-tty", "-t", action="store_true", help="Skip changing colors in tty")
    parser.add_argument("--skip-reload", "-e", action="store_true", help="Skip reloading gtk/xrdb/i3/sway/polybar")
    parser.add_argument("--quiet", "-q", action="store_true", help="Quiet mode")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose mode")
    return parser.parse_args()

def load_config(config_path):
    """Load settings from config file."""
    settings = {
        "mode": "dark",
        "cols16": "true",
        "saturate": "0.6",
        "backend": "wal",
        "contrast": "1.0",
        "skip_wallpaper": "false",
        "skip_terminals": "false",
        "skip_tty": "false",
        "skip_reload": "false"
    }

    if not config_path or not os.path.exists(config_path):
        return settings

    try:
        with open(config_path, "r") as f:
            in_pywal_section = False
            for line in f:
                line = line.strip()
                if not line or line.startswith("#"):
                    continue

                if line == "[Pywal]":
                    in_pywal_section = True
                    continue
                elif line.startswith("[") and line.endswith("]"):
                    in_pywal_section = False
                    continue

                if in_pywal_section and "=" in line:
                    key, value = line.split("=", 1)
                    key = key.strip().lower()
                    value = value.strip()

                    # Map config file keys to settings keys
                    if key == "mode":
                        settings["mode"] = value
                    elif key == "cols16":
                        settings["cols16"] = value
                    elif key == "cols16_method":
                        settings["cols16_method"] = value
                    elif key == "saturate":
                        settings["saturate"] = value
                    elif key == "backend":
                        settings["backend"] = value
                    elif key == "contrast":
                        settings["contrast"] = value
                    elif key == "skip_wallpaper":
                        settings["skip_wallpaper"] = value
                    elif key == "skip_terminals":
                        settings["skip_terminals"] = value
                    elif key == "skip_tty":
                        settings["skip_tty"] = value
                    elif key == "skip_reload":
                        settings["skip_reload"] = value
    except Exception as e:
        print(f"Error loading config: {e}", file=sys.stderr)

    return settings

def build_pywal_command(args, settings):
    """Build the pywal command with all options."""
    # Start with the base command
    cmd = ["wal"]

    # Add the image path
    cmd.extend(["-i", args.image])

    # Add mode (light/dark)
    mode = args.mode if args.mode else settings["mode"]
    if mode == "light":
        cmd.append("-l")

    # Add 16 colors mode
    cols16 = args.cols16 or (settings["cols16"].lower() == "true")
    if cols16:
        cols16_method = args.cols16_method if hasattr(args, "cols16_method") else "darken"
        cmd.extend(["--cols16", cols16_method])

    # Add saturation
    saturate = args.saturate if args.saturate is not None else float(settings["saturate"])
    cmd.extend(["--saturate", str(saturate)])

    # Add backend
    backend = args.backend if args.backend else settings["backend"]
    if backend and backend != "wal":
        cmd.extend(["--backend", backend])

    # Add contrast
    contrast = args.contrast if args.contrast is not None else float(settings["contrast"])
    cmd.extend(["--contrast", str(contrast)])

    # Add skip options
    if args.skip_wallpaper or settings["skip_wallpaper"].lower() == "true":
        cmd.append("-n")

    if args.skip_terminals or settings["skip_terminals"].lower() == "true":
        cmd.append("-s")

    if args.skip_tty or settings["skip_tty"].lower() == "true":
        cmd.append("-t")

    if args.skip_reload or settings["skip_reload"].lower() == "true":
        cmd.append("-e")

    # Add quiet mode if specified
    if args.quiet:
        cmd.append("-q")

    return cmd

def run_pywal(cmd):
    """Run the pywal command and return the output."""
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
        print(f"Error running pywal: {e}", file=sys.stderr)
        return False

def main():
    """Main function."""
    # Parse arguments
    args = parse_arguments()

    # Load config
    config_path = args.config or os.path.expanduser("~/.config/wallselect/config.ini")
    settings = load_config(config_path)

    # Print loaded settings for debugging
    print("Loaded pywal settings from config:")
    for key, value in settings.items():
        print(f"  {key}: {value}")

    # Build and run the pywal command
    cmd = build_pywal_command(args, settings)
    success = run_pywal(cmd)

    # Exit with appropriate code
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()
