#!/bin/bash

# Wallpaper Switcher with Multiple Color Generators

readonly SCRIPT_DIR="$(dirname "$0")"
readonly LOCAL_DIR="$HOME/.local/share/wallselect"
readonly CONFIG_DIR="$HOME/.config/wallpaper-switcher"
readonly CACHE_EXPIRY_SECONDS=604800
readonly SUPPORTED_EXTENSIONS=("jpg" "jpeg" "png" "webp")

readonly CONFIG_FILE="$CONFIG_DIR/config.ini"
readonly DEV_CONFIG_FILE="$SCRIPT_DIR/config.ini"
readonly GENERATOR_CONFIG="$CONFIG_DIR/generators.conf"

WALLPAPER_DIR="$HOME/wallpapers"
CACHE_DIR="$HOME/.cache/wallpapers"
BLUR_AMOUNT="50x30"
DEFAULT_GENERATOR="pywal"
TRANSITION_TYPE="grow"

declare -A CONFIG_CACHE
AVAILABLE_GENERATORS_CACHE=""
WALLPAPER_LIST_CACHE=""

log_message() {
    echo ":: $1"
}

command_exists() {
    command -v "$1" >/dev/null 2>&1
}

get_active_config_file() {
    if [ -f "$DEV_CONFIG_FILE" ]; then
        echo "$DEV_CONFIG_FILE"
    elif [ -f "$CONFIG_FILE" ]; then
        echo "$CONFIG_FILE"
    else
        echo ""
    fi
}

find_generator_script() {
    local generator="$1"
    local extensions=("py" "sh")
    local search_dirs=("$SCRIPT_DIR/generators" "$LOCAL_DIR/generators")
    
    for dir in "${search_dirs[@]}"; do
        for ext in "${extensions[@]}"; do
            local script_path="$dir/$generator.$ext"
            if [ -f "$script_path" ] && [ -x "$script_path" ]; then
                echo "$script_path"
                return 0
            fi
        done
    done
    
    return 1
}

ensure_directories() {
    mkdir -p "$CACHE_DIR" "$CONFIG_DIR" "$LOCAL_DIR/generators" "$CACHE_DIR/colors" "$CACHE_DIR/blurred"
}

init_generator_config() {
    [ -f "$GENERATOR_CONFIG" ] && return
    
    cat > "$GENERATOR_CONFIG" << EOF
# Color Generator Configuration
# Format: generator_name:enabled:priority
pywal:true:1
matugen:true:2
hellwall:true:3
material:true:4
EOF
}

init_main_config() {
    [ -f "$CONFIG_FILE" ] && return
    
    if [ -f "$DEV_CONFIG_FILE" ]; then
        log_message "Copying development config.ini to $CONFIG_FILE"
        cp "$DEV_CONFIG_FILE" "$CONFIG_FILE"
        return
    fi
    
    log_message "Generating default config.ini"
    cat > "$CONFIG_FILE" << EOF
# Wallpaper Switcher Configuration File

[General]
wallpaper_dir = ~/wallpapers
cache_dir = ~/.cache/wallpapers
default_generator = pywal
blur_amount = 50x30
transition_type = grow

[Pywal]
mode = dark
cols16 = true
cols16_method = darken
saturate = 0.6
backend = wal
contrast = 1.0
skip_wallpaper = false
skip_terminals = false
skip_tty = false
skip_reload = false

[Matugen]
mode = dark
type = scheme-tonal-spot
contrast = 0
dry_run = false
show_colors = false
json = 
quiet = false
debug = false

[Material]
mode = dark
contrast = 0.0
template = 
output = ~/.cache/wallpapers/material/gtk.css
apply_theme = true

[Hellwal]
mode = dark
neon_mode = false
gray_scale = 0
dark_offset = 0.2
bright_offset = 0.2
invert = false
random = false
quiet = false
json = false
skip_term = false
skip_lum = false
debug = false
no_cache = false
EOF
}

