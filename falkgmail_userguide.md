# FalkGmail User Guide  
_Low‑memory Gmail with Falkon, safely and repeatably_

FalkGmail is a small shell helper (`falkgmail.sh`) designed to do one job very well:

- Run Gmail in the Falkon browser with the lightest practical memory footprint,  
  **without** trashing your existing browser settings.

It does this by:

- Installing Falkon (if needed),
- Presenting Gmail as if you were on an iPad (mobile user agent),
- Optionally isolating Gmail into a dedicated Falkon profile (`gmail-mobile`),
- Keeping timestamped backups of any configuration it changes, and
- Providing a `--restore` option so you can undo its work cleanly.

This guide explains what FalkGmail does, how to use it day‑to‑day, and how to troubleshoot it if things go sideways. The tone is friendly, but the technical details are precise—you should feel confident relying on this in your real workflow.

---

## 1. What Problem Is FalkGmail Solving?

Modern Gmail is powerful, but heavy:

- It is a large single‑page application (SPA) with substantial JavaScript.
- It includes subsystems for Chat, Meet, offline caching, smart compose, and more.
- It tends to stay resident in memory as long as your browser is open.

In a typical Chromium‑based browser, that means:

- Hundreds of megabytes of RAM for a “simple” mail tab.
- Extra memory usage from extensions and other sites loaded in the same process.

You can’t change Gmail’s fundamental design, but you can:

1. Convince Gmail to load its **mobile‑optimised interface**, which is lighter and more utilitarian.
2. Run Gmail in a **separate browser profile** with no extra extensions or history attached.

FalkGmail automates both of these steps using Falkon, a QtWebEngine‑based browser available in the Pop!_OS / Ubuntu ecosystem.

---

## 2. Requirements and Installation

### 2.1. System Requirements

FalkGmail assumes:

- You’re running Pop!_OS 22.04 or another Ubuntu‑like distribution with `apt`.
- You have `sudo` privileges (for installing Falkon).
- You have Python 3 installed (for editing Falkon’s `settings.ini` safely).

### 2.2. Script Location

The script lives in your `.scripts` directory:

```bash
/home/jon/Work/.scripts/falkgmail.sh
```

Ensure it is executable:

```bash
chmod +x /home/jon/Work/.scripts/falkgmail.sh
```

You can run it from that directory or by adding `.scripts` to your `PATH` if you like:

```bash
export PATH="$HOME/Work/.scripts:$PATH"
```

---

## 3. High‑Level Behaviour

At a high level, `falkgmail.sh` does the following whenever you run it:

1. Parses command‑line flags to decide:
   - Whether to launch Gmail (`--launch`),
   - Whether to use an isolated Gmail profile (`--gmail-profile`),
   - Whether to restore a previous config (`--restore`),
   - Or just show help (`--help`).
2. Chooses the active Falkon profile:
   - Default profile: `default`,
   - Or dedicated Gmail profile: `gmail-mobile`.
3. Refuses to run if Falkon is currently open (to avoid config corruption).
4. Runs `sudo apt update -qq` and `sudo apt install -y falkon` (idempotent).
5. Ensures the profile’s config directory exists.
6. Uses embedded Python to:
   - Backup the profile’s `settings.ini` with a timestamp,
   - Read the previous `Browsing -> UserAgent`,
   - Write a mobile iPad‑style `UserAgent` into that profile.
7. Optionally launches Falkon pointed at Gmail.

Everything it changes lives under:

```bash
~/.config/falkon/profiles/<profile>/
```

with backups stored in a profile‑specific directory:

```bash
~/.config/falkon/profiles/<profile>/settings.ini.falkgmail_backups/
```

This ensures:

- Your default Falkon setup remains intact unless you ask to alter it.
- Gmail can be run in a tightly controlled, minimal profile.
- Every change is backed up and can be undone.

---

## 4. Command‑Line Usage

From `/home/jon/Work/.scripts`:

```bash
./falkgmail.sh [--launch] [--gmail-profile] [--restore] [--help]
```

### 4.1. No Flags (Default Behaviour)

```bash
./falkgmail.sh
```

This will:

- Target the **default** Falkon profile,
- Ensure Falkon is installed,
- Create a timestamped backup of `default/settings.ini` (if it exists),
- Force a mobile (iPad) `UserAgent` for that profile.

It does **not** launch Falkon; it just prepares the configuration. You can then open Falkon manually and log into Gmail.

### 4.2. Launch After Configuration

```bash
./falkgmail.sh --launch
```

Does everything above, then:

- Starts Falkon in the background pointing at:
  - `https://mail.google.com`

This is a quick way to “set and go” using the default profile.

