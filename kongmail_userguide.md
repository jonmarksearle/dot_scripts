# 🦍 Kongmail: The Ultimate Guide to Taming Gmail Bloat
### *Or: How to reclaim your RAM without losing your sanity.*

**Version 1.0**

---

## 1. Introduction: Why is my laptop screaming?

G'day, legends. 👋

Let’s be honest for a second. The modern web is a bit of a porker.

You fire up your browser just to check an email, and suddenly your laptop fans are screaming like a banshee, your RAM usage is climbing faster than a climber on Uluru (back when you could climb it), and your battery percentage is dropping like a stone. You’re not mining crypto. You’re not rendering Pixar’s next movie. You’re just trying to read a message from your mum.

It’s ridiculous. It’s bloated. And quite frankly, it’s un-Australian to make a computer work that hard for something so simple.

Modern Gmail is a "Single Page Application" (SPA). That means when you load it, you aren't just downloading a web page; you're downloading an entire software suite. Chat, Meet, spellcheckers, offline caching engines, predictive text AI—it all gets shoved into your browser's memory.

**Kongmail** is the solution. It’s a precision-engineered utility that configures the lightweight **Falkon** browser to force Google to serve you the mobile-optimized version of Gmail. It’s fast, it’s light, and it runs in complete isolation from your main browser.

---

## 2. The Philosophy: Sanity Over Purity

I built `kongmail.sh` with one core philosophy: **Robustness**.

A "safe" script asks you for permission every five seconds. A **robust** script knows what it’s doing, checks for hazards, and gets the job done without fuss.

We believe in:
1.  **Don't ask questions you know the answer to.** (If you run the script, you want the fix.)
2.  **Don't hide the mess.** (Backups should be visible and accessible.)
3.  **Fail fast, fail safe.** (If the browser is open, stop. Don't corrupt the config.)
4.  **Use the right tool for the job.** (Bash for the flow, Python for the logic.)

---

## 3. Technical Deep Dive: Under the Hood

Kongmail isn't just a hacked-together shell script. It's built like a brick outhouse.

### 🛡️ The Holy Trinity of Safety
Every execution starts with `set -euo pipefail`.
*   **`-e`:** Exit immediately if any command fails. No cascading disasters.
*   **`-u`:** Exit if a variable is undefined. No `rm -rf /` accidents.
*   **`-o pipefail`:** Catch errors even when they happen inside a pipeline.

### 🔒 Atomic Process Checking
Browsers love to overwrite their config files on exit. If we edit `settings.ini` while Falkon is running, Falkon will just overwrite our work when it closes.
Kongmail checks the process table (`pgrep -x falkon`). If Falkon is running, it stops and tells you to close it. No data corruption, ever.

### 🐍 Precision Python Injection
We don't use `sed` or regex to edit configuration files. That's a recipe for disaster.
Kongmail embeds a Python script that uses the `configparser` library to:
1.  Read the INI file structure.
2.  Understand Sections and Keys.
3.  Safely modify *only* the User Agent string.
4.  Write it back without mangling your other settings.

### 💾 Timestamped Backups
Before we touch a single byte, we create a backup.
*   Format: `settings.ini.kongmail_bak.YYYYMMDD_HHMMSS`
*   Location: Right next to the original file.
*   Benefit: Instant visibility and easy rollback.

---

## 4. User Guide: How to Use Kongmail

### Prerequisites
*   A Linux system (Debian/Ubuntu/Pop!_OS based).
*   `sudo` privileges (to install Falkon).

### Scenario A: The "Daily Driver" Setup (Quickest)
You want to use Falkon as your main browser, but you want Gmail to be fast.

**Command:**
```bash
./kongmail.sh --launch
```

**What happens:**
1.  Installs Falkon.
2.  Backs up your default profile config.
3.  Sets the Global User Agent to an iPad.
4.  Launches Falkon pointed at Gmail.

**Pros:** fast setup.
**Cons:** *Every* site you visit in Falkon will think you are on an iPad.

### Scenario B: The "Dedicated App" Setup (Recommended) 🏆
You want your normal browsing to be normal, but you want a special, isolated "Gmail App" that is ultra-fast.

**Command:**
```bash
./kongmail.sh --gmail-profile --launch
```

**What happens:**
1.  Creates a brand new Falkon profile named `gmail-mobile`.
2.  Configures *only* that profile to act like an iPad.
3.  Launches Falkon in that specific profile.

**Pros:**
*   Total isolation. Your main Falkon profile (if you use it) is untouched.
*   Cookies and history are separate.
*   You get the best of both worlds.

### Scenario C: The "Oops" (Restoring)
You want to go back to how things were.

**Command:**
```bash
# If you used the default profile:
./kongmail.sh --restore

# If you used the gmail-profile:
./kongmail.sh --gmail-profile --restore
```

**What happens:**
1.  Finds the most recent timestamped backup for that profile.
2.  Copies it back to `settings.ini`.
3.  You are back to stock settings.

---

## 5. Ongoing Maintenance

### Updating
Falkon is installed via your system package manager (`apt`). It will update automatically when you run your system updates. Kongmail doesn't need to do anything.

### If Google Changes Things
Occasionally, Google might change how they detect mobile devices. If the "iPad" trick stops working:
1.  Open `kongmail.sh` in a text editor.
2.  Look for the `MOBILE_UA` variable.
3.  Update it to a newer User Agent string (you can find these online).
4.  Run `./kongmail.sh --gmail-profile` again to apply the new string.

---

## 6. Troubleshooting

### "Falkon is running. Please close it first."
**Cause:** You have Falkon open.
**Fix:** Close the browser. If it's stuck, run `killall falkon` in your terminal.

### "Permission denied"
**Cause:** The script isn't executable.
**Fix:** Run `chmod +x kongmail.sh`.

### "Backup failed"
**Cause:** Weird file permissions in your home directory.
**Fix:** Check that you own your `~/.config` directory. Run `chown -R $USER:$USER ~/.config/falkon`.

### "I still see the Desktop view"
**Cause:** Google might have cached the old view.
**Fix:**
1.  In Falkon, go to **Preferences > Privacy**.
2.  Clear Cookies and Cache.
3.  Restart Falkon.

### "Why Falkon? Why not Firefox/Chrome?"
**Answer:**
Falkon is based on QtWebEngine (which is basically Chromium), but it strips out all the "Google stuff." No telemetry, no heavy account sync services running in the background. It is significantly lighter on RAM than full Chrome, making it the perfect candidate for this specific job.

---

## 7. FAQ

**Q: Will this delete my emails?**
A: No. We are changing how the *browser* presents itself to Google. We are not touching your account data.

**Q: Can I use this for other heavy sites?**
A: Absolutely! If you create a profile for, say, `youtube-mobile`, you could force YouTube to serve you the lighter mobile site too. You'd just need to hack the script slightly to accept a custom profile name.

**Q: Is this safe?**
A: Yes. The script is open-source (it's a shell script, you can read it!). It only touches config files inside `~/.config/falkon`. It acts with the permission of your user account.

---

**Kongmail.**
Because life is too short for loading bars.