read_config_value() {
    local section="$1"
    local key="$2"
    local default_value="$3"
    local cache_key="${section}:${key}"
    local config_file
    
    [[ -n "${CONFIG_CACHE[$cache_key]}" ]] && {
        echo "${CONFIG_CACHE[$cache_key]}"
        return
    }
    
    config_file=$(get_active_config_file)
    if [ -z "$config_file" ]; then
        CONFIG_CACHE[$cache_key]="$default_value"
        echo "$default_value"
        return
    fi
    
    local value=$(awk -v section="$section" -v key="$key" '
        BEGIN { in_section = 0 }
        /^\[.*\]$/ { in_section = (substr($0, 2, length($0)-2) == section) }
        in_section && /^[[:space:]]*[^#]/ {
            if (match($0, "^[[:space:]]*" key "[[:space:]]*=")) {
                sub("^[[:space:]]*" key "[[:space:]]*=[[:space:]]*", "")
                print $0
                exit
            }
        }
    ' "$config_file")
    
    value=${value:-$default_value}
    CONFIG_CACHE[$cache_key]="$value"
    echo "$value"
}

load_config() {
    local config_file=$(get_active_config_file)
    [ -z "$config_file" ] && return
    
    log_message "Loading configuration"
    
    local wp_dir=$(read_config_value "General" "wallpaper_dir" "$HOME/wallpapers")
    wp_dir=${wp_dir/#\~/$HOME}
    WALLPAPER_DIR="$wp_dir"
    
    local cache=$(read_config_value "General" "cache_dir" "$HOME/.cache/wallpapers")
    cache=${cache/#\~/$HOME}
    CACHE_DIR="$cache"
    
    BLUR_AMOUNT=$(read_config_value "General" "blur_amount" "50x30")
    DEFAULT_GENERATOR=$(read_config_value "General" "default_generator" "pywal")
    TRANSITION_TYPE=$(read_config_value "General" "transition_type" "grow")
}

get_available_generators() {
    [ -n "$AVAILABLE_GENERATORS_CACHE" ] && {
        echo "$AVAILABLE_GENERATORS_CACHE"
        return
    }
    
    local available_gens=""
    local generators_found=false
    
    while IFS=':' read -r gen_name enabled priority; do
        [[ "$gen_name" =~ ^#.*$ ]] || [[ -z "$gen_name" ]] && continue

        if [ "$enabled" = "true" ] && find_generator_script "$gen_name" >/dev/null; then
            available_gens="$available_gens$gen_name:$priority "
            generators_found=true
        fi
    done < "$GENERATOR_CONFIG"

    if [ "$generators_found" = true ]; then
        AVAILABLE_GENERATORS_CACHE=$(echo "$available_gens" | tr ' ' '\n' | sort -t: -k2 -n | cut -d: -f1)
        echo "$AVAILABLE_GENERATORS_CACHE"
    else
        echo "$DEFAULT_GENERATOR"
    fi
}

is_cache_valid() {
    local cache_file="$1"
    [ -f "$cache_file" ] || return 1
    
    local cache_age=$(( $(date +%s) - $(stat -c %Y "$cache_file") ))
    [ $cache_age -lt $CACHE_EXPIRY_SECONDS ]
}

execute_generator_script() {
    local script_path="$1"
    local wallpaper_path="$2"
    local config_file=$(get_active_config_file)
    
    case "$script_path" in
        *.py)
            if [ -n "$config_file" ]; then
                python3 "$script_path" --image "$wallpaper_path" --config "$config_file"
            else
                python3 "$script_path" --image "$wallpaper_path"
            fi
            ;;
        *.sh)
            "$script_path" "$wallpaper_path"
            ;;
    esac
}

run_color_generator() {
    local generator="$1"
    local wallpaper_path="$2"
    local wallpaper_hash=$(md5sum "$wallpaper_path" | cut -d' ' -f1)
    local cache_file="$CACHE_DIR/colors/${generator}_${wallpaper_hash}.cache"
    local script_path
    
    if is_cache_valid "$cache_file"; then
        log_message "Using cached color scheme for $(basename "$wallpaper_path")"
        return 0
    fi
    
    if script_path=$(find_generator_script "$generator"); then
        log_message "Running $generator color generator"
        if execute_generator_script "$script_path" "$wallpaper_path"; then
            touch "$cache_file"
            return 0
        fi
    else
        log_message "Error: Generator '$generator' not found"
    fi
    
    return 1
}

build_wallpaper_cache() {
    [ -n "$WALLPAPER_LIST_CACHE" ] && return
    
    local find_args="-type f \\("
    for i in "${!SUPPORTED_EXTENSIONS[@]}"; do
        [ $i -gt 0 ] && find_args+=" -o"
        find_args+=" -name \"*.${SUPPORTED_EXTENSIONS[$i]}\""
    done
    find_args+=" \\)"
    
    WALLPAPER_LIST_CACHE=$(eval "find \"$WALLPAPER_DIR\" $find_args 2>/dev/null")
}

select_wallpaper() {
    local mode="$1"
    local specific_path="$2"
    local current_wp_file="$CACHE_DIR/current_wallpaper"
    
    case "$mode" in
        "init")
            if [ -f "$current_wp_file" ] && [ -f "$(cat "$current_wp_file")" ]; then
                cat "$current_wp_file"
            elif [ -f "$WALLPAPER_DIR/default.png" ]; then
                echo "$WALLPAPER_DIR/default.png"
            else
                build_wallpaper_cache
                echo "$WALLPAPER_LIST_CACHE" | head -1
            fi
            ;;
        "specific")
            if [ -f "$specific_path" ]; then
                echo "$specific_path"
            else
                log_message "Error: Specified wallpaper not found: $specific_path"
                return 1
            fi
            ;;
        *)
            build_wallpaper_cache
            echo "$WALLPAPER_LIST_CACHE" | shuf -n 1
            ;;
    esac
}