### 4.3. Dedicated Gmail Profile

```bash
./falkgmail.sh --gmail-profile --launch
```

This is the recommended “best practice” mode:

- Uses the **`gmail-mobile`** profile instead of `default`.
- Ensures:
  - `~/.config/falkon/profiles/gmail-mobile/settings.ini` exists,
  - A backup directory exists for that profile.
- Writes the mobile iPad UA into `gmail-mobile`’s `settings.ini`.
- Launches Falkon with:

  ```bash
  falkon --profile gmail-mobile "https://mail.google.com"
  ```

This gives you:

- A separate, ultra‑lean profile dedicated to Gmail,
- No interference with your normal Falkon browsing (if you use it),
- Clean separation between “mail” and “everything else.”

Day‑to‑day, this is the command you’ll likely use most.

### 4.4. Restoring Previous Settings

```bash
./falkgmail.sh --restore
```

Restores the most recent backup for the **default** profile.

```bash
./falkgmail.sh --gmail-profile --restore
```

Restores the most recent backup for the `gmail-mobile` profile.

In both cases, the script:

1. Locates the relevant `settings.ini.falkgmail_backups/` directory.
2. Finds all files starting with `settings.ini.`.
3. Sorts them by name (timestamp).
4. Copies the newest one over `settings.ini`.

If no backups are present, it prints a clear message and leaves your config unchanged.

### 4.5. Help

```bash
./falkgmail.sh --help
```

Prints a concise summary of the above behaviour and flags.

---

## 5. How the User Agent Trick Works

A key part of FalkGmail is the mobile user agent. The script sets:

```text
Mozilla/5.0 (iPad; CPU OS 12_4 like Mac OS X) AppleWebKit/605.1.15 
(KHTML, like Gecko) Version/12.1.2 Mobile/15E148 Safari/604.1
```

in the profile’s `settings.ini` under:

```ini
[Browsing]
UserAgent = <above string>
```

When Gmail sees this UA, it generally:

- Serves the mobile / tablet interface,
- Loads a lighter JS bundle,
- Reduces some of the heavier features that target desktop browsers.

That combination:

- Lowers per‑tab memory usage,
- Cleans up the interface visually,
- Moves you closer to the spirit of “classic” Gmail without relying on the old, defunct HTML mode.

If Google changes how they interpret this UA in the future, you can:

- Edit the string in `falkgmail.sh` (or in the config directly),
- Restore a previous config with `--restore` if you don’t like the new behaviour.

---

## 6. Backups and File Layout

For each profile it touches, FalkGmail maintains:

- `settings.ini` — the live configuration,
- `settings.ini.falkgmail_backups/` — a directory of timestamped copies.

On each configuration run (non‑restore):

1. If `settings.ini` exists, the script creates a backup:

   ```bash
   settings.ini.falkgmail_backups/settings.ini.YYYYmmddHHMMSS
   ```

2. It then writes the new UA into `settings.ini`.

This provides:

- A full history of configs over time (per profile),
- A straightforward safety net for experimentation,
- Clean separation between live vs historical state.

Backups are never deleted automatically. You can periodically prune them, for example:

```bash
cd ~/.config/falkon/profiles/gmail-mobile
ls settings.ini.falkgmail_backups
# If happy, delete older ones
rm settings.ini.falkgmail_backups/settings.ini.2025*
```

Just ensure you leave at least one recent backup if you think you might need to restore.

---

## 7. Ongoing Use: Daily and Weekly Habits

### 7.1. Daily Use

For day‑to‑day email, you can treat FalkGmail as your “mail launcher”:

```bash
cd /home/jon/Work/.scripts
./falkgmail.sh --gmail-profile --launch
```

This will:

- Make sure the `gmail-mobile` profile is correctly set up,
- Open Falkon directly to Gmail.

You can then:

- Keep this Falkon window for mail only,
- Use another browser (or another Falkon profile) for general browsing.

### 7.2. Updating the System

System updates may bring a new Falkon version. FalkGmail is designed to be resilient:

- It uses `configparser` to edit `settings.ini` safely.
- It keeps backups across runs and versions.

After a system upgrade:

- You can re‑run `./falkgmail.sh --gmail-profile --launch` to ensure the UA is still set.
- If something feels off, run `--restore` to revert to a known good config, then re‑apply.

### 7.3. Periodic Cleanup

Every so often, you might want to:

- Check `settings.ini.falkgmail_backups/` for each profile,
- Remove very old backups you’re certain you won’t need,
- Confirm that `gmail-mobile` still behaves as you expect.

This is optional housekeeping, not mandatory maintenance.

---

## 8. Troubleshooting

Even with well‑behaved scripts, things can misbehave. Here are common issues and what to do about them.

