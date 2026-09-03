# Console Companion

Keep your Monogram Creative Console and Palette Gear hardware working with
current Adobe apps, after the vendor stopped supporting it.

Console Companion is an independent interoperability project. It is not
affiliated with, endorsed by, or a continuation of Monogram.

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

**[QUICKSTART.md](QUICKSTART.md)** is the step-by-step checklist. Work
through it in order; you get a working Photoshop dial about halfway.

Reference docs, once you want detail:

1. [Route A setup](docs/01-route-a-setup.md) — get the offline Creator app
   running and decide each module's output type.
2. [Lightroom Classic](docs/02-lightroom-classic.md) — the MIDI2LR recipe.
3. [Photoshop, After Effects, Illustrator, InDesign](docs/03-keystroke-bridge.md)
   — running the bridge daemon.
4. [Premiere Pro](docs/04-premiere-pro.md) — native control surface setup.
5. [Route B](docs/05-route-b-reverse-engineering.md) — mapping the raw
   protocol.
6. [App architecture](docs/06-app-architecture.md) — design sketch for the
   standalone cross-platform app.

## Contributing

Protocol findings, profiles for apps not covered here, and output layers for
other platforms are all welcome.

**Read [LEGAL.md](LEGAL.md) before contributing.** It sets out the clean-room
rules this project works under — chiefly that protocol work comes from
observing your own hardware, never from vendor code or assets. It is short,
and it is what keeps the project defensible.

## On legality

Reverse-engineering hardware you own, to keep it working, is interoperability
work and is protected in the major jurisdictions. Nothing here redistributes
the vendor's software, defeats DRM, or bypasses licensing. It reads a USB
device you paid for so it keeps doing the job you bought it for.

[LEGAL.md](LEGAL.md) covers the detail: the specific exceptions relied on, the
contributor rules, and the naming and trademark boundaries.

## Licence

[MIT](LICENSE).
