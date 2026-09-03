# Route A: base setup

This gets the console talking again through open standards, before any
per-app work.

## 1. Install the final offline Creator build

The last release of Monogram Creator (around v5.10.1) had the login and
authentication server dependency removed, specifically so units would not
brick when the servers went dark. It launches and runs fully offline.

Get it from [monogramcc.com/download](https://monogramcc.com/download/) while
that page is still up.

**Archive the installer now.** The site is unmaintained and could vanish
without warning. Keep a copy somewhere you control, alongside a note of the
version number. If the download is already gone, community mirrors have
circulated in the [VI-Control
thread](https://vi-control.net/community/threads/beware-of-monogram-control-surface-company.153413/)
and the Palette Gear / Monogram user group.

If Creator prompts you to sign in, you have an older build. Get the final one.

## 2. Confirm the hardware is seen

Launch Creator with the console plugged in. Each physical module should appear
in the app. If they do, layer 1 is healthy and everything else is a software
routing problem.

If modules do *not* appear, try a different USB cable and port before
suspecting the device. These consoles are sensitive to underpowered hubs;
connect directly to the Mac.

## 3. Choose an output type per module

This is the key decision. In Creator, each module can emit different things.
Ignore the app-specific "smart" profiles entirely, they are the broken part.
Use these instead:

**Keyboard shortcut** — for anything discrete: tool selection, undo, save,
play/pause. Rock solid, works in every app, no bridge software needed. If a
control can be a keystroke, make it a keystroke.

**MIDI** — for anything continuous: dials, sliders, scrub wheels. This is what
Lightroom Classic and Premiere consume directly, and what the bridge daemon
translates for everything else.

For MIDI dials, match the settings the rest of this project assumes:

- Type: **CC (Control Change)**
- Dials: **Relative** mode
- Sliders: **Absolute** mode
- Give every control a **unique CC number**. Note them down; you will need
  them in every later step.

Assigning CC numbers in a predictable block makes profiles much easier to
write. This project's example profiles assume:

| Control type | Range |
|---|---|
| Dials | CC 21 onward |
| Sliders | CC 30 onward |
| Buttons | Notes 36 onward |

You do not have to follow that, but if you deviate, run the monitor in step 4
and edit the profiles to match.

## 4. Verify the MIDI is actually arriving

Before touching any Adobe app, confirm macOS sees the MIDI:

```bash
cd bridge
pip install mido python-rtmidi pyyaml
python3 companion.py --list-ports
```

The console should appear as an input port. Then watch live values:

```bash
python3 companion.py --monitor
```

Turn each dial and press each button. You will see the CC and note numbers
each control sends. **Write these down** — this is the map everything else
depends on. Confirm that:

- Each control sends a *unique* number.
- Dials in relative mode send small values near 1 one way and near 127 the
  other. If yours send a smooth 0-127 sweep instead, they are in absolute
  mode; change it in Creator or set `relative_mode` accordingly.

## 5. Continue per app

- [Lightroom Classic](02-lightroom-classic.md)
- [Photoshop, After Effects, Illustrator, InDesign](03-keystroke-bridge.md)
- [Premiere Pro](04-premiere-pro.md)

## Keeping it working

Two habits protect you long-term:

1. **Archive the Creator installer** somewhere durable, with its version noted.
2. **Export your Creator configuration** once you have it tuned, so a machine
   rebuild does not mean redoing the mapping from scratch.
