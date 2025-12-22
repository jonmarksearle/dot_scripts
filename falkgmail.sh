#!/usr/bin/env bash
set -euo pipefail

# FalkGmail: Minimal-RAM Gmail in Falkon
# v3.1 — Installs Falkon, enforces a mobile-style UA for leaner Gmail,
# keeps timestamped backups, supports restore, can launch straight into Gmail,
# and (optionally) isolates Gmail into its own minimal profile so the rest of
# your browsing stays untouched.

PROFILE_NAME="default"
GMAIL_PROFILE_NAME="gmail-mobile"

CONFIG_ROOT="${HOME}/.config/falkon/profiles"
CONFIG_DIR="${CONFIG_ROOT}/${PROFILE_NAME}"
SETTINGS_FILE="${CONFIG_DIR}/settings.ini"
BACKUP_DIR="${SETTINGS_FILE}.falkgmail_backups"

# iPad-style UA string (mobile-optimized Gmail, closer to classic + lighter JS).
MOBILE_UA="Mozilla/5.0 (iPad; CPU OS 12_4 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/12.1.2 Mobile/15E148 Safari/604.1"

usage() {
  cat <<EOF
Usage: ./falkgmail.sh [--launch] [--gmail-profile] [--restore] [--help]

Without flags:
  - Ensures Falkon is not running.
  - Installs Falkon via apt if needed.
  - Creates a timestamped backup of the active profile's settings.ini.
  - Forces a mobile-style User Agent in Browsing -> UserAgent
    for the active profile to push Gmail onto a lighter, mobile-optimized code path.

--launch:
  - After configuration, starts Falkon pointed at Gmail.

--gmail-profile:
  - Instead of touching your main `default` profile, configures a dedicated
    ultra-minimal `gmail-mobile` profile with the mobile UA and (with --launch)
    starts Falkon using that profile only for Gmail.

--restore:
  - Restores the most recent backup for the active profile (default or gmail-mobile).

EOF
}

flag_launch=false
flag_restore=false
flag_gmail_profile=false

for arg in "$@"; do
  case "${arg}" in
    --help)
      usage
      exit 0
      ;;
    --launch)
      flag_launch=true
      ;;
    --restore)
      flag_restore=true
      ;;
    --gmail-profile)
      flag_gmail_profile=true
      ;;
    *)
      echo "[falkgmail] Unknown argument: ${arg}"
      usage
      exit 1
      ;;
  esac
done

# Switch to the dedicated Gmail profile if requested.
if "${flag_gmail_profile}"; then
  PROFILE_NAME="${GMAIL_PROFILE_NAME}"
  CONFIG_DIR="${CONFIG_ROOT}/${PROFILE_NAME}"
  SETTINGS_FILE="${CONFIG_DIR}/settings.ini"
  BACKUP_DIR="${SETTINGS_FILE}.falkgmail_backups"
fi

if "${flag_restore}"; then
  echo "[falkgmail] Restore mode activated for profile: ${PROFILE_NAME}"
  python3 - <<PYCODE
import os
from pathlib import Path
import shutil

settings = Path("${SETTINGS_FILE}")
backup_dir = Path("${BACKUP_DIR}")

if not backup_dir.exists():
    print("[falkgmail] No backup directory found; nothing to restore.")
else:
    backups = sorted(backup_dir.glob("settings.ini.*"))
    if not backups:
        print("[falkgmail] No backup files found in backup directory.")
    else:
        latest = backups[-1]
        shutil.copy2(latest, settings)
        print(f"[falkgmail] Restored Falkon settings for profile '${PROFILE_NAME}' from: {latest}")
PYCODE
  exit 0
fi

echo "[falkgmail] Preparing Falkon install/config (v3.1) for profile: ${PROFILE_NAME}…"

# Safety: avoid touching config while Falkon is running.
if pgrep -x "falkon" >/dev/null 2>&1; then
  echo "[falkgmail] Falkon appears to be running. Please close it and re-run this script."
  exit 1
fi

echo "[falkgmail] Updating apt package lists..."
sudo apt update -qq

echo "[falkgmail] Installing Falkon browser (if not already present)..."
sudo apt install -y falkon

echo "[falkgmail] Ensuring Falkon config directory exists at: ${CONFIG_DIR}"
mkdir -p "${CONFIG_DIR}"
mkdir -p "${BACKUP_DIR}"

echo "[falkgmail] Applying minimal-RAM UA configuration via embedded Python…"

python3 - <<PYCODE
import configparser
import os
import shutil
from datetime import datetime
from pathlib import Path

settings_path = Path("${SETTINGS_FILE}")
backup_dir = Path("${BACKUP_DIR}")
mobile_ua = "${MOBILE_UA}"

config = configparser.ConfigParser()
config.optionxform = str  # preserve key case

previous_ua = None
if settings_path.exists():
    try:
        config.read(settings_path)
        previous_ua = config.get("Browsing", "UserAgent", fallback=None)
    except Exception as exc:
        print(f"[falkgmail] Warning: could not read existing settings.ini ({exc}); starting from a fresh config.")

# Always create a timestamped backup if settings.ini exists.
if settings_path.exists():
    ts = datetime.now().strftime("%Y%m%d%H%M%S")
    backup_path = backup_dir / f"settings.ini.{ts}"
    try:
        shutil.copy2(settings_path, backup_path)
        print(f"[falkgmail] Backed up existing settings.ini for profile '${PROFILE_NAME}' to: {backup_path}")
    except OSError as exc:
        print(f"[falkgmail] Warning: could not backup settings.ini ({exc}); continuing without backup.")

if "Browsing" not in config:
    config["Browsing"] = {}

if previous_ua:
    print(f"[falkgmail] Previous Browsing->UserAgent detected for profile '${PROFILE_NAME}': {previous_ua!r}")

# Enforce mobile-style UA for leaner Gmail; user can restore via --restore if desired.
config["Browsing"]["UserAgent"] = mobile_ua

    try:
        with settings_path.open("w") as fh:
            config.write(fh)
        print(f"[falkgmail] Wrote mobile-style UserAgent into Falkon’s settings.ini for profile '{PROFILE_NAME}'.")
    except OSError as exc:
        print(f"[falkgmail] Error: failed to write settings.ini ({exc}).")

PYCODE

if "${flag_launch}"; then
  echo "[falkgmail] Launching Falkon to Gmail (background)…"
  if "${flag_gmail_profile}"; then
    nohup falkon --profile "${GMAIL_PROFILE_NAME}" "https://mail.google.com" >/dev/null 2>&1 &
  else
    nohup falkon "https://mail.google.com" >/dev/null 2>&1 &
  fi
fi

cat <<'EOF'

[falkgmail] Done.

A mobile-style (iPad) User Agent is now set in the selected Falkon profile
to encourage Gmail to serve its lighter, mobile-optimized interface and
reduce memory use.

If you used --gmail-profile, your everyday browsing profile remains untouched;
Gmail runs in a dedicated, ultra-lean profile for best isolation and lowest RAM.

Recommended checks (inside Falkon):
  1. Launch Falkon (or use --launch with this script).
  2. Open: Preferences → Browsing → Browsing → User Agent, confirm the UA value.
  3. Log into Gmail and verify you see the simplified mobile-style UI.

To restore your original settings for the selected profile from the most recent backup:
  ./falkgmail.sh --restore

EOF
