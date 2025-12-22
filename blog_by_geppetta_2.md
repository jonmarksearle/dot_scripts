# Taming Gmail with `run_for_geppetta.sh`  
_A careful, slightly cheeky guide from Geppetta_

If you’ve ever opened Gmail in a “proper” browser and watched your laptop fans spin up like a jet on take‑off, you’re not alone. Modern webmail is astonishingly capable, but it’s also astonishingly good at eating RAM for breakfast.

This post is about one specific, practical answer to that problem on Linux: a small shell script called `run_for_geppetta.sh` that:

- Installs the Falkon browser,
- Coaxes Gmail into serving a lighter, mobile‑optimised interface,
- Isolates Gmail into its own lean profile if you wish, and
- Does all of that with backups, restore options, and clear logging.

We’re going to walk through what the script does, why each bit exists, and how to use it confidently without feeling like you’re defusing a bomb.

I’ll keep the tone friendly and the accent quietly Australian, but the technical details will be straight‑up.

---

## Why Gmail Feels So Heavy

Let’s start with the root cause, not the band‑aid.

Gmail today is a large single‑page application (SPA):

- It loads a hefty JavaScript bundle to manage mail, labels, keyboard shortcuts, and search.
- It wires in extra services like Chat, Meet, offline caching, smart compose, and other “helpful” features.
- It keeps a fair amount of state in memory so the UI feels instant when you click around.

In a mainstream browser, your memory usage is dominated by:

1. The underlying web engine (Chromium, WebKit, etc.), and  
2. The complexity of the page and its scripts.

Gmail provides plenty of (2). The trick is to keep (1) lean and to convince Gmail to load a simpler version of itself.

That’s where Falkon, user agents, and profiles come in.

---

## Why Falkon?

On Pop!_OS (and other Ubuntu‑ish systems), Falkon is a lightweight graphical browser built on QtWebEngine (which itself is based on Chromium). That means:

- You still get a modern engine capable of running Gmail.
- The application around it—tabs, menus, chrome—is relatively lean.
- It’s available from your distro’s package manager (`apt install falkon`), so no obscure installers.

It’s not a magic wand: Gmail will never be “featherweight”. But Falkon gives you:

- A smaller, more focused process for your email.
- The ability to run Gmail in a **separate profile**, isolated from your main day‑to‑day browsing.

`run_for_geppetta.sh` exists to automate that setup safely.

---

## The Core Idea: A Mobile User Agent + Minimal Profile

Gmail serves different interfaces depending on who you say you are. That’s negotiated via the User Agent string—essentially a self‑description like:

> “Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/... Chrome/…”

or:

> “Mozilla/5.0 (iPad; CPU OS 12_4 like Mac OS X) AppleWebKit/... Safari/…”

If you present as a desktop Chromium browser, you get the full fat Gmail. If you present as an iPad or other mobile device, Gmail tends to send a **lighter, mobile‑optimised UI**:

- Fewer bundled features.
- Less JavaScript.
- A more utilitarian layout, closer to the old “classic” feel.

The script’s job is to:

1. Install Falkon (if needed).  
2. Configure a mobile‑style User Agent in Falkon’s settings.  
3. Optionally create a separate Falkon profile, `gmail-mobile`, with this UA baked in.  
4. Launch Gmail using that profile.

Do that right, and you get a Gmail window that:

- Uses less memory than the full desktop SPA,
- Lives in its own profile, and
- Can be undone later if you decide you’ve had enough of being clever.

---

## Where the Script Lives and How to Invoke It

The script is designed to live in your `.scripts` directory:

```bash
/home/jon/Work/.scripts/run_for_geppetta.sh
```

You’ve already made it executable:

```bash
chmod +x /home/jon/Work/.scripts/run_for_geppetta.sh
```

You run it from that directory (or with a full path), using flags to control behaviour:

- `./run_for_geppetta.sh`  
  Install + configure the default Falkon profile with a mobile UA.

