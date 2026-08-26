# Route B: mapping the raw protocol

Route A depends on the Monogram Creator app continuing to run. That is a real
dependency with a real expiry date: an unmaintained app will eventually be
broken by a macOS release, and nobody will fix it.

Route B removes that dependency by reading the console's USB HID reports
directly, so a native driver can drive Adobe with no Monogram software in the
loop.

**You do not need this yet.** Do Route A first. This is insurance, and the
work is best done *while* Creator still runs, because a working app is the
reference you check your decoding against.

## What is known

The console enumerates as standard **HID and MIDI** interfaces, which is
promising: it means the transport is documented even if the payload is not.
Monogram's own materials describe the hardware as a re-engineered
implementation of HID joystick, HID keyboard and MIDI connections.

No public protocol dump exists. There were community attempts at the
predecessor Palette Gear, but nothing was released as a usable library. So
this starts from scratch, and `probe/monoprobe.py` is built for that.

## Install

```bash
brew install hidapi
pip install hidapi
```

## Step 1: find the device

```bash
cd probe
python3 monoprobe.py --scan
```

This flags anything whose manufacturer or product string mentions Monogram or
Palette. If nothing matches, the device may report a generic name:

```bash
python3 monoprobe.py --scan --all
```

Run that with the console unplugged, then plugged in, and diff the two lists.
Whatever appears is your device.

A modular console typically exposes **several interfaces** — one for HID, one
for keyboard emulation, one for MIDI. Note every VID:PID and interface number;
you will need to try each.

## Step 2: watch the reports

```bash
python3 monoprobe.py --watch 0xVVVV:0xPPPP
```

Bytes that changed since the previous report are `[bracketed]`, with a byte
offset ruler across the top. Turn one dial slowly. If bytes move, this is the
interface carrying module data. If nothing moves, try the next interface.

You will likely have to **quit Monogram Creator first** — it holds the device
open and macOS will not hand it to two readers. On macOS, raw HID access to a
claimed device may also need `sudo`.

## Step 3: record a labelled session

The point is one control at a time, each labelled:

```bash
python3 monoprobe.py --watch 0xVVVV:0xPPPP \
    --record session.jsonl --label dial-1-clockwise
```

Turn dial 1 clockwise for a few seconds, stop with Ctrl-C, then repeat with a
new label for each control and direction:

- `dial-1-clockwise`, `dial-1-counterclockwise`
- `dial-2-clockwise`, ...
- `button-1-press`
- `slider-1-sweep`

All labels append to the same file.

## Step 4: let the data show you the layout

```bash
python3 monoprobe.py --analyse session.jsonl
```

This reports which byte offsets varied under each label, then compares across
labels. The comparison is the useful part:

- Offsets that vary under **every** label are counters, timestamps or
  checksums — structural noise, not control data.
- Offsets that vary under **exactly one** label are that control's payload.

So the field layout falls out of the recording rather than being guessed.
Typical shape once decoded: a report id, a module or control identifier, and a
value or delta byte.

## Step 5: decode the values

With offsets known, work out the encoding:

- **Dials** are usually signed deltas. Check whether counter-clockwise reads
  as `0xFF, 0xFE ...` (two's complement) or `0x41, 0x42 ...` (signed bit) —
  the same distinction `bridge/monobridge.py` handles for MIDI, since it
  reflects how the firmware thinks.
- **Buttons** are usually a bit in a bitmask, so watch a byte while pressing
  several buttons and see which bit flips.
- **Sliders** are usually an absolute 0-255 or a 16-bit pair. If a value
  wraps oddly at 255, look for a second byte moving with it.

Check your decoding against Creator: run the app, move a control, and confirm
its on-screen value matches what you decoded.

## Step 6: write the driver

Once decoding is confirmed, the driver is small. Read reports in a loop,
decode to control events, and emit — reusing `bridge/monobridge.py`'s
`Keyboard` class for keystrokes, or a virtual MIDI port for apps that want
MIDI. At that point the Creator app is out of the loop entirely.

## Please publish what you find

A working protocol map for this hardware does not exist publicly. Everyone
else with one of these consoles is facing the same shutdown, and a recording
plus a decode table would be the most useful thing anyone has contributed to
that. Consider posting the `--analyse` output somewhere findable.

## If HID turns out to be a dead end

If the HID interfaces carry only the *configured output* (keystrokes, MIDI)
rather than raw module state, then Creator is doing the mapping in software
and the raw state may only be visible on a vendor-specific interface. In that
case:

- Capture USB traffic at the bus level with Wireshark plus a USB capture
  backend, rather than at the HID layer.
- Inspect the Creator app bundle. It is likely Electron, in which case the
  device logic is readable JavaScript inside `app.asar`, and unpacking it
  usually reveals the protocol faster than black-box probing.

That second one is often the shortcut. If you have the installer, it is worth
looking there before spending long on captures.
