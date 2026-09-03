# Quickstart

Work through these in order. Each step has a "done when" so you know whether
to continue or stop and fix something.

Total time is about 40 minutes, and you get a working Photoshop dial at the
halfway point.

---

## Step 1 — Archive the installer (do this first, today)

Download Monogram Creator from
[monogramcc.com/download](https://monogramcc.com/download/).

Then **copy the installer somewhere you control** — external drive, Dropbox,
anywhere that is not that website. The site is unmaintained and everything
here depends on it. Note the version number in the filename.

*Done when:* you have a saved copy of the installer outside your Downloads
folder.

---

## Step 2 — Confirm the hardware still talks

Install and launch Creator with the console plugged in. Your modules should
appear in the app.

If they do not: try a different cable, and plug directly into the Mac rather
than a hub. These are fussy about underpowered hubs.

If Creator asks you to sign in, you have an older build — get the final one
from Step 1.

*Done when:* every physical module shows up in Creator.

---

## Step 3 — Get the code onto your Mac

```bash
git clone https://github.com/mitchwooddigital/ideal-computing-machine.git
cd ideal-computing-machine/bridge
pip3 install -r requirements.txt
```

*Done when:* `python3 monobridge.py --check` prints `OK: 4 profile(s) valid.`

---

## Step 4 — Switch your modules to MIDI

In Creator, for each module you want on a dial or slider:

- Type: **CC (Control Change)**
- Dials: **Relative**
- Sliders: **Absolute**
- Each control gets a **unique CC number**

Buttons can stay as keyboard shortcuts if you prefer — those already work
without any of this. Only use MIDI for buttons you want the bridge to handle.

*Done when:* every control has its own number and none are duplicated.

---

## Step 5 — Write down your control numbers

```bash
python3 monobridge.py --monitor
```

Turn each dial and press each button one at a time. Note what each sends.

Two things to check:

- Every control shows a **different** number.
- Dials send small values near `1` one way and near `127` the other. If a dial
  instead sweeps smoothly 0→127, it is in Absolute mode — go back to Step 4.

*Done when:* you have a written list like "dial 1 = cc 21, dial 2 = cc 22,
button 1 = note 36".

---

## Step 6 — Grant Accessibility permission

**System Settings → Privacy & Security → Accessibility** → add your Terminal.

Skip this and the daemon runs, reports no errors, and does nothing at all.
It is the single most common reason this appears broken.

*Done when:* Terminal is listed and toggled on.

---

## Step 7 — Match the profile to your hardware

Open `profiles/photoshop.yaml` and edit the `cc:` and `note:` numbers to match
your list from Step 5. Change nothing else yet.

*Done when:* `python3 monobridge.py --check` still passes.

---

## Step 8 — Test without sending anything

```bash
python3 monobridge.py --dry-run -v
```

Turn the dial you mapped to brush size. You should see logged keystrokes.

If you see `no profile for frontmost app ...`, that is expected here — you are
in Terminal, not Photoshop. It confirms MIDI is arriving.

*Done when:* moving a control prints something.

---

## Step 9 — First real win

```bash
python3 monobridge.py -v
```

Open Photoshop, pick the brush tool, and turn your brush-size dial.

**The brush should resize.** That is the whole thing working end to end.

If the dial only grows and never shrinks, add this under that control in the
YAML:

```yaml
    relative_mode: signed_bit
```

If it jumps too far per click, lower `step`. Too slow, raise it.

*Done when:* the dial drives the brush smoothly in both directions.

---

## Step 10 — Lightroom Classic

Separate tool, unrelated to the bridge. Install
[MIDI2LR](https://github.com/rsjaffe/MIDI2LR/releases) (6.2.1.0+).

In its panel, click a Lightroom parameter (Exposure), then move the dial you
want bound to it.

**Then right-click each dial mapping and choose "Two's Complement."** Miss
this and dials only move one direction. Save the profile as XML.

*Done when:* a dial drives Exposure in both directions.

---

## Step 11 — The rest, at your own pace

Now that one app works, the others are the same edit repeated:

- `profiles/after-effects.yaml`, `illustrator.yaml`, `indesign.yaml` — update
  the numbers to match Step 5.
- Premiere Pro needs no bridge; it has native control-surface support. See
  [docs/04-premiere-pro.md](docs/04-premiere-pro.md).

The daemon switches profiles automatically as you change apps, so one physical
layout serves all of them.

---

## Step 12 — Start it automatically (optional)

Once tuned, set up the LaunchAgent in
[docs/03-keystroke-bridge.md](docs/03-keystroke-bridge.md) so it runs at
login. Note it needs its own Accessibility permission, separate from
Terminal's.

---

## If you get stuck

| Symptom | Cause |
|---|---|
| Nothing on `--monitor` | Creator not running, or module not set to MIDI |
| Events log but app ignores them | Accessibility permission (Step 6) |
| `no profile for frontmost app X` | Paste the bundle id it prints into the YAML |
| Dial only goes one way | Add `relative_mode: signed_bit` |
| Dial overshoots | Lower `max_repeats`, then `step` |

Full detail per app lives in [docs/](docs/).