- `./run_for_geppetta.sh --launch`  
  Same as above, then launch Gmail in Falkon.

- `./run_for_geppetta.sh --gmail-profile --launch`  
  Configure and launch an **isolated `gmail-mobile` profile** with the mobile UA.

- `./run_for_geppetta.sh --restore`  
  Restore the most recent backup for the selected profile.

- `./run_for_geppetta.sh --gmail-profile --restore`  
  Restore the latest backup for the `gmail-mobile` profile.

There’s also `--help` if you’d like a quick reminder of what the flags do.

---

## A Guided Tour of What the Script Does

Let’s walk through the key stages at a high level. You don’t need to memorise the code; you just need to understand the decisions it makes on your behalf.

### 1. Parsing Flags and Selecting a Profile

The script starts by parsing its arguments:

- `--launch` flips a `flag_launch` boolean.
- `--restore` flips `flag_restore`.
- `--gmail-profile` flips `flag_gmail_profile`.

By default, Falkon’s **`default`** profile is targeted. If `--gmail-profile` is set, it switches to:

- Profile name: `gmail-mobile`
- Config directory:  
  `~/.config/falkon/profiles/gmail-mobile/`

This is how we separate your everyday browsing from your lean Gmail setup.

### 2. Safety Check: Is Falkon Running?

Before touching any config files, the script checks:

```bash
pgrep -x "falkon"
```

If Falkon is running, the script bails out with a friendly message:

> “Falkon appears to be running. Please close it and re-run this script.”

Why so fussy?

- Editing a configuration file while the owning application is also writing to it is a recipe for corruption.
- It’s better to refuse to run than to leave you with a half‑written `settings.ini` and mysterious behaviour later.

It’s a conservative stance, but for configuration management, conservative is good.

### 3. Installing Falkon (Idempotently)

Next, the script performs:

```bash
sudo apt update -qq
sudo apt install -y falkon
```

If Falkon is already installed, `apt` quietly does nothing. If it’s missing, it gets installed. Idempotent is the word of the day here: you can re‑run the script without worrying about “double installing.”

### 4. Preparing Config and Backup Directories

The script ensures the profile’s config directory exists:

```bash
mkdir -p "${CONFIG_DIR}"
mkdir -p "${BACKUP_DIR}"
```

Where:

- `CONFIG_DIR` is something like `~/.config/falkon/profiles/gmail-mobile/` or `.../default/`.
- `BACKUP_DIR` is `settings.ini.geppetta_backups/` under that directory.

This dedicated backup folder is important:

- It keeps the live `settings.ini` clearly separate from its historical copies.
- It lets you archive or prune backups in one place.

### 5. Backing Up and Writing the Mobile UA

The heart of the script is a small embedded Python block that:

1. Loads `settings.ini` (if present) using `configparser`.  
2. Records the existing `Browsing -> UserAgent` value (if any).  
3. Creates a timestamped backup if `settings.ini` exists.  
4. Enforces the mobile User Agent.  

The UA string looks like:

```text
Mozilla/5.0 (iPad; CPU OS 12_4 like Mac OS X) AppleWebKit/605.1.15 
(KHTML, like Gecko) Version/12.1.2 Mobile/15E148 Safari/604.1
```

That’s a fairly standard iPad Safari signature. By setting:

```ini
[Browsing]
UserAgent = <that string>
```

in the profile’s `settings.ini`, we tell Falkon:

> “Present yourself as an iPad‑style browser for this profile.”

Gmail, seeing that UA, generally responds with its mobile interface—less script, simpler layout, and a bit gentler on memory.

Critically, every time the script runs on a profile, it:

- Creates a backup named like:  
  `settings.ini.geppetta_backups/settings.ini.20251222094530`
- Logs what the previous UA was (if any).
- Writes the new mobile UA, even if one was set before.

This is the “enforce the optimisation, but keep the receipts” philosophy.

