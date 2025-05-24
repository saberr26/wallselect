#!/usr/bin/env python3
"""
Hellwal Generator Script for Wallselect

This script handles generating color schemes using hellwal with all available options.
It reads settings from the config file and applies them correctly.
"""

import os
import sys
import subprocess
import json
import argparse

def parse_arguments():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description="Generate color schemes using hellwal")
    parser.add_argument("--image", "-i", required=True, help="Path to the wallpaper image")
    parser.add_argument("--config", "-c", help="Path to config file (optional)")
    parser.add_argument("--mode", "-m", choices=["dark", "light"], default="dark", help="Color scheme mode")
    parser.add_argument("--neon-mode", action="store_true", help="Enhance colors for a neon effect")
    parser.add_argument("--invert", "-v", action="store_true", help="Invert colors in the palette")
    parser.add_argument("--gray-scale", "-g", type=float, help="Apply grayscale filter (0-1)")
    parser.add_argument("--dark-offset", "-n", type=float, help="Adjust darkness offset (0-1)")
    parser.add_argument("--bright-offset", "-b", type=float, help="Adjust brightness offset (0-1)")
    parser.add_argument("--random", "-r", action="store_true", help="Pick random image or theme")
    parser.add_argument("--quiet", "-q", action="store_true", help="Suppress output")
    parser.add_argument("--json", "-j", action="store_true", help="Prints colors to stdout in json format")
    parser.add_argument("--skip-term-colors", action="store_true", help="Skip setting colors to the terminal")
    parser.add_argument("--skip-luminance-sort", action="store_true", help="Skip sorting colors before applying")
    parser.add_argument("--debug", action="store_true", help="Enable debug mode")
    parser.add_argument("--no-cache", action="store_true", help="Disable caching")
    return parser.parse_args()

def load_config(config_path):
    """Load settings from config file."""
    settings = {
        "mode": "dark",
        "neon_mode": "false",
        "gray_scale": "0",
        "dark_offset": "0.2",
        "bright_offset": "0.2",
        "invert": "false",
        "random": "false",
        "quiet": "false",
        "json": "false",
        "skip_term": "false",
        "skip_lum": "false",
        "debug": "false",
        "no_cache": "false"
    }
    
    if not config_path or not os.path.exists(config_path):
        return settings
    
    try:
        with open(config_path, "r") as f:
            in_hellwal_section = False
            for line in f:
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                
                if line == "[Hellwal]":
                    in_hellwal_section = True
                    continue
                elif line.startswith("[") and line.endswith("]"):
                    in_hellwal_section = False
                    continue
                
                if in_hellwal_section and "=" in line:
                    key, value = line.split("=", 1)
                    key = key.strip().lower()
                    value = value.strip()
                    
                    # Map config file keys to settings keys
                    if key == "mode":
                        settings["mode"] = value
                    elif key == "neon_mode":
                        settings["neon_mode"] = value
                    elif key == "gray_scale":
                        settings["gray_scale"] = value
                    elif key == "dark_offset":
                        settings["dark_offset"] = value
                    elif key == "bright_offset":
                        settings["bright_offset"] = value
                    elif key == "invert":
                        settings["invert"] = value
                    elif key == "random":
                        settings["random"] = value
                    elif key == "quiet":
                        settings["quiet"] = value
                    elif key == "json":
                        settings["json"] = value
                    elif key == "skip_term":
                        settings["skip_term"] = value
                    elif key == "skip_lum":
                        settings["skip_lum"] = value
                    elif key == "debug":
                        settings["debug"] = value
                    elif key == "no_cache":
                        settings["no_cache"] = value
    except Exception as e:
        print(f"Error loading config: {e}", file=sys.stderr)
    
    return settings

def build_hellwal_command(args, settings):
    """Build the hellwal command with all options."""
    # Start with the base command
    cmd = ["hellwal"]
    
    # Add the image path
    cmd.extend(["-i", args.image])
    
    # Add mode (light/dark)
    mode = args.mode if args.mode else settings["mode"]
    if mode == "light":
        cmd.append("-l")
    else:
        cmd.append("-d")
    
    # Add neon mode
    if args.neon_mode or settings["neon_mode"].lower() == "true":
        cmd.append("-m")
    
    # Add invert option
    if args.invert or settings["invert"].lower() == "true":
        cmd.append("-v")
    
    # Add gray scale
    gray_scale = args.gray_scale if args.gray_scale is not None else float(settings["gray_scale"] or 0)
    if gray_scale > 0:
        cmd.extend(["-g", str(gray_scale)])
    
    # Add dark offset
    dark_offset = args.dark_offset if args.dark_offset is not None else float(settings["dark_offset"] or 0.2)
    cmd.extend(["-n", str(dark_offset)])
    
    # Add bright offset
    bright_offset = args.bright_offset if args.bright_offset is not None else float(settings["bright_offset"] or 0.2)
    cmd.extend(["-b", str(bright_offset)])
    
    # Add random option
    if args.random or settings["random"].lower() == "true":
        cmd.append("-r")
    
    # Add quiet mode
    if args.quiet or settings["quiet"].lower() == "true":
        cmd.append("-q")
    
    # Add json output
    if args.json or settings["json"].lower() == "true":
        cmd.append("-j")
    
    # Add skip term colors
    if args.skip_term_colors or settings["skip_term"].lower() == "true":
        cmd.append("--skip-term-colors")
    
    # Add skip luminance sort
    if args.skip_luminance_sort or settings["skip_lum"].lower() == "true":
        cmd.append("--skip-luminance-sort")
    
    # Add debug mode
    if args.debug or settings["debug"].lower() == "true":
        cmd.append("--debug")
    
    # Add no cache option
    if args.no_cache or settings["no_cache"].lower() == "true":
        cmd.append("--no-cache")
    
    return cmd

def run_hellwal(cmd):
    """Run the hellwal command and return the output."""
    try:
        # Print the command for debugging
        print(f"Running hellwal command: {' '.join(cmd)}")
        
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
        print(f"Error running hellwal: {e}", file=sys.stderr)
        return False

def main():
    """Main function."""
    # Parse arguments
    args = parse_arguments()
    
    # Load config
    config_path = args.config or os.path.expanduser("~/.config/wallselect/config.ini")
    settings = load_config(config_path)
    
    # Print loaded settings for debugging
    print("Loaded settings from config:")
    for key, value in settings.items():
        print(f"  {key}: {value}")
    
    # Build and run the hellwal command
    cmd = build_hellwal_command(args, settings)
    success = run_hellwal(cmd)
    
    # Exit with appropriate code
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()
