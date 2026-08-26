#!/usr/bin/env python3
"""monobridge - drive Adobe apps from a Monogram Creative Console over MIDI.

The Monogram Creator app still talks to the hardware fine, but its "smart"
Adobe plugins are dead and will not be fixed. Creator can however emit plain
MIDI, and MIDI is forever. This daemon listens to that MIDI and synthesises
macOS keystrokes, so any app with a keyboard shortcut becomes controllable --
Photoshop, After Effects, Illustrator and InDesign have no MIDI support of
their own and would otherwise be unreachable.

Profiles are per-application and switch automatically as you change apps, so
one physical layout serves every program.

    python3 monobridge.py --list-ports
    python3 monobridge.py --profiles profiles/
"""

import argparse
import os
import sys
import time
from collections import defaultdict

import keycodes

# --- Optional imports, checked lazily so --help and --check work anywhere ----

def _require_macos_bindings():
    try:
        import Quartz
        from AppKit import NSWorkspace
        return Quartz, NSWorkspace
    except ImportError as exc:
        sys.exit(
            "Missing macOS bindings: {}\n"
            "Install them with:  pip install pyobjc-framework-Quartz "
            "pyobjc-framework-Cocoa".format(exc)
        )


def _require_mido():
    try:
        import mido
        return mido
    except ImportError as exc:
        sys.exit(
            "Missing MIDI support: {}\n"
            "Install it with:  pip install mido python-rtmidi".format(exc)
        )


# --- Keystroke output --------------------------------------------------------

class Keyboard:
    """Synthesises key events at the HID event tap.

    Posting at kCGHIDEventTap (rather than the session tap) puts the events
    where a real keyboard's would appear, which is what Adobe's tool shortcuts
    listen for.
    """

    def __init__(self, dry_run=False):
        self.dry_run = dry_run
        if not dry_run:
            self.Quartz, _ = _require_macos_bindings()

    def tap(self, keycode, flags=0):
        if self.dry_run:
            print(f"    [dry-run] keycode={keycode} flags={flags:#010x}")
            return
        Q = self.Quartz
        for is_down in (True, False):
            event = Q.CGEventCreateKeyboardEvent(None, keycode, is_down)
            if flags:
                Q.CGEventSetFlags(event, flags)
            else:
                # Clear inherited modifiers; a physically held key would
                # otherwise leak into the synthetic event.
                Q.CGEventSetFlags(event, 0)
            Q.CGEventPost(Q.kCGHIDEventTap, event)


class FrontmostApp:
    """Reports the bundle id of the frontmost application, cached briefly.

    The lookup is cheap but not free, and a fast encoder can fire dozens of
    events per second; a short cache keeps that off the critical path.
    """

    def __init__(self, ttl=0.25, dry_run=False):
        self.ttl = ttl
        self.dry_run = dry_run
        self._value = None
        self._checked_at = 0.0
        if not dry_run:
            _, self.NSWorkspace = _require_macos_bindings()

    def get(self):
        if self.dry_run:
            return "dry.run.app"
        now = time.monotonic()
        if self._value is None or now - self._checked_at > self.ttl:
            app = self.NSWorkspace.sharedWorkspace().frontmostApplication()
            self._value = app.bundleIdentifier() if app else None
            self._checked_at = now
        return self._value


# --- Relative encoder decoding ----------------------------------------------

def decode_relative(value, mode):
    """Turn a relative-encoder CC value into a signed delta.

    Monogram dials in relative mode use one of two conventions depending on
    how the module is configured in Creator. Guessing wrong makes a dial that
    only ever counts up, so both are supported explicitly.
    """
    if mode == "twos_complement":
        # 1..63 = clockwise, 127..65 = counter-clockwise.
        return value - 128 if value >= 64 else value
    if mode == "signed_bit":
        # 65..127 = clockwise, 1..63 = counter-clockwise.
        return value - 64 if value >= 64 else -value
    raise ValueError(
        f"unknown relative mode {mode!r}; "
        "expected 'twos_complement' or 'signed_bit'"
    )


# --- Profiles ----------------------------------------------------------------