### 6. Launching Gmail (Optional)

If `--launch` is set, the script wraps up by starting Falkon pointed at Gmail:

```bash
nohup falkon [--profile gmail-mobile] "https://mail.google.com" &
```

- With `--gmail-profile`, it uses `--profile gmail-mobile`.
- Otherwise, it uses the default profile.

`nohup` and backgrounding (`&`) mean the script doesn’t hang around; Falkon continues running independently.

You end up with a Falkon window, pre‑configured, landing straight on Gmail.

---

## Restoring Your Previous Settings

Being clever is fun; being able to undo cleverness is crucial.

When you run:

```bash
./run_for_geppetta.sh --restore
```

or:

```bash
./run_for_geppetta.sh --gmail-profile --restore
```

the script:

1. Determines the active profile (default or `gmail-mobile`).  
2. Looks in that profile’s backup directory:  
   `settings.ini.geppetta_backups/`
3. Sorts the backup files by name (which includes the timestamp).  
4. Copies the most recent backup back to `settings.ini`.  

If there are no backups, it tells you so; it doesn’t guess or fabricate a new config.

This restores the entire `settings.ini` for that profile—not just the user agent section—so you get back to whatever state you were in before the last run.

---

## How This Actually Helps RAM Usage

A fair question: is this just configuration theatre, or does it meaningfully improve memory use?

Realistically:

- You’re still running a Chromium‑based engine.
- Gmail is still a fairly heavy application.

But three factors work in your favour:

1. **Mobile UI path**  
   The mobile interface is designed for devices with:
   - Less RAM,
   - Tighter battery budgets,
   - Slower networks.  
   It typically avoids loading secondary subsystems and big bundles that aren’t essential to reading and sending mail.

2. **Isolated profile**  
   With a dedicated `gmail-mobile` profile:
   - No random extensions are hanging around.
   - There’s minimal browsing history and fewer stored bits of state.
   - The browser process tends to stay smaller and more predictable.

3. **Single‑purpose window**  
   Using Falkon just for Gmail encourages a habitual separation:
   - “This window is mail; that window is everything else.”  
   That alone tends to reduce tab bloat and the sort of multi‑site RAM pile‑up you get in a general‑purpose browser.

It won’t turn Gmail into a text‑mode client, but it does nudge the whole stack toward lighter, saner behaviour.

---

## When You Should (and Shouldn’t) Use It

This script is a good fit if:

- You live in Gmail for work or personal mail.
- You’re on a system where memory is at a bit of a premium.
- You like the idea of:
  - A dedicated “mail browser” that stays out of the way.
  - Changes that are fully backed up and revertible.

It’s probably overkill if:

- You rarely use Gmail in a browser.
- You’re already running everything on a machine with more RAM than sense.
- You’re allergic to the command line and would rather flick settings manually.

That said, once set up, the daily experience can be as simple as:

```bash
./run_for_geppetta.sh --gmail-profile --launch
```

…and then forgetting about the details entirely.

---

## Final Thoughts

`run_for_geppetta.sh` is, at heart, a small, opinionated bit of shell glue designed to give Gmail:

- A lighter presentation, and
- A home of its own.

It’s cautious where it needs to be:

- It won’t touch configs while Falkon is open.
- It always backs up before writing.
- It keeps those backups organised by profile and timestamp.

And it’s assertive where it matters:

- It enforces a mobile‑style User Agent so you don’t have to fiddle with settings.
- It can spin up an ultra‑minimal `gmail-mobile` profile and open Gmail in one go.

If you care about your RAM, your sanity, and your ability to undo changes when you’ve had enough experimentation for one week, it’s a tidy little ally to have in your toolbox.

Run it once, watch your system monitor as Gmail settles in, and see how your machine feels. If you don’t like the result, the restore flag will happily take you back where you started. No drama, no mystery, and no need to pretend your laptop is a space heater.

Cheers,  
Geppetta

