# Photoshop, After Effects, Illustrator, InDesign

None of these four apps support MIDI or control surfaces in any form. Adobe
never built the API, and the Monogram plugin that faked it is dead. So the
console has to reach them the way a keyboard does.

That is what `bridge/monobridge.py` is: a daemon that listens to the console's
MIDI and synthesises real macOS key events. Because it watches which app is
frontmost, one physical layout serves every app and switches automatically as
you move between them.

## Install

```bash
cd bridge
pip install mido python-rtmidi pyyaml \
            pyobjc-framework-Quartz pyobjc-framework-Cocoa
```

## Grant Accessibility permission

macOS blocks synthetic key events from unapproved apps. Add whatever you run
the script from (Terminal, iTerm) under:

**System Settings > Privacy & Security > Accessibility**

Without this the daemon runs, reports no errors, and nothing happens. If you
see events logged with `-v` but the app does not react, this is why.

## Find your control numbers

```bash
python3 monobridge.py --monitor
```

Turn each dial and press each button, and note the CC and note numbers. The
supplied profiles assume dials on CC 21+ and buttons on note 36+. If yours
differ, either reassign them in Creator or edit the profiles.

## Run it

```bash
python3 monobridge.py --profiles profiles/ -v
```

To see what *would* be sent without actually sending it:

```bash
python3 monobridge.py --profiles profiles/ --dry-run -v
```

To check profiles parse without connecting to hardware:

```bash
python3 monobridge.py --check
```

## Writing profiles

Profiles are YAML, one per app, keyed by bundle id. A dial:

```yaml
brush_size:
  type: dial
  cc: 21
  clockwise: "]"
  counterclockwise: "["
  step: 2            # keystrokes per detent
  max_repeats: 24    # ceiling on one fast spin
```

A button:

```yaml
undo:
  note: 36
  press: "cmd+z"
```

A hold-to-preview control, firing on both press and release:

```yaml
hide_edges:
  note: 44
  press: "cmd+h"
  release: "cmd+h"
```

Modifiers are `cmd`, `shift`, `opt`, `ctrl`, `fn`, combined with `+`. Symbol
keys can be written literally (`"["`, `"]"`, `"="`) or by name
(`leftbracket`, `equal`). A typo in a shortcut fails loudly at load time with
the offending token named, rather than silently binding nothing.

### Tuning dials

`step` and `max_repeats` are what make a dial feel right:

- **`step`** — keystrokes per detent. Photoshop brush size moves in small
  increments, so `step: 2` tracks hand movement better than 1.
- **`max_repeats`** — ceiling on a single fast spin. Zoom compounds, so a
  low ceiling (6-8) stops one flick from zooming to 3200%. Frame stepping
  does not compound, so a high ceiling (30) lets you scrub a long way.

### Finding a bundle id

```bash
osascript -e 'id of app "Photoshop"'
```

## Included profiles

`photoshop.yaml`, `after-effects.yaml`, `illustrator.yaml`, `indesign.yaml`.
These are starting points using each app's default shortcuts. Treat them as a
skeleton and rebind to the tools you actually reach for.

## Run it automatically

Once it is tuned, a LaunchAgent starts it at login. Write this to
`~/Library/LaunchAgents/com.local.monobridge.plist`, correcting the paths:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN"
  "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
  <key>Label</key>
  <string>com.local.monobridge</string>
  <key>ProgramArguments</key>
  <array>
    <string>/usr/bin/python3</string>
    <string>/full/path/to/bridge/monobridge.py</string>
    <string>--profiles</string>
    <string>/full/path/to/bridge/profiles</string>
  </array>
  <key>RunAtLoad</key><true/>
  <key>KeepAlive</key><true/>
</dict>
</plist>
```

Then `launchctl load ~/Library/LaunchAgents/com.local.monobridge.plist`.

Note that the LaunchAgent needs its own Accessibility permission, separate
from your terminal's.

## Troubleshooting

**Events log with `-v` but the app does not respond.** Accessibility
permission. See above.

**"no profile for frontmost app ...".** That app has no profile, or its bundle
id differs from the one in the YAML. The log prints the id it saw; paste that
into the profile.

**A dial only moves one direction.** Set `relative_mode: signed_bit` on that
control. Monogram modules use one of two conventions and the default assumes
two's complement.

**A dial overshoots wildly.** Lower `max_repeats`, then `step`.

**Nothing at all on `--monitor`.** The problem is upstream: Creator is not
running, or that module is not set to a MIDI output type.

## Tests

```bash
python3 test_monobridge.py
```

Covers encoder decoding, shortcut parsing and event routing — the parts whose
bugs otherwise show up as confusing hardware behaviour.
