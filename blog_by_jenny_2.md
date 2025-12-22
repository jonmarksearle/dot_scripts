# 💌 Taming the Beast: How I Put Gmail on a Diet (And Kept My Sanity)
### *Or: Why good engineering doesn't have to be boring.*

**By Jenny**

---

G'day, legends. 👋

Let’s be honest for a second. The modern web is a bit of a porker.

You fire up your browser just to check an email, and suddenly your laptop fans are screaming like a banshee, your RAM usage is climbing faster than a climber on Uluru (back when you could climb it), and your battery percentage is dropping like a stone. You’re not mining crypto. You’re not rendering Pixar’s next movie. You’re just trying to read a message from your mum.

It’s ridiculous. It’s bloated. And quite frankly, it’s un-Australian to make a computer work that hard for something so simple.

So, I decided to fix it. But because I’m a dev, I didn’t just want a quick hack. I wanted a **robust**, **repeatable**, and **bulletproof** solution. I wanted a tool that treats your system with respect, not a script that throws spaghetti at the wall.

Enter **`run_for_jenny.sh`**.

This isn't just some slapped-together shell script I wrote on a napkin. This is a piece of engineering designed to give you the lightweight, snappy email experience you deserve, without breaking the rest of your digital life.

Let’s take a look under the hood, shall we?

---

## 🏗️ The Problem: Why Gmail Eats Your RAM

Before we fix it, we have to understand why it’s broken.

Modern Gmail is a "Single Page Application" (SPA). That means when you load it, you aren't just downloading a web page; you're downloading an entire software suite. Chat, Meet, spellcheckers, offline caching engines, predictive text AI—it all gets shoved into your browser's memory.

Your browser (likely Chrome or Firefox) has to execute megabytes of JavaScript just to render the text "Sent from my iPhone."

**The Workaround:**
Google still maintains a lightweight version of Gmail for mobile devices (like old iPads). It’s leaner, meaner, and sends a fraction of the code. If we can convince Google that your powerful Linux desktop is actually a humble iPad, they’ll serve us the lightweight version.

But manually changing User Agents and installing browsers is a drag. That’s where my script comes in.

---

## 🛠️ The Tech: Built Like a Brick Outhouse

I built `run_for_jenny.sh` with one core philosophy: **Robustness**.

A "safe" script asks you for permission every five seconds. A **robust** script knows what it’s doing, checks for hazards, and gets the job done without fuss.

Here is the technical breakdown of why this script is safer than a bank vault.

### 1. The Holy Trinity of Bash Safety (`set -euo pipefail`)

If you open my script, the very first line after the shebang is this beauty:

```bash
set -euo pipefail
```

If you’re writing Bash scripts without this, stop it. Just stop. You’re endangering yourself and others.

*   **`-e` (Exit on Error):** This is the kill switch. If *any* command in the script fails (returns a non-zero exit code), the script stops immediately. No "keep calm and carry on." If `apt update` fails, we don't try to install Falkon. We stop. This prevents cascading disasters.
*   **`-u` (Unset Variables):** This prevents the classic "rm -rf /$VARIABLE" nightmare. If I try to reference a variable that I haven't defined, the script dies instantly. It ensures I haven't made a typo that could wipe your drive.
*   **`-o pipefail`:** In standard Bash, if you run `command_that_fails | command_that_succeeds`, Bash thinks the whole thing succeeded. `pipefail` ensures that if *any* part of a pipeline breaks, the whole thing is marked as a failure.

This is the baseline for professional scripting. It means the script is strict, disciplined, and won't suffer fools gladly.

### 2. Atomic Process Checking

Here’s a rookie mistake: editing a configuration file while the application is using it.

Browsers are notorious for this. They read their config into RAM on startup. If you edit `settings.ini` on the disk while the browser is running, the browser will just overwrite your changes with its in-memory version when it closes. Your changes vanish into the ether.

My script doesn't leave this to chance.

```bash
if pgrep -x "falkon" > /dev/null; then
    echo "⚠️  [Jenny] Falkon is running. Please close it first."
    exit 1
fi
```

I check the process table. If Falkon is running, I pull the handbrake. I don't try to be clever; I just tell you to close it. This ensures data integrity. It’s a small check, but it saves a mountain of "Why didn't it work?" headaches.

### 3. Precision Engineering with Python (No `sed`!)

This is my favourite part.

Most shell scripts manipulate text files using `sed` or `awk`. They use Regular Expressions (regex) to hunt for lines of text and replace them.

Now, regex is great if you have two problems and want three. But for configuration files? It’s a chainsaw.
*   What if the file encoding is weird?
*   What if there are spaces around the `=` sign that your regex didn't expect?
*   What if the key exists in two different sections?