find_swww_helper() {
    if [[ -f "$SCRIPT_DIR/swww.py" ]]; then
        echo "$SCRIPT_DIR/swww.py"
    elif [[ -f "$LOCAL_DIR/swww.py" ]]; then
        echo "$LOCAL_DIR/swww.py"
    else
        return 1
    fi
}

apply_wallpaper() {
    local wallpaper_path="$1"
    local transition_theme="${2:-$TRANSITION_TYPE}"
    local swww_helper
    
    case "$transition_theme" in
        smooth|dramatic|minimal|dynamic|random) ;;
        *) transition_theme="random" ;;
    esac
    
    if command_exists swww; then
        log_message "Applying wallpaper with swww (theme: $transition_theme)"
        if swww_helper=$(find_swww_helper); then
            python3 "$swww_helper" "$wallpaper_path" --theme "$transition_theme"
        else
            log_message "Error: swww helper not found"
        fi
    else
        log_message "Warning: swww not found, skipping wallpaper application"
    fi
}

create_blurred_wallpaper() {
    local wallpaper_path="$1"
    local wallpaper_name=$(basename "$wallpaper_path")
    local cached_blur="$CACHE_DIR/blurred/$wallpaper_name"
    local blurred_wp_file="$CACHE_DIR/current_wallpaper_blurred.png"
    
    if [ -f "$cached_blur" ]; then
        log_message "Using cached blurred version"
        cp "$cached_blur" "$blurred_wp_file"
        return 0
    fi

    if command_exists magick; then
        log_message "Creating blurred version"
        magick "$wallpaper_path" -strip -resize 1920x1080\! "$wallpaper_path.tmp"
        log_message "Resized wallpaper"

        if [ "$BLUR_AMOUNT" != "0x0" ]; then
            magick "$wallpaper_path.tmp" -strip -blur "$BLUR_AMOUNT" "$blurred_wp_file"
            cp "$blurred_wp_file" "$cached_blur"
            rm -f "$wallpaper_path.tmp"
            log_message "Created blurred wallpaper"
        else
            mv "$wallpaper_path.tmp" "$blurred_wp_file"
            cp "$blurred_wp_file" "$cached_blur"
        fi
    else
        log_message "Warning: ImageMagick not found, skipping blurred wallpaper creation"
    fi
}

