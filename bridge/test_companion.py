#!/usr/bin/env python3
"""Tests for the parts that are easy to get subtly wrong.

Encoder decoding and shortcut parsing are where a bug shows up as "the dial
only counts up" or "this button does nothing", which are annoying to diagnose
against real hardware. Run with:  python3 test_companion.py
"""

import unittest

import keycodes
from companion import Binding, Bridge, decode_relative


class TestRelativeDecoding(unittest.TestCase):

    def test_twos_complement_clockwise(self):
        self.assertEqual(decode_relative(1, "twos_complement"), 1)
        self.assertEqual(decode_relative(3, "twos_complement"), 3)
        self.assertEqual(decode_relative(63, "twos_complement"), 63)

    def test_twos_complement_counterclockwise(self):
        self.assertEqual(decode_relative(127, "twos_complement"), -1)
        self.assertEqual(decode_relative(125, "twos_complement"), -3)
        self.assertEqual(decode_relative(64, "twos_complement"), -64)

    def test_signed_bit_clockwise(self):
        self.assertEqual(decode_relative(65, "signed_bit"), 1)
        self.assertEqual(decode_relative(67, "signed_bit"), 3)

    def test_signed_bit_counterclockwise(self):
        self.assertEqual(decode_relative(1, "signed_bit"), -1)
        self.assertEqual(decode_relative(3, "signed_bit"), -3)

    def test_zero_is_no_movement(self):
        self.assertEqual(decode_relative(0, "twos_complement"), 0)

    def test_unknown_mode_names_itself(self):
        with self.assertRaises(ValueError) as ctx:
            decode_relative(1, "absolute")
        self.assertIn("absolute", str(ctx.exception))


class TestKeyParsing(unittest.TestCase):

    def test_bare_key(self):
        code, mods = keycodes.parse("b")
        self.assertEqual(code, keycodes.KEYCODES["b"])
        self.assertEqual(mods, 0)

    def test_single_modifier(self):
        code, mods = keycodes.parse("cmd+z")
        self.assertEqual(code, keycodes.KEYCODES["z"])
        self.assertEqual(mods, keycodes.MODIFIERS["cmd"])

    def test_stacked_modifiers(self):
        code, mods = keycodes.parse("cmd+shift+opt+z")
        expected = (keycodes.MODIFIERS["cmd"]
                    | keycodes.MODIFIERS["shift"]
                    | keycodes.MODIFIERS["opt"])
        self.assertEqual(code, keycodes.KEYCODES["z"])
        self.assertEqual(mods, expected)

    def test_symbol_aliases(self):
        self.assertEqual(keycodes.parse("[")[0],
                         keycodes.KEYCODES["leftbracket"])
        self.assertEqual(keycodes.parse("]")[0],
                         keycodes.KEYCODES["rightbracket"])

    def test_case_insensitive(self):
        self.assertEqual(keycodes.parse("CMD+Z"), keycodes.parse("cmd+z"))

    def test_whitespace_tolerated(self):
        self.assertEqual(keycodes.parse(" cmd + z "), keycodes.parse("cmd+z"))

    def test_unknown_key_rejected(self):
        with self.assertRaises(keycodes.KeySpecError):
            keycodes.parse("cmd+nosuchkey")

    def test_modifier_without_key_rejected(self):
        with self.assertRaises(keycodes.KeySpecError):
            keycodes.parse("cmd+shift")

    def test_two_keys_rejected(self):
        with self.assertRaises(keycodes.KeySpecError):
            keycodes.parse("a+b")

    def test_empty_rejected(self):
        with self.assertRaises(keycodes.KeySpecError):
            keycodes.parse("")


class FakeKeyboard:
    def __init__(self):
        self.taps = []

    def tap(self, keycode, flags=0):
        self.taps.append((keycode, flags))


class FakeFrontmost:
    def __init__(self, bundle):
        self.bundle = bundle

    def get(self):
        return self.bundle


class FakeMessage:
    def __init__(self, type, **kwargs):
        self.type = type
        for key, value in kwargs.items():
            setattr(self, key, value)