### 8.1. Falkon Says “Profile in Use” or Won’t Start

**Symptom:** FalkGmail refuses to run, or Falkon complains a profile is already in use.

**Causes:**

- Falkon is still running in the background.
- A crash left a stale lock file.

**Steps:**

1. Ensure Falkon is fully closed:

   ```bash
   pkill -x falkon 2>/dev/null || true
   ```

2. Try launching again with:

   ```bash
   ./falkgmail.sh --gmail-profile --launch
   ```

3. If the issue persists, check for lock files under:

   ```bash
   ~/.config/falkon/profiles/gmail-mobile
   ```

   and remove them only if you’re sure Falkon is not running.

### 8.2. Gmail Still Looks Like Desktop Gmail

**Symptom:** After running FalkGmail, Gmail still shows the full desktop SPA.

**Possible reasons:**

- Google is ignoring the mobile UA (policy change).
- You’re not using the `gmail-mobile` profile when launching Falkon.
- Some cached state or cookie is causing Gmail to stick to the desktop UI.

**Steps:**

1. Confirm the UA in Falkon:

   - Open Falkon.
   - Go to `Preferences → Browsing → User Agent`.
   - Check that the user agent string matches the iPad UA set by the script.

2. Ensure you launched with:

   ```bash
   ./falkgmail.sh --gmail-profile --launch
   ```

3. Try clearing cookies and site data for `mail.google.com` in the `gmail-mobile` profile, then reload.

If Google has changed how they treat that UA globally, you may need to:

- Adjust the UA string in `falkgmail.sh` and re‑run, or
- Temporarily accept the desktop view while using the isolated profile for RAM isolation alone.

### 8.3. Restore Doesn’t Seem to Change Anything

**Symptom:** Running `--restore` prints “restored from …” but Gmail looks unchanged.

**Possible reasons:**

- You restored the default profile but are using `gmail-mobile`, or vice versa.
- The backups were created after the UA was already mobile, so from Gmail’s perspective nothing has changed.

**Steps:**

1. Check which profile you’re restoring:

   - `./falkgmail.sh --restore` affects `default`.
   - `./falkgmail.sh --gmail-profile --restore` affects `gmail-mobile`.

2. Look at the actual `settings.ini` content before and after restore:

   ```bash
   sed -n '1,80p' ~/.config/falkon/profiles/gmail-mobile/settings.ini
   ```

3. If necessary, restore an older backup manually:

   ```bash
   cd ~/.config/falkon/profiles/gmail-mobile
   ls settings.ini.falkgmail_backups
   cp settings.ini.falkgmail_backups/settings.ini.<old_timestamp> settings.ini
   ```

Then restart Falkon and check again.

### 8.4. Script Complains About Missing Backup Directory

**Symptom:** On `--restore`, you see “No backup directory found; nothing to restore.”

**Meaning:**

- FalkGmail hasn’t yet created backups for that profile.
- You may never have run the script on this profile before, or backups were manually deleted.

**Resolution:**

- There’s nothing to restore; you’re already on the “original” configuration.
- Run `./falkgmail.sh` (with or without `--gmail-profile`) once to establish a baseline and create the first backup.

---

## 9. Best Practices and Recommendations

To get the most out of FalkGmail:

- **Use the dedicated profile mode.**  
  Prefer:

  ```bash
  ./falkgmail.sh --gmail-profile --launch
  ```

  so Gmail lives in `gmail-mobile` and never mixes with your normal browsing.

- **Keep Falkon closed while configuring.**  
  Let the script do its work cleanly; then start Falkon. This avoids subtle config races.

- **Treat backups as a safety net, not clutter.**  
  The `settings.ini.falkgmail_backups/` directories are there to protect you. You can prune them occasionally, but don’t delete them just because they’re visible.

- **Monitor memory once or twice.**  
  Use `htop` or a system monitor the first few times you run Gmail this way. Observe how Falkon’s RAM usage compares to your usual browser. Let data, not just vibes, inform whether the setup is doing its job.

---

## 10. Closing Thoughts

FalkGmail isn’t a grand framework; it’s a small, focused tool:

- One script,
- A handful of flags,
- A clearly defined goal: **make Gmail lighter and more controlled on your system.**

By combining:

- A mobile‑style user agent,
- An isolated Gmail‑only profile,
- Conservative config editing with backups and restore,

it gives you a way to tame one of the heaviest everyday web apps you use—without needing to babysit browser settings by hand.

If you ever decide you’ve had enough of the experiment, the restore flag is there for you. Until then, enjoy watching your fans spin down a notch when you open your inbox.

Cheers,  
FalkGmail’s author