save_current_wallpaper() {
    local wallpaper_path="$1"
    echo "$wallpaper_path" > "$CACHE_DIR/current_wallpaper"
    log_message "Updated current wallpaper file"
}

update_system_components() {
    if command_exists hyprctl; then
        hyprctl reload >/dev/null 2>&1 || true
    fi
    
    if command_exists gdbus; then
        gdbus emit --session --object-path /org/wallselector --signal org.wallselector.Changed >/dev/null 2>&1 || true
    fi
}

main() {
    local mode="${1:-random}"
    local specific_wallpaper="$2"
    local requested_generator="$3"
    local start_time=$(date +%s.%N)

    log_message "Starting wallpaper switcher (mode: $mode)"

    ensure_directories
    init_generator_config
    init_main_config
    load_config

    local selected_wallpaper
    selected_wallpaper=$(select_wallpaper "$mode" "$specific_wallpaper")

    if [ $? -ne 0 ] || [ -z "$selected_wallpaper" ]; then
        log_message "Error: Could not select wallpaper"
        exit 1
    fi

    log_message "Selected wallpaper: $(basename "$selected_wallpaper")"

    local generator_to_use="$requested_generator"
    if [ -z "$generator_to_use" ]; then
        generator_to_use=$(get_available_generators | head -1)
        [ -z "$generator_to_use" ] && generator_to_use="$DEFAULT_GENERATOR"
    fi

    apply_wallpaper "$selected_wallpaper"
    save_current_wallpaper "$selected_wallpaper"
    
    local fast_end_time=$(date +%s.%N)
    local fast_execution_time=$(echo "$fast_end_time - $start_time" | bc)
    fast_execution_time=$(printf "%.2f" $fast_execution_time)
    
    log_message "Fast wallpaper applied in $fast_execution_time seconds"
    
    {
        log_message "Starting background processing with $generator_to_use"
        
        if ! run_color_generator "$generator_to_use" "$selected_wallpaper"; then
            log_message "Warning: Color generator failed, but continuing..."
        fi
        
        create_blurred_wallpaper "$selected_wallpaper"
        update_system_components
        
        local end_time=$(date +%s.%N)
        local execution_time=$(echo "$end_time - $start_time" | bc)
        execution_time=$(printf "%.2f" $execution_time)
        
        log_message "Background processing completed in $execution_time seconds"
    } &
    
    return 0
}

show_help() {
    cat << EOF
Wallpaper Switcher with Multiple Color Generators

Usage: $0 [MODE] [WALLPAPER_PATH] [GENERATOR]

Modes:
    init        Use current/default wallpaper
    random      Select random wallpaper (default)
    specific    Use specific wallpaper (requires WALLPAPER_PATH)

Arguments:
    WALLPAPER_PATH    Path to specific wallpaper (for 'specific' mode)
    GENERATOR         Color generator to use (pywal, matugen, etc.)

Examples:
    $0                                    # Random wallpaper with default generator
    $0 init                               # Use current/default wallpaper
    $0 random pywal                       # Random wallpaper with pywal
    $0 specific ~/wallpapers/sunset.jpg   # Specific wallpaper
    $0 specific ~/wallpapers/sunset.jpg matugen  # Specific wallpaper with matugen

Configuration:
    Config file:       $CONFIG_FILE
    Generators config: $GENERATOR_CONFIG
EOF
}

MODE="random"
WALLPAPER_PATH=""
GENERATOR=""

case "$1" in
    "-h"|"--help"|"help")
        show_help
        exit 0
        ;;
    *)
        MODE="${1:-random}"
        shift
        if [ -n "$1" ]; then
            if [ -f "$1" ]; then
                WALLPAPER_PATH="$1"
                shift
                [ -n "$1" ] && GENERATOR="$1"
            else
                GENERATOR="$1"
            fi
        fi
        ;;
esac

main "$MODE" "$WALLPAPER_PATH" "$GENERATOR"