def build_bridge(bundle="com.adobe.Photoshop"):
    keyboard = FakeKeyboard()
    profiles = {
        "com.adobe.Photoshop": {
            "name": "Photoshop",
            "controls": {
                ("cc", 21): Binding(
                    {"type": "dial", "cc": 21,
                     "clockwise": "]", "counterclockwise": "[",
                     "step": 2, "max_repeats": 10},
                    "brush_size"),
                ("cc", 23): Binding(
                    {"type": "dial", "cc": 23, "clockwise": "cmd+equal"},
                    "zoom_in_only"),
                ("note", 36): Binding(
                    {"note": 36, "press": "cmd+z"}, "undo"),
                ("note", 44): Binding(
                    {"note": 44, "press": "cmd+h", "release": "cmd+h"},
                    "hold"),
            },
        }
    }
    bridge = Bridge(profiles, keyboard, FakeFrontmost(bundle))
    return bridge, keyboard


class TestBridgeRouting(unittest.TestCase):

    def test_dial_clockwise_applies_step(self):
        bridge, keyboard = build_bridge()
        bridge.handle(FakeMessage("control_change", control=21, value=1))
        # delta of 1, step of 2 -> two keystrokes
        self.assertEqual(len(keyboard.taps), 2)
        self.assertEqual(keyboard.taps[0][0],
                         keycodes.KEYCODES["rightbracket"])

    def test_dial_counterclockwise_uses_other_key(self):
        bridge, keyboard = build_bridge()
        bridge.handle(FakeMessage("control_change", control=21, value=127))
        self.assertEqual(len(keyboard.taps), 2)
        self.assertEqual(keyboard.taps[0][0],
                         keycodes.KEYCODES["leftbracket"])

    def test_fast_spin_is_clamped(self):
        bridge, keyboard = build_bridge()
        # delta 20 * step 2 = 40, clamped to max_repeats of 10
        bridge.handle(FakeMessage("control_change", control=21, value=20))
        self.assertEqual(len(keyboard.taps), 10)

    def test_dial_with_no_binding_for_direction_is_silent(self):
        bridge, keyboard = build_bridge()
        # zoom_in_only has no counterclockwise mapping
        bridge.handle(FakeMessage("control_change", control=23, value=127))
        self.assertEqual(keyboard.taps, [])

    def test_button_press(self):
        bridge, keyboard = build_bridge()
        bridge.handle(FakeMessage("note_on", note=36, velocity=127))
        self.assertEqual(len(keyboard.taps), 1)
        self.assertEqual(keyboard.taps[0],
                         (keycodes.KEYCODES["z"], keycodes.MODIFIERS["cmd"]))

    def test_button_without_release_ignores_note_off(self):
        bridge, keyboard = build_bridge()
        bridge.handle(FakeMessage("note_off", note=36, velocity=0))
        self.assertEqual(keyboard.taps, [])

    def test_hold_control_fires_on_both_edges(self):
        bridge, keyboard = build_bridge()
        bridge.handle(FakeMessage("note_on", note=44, velocity=127))
        bridge.handle(FakeMessage("note_off", note=44, velocity=0))
        self.assertEqual(len(keyboard.taps), 2)

    def test_note_on_with_zero_velocity_is_a_release(self):
        # Many controllers send note_on velocity 0 instead of note_off.
        bridge, keyboard = build_bridge()
        bridge.handle(FakeMessage("note_on", note=44, velocity=0))
        self.assertEqual(len(keyboard.taps), 1)

    def test_unmapped_control_is_silent(self):
        bridge, keyboard = build_bridge()
        bridge.handle(FakeMessage("control_change", control=99, value=64))
        self.assertEqual(keyboard.taps, [])

    def test_other_app_in_front_sends_nothing(self):
        bridge, keyboard = build_bridge(bundle="com.apple.Safari")
        bridge.handle(FakeMessage("note_on", note=36, velocity=127))
        self.assertEqual(keyboard.taps, [])

    def test_non_midi_message_ignored(self):
        bridge, keyboard = build_bridge()
        bridge.handle(FakeMessage("clock"))
        self.assertEqual(keyboard.taps, [])


if __name__ == "__main__":
    unittest.main(verbosity=2)
