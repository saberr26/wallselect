#!/usr/bin/env python3
import random
import subprocess
import sys
import os
import time
import json
from pathlib import Path

def exec_async(command):
    """Execute a command asynchronously"""
    subprocess.Popen(command)

def create_swww_command(image_path, options):
    """Create the swww command with options"""
    command = ["swww", "img", image_path]

    if options.get("noResize"):
        command.append("--no-resize")

    if options.get("resize"):
        command.extend(["--resize", options["resize"]])

    if options.get("fillColor"):
        command.extend(["--fill-color", options["fillColor"]])

    if options.get("filter"):
        command.extend(["-f", options["filter"]])

    if options.get("transitionType"):
        command.extend(["--transition-type", options["transitionType"]])

    if options.get("transitionStep") is not None:
        command.extend(["--transition-step", str(options["transitionStep"])])

    if options.get("transitionDuration") is not None:
        command.extend(["--transition-duration", str(options["transitionDuration"])])

    if options.get("transitionFps") is not None:
        command.extend(["--transition-fps", str(options["transitionFps"])])

    if options.get("transitionAngle") is not None:
        command.extend(["--transition-angle", str(options["transitionAngle"])])

    if options.get("transitionPos"):
        command.extend(["--transition-pos", options["transitionPos"]])

    return command

def generate_random_swww_options():
    """Generate random transition options for swww with enhanced variety"""
    def get_random_element(arr):
        return arr[random.randint(0, len(arr) - 1)]

    # Expanded transition types with more variety
    transition_types = [
        # Basic directional transitions
        "fade", "left", "right", "top", "bottom",

        # Advanced transitions
        "wipe", "wave", "grow", "center", "outer",

        # Diagonal transitions
        "top-left", "top-right", "bottom-left", "bottom-right",

        # Circular/radial transitions
        "center-out", "outer-in",

        # Complex transitions
        "spiral", "diamond", "hexagon"
    ]

    # More diverse position options
    positions = [
        # Corner positions
        "center", "top", "left", "right", "bottom",
        "top-left", "top-right", "bottom-left", "bottom-right",

        # Edge midpoints
        "top-center", "bottom-center", "left-center", "right-center",

        # Quarter positions
        "quarter-top-left", "quarter-top-right",
        "quarter-bottom-left", "quarter-bottom-right",

        # Random coordinates (0-100 range)
        f"{random.randint(10, 90)},{random.randint(10, 90)}",
        f"{random.randint(0, 50)},{random.randint(0, 50)}",
        f"{random.randint(50, 100)},{random.randint(50, 100)}"
    ]

    # Resize options with weights (crop is most common)
    resize_options = ["crop", "crop", "crop", "fit", "no"]  # Weighted towards crop

    # Filter options for visual effects
    filters = [
        None, None, None,  # Most of the time no filter
        "Lanczos3", "Mitchell", "CatmullRom", "Triangle", "Gaussian"
    ]

    # Fill colors for letterboxing
    fill_colors = [
        None, None,  # Usually no fill color
        "#000000", "#FFFFFF", "#1a1a1a", "#2d2d2d",
        "#0f0f0f", "#333333", "#404040"
    ]

    # Generate random values with realistic ranges
    transition_step = random.choice([
        # Fast transitions
        200, 220, 240, 255,
        # Medium transitions
        120, 140, 160, 180,
        # Slow transitions (less common)
        60, 80, 100
    ])

    transition_duration = random.choice([
        # Quick transitions (most common)
        0.5, 0.8, 1.0, 1.2, 1.5,
        # Medium transitions
        2.0, 2.5, 3.0,
        # Slow transitions (rare)
        4.0, 5.0
    ])

    transition_fps = random.choice([
        # High FPS (smooth)
        60, 60, 60
    ])

    # Special angle handling for specific transition types
    selected_transition = get_random_element(transition_types)

    if selected_transition in ["wipe", "wave", "spiral"]:
        # These transitions benefit from varied angles
        transition_angle = random.randint(0, 359)
    elif selected_transition in ["grow", "center", "outer"]:
        # These work well with cardinal angles
        transition_angle = random.choice([0, 45, 90, 135, 180, 225, 270, 315])
    else:
        # Default random angle
        transition_angle = random.randint(0, 359)

    options = {
        "resize": get_random_element(resize_options),
        "transitionType": selected_transition,
        "transitionStep": transition_step,
        "transitionDuration": transition_duration,
        "transitionFps": transition_fps,
        "transitionAngle": transition_angle,
        "transitionPos": get_random_element(positions),
        "filter": get_random_element(filters),
        "fillColor": get_random_element(fill_colors)
    }

    # Remove None values
    options = {k: v for k, v in options.items() if v is not None}

    return options

