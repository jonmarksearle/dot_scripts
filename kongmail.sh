#!/usr/bin/env bash
set -euo pipefail

# Kongmail Utility (v1.1 - Smart Launcher Edition)
# Installs Falkon (only if needed), Configures UA (only if changed), and Launches.

DEFAULT_PROFILE="default"
GMAIL_PROFILE="gmail-mobile"

TARGET_PROFILE="$DEFAULT_PROFILE"
IS_GMAIL_PROFILE=false
LAUNCH_MODE=false

# 1. Parse Arguments
for arg in "$@"; do
    case "$arg" in
        --gmail-profile)
            TARGET_PROFILE="$GMAIL_PROFILE"
            IS_GMAIL_PROFILE=true
            ;;
        --launch)
            LAUNCH_MODE=true
            ;;
        --restore)
            # We handle restore logic later, but we need to know args aren't just for launching
            ;;
        --help)
            echo "✨ [Kongmail] Utility Options:"
            echo "   ./kongmail.sh                 - Configure profile."
            echo "   ./kongmail.sh --launch        - Configure and Launch."
            echo "   ./kongmail.sh --gmail-profile - Use dedicated Gmail profile."
            exit 0
            ;;
    esac
done

CONFIG_ROOT="$HOME/.config/falkon/profiles"
CONFIG_DIR="$CONFIG_ROOT/$TARGET_PROFILE"
SETTINGS_FILE="$CONFIG_DIR/settings.ini"

# --- RESTORE LOGIC ---
if [[ "${1:-}" == "--restore" ]]; then
    echo "↺ [Kongmail] Rewinding time for profile: '$TARGET_PROFILE'..."
    LATEST_BACKUP=$(ls -t "$CONFIG_DIR"/settings.ini.kongmail_bak.* 2>/dev/null | head -n 1 || true)
    if [[ -n "$LATEST_BACKUP" ]]; then
        cp -v "$LATEST_BACKUP" "$SETTINGS_FILE"
        echo "✅ [Kongmail] Restored settings."
    else
        echo "❌ [Kongmail] No backups found."
    fi
    exit 0
fi

# --- SMART INSTALL ---
if ! command -v falkon >/dev/null 2>&1; then
    echo "📦 [Kongmail] Falkon not found. Installing..."
    sudo apt update -qq
    sudo apt install -y falkon
fi

# --- SMART CONFIG ---
MOBILE_UA="Mozilla/5.0 (iPad; CPU OS 12_4 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/12.1.2 Mobile/15E148 Safari/604.1"
NEEDS_CONFIG=true

# Check if config exists and already has the correct UA
if [ -f "$SETTINGS_FILE" ]; then
    # We use a simple grep to see if the UA is already there. 
    # It's a quick check to avoid firing up Python and blocking on processes.
    if grep -Fq "$MOBILE_UA" "$SETTINGS_FILE"; then
        NEEDS_CONFIG=false
    fi
fi

if [ "$NEEDS_CONFIG" = true ]; then
    echo "⚙️ [Kongmail] Configuration needed for profile: '$TARGET_PROFILE'"
    
    # Only check for running process if we actually need to write to the file
    if pgrep -x "falkon" > /dev/null; then
        echo "⚠️  [Kongmail] Falkon is running. Please close it to apply updates."
        exit 1
    fi

    mkdir -p "$CONFIG_DIR"

    # Python Injection
    python3 -c "
import configparser
import os
import shutil
import datetime
import sys

config_file = '$SETTINGS_FILE'
ua_string = '$MOBILE_UA'
timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
backup_file = f'{config_file}.kongmail_bak.{timestamp}'

if os.path.exists(config_file):
    try:
        shutil.copy2(config_file, backup_file)
    except: pass

config = configparser.ConfigParser()
config.optionxform = str

if os.path.exists(config_file):
    try: config.read(config_file)
    except: pass

if 'Browsing' not in config: config['Browsing'] = {}
config['Browsing']['UserAgent'] = ua_string

with open(config_file, 'w') as f:
    config.write(f)
"
    echo "✅ [Kongmail] Configuration applied."
else
    # Silent mode if everything is good
    :
fi

# --- LAUNCH ---
if [ "$LAUNCH_MODE" = true ]; then
    if [ "$TARGET_PROFILE" == "$DEFAULT_PROFILE" ]; then
        nohup falkon "https://mail.google.com" >/dev/null 2>&1 &
    else
        nohup falkon -p "$TARGET_PROFILE" "https://mail.google.com" >/dev/null 2>&1 &
    fi
fi
