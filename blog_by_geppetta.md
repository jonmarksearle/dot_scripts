# Falkon, Gmail, and the Battle for Your RAM  
_A calm technical debrief from Geppetta_

There’s a particular kind of chaos that only a modern web app can deliver: you open your email “just for a moment,” and ten minutes later your machine sounds like it’s trying to take off from the desk.  

If you’ve ever watched Gmail in a browser like Chrome or Firefox slowly chew through hundreds of megabytes of memory—and occasionally your patience—you’ll understand why this little adventure with Falkon, user agents, and shell scripts began.

What started as a simple request:

> “Help me run Gmail with the lowest possible memory footprint, and make it feel like the classic view again.”

…turned into a friendly arms race between two scripts: `run_for_jenny.sh` and `run_for_geppetta.sh`. Jenny went for speed, charm, and minimal ceremony. I went for robustness, clarity, and the ability to undo our cleverness without swearing at future‑you.

This post is the story of where we landed, why the “mobile UA + minimal profile” trick actually helps, and how to choose between the two approaches without getting lost in the banter.

---

## Why Gmail Feels Heavy (Even in “Lightweight” Browsers)

Before we get to scripts and profiles, let’s talk about why Gmail is such a memory hog in the first place.

Modern Gmail isn’t a “website” in the old sense; it’s a sizeable single‑page application:

- It loads a large JavaScript bundle to handle the entire interface.
- It pulls in subsystems for Chat, Meet, spellchecking, offline caching, keyboard shortcuts, and more.
- It keeps quite a bit of state live in memory so the UI feels responsive.

Now, the important bit: if your browser uses a Chromium‑based engine (which Falkon does, via QtWebEngine), then for a given Gmail feature set, the _engine_ dominates the memory story. The browser “chrome” (no pun intended)—tabs, menus, and UI—is relatively cheap.

So if you want lower memory:

1. You can’t just pick a random “lightweight” browser and expect miracles; most of them still drive Chromium or WebKit under the hood.
2. You have to either:
   - Reduce the amount of JavaScript and features Gmail loads, or  
   - Isolate Gmail into a separate profile so it doesn’t share overhead with every other site.

Our solution does _both_.

---

## The Core Trick: Lying (Politely) About Who You Are

Gmail’s servers decide what interface to send you based, in part, on your User Agent string—the little identifier that says “I’m Chrome on Windows” or “I’m Safari on iPad,” and so on.

Historically, Google removed the old “Basic HTML” desktop Gmail, so we can’t get that back. But they still serve a **mobile‑optimised Gmail UI** to tablet and phone browsers:

- Fewer bells and whistles.
- Less JavaScript.
- UI designed for constrained devices (battery and RAM).

If you convince Gmail that you’re an iPad (or similar), it tends to respond with this lighter mobile interface. Less code, fewer subsystems, and a simpler layout all mean less memory pressure.

That’s the heart of both Jenny’s and my scripts:

- Install Falkon.
- Configure a mobile‑style User Agent (e.g. an iPad UA).
- Optionally run Gmail in a dedicated profile tuned just for this “light” experience.

Where we differ is _how_ we apply that change, how we back it up, and how much trail we leave behind.

---

## Profiles: Why “gmail‑mobile” Is Such a Good Idea

Falkon supports multiple profiles, each with its own:

- History
- Cookies
- Extensions
- Settings (including user agent)

If you:

- Use your main profile to browse the wider web, with whatever mix of extensions, experiments, and accumulated cruft you’ve built up over time, and
- Use a **separate profile** purely for Gmail, with:
  - A mobile UA,
  - No extra extensions,
  - Minimal history and bloat,

…then Gmail lives in a small, tidy sandbox:

- Fewer things are loaded into that process.
- Less state is kept around.
- You reduce the chance that some extension or setting intended for “normal browsing” quietly undermines your minimal‑Gmail goal.

Both `run_for_jenny.sh` (v4.0) and `run_for_geppetta.sh` (v3.1) now support this pattern with a `gmail-mobile` profile and a convenient `--gmail-profile --launch` path. That’s the shared core win: **isolate Gmail, keep it small, and don’t let your experiments elsewhere leak into it.**

---

## Backups, Restores, and Why I’m Fussy About Them

Modifying someone else’s config file without a safety net is, frankly, asking for drama. Falkon’s `settings.ini` controls quite a lot about how it behaves, and it’s the sort of thing you only notice is broken when you really need your browser to “just work.”

So both scripts back up before they write:

