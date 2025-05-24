#!/usr/bin/env python3
"""
Material Generator integration for wallselect.
Extracts Material You colors from a wallpaper image.
"""

import os
import sys
import math
import argparse
import json
from PIL import Image

# Try to import the materialyoucolor library
try:
    from materialyoucolor.quantize import QuantizeCelebi
    from materialyoucolor.hct import Hct
    from materialyoucolor.scheme.scheme_tonal_spot import SchemeTonalSpot
    from materialyoucolor.dynamiccolor.material_dynamic_colors import MaterialDynamicColors
    from materialyoucolor.score.score import Score
except ImportError:
    print("Error: materialyoucolor library not found.")
    print("Please install it with: pip install materialyoucolor")
    sys.exit(1)

# Define constants
CACHE_DIR = os.path.expanduser("~/.cache/wallpapers/material")
os.makedirs(CACHE_DIR, exist_ok=True)

def rgba_to_hex(rgba: list) -> str:
    """Convert RGBA values to hex color code."""
    return "#{:02x}{:02x}{:02x}".format(*rgba)

def calculate_optimal_size(width: int, height: int, bitmap_size: int) -> tuple:
    """Calculate optimal image size for color extraction."""
    image_area = width * height
    bitmap_area = bitmap_size**2
    scale = math.sqrt(bitmap_area / image_area) if image_area > bitmap_area else 1
    new_width = round(width * scale)
    new_height = round(height * scale)
    if new_width == 0:
        new_width = 1
    if new_height == 0:
        new_height = 1
    return new_width, new_height

def get_colors_from_img(path: str, dark_mode: bool = True) -> dict:
    """Extract Material You colors from an image."""
    # Always use dark mode for consistency
    dark_mode = True
    
    image = Image.open(path)
    wsize, hsize = image.size
    wsize_new, hsize_new = calculate_optimal_size(wsize, hsize, 128)
    if wsize_new < wsize or hsize_new < hsize:
        image = image.resize((wsize_new, hsize_new), Image.Resampling.BICUBIC)

    pixel_len = image.width * image.height
    image_data = image.getdata()
    pixel_array = [image_data[_] for _ in range(0, pixel_len, 1)]

    colors = QuantizeCelebi(pixel_array, 128)
    argb = Score.score(colors)[0]

    hct = Hct.from_int(argb)
    scheme = SchemeTonalSpot(hct, dark_mode, 0.0)

    material_colors = {}
    for color in vars(MaterialDynamicColors).keys():
        color_name = getattr(MaterialDynamicColors, color)
        if hasattr(color_name, "get_hct"):
            rgba = color_name.get_hct(scheme).to_rgba()
            material_colors[color] = rgba_to_hex(rgba)

    return material_colors

def extract_colors(wallpaper_path: str, output_path: str = None) -> str:
    """Extract colors from wallpaper and save to JSON file."""
    if not os.path.isfile(wallpaper_path):
        print(f"Error: Wallpaper file not found: {wallpaper_path}")
        return None

    # Extract colors from the wallpaper
    colors = get_colors_from_img(wallpaper_path, True)
    
    # Create the output directory if it doesn't exist
    if not output_path:
        output_path = f"{CACHE_DIR}/colors.json"
    
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    # Save colors to JSON file
    with open(output_path, 'w') as f:
        json.dump(colors, f, indent=2)
    
    print(f"Material colors extracted and saved to: {output_path}")
    return output_path

# When run directly, extract colors
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Extract Material You colors from a wallpaper image")
    parser.add_argument("--image", help="Path to the wallpaper image")
    parser.add_argument("--config", help="Path to the configuration file (ignored)")
    parser.add_argument("--output", default=f"{CACHE_DIR}/colors.json", help="Output JSON file path")
    
    # Also support positional argument for backward compatibility
    parser.add_argument("wallpaper", nargs="?", help="Path to the wallpaper image (alternative to --image)")
    
    # Parse known args to handle unknown arguments gracefully
    args, unknown = parser.parse_known_args()
    
    # Determine wallpaper path (prefer --image if provided)
    wallpaper_path = args.image if args.image else args.wallpaper
    
    if not wallpaper_path:
        print("Error: No wallpaper path provided. Use --image or provide as positional argument.")
        sys.exit(1)
    
    output_path = extract_colors(wallpaper_path, args.output)
    
    if output_path:
        print(f"Material colors extracted and saved to: {output_path}")