class Binding:
    """One control's mapping, pre-parsed so the hot path does no string work."""

    __slots__ = ("kind", "cc", "note", "down", "up", "cw", "ccw",
                 "mode", "step", "max_repeats", "label")

    def __init__(self, spec, label):
        self.label = label
        self.kind = spec.get("type", "button")
        self.cc = spec.get("cc")
        self.note = spec.get("note")
        self.mode = spec.get("relative_mode", "twos_complement")
        self.step = max(1, int(spec.get("step", 1)))
        self.max_repeats = max(1, int(spec.get("max_repeats", 24)))
        self.down = self._parse(spec.get("press") or spec.get("key"))
        self.up = self._parse(spec.get("release"))
        self.cw = self._parse(spec.get("clockwise") or spec.get("cw"))
        self.ccw = self._parse(spec.get("counterclockwise") or spec.get("ccw"))

    @staticmethod
    def _parse(value):
        if value is None:
            return None
        return keycodes.parse(value)


def load_profiles(path):
    """Load every .yaml/.yml profile in a directory, keyed by bundle id."""
    try:
        import yaml
    except ImportError:
        sys.exit("Missing YAML support. Install it with:  pip install pyyaml")

    if not os.path.isdir(path):
        sys.exit(f"Profile directory not found: {path}")

    profiles = {}
    names = sorted(
        n for n in os.listdir(path) if n.endswith((".yaml", ".yml"))
    )
    if not names:
        sys.exit(f"No .yaml profiles found in {path}")

    for name in names:
        full = os.path.join(path, name)
        with open(full) as handle:
            try:
                data = yaml.safe_load(handle) or {}
            except yaml.YAMLError as exc:
                sys.exit(f"{name}: invalid YAML: {exc}")

        bundle = data.get("bundle_id")
        if not bundle:
            sys.exit(f"{name}: missing required 'bundle_id' field")

        table = {}
        for label, spec in (data.get("controls") or {}).items():
            try:
                binding = Binding(spec, label)
            except (keycodes.KeySpecError, ValueError) as exc:
                sys.exit(f"{name}: control {label!r}: {exc}")

            if binding.cc is not None:
                table[("cc", int(binding.cc))] = binding
            elif binding.note is not None:
                table[("note", int(binding.note))] = binding
            else:
                sys.exit(
                    f"{name}: control {label!r} sets neither 'cc' nor 'note'"
                )

        profiles[bundle] = {
            "name": data.get("name", name),
            "controls": table,
        }
        print(f"  loaded {data.get('name', name)!r} "
              f"({len(table)} controls) -> {bundle}")

    return profiles


# --- Event loop --------------------------------------------------------------

class Bridge:
    def __init__(self, profiles, keyboard, frontmost, verbose=False):
        self.profiles = profiles
        self.keyboard = keyboard
        self.frontmost = frontmost
        self.verbose = verbose
        self._warned = set()
        self._last_profile = None

    def active_profile(self):
        bundle = self.frontmost.get()
        profile = self.profiles.get(bundle)
        if self.verbose and profile is not None:
            if profile["name"] != self._last_profile:
                print(f"-> profile: {profile['name']}")
                self._last_profile = profile["name"]
        return bundle, profile

    def handle(self, message):
        if message.type == "control_change":
            key = ("cc", message.control)
            value = message.value
        elif message.type in ("note_on", "note_off"):
            key = ("note", message.note)
            value = message.velocity if message.type == "note_on" else 0
        else:
            return

        bundle, profile = self.active_profile()
        if profile is None:
            if self.verbose and bundle not in self._warned:
                print(f"   (no profile for frontmost app {bundle})")
                self._warned.add(bundle)
            return

        binding = profile["controls"].get(key)
        if binding is None:
            if self.verbose:
                print(f"   (unmapped {key[0]} {key[1]} in {profile['name']})")
            return

        if binding.kind == "dial":
            self._dial(binding, value)
        else:
            self._button(binding, value)

    def _dial(self, binding, value):
        delta = decode_relative(value, binding.mode)
        if delta == 0:
            return
        target = binding.cw if delta > 0 else binding.ccw
        if target is None:
            return

        # Scale by step, then clamp. A fast spin can emit a large delta and an
        # unbounded repeat count would lock the UI mid-gesture.
        repeats = min(abs(delta) * binding.step, binding.max_repeats)
        if self.verbose:
            direction = "cw" if delta > 0 else "ccw"
            print(f"   {binding.label}: {direction} x{repeats}")
        for _ in range(repeats):
            self.keyboard.tap(*target)

    def _button(self, binding, value):
        if value > 0:
            if binding.down:
                if self.verbose:
                    print(f"   {binding.label}: press")
                self.keyboard.tap(*binding.down)
        else:
            if binding.up:
                if self.verbose:
                    print(f"   {binding.label}: release")
                self.keyboard.tap(*binding.up)