def generate_themed_transition(theme="random"):
    """Generate transition options based on a theme"""
    themes = {
        "smooth": {
            "transitionType": random.choice(["fade", "grow", "center"]),
            "transitionStep": random.randint(180, 255),
            "transitionDuration": random.uniform(1.5, 3.0),
            "transitionFps": 60
        },
        "dramatic": {
            "transitionType": random.choice(["wipe", "wave", "spiral"]),
            "transitionStep": random.randint(200, 255),
            "transitionDuration": random.uniform(0.5, 1.5),
            "transitionFps": random.choice([60, 60]),
            "transitionAngle": random.randint(0, 359)
        },
        "minimal": {
            "transitionType": "fade",
            "transitionStep": 255,
            "transitionDuration": 1.0,
            "transitionFps": 30
        },
        "dynamic": {
            "transitionType": random.choice(["left", "right", "top", "bottom", "diagonal"]),
            "transitionStep": random.randint(150, 220),
            "transitionDuration": random.uniform(0.8, 2.0),
            "transitionFps": random.choice([60, 60])
        }
    }

    if theme == "random" or theme not in themes:
        return generate_random_swww_options()

    base_options = themes[theme].copy()
    base_options.update({
        "resize": "crop",
        "transitionPos": random.choice(["center", "top-left", "top-right", "bottom-left", "bottom-right"])
    })

    return base_options

def set_wallpaper(wallpaper_path, theme="random"):
    """Set the wallpaper using swww with random transition effects"""
    options = generate_themed_transition(theme)
    command = create_swww_command(wallpaper_path, options)

    # Print the transition info
    print(f"🎨 Transition: {options.get('transitionType', 'fade')}")
    print(f"⚡ Speed: {options.get('transitionStep', 255)}")
    print(f"⏱️  Duration: {options.get('transitionDuration', 1)}s")

    # Execute the command
    try:
        subprocess.run(command, check=True)
        return True
    except subprocess.CalledProcessError as e:
        print(f"Error executing swww command: {e}")
        return False

def parse_command_line_args():
    """Parse command line arguments"""
    import argparse
    parser = argparse.ArgumentParser(description="Enhanced helper script for setting wallpapers with swww")
    parser.add_argument("image_path", help="Path to the wallpaper image")
    parser.add_argument("--theme", choices=["random", "smooth", "dramatic", "minimal", "dynamic"],
                       default="random", help="Transition theme")
    parser.add_argument("--transition-type", dest="transitionType", help="Specific transition type")
    parser.add_argument("--transition-step", dest="transitionStep", type=float, help="Transition step size (0-255)")
    parser.add_argument("--transition-duration", dest="transitionDuration", type=float, help="Transition duration in seconds")
    parser.add_argument("--transition-fps", dest="transitionFps", type=int, help="Transition frames per second")
    parser.add_argument("--transition-angle", dest="transitionAngle", type=float, help="Transition angle in degrees")
    parser.add_argument("--transition-position", dest="transitionPos", help="Transition position")
    parser.add_argument("--filter", help="Image filter to apply")
    parser.add_argument("--no-resize", dest="noResize", action="store_true", help="Disable image resizing")
    parser.add_argument("--resize", help="Resize mode (scale, fit, center)")
    parser.add_argument("--fill-color", dest="fillColor", help="Fill color for letterboxing")
    parser.add_argument("--random", action="store_true", help="Use completely random transition effects")
    parser.add_argument("--list-transitions", action="store_true", help="List all available transition types")

    return parser.parse_args()

def list_available_transitions():
    """List all available transition types"""
    transitions = [
        "fade", "left", "right", "top", "bottom",
        "wipe", "wave", "grow", "center", "outer",
        "top-left", "top-right", "bottom-left", "bottom-right",
        "center-out", "outer-in", "spiral", "diamond", "hexagon"
    ]

    print("Available transition types:")
    for i, transition in enumerate(transitions, 1):
        print(f"  {i:2d}. {transition}")
    print(f"\nTotal: {len(transitions)} transitions available")

if __name__ == "__main__":
    # Parse command line arguments
    args = parse_command_line_args()

    # Handle list transitions
    if args.list_transitions:
        list_available_transitions()
        sys.exit(0)

    # Get options from arguments or generate themed/random ones
    if args.random:
        options = generate_random_swww_options()
    elif hasattr(args, 'theme') and args.theme != "random":
        options = generate_themed_transition(args.theme)
    else:
        # Convert argparse Namespace to dictionary, filtering out None values
        options = {k: v for k, v in vars(args).items()
                  if v is not None and k not in ['image_path', 'random', 'theme', 'list_transitions']}

        # If no specific options provided, use themed generation
        if not options:
            options = generate_themed_transition(getattr(args, 'theme', 'random'))

    # Execute the command
    command = create_swww_command(args.image_path, options)
    print(f"🚀 Executing: {' '.join(command)}")

    try:
        exec_async(command)
        print("✅ Wallpaper application started successfully!")
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)