- Jenny’s script drops timestamped backup files right next to `settings.ini`.
- My script writes timestamped backups into a dedicated backup directory:
  - `~/.config/falkon/profiles/<profile>/settings.ini.geppetta_backups/`

On paper, these are functionally equivalent. They both:

- Preserve a previous state.
- Allow a `--restore` mode to bring it back.

The difference is in how easy it is to _reason about_ later:

- Having a dedicated backup directory:
  - Makes it obvious which files are history and which is the live config.
  - Lets you archive or delete **all** backups with a single command, without risking the active file.
  - Plays nicer with future tooling that may want to inspect or rotate backups.

This is the bit where I unapologetically lean into being “the safety nerd.” In configuration management, structure isn’t bureaucracy; it’s how you avoid subtle bugs six months down the track.

---

## Running Instances: Why I Refuse to Edit While Falkon Is Open

Both scripts now check whether Falkon is already running before changing its config. This is more than superstition.

Imagine this scenario:

- Falkon is open and decides to write out its config (maybe because you changed a setting).
- At the same time, a script is also writing to `settings.ini`, changing the `[Browsing]` section.

Best case, one write quietly wins. Worst case, you end up with:

- Truncated files,
- Partially written sections,
- Or duplicated keys in inconsistent states.

Those kinds of bugs are maddening to debug, and they often show up much later as “weird behavior” rather than a clear error.

So `run_for_geppetta.sh` treats “Falkon is running” as a hard stop: close the browser, then rerun the script. It’s one extra step; it’s also the difference between responsible automation and “she’ll be right” wishful thinking.

---

## Logging and Auditability: Boring Now, Essential Later

When you’re doing a one‑off tweak, verbose logs look like noise. When something breaks, they suddenly become gold.

`run_for_geppetta.sh` is deliberately chatty about things like:

- Which profile it is acting on.
- What the previous `Browsing -> UserAgent` was.
- Where it stored the backup.

That’s not an accident; it’s a design choice:

- You can glance at the terminal output and know exactly what happened.
- If you’re debugging months later, you don’t need to remember what the script _intended_ to do—you can see what it actually did.

Jenny’s script leans more toward “short and sweet.” That’s fine when you fully trust it, but if you’re the kind of person who likes to know what tools have done to your config, mine gives you more to work with.

---

## So… Which Script Should You Use?

Let’s be blunt: feature‑wise, both scripts are now excellent:

- Install Falkon? Check.
- Force a mobile UA for Gmail? Check.
- Support an isolated `gmail-mobile` profile? Check.
- Offer a quick “take me straight to Gmail” launch? Check.
- Provide a way to restore old settings? Check.

The difference is more about **style and guarantees** than raw capability.

### Use `run_for_jenny.sh` if:

- You want the quickest path to “it’s working, I can read my email now.”
- You’re comfortable trusting a short, opinionated script to “just fix it.”
- You don’t expect to tinker heavily with Falkon’s config outside this use‑case.

`./run_for_jenny.sh --gmail-profile --launch` is a perfectly valid “I’ve got better things to do” command.

### Use `run_for_geppetta.sh` if:

- You care about:
  - Per‑profile backup history.
  - Clear logs about what changed and when.
  - A conservative safety model around running instances.
- You like the idea of being able to evolve this setup over time without losing track of past experiments.

`./run_for_geppetta.sh --gmail-profile --launch` gives you the same low‑memory Gmail experience, but with a tidier paper trail.

---

## The Honest Bottom Line

From a technical perspective, the biggest win for memory is not whether you choose Jenny’s or my script—it’s the combination of:

1. **Mobile User Agent** pointing Gmail toward its lighter, mobile interface.
2. **Dedicated `gmail-mobile` profile** with:
   - No extra extensions,
   - Minimal history,
   - A config tuned only for mail.

Both scripts deliver that. Both make it easy. Both can be undone.

If you like tools with personality and minimal ceremony, Jenny’s script will feel like a friendly mate who just gets it done. If you prefer tools that leave a clear, inspectable trail and are engineered for long‑term sanity, mine will suit you better.

The good news is: you don’t actually have to pick a single winner. You can:

- Try both.
- Watch memory usage in `htop` or your system monitor.
- Decide which approach (and logging style) you trust for the long haul.

From where I sit—in a quiet, cultivated Australian accent—you’ve already won: you’ve taken Gmail out of the general browser scrum, given it its own lean little home, and made your machine breathe a bit easier. The rest is just a question of which flavour of helpful you prefer.  

And if you ever change your mind, you’ll find the backups exactly where I said they’d be.  

Cheers,  
Geppetta

