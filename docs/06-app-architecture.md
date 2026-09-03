# Console Companion: app architecture

A design sketch for turning the working bridge into something a
non-technical person can install and use.

## Who this is for

Worth being precise, because it drives every decision below.

People whose Creator install still works are not desperate — the bridge plus
the docs already serves them. The genuinely stranded are:

1. People who never archived the Creator installer before the site went quiet.
2. People on a macOS version where Creator no longer launches.
3. Windows users in the same position.
4. Linux users, who never had support at all.

**Groups 1-4 are only reachable once the raw protocol is known.** Until then
any app is a companion to Creator, not a replacement, and it helps nobody who
is actually stuck. That single fact sets the staging.

## Goals

- Install and run without a terminal.
- Visual mapping: click a control, turn a dial, done.
- Per-app profiles that switch automatically.
- Cross-platform, with Linux a first-class target rather than an afterthought.
- Config that is plain text, diffable, and shareable between users.

## Non-goals

- Replicating Creator's look. We copy the interaction model, not the visual
  design — see [LEGAL.md](../LEGAL.md).
- Cloud accounts, telemetry, licensing. The absence of these is the entire
  point; a project whose servers can go dark has learned nothing.
- Supporting every controller ever made. Do one device properly.

## The staging

### v1 — Companion (weeks, not months)

The Tauri app is a **config editor and supervisor**. The Python daemon stays
exactly as it is and does the work.

```
  Creator app  ──MIDI──>  companion.py  ──keystrokes──>  Adobe
                               ▲
                               │ reads profiles/*.yaml
                               │
                    Console Companion (Tauri)
                    edits config, starts/stops daemon,
                    shows live control activity
```

This ships a GUI fast and risks nothing that already works. Its ceiling is
that it still needs Creator and still needs Python.

### v2 — Standalone (after Route B)

Once `hidprobe.py` yields the protocol, the engine is ported to Rust and the
whole thing becomes one binary with no Python and no Creator.

```
  Console hardware  ──USB HID──>  Console Companion  ──keystrokes/MIDI──>  Any app
                                  (single binary)
```

This is the version that reaches the stranded users. **The protocol is the
gating item — not the UI.**

## Layers

Keep these strictly separated. It is what makes headless operation, testing,
and the v1-to-v2 transition possible.

```
┌─────────────────────────────────────────────┐
│  UI            Tauri + web frontend         │
│                mapping editor, learn mode   │
├─────────────────────────────────────────────┤
│  IPC           JSON over stdio or socket    │
├─────────────────────────────────────────────┤
│  Engine        profile matching, encoder    │
│                decoding, app switching      │
├───────────────┬─────────────────────────────┤
│  Input        │  Output                     │
│  HID / MIDI   │  keystroke / MIDI / OSC     │
├───────────────┴─────────────────────────────┤
│  Platform      macOS Quartz                 │
│                Windows SendInput            │
│                Linux uinput                 │
└─────────────────────────────────────────────┘
```

**The engine must run headless.** No UI import, no window handle, no
dependency on the frontend existing. Users on a Linux box or a render node
should be able to run just the engine from a service file, and the UI should
be an optional convenience. This also means the engine is testable without a
display, which is how it stays correct.

## Config format

Keep the YAML profile format the bridge already uses. It is human-readable,
diffable, and shareable — a user can paste their Photoshop profile into a
forum post and someone else can drop it straight in.

The GUI is a *view over the file*, never a replacement for it. Hand-editing
must stay first-class, and the app must reload cleanly when the file changes
underneath it.

```
~/.config/console-companion/
  profiles/
    photoshop.yaml
    after-effects.yaml
  device.yaml        # which physical control is which
```

The one addition v2 needs is `device.yaml`, separating *physical layout*
(module 3 is a dial in slot 2) from *bindings* (that dial adjusts brush size).
Today Creator holds the former. Once we read the hardware directly, we own it.

## Platform output abstraction

One trait, three implementations. The macOS one already exists in
`bridge/companion.py` as the `Keyboard` class and ports directly.

| Platform | Mechanism | Notes |
|---|---|---|
| macOS | `CGEventCreateKeyboardEvent` at the HID tap | Needs Accessibility permission |
| Windows | `SendInput` | Generally no special permission |
| Linux | `uinput` | Needs device permission or a udev rule; works on Wayland, unlike XTest |

Keycodes are positional and differ per platform, so the shared layer should
speak in *logical* keys ("left bracket") with per-platform tables underneath.
The existing `keycodes.py` is already shaped this way.

## Learn mode

The single feature that makes this feel like a real app: click a parameter in
the UI, turn a physical control, and the binding is captured. MIDI2LR does
this well and it is the right model to follow.

The engine needs a mode where, instead of dispatching events, it forwards the
next control it sees to the UI. That is a small addition — one flag on the
event loop — but it should be designed in from the start rather than bolted on.

## Why Tauri

Small binaries, no bundled browser runtime, good cross-platform story, and a
Rust core that v2 wants anyway. Electron would work and is more familiar, but
ships ~100MB per platform for a config editor, and would need a second rewrite
at v2.

The honest cost: Tauri uses the system webview, so rendering differs slightly
across platforms. For a mapping UI that is a non-issue.

**Packaging caveat for v1.** Bundling a Python runtime inside a Tauri app is
genuinely awkward. Two ways out: require Python and detect it (fine for the
early technical audience), or treat v1 as terminal-only and let the GUI land
with v2's Rust engine. The second is cleaner and probably right if the
protocol work moves quickly.

## Suggested order

1. **Crack the protocol.** Everything meaningful is downstream of this.
   Publish the byte map as its own document regardless of whether the app
   ever ships — it is the part that outlives the project.
2. **Port the engine to Rust**, matching the existing Python behaviour, with
   the test suite in `bridge/test_companion.py` as the specification. Those
   27 tests translate directly and pin the encoder and routing semantics.
3. **macOS output layer**, since that is where the hardware is.
4. **Tauri shell** with profile editing and learn mode.
5. **Linux, then Windows** output layers.

Step 1 is the only hard one. Steps 2-5 are ordinary work with a known answer.
