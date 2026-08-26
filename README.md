# Monogram Console Revival

Getting a Monogram Creative Console working with current Adobe apps on macOS
after the company shut down.

Monogram's hardware is fine. What broke is the software layer between the
console and Adobe: the "smart" plugins (the Lightroom plugin talking to
`localhost:50110`, the Photoshop and Premiere panels) break with each Adobe
update and will never be fixed. This project routes around them.

## The three layers

It helps to see the stack, because only one layer is actually broken:

| Layer | What it is | Status |
|---|---|---|
| Hardware to Creator app | Proprietary USB protocol | **Works.** Monogram shipped a final build with the login servers stripped out, so it runs offline. |
| Creator app to output | Keyboard / MIDI / HID emission | **Works.** These are open standards that no Adobe update can break. |
| Output to Adobe | The old "smart" plugins | **Broken, permanently.** This is the only part to replace. |

Because layer 1 still works, most of the hard reverse-engineering is
unnecessary. The job is to bypass layer 3.

## Two routes

**Route A — bridge through open standards.** Use the offline Creator app to
emit plain MIDI and keystrokes, then bridge those into Adobe. Works today,
survives future Adobe updates. Start here.

**Route B — a native driver.** Read the console's raw USB HID reports
directly and cut the Creator app out entirely. Only needed if Creator itself
stops running one day (a future macOS drops it), or if you want a driver on a
platform Monogram never supported. The `probe/` toolkit is the groundwork.

## What is here

```
docs/       Setup guides, one per Adobe app
bridge/     Route A: MIDI-to-keystroke daemon for apps with no MIDI support
probe/      Route B: HID discovery toolkit for writing a native driver
```

## Per-app support

| App | Approach | Notes |
|---|---|---|
| Lightroom Classic | MIDI2LR | Best case. Mature open-source bridge, near turnkey. |
| Photoshop | `bridge/` | No MIDI support at all; keystroke relay required. |
| After Effects | `bridge/` | Same. Dial-driven frame stepping works well. |
| Illustrator | `bridge/` | Same. |
| InDesign | `bridge/` | Same. |
| Premiere Pro | Native control surface | Has real MIDI support built in; no bridge needed. |
| Lightroom (cloud) | Limited | No control-surface API exists. Keyboard shortcuts only. |

## Start here

1. [Route A setup](docs/01-route-a-setup.md) — get the offline Creator app
   running and decide each module's output type.
2. [Lightroom Classic](docs/02-lightroom-classic.md) — the MIDI2LR recipe.
3. [Photoshop, After Effects, Illustrator, InDesign](docs/03-keystroke-bridge.md)
   — running the bridge daemon.
4. [Premiere Pro](docs/04-premiere-pro.md) — native control surface setup.
5. [Route B](docs/05-route-b-reverse-engineering.md) — mapping the raw
   protocol.

## On legality

Reverse-engineering hardware you own, to keep it working with software you
own, is interoperability work. In most jurisdictions that is explicitly
protected: it is not circumvention of copy protection, and no license is being
evaded. Nothing here redistributes Monogram's software, defeats DRM, or
bypasses licensing. It reads a USB device you paid for so it keeps doing the
job you bought it for.