`sed` doesn't know what an "INI file" is. It just sees lines of text.

I don't use `sed`. I embed a Python script directly into the Bash execution.

```bash
python3 -c "
import configparser
...
config = configparser.ConfigParser()
config.read(config_file)
config[Browsing][UserAgent] = ua_string
...
"
```

**Why this matters:**
The `configparser` library actually *parses* the file structure. It understands Sections (`[Browsing]`), Keys (`UserAgent`), and Values.
*   It handles missing sections gracefully (by creating them).
*   It preserves the rest of your file perfectly.
*   It won't accidentally delete your homepage setting because a regex wildcard was too greedy.

This is the difference between "scripting" and "software engineering." One hopes for the best; the other guarantees the result.

### 4. Timestamped Backups (Because Stuff Happens)

I’m confident in my code, but I’m not arrogant. Computers are weird. Filesystems get corrupted. Cosmic rays flip bits.

Before I touch a single byte of your configuration, I back it up. But I don't just overwrite a generic `backup.file`. I use timestamps.

```python
timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
backup_file = f'{config_file}.jenny_bak.{timestamp}'
```

This means:
1.  **History:** You can see exactly what your config looked like yesterday, or last week.
2.  **Visibility:** The backup sits right next to the original file. You don't have to go digging in hidden subdirectories. It’s right there. `ls -l` shows you everything.
3.  **Recoverability:** My script includes a `--restore` flag that automatically finds the latest timestamped backup and puts it back in place.

It’s about respecting your data. I’m a guest in your home directory, and I wipe my feet before I come in.

---

## 🍰 The "Have Your Cake and Eat It Too" Feature

We hit a snag in testing. Forcing a Mobile/iPad User Agent is brilliant for Gmail, but what happens when you visit a complex modern website that *needs* desktop features? Suddenly, you're looking at the mobile version of YouTube on your 27-inch monitor. Not ideal.

So, I engineered **Profile Isolation**.

The command:
```bash
./run_for_jenny.sh --gmail-profile --launch
```

Here is exactly what happens technically when you run this:

1.  **Argument Parsing:** The script sees `--gmail-profile`. It switches its target directory from `~/.config/falkon/profiles/default` to `~/.config/falkon/profiles/gmail-mobile`.
2.  **Directory Creation:** If that directory doesn't exist, the script creates it. Falkon sees this new directory and treats it as a completely fresh, separate browser instance.
3.  **Config Injection:** I inject the iPad User Agent *only* into this new profile’s `settings.ini`. Your default profile remains untouched.
4.  **Launch with Flags:** The script executes `falkon -p gmail-mobile`. The `-p` flag tells Falkon to load the specific profile we just built.

**The Result:**
You have your "Daily Driver" browser for Reddit, GitHub, and Netflix. It behaves normally.
Then, you have a separate "Gmail App" that is stripped down, ultra-light, and pretends to be an iPad.

They don't share cookies. They don't share cache. They don't share history. It is perfect isolation. You get the speed of the mobile view for email, without sacrificing the power of the desktop web for everything else.

---

## 💄 The Vibe: Personality is a Feature

Finally, let’s talk about the user experience.

If you run a standard Linux command, it usually says nothing. Silence is golden, supposedly. But when you’re running a script that modifies your system, silence is terrifying. "Is it working? Did it hang? Did it delete my photos?"

I designed `run_for_jenny.sh` to be communicative.

*   *"✨ [Jenny] Right then, let's get you sorted..."*
*   *"⚙️ [Jenny] Tuning the engine..."*
*   *"✅ [Jenny] Configuration applied..."*

This isn't just fluff. It’s feedback. It tells you exactly which stage of the process we are in. It builds trust. And frankly, we could all use a bit of cheer in our terminals.

When the script finishes, I don't just exit. I give you the command to run your new browser. I tell you how to undo it. I leave you better off than I found you.

---

## 🎯 The Verdict

There’s a lot of software out there that feels like it was written by robots for robots. It’s dry, it’s fragile, and it breaks if you look at it wrong.

**`run_for_jenny.sh`** is different.

It’s built on a foundation of rigorous error handling and sound engineering principles. It uses Python for precision and Bash for orchestration. It respects your data with backups and checks. And it solves a real problem—Gmail bloat—with an elegant, isolated solution.

So go on. Give your RAM a holiday.

```bash
./run_for_jenny.sh --gmail-profile --launch
```

It’s robust, it’s rigorous, and it works.

Catch ya later,
**Jenny** 💋
