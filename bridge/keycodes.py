"""macOS virtual key codes and modifier masks.

Key codes are the ANSI layout constants from Carbon's Events.h. They are
positional, not character-based: `KEYCODES["a"]` is the key in the "a" position
on a US layout, which is where Adobe's default shortcuts are defined.
"""

KEYCODES = {
    "a": 0, "s": 1, "d": 2, "f": 3, "h": 4, "g": 5, "z": 6, "x": 7, "c": 8,
    "v": 9, "b": 11, "q": 12, "w": 13, "e": 14, "r": 15, "y": 16, "t": 17,
    "1": 18, "2": 19, "3": 20, "4": 21, "6": 22, "5": 23, "9": 25, "7": 26,
    "8": 28, "0": 29, "o": 31, "u": 32, "i": 34, "p": 35, "l": 37, "j": 38,
    "k": 40, "n": 45, "m": 46,

    "equal": 24, "minus": 27, "rightbracket": 30, "leftbracket": 33,
    "quote": 39, "semicolon": 41, "backslash": 42, "comma": 43, "slash": 44,
    "period": 47, "grave": 50,

    "return": 36, "tab": 48, "space": 49, "delete": 51, "escape": 53,
    "forwarddelete": 117, "help": 114, "home": 115, "end": 119,
    "pageup": 116, "pagedown": 121,

    "left": 123, "right": 124, "down": 125, "up": 126,

    "f1": 122, "f2": 120, "f3": 99, "f4": 118, "f5": 96, "f6": 97, "f7": 98,
    "f8": 100, "f9": 101, "f10": 109, "f11": 103, "f12": 111, "f13": 105,
    "f14": 107, "f15": 113, "f16": 106, "f17": 64, "f18": 79, "f19": 80,
    "f20": 90,

    "keypad0": 82, "keypad1": 83, "keypad2": 84, "keypad3": 85, "keypad4": 86,
    "keypad5": 87, "keypad6": 88, "keypad7": 89, "keypad8": 91, "keypad9": 92,
    "keypadplus": 69, "keypadminus": 78, "keypadmultiply": 67,
    "keypaddivide": 75, "keypadenter": 76, "keypaddecimal": 65,
}

# Friendly aliases so profiles can be written the way people actually speak.
ALIASES = {
    "esc": "escape", "del": "delete", "backspace": "delete",
    "ret": "return", "enter": "return", "spc": "space",
    "[": "leftbracket", "]": "rightbracket",
    "-": "minus", "=": "equal", ",": "comma", ".": "period", "/": "slash",
    "\\": "backslash", ";": "semicolon", "'": "quote", "`": "grave",
    "arrowleft": "left", "arrowright": "right",
    "arrowup": "up", "arrowdown": "down",
}

MODIFIERS = {
    "cmd": 0x00100000, "command": 0x00100000,
    "shift": 0x00020000,
    "opt": 0x00080000, "option": 0x00080000, "alt": 0x00080000,
    "ctrl": 0x00040000, "control": 0x00040000,
    "fn": 0x00800000,
}


class KeySpecError(ValueError):
    """Raised when a profile contains a shortcut we cannot parse."""


def parse(spec):
    """Parse a shortcut like "cmd+shift+z" into (keycode, modifier_mask).

    Raises KeySpecError with the offending token so a typo in a profile names
    itself instead of silently binding nothing.
    """
    if not isinstance(spec, str) or not spec.strip():
        raise KeySpecError(f"empty or non-string key spec: {spec!r}")

    # A bare "+" is the key itself, not a separator.
    raw = spec.strip()
    if raw == "+":
        return KEYCODES["equal"], 0

    tokens = [t.strip().lower() for t in raw.split("+") if t.strip()]
    if not tokens:
        raise KeySpecError(f"no tokens in key spec: {spec!r}")

    mask = 0
    key_token = None
    for token in tokens:
        if token in MODIFIERS:
            mask |= MODIFIERS[token]
        elif key_token is None:
            key_token = token
        else:
            raise KeySpecError(
                f"key spec {spec!r} names two keys ({key_token!r} and {token!r}); "
                "only one non-modifier key is allowed"
            )

    if key_token is None:
        raise KeySpecError(f"key spec {spec!r} has modifiers but no key")

    key_token = ALIASES.get(key_token, key_token)
    if key_token not in KEYCODES:
        raise KeySpecError(f"unknown key {key_token!r} in spec {spec!r}")

    return KEYCODES[key_token], mask