def list_ports():
    mido = _require_mido()
    names = mido.get_input_names()
    if not names:
        print("No MIDI input ports found.")
        print("Check that Monogram Creator is running and at least one module "
              "is set to a MIDI output type.")
        return
    print("Available MIDI input ports:")
    for name in names:
        print(f"  - {name}")


def pick_port(mido, requested):
    names = mido.get_input_names()
    if not names:
        sys.exit(
            "No MIDI input ports found. Is Monogram Creator running with at "
            "least one module set to MIDI?"
        )
    if requested:
        for name in names:
            if requested.lower() in name.lower():
                return name
        sys.exit(
            "No MIDI port matching {!r}.\nAvailable: {}".format(
                requested, ", ".join(names)
            )
        )
    # Prefer something that looks like the console before falling back.
    for name in names:
        if "monogram" in name.lower() or "palette" in name.lower():
            return name
    return names[0]


def monitor(port_name):
    """Print incoming MIDI without mapping it, to discover CC numbers."""
    mido = _require_mido()
    name = pick_port(mido, port_name)
    print(f"Monitoring {name!r}. Move each control; press Ctrl-C to stop.\n")
    seen = defaultdict(int)
    with mido.open_input(name) as port:
        try:
            for message in port:
                if message.type == "control_change":
                    seen[("cc", message.control)] += 1
                    print(f"  cc {message.control:<4} value {message.value:<4} "
                          f"(seen {seen[('cc', message.control)]}x)")
                elif message.type in ("note_on", "note_off"):
                    seen[("note", message.note)] += 1
                    print(f"  note {message.note:<4} "
                          f"{'on ' if message.type == 'note_on' else 'off'} "
                          f"(seen {seen[('note', message.note)]}x)")
        except KeyboardInterrupt:
            pass

    if seen:
        print("\nSummary of controls seen:")
        for (kind, number), count in sorted(seen.items()):
            print(f"  {kind} {number}  ({count} events)")


def main():
    parser = argparse.ArgumentParser(
        description="Bridge Monogram Console MIDI to macOS keystrokes.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument("--profiles", default="profiles",
                        help="directory of .yaml profiles (default: profiles)")
    parser.add_argument("--port", default=None,
                        help="MIDI input port name, or a substring of it")
    parser.add_argument("--list-ports", action="store_true",
                        help="list MIDI inputs and exit")
    parser.add_argument("--monitor", action="store_true",
                        help="print incoming MIDI to discover CC numbers")
    parser.add_argument("--check", action="store_true",
                        help="validate profiles and exit without connecting")
    parser.add_argument("--dry-run", action="store_true",
                        help="log keystrokes instead of sending them")
    parser.add_argument("-v", "--verbose", action="store_true",
                        help="log every mapped event")
    args = parser.parse_args()

    if args.list_ports:
        list_ports()
        return
    if args.monitor:
        monitor(args.port)
        return

    print("Loading profiles...")
    profiles = load_profiles(args.profiles)
    if args.check:
        print(f"\nOK: {len(profiles)} profile(s) valid.")
        return

    mido = _require_mido()
    name = pick_port(mido, args.port)

    bridge = Bridge(
        profiles,
        Keyboard(dry_run=args.dry_run),
        FrontmostApp(dry_run=args.dry_run),
        verbose=args.verbose,
    )

    print(f"\nListening on {name!r}.")
    if args.dry_run:
        print("Dry run: keystrokes will be logged, not sent.")
    else:
        print("If nothing happens, grant Accessibility permission to your "
              "terminal in\nSystem Settings > Privacy & Security > Accessibility.")
    print("Press Ctrl-C to stop.\n")

    with mido.open_input(name) as port:
        try:
            for message in port:
                bridge.handle(message)
        except KeyboardInterrupt:
            print("\nStopped.")


if __name__ == "__main__":
    main()
