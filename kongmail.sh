#!/usr/bin/env bash
set -euo pipefail

# Kongmail Utility (v1.0)
# Installs Falkon, auto-configures the mobile User Agent, and supports Dedicated Gmail Profiles.

DEFAULT_PROFILE="default"
GMAIL_PROFILE="gmail-mobile"

# By default, we modify the main profile.
# If user passes --gmail-profile, we switch targets.
TARGET_PROFILE="$DEFAULT_PROFILE"
IS_GMAIL_PROFILE=false

# 1. Parse Arguments (Before we do anything else)
for arg in "$@"; do
    case "$arg" in
        --gmail-profile)
            TARGET_PROFILE="$GMAIL_PROFILE"
            IS_GMAIL_PROFILE=true
            ;;
        --help)
            echo "✨ [Kongmail] Utility Options:"
            echo "   ./kongmail.sh                 - Setup your main browser for lightweight Gmail."
            echo "   ./kongmail.sh --gmail-profile - Create a SEPARATE 'app-like' profile just for Gmail."
            echo "   ./kongmail.sh --launch        - Do the above AND launch it."
            echo "   ./kongmail.sh --restore       - Undo the last change to the selected profile."
            exit 0
            ;;
    esac
done

CONFIG_ROOT="$HOME/.config/falkon/profiles"
CONFIG_DIR="$CONFIG_ROOT/$TARGET_PROFILE"
SETTINGS_FILE="$CONFIG_DIR/settings.ini"

# Function to list backups
list_backups() {
    ls "$CONFIG_DIR"/settings.ini.kongmail_bak.* 2>/dev/null || true
}

# Handle Restore Mode
if [[ "${1:-}" == "--restore" ]]; then
    echo "↺ [Kongmail] Rewinding time for profile: '$TARGET_PROFILE'..."
    LATEST_BACKUP=$(ls -t "$CONFIG_DIR"/settings.ini.kongmail_bak.* 2>/dev/null | head -n 1 || true)
    
    if [[ -n "$LATEST_BACKUP" ]]; then
        cp -v "$LATEST_BACKUP" "$SETTINGS_FILE"
        echo "✅ [Kongmail] Restored settings from $(basename "$LATEST_BACKUP")"
    else
        echo "❌ [Kongmail] No backups found for profile '$TARGET_PROFILE'."
    fi
    exit 0
fi

echo "✨ [Kongmail] Optimizing Gmail for profile: '$TARGET_PROFILE'"

# 0. Check for running instance
if pgrep -x "falkon" > /dev/null; then
    echo "⚠️  [Kongmail] Falkon is running. Please close it first."
    exit 1
fi

# 1. Install Falkon
echo "📦 [Kongmail] Installing Falkon..."
sudo apt update -qq
sudo apt install -y falkon

# 2. Configure User Agent automatically
MOBILE_UA="Mozilla/5.0 (iPad; CPU OS 12_4 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/12.1.2 Mobile/15E148 Safari/604.1"

echo "⚙️ [Kongmail] Tuning the engine..."

# Ensure config directory exists
mkdir -p "$CONFIG_DIR"

# 3. Create Timed Backup & Inject Config
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
is_new_profile = not os.path.exists(config_file)

# Backup Logic (Only if file exists)
if os.path.exists(config_file):
    try:
        shutil.copy2(config_file, backup_file)
        print(f'💾 [Kongmail] Backup saved: {os.path.basename(backup_file)}')
    except Exception as e:
        print(f'⚠️ [Kongmail] Warning: Backup failed ({e})')

config = configparser.ConfigParser()
config.optionxform = str

# Read existing config
if os.path.exists(config_file):
    try:
        config.read(config_file)
    except Exception as e:
        print(f'⚠️ [Kongmail] Fresh start (config unreadable: {e})')

# Ensure 'Browsing' section exists
if 'Browsing' not in config:
    config['Browsing'] = {}

# Set the UA
config['Browsing']['UserAgent'] = ua_string

try:
    with open(config_file, 'w') as f:
        config.write(f)
    print(f'✅ [Kongmail] Configuration applied to {config_file}')
except Exception as e:
    print(f'❌ [Kongmail] Error writing config: {e}')
    sys.exit(1)
"

# 4. Final Polish & Launch
if [[ "${*:-}" == *"--launch"* ]]; then
    echo "🚀 [Kongmail] Launching Gmail in profile: '$TARGET_PROFILE'..."
    if [[ "$TARGET_PROFILE" == "$DEFAULT_PROFILE" ]]; then
        falkon "https://mail.google.com" &
    else
        falkon -p "$TARGET_PROFILE" "https://mail.google.com" &
    fi
else
    cat <<MSG

🎉 [Kongmail] All done!

Profile '$TARGET_PROFILE' is now optimized for minimal RAM usage.

🚀 To launch:
   ${TARGET_PROFILE == "$DEFAULT_PROFILE" ? "falkon" : "falkon -p $TARGET_PROFILE"} https://mail.google.com

↺  To undo:
   ./kongmail.sh ${IS_GMAIL_PROFILE == true ? "--gmail-profile " : ""}--restore

MSG
fi
