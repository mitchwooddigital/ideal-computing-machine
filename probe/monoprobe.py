#!/usr/bin/env python3
"""monoprobe - map the Monogram Console's raw USB HID protocol.

Route A (MIDI -> keystrokes) depends on Monogram Creator still running. This
tool exists for the day it does not: it reads the console's raw HID reports so
a native driver can be written with no Monogram software in the loop at all.

No public protocol dump exists for this hardware, so this is a discovery tool
rather than a finished decoder. The workflow is:

    1. python3 monoprobe.py --scan
         Find the console and note its vendor/product id.

    2. python3 monoprobe.py --watch 0x1234:0x5678
         Turn one control at a time. Bytes that change are highlighted, which
         is usually enough to spot the layout by eye.

    3. python3 monoprobe.py --record session.jsonl --watch 0x1234:0x5678
         Capture a labelled session, one control at a time.

    4. python3 monoprobe.py --analyse session.jsonl
         Report which byte offsets moved for which control, so the field
         layout falls out of the data instead of guesswork.

On macOS, reading raw HID from a device the system claims may require running
as root, or unloading the kernel driver that has grabbed it.
"""

import argparse
import json
import sys
import time
from collections import defaultdict


def _require_hid():
    try:
        import hid
        return hid
    except ImportError:
        sys.exit(
            "Missing HID support. Install it with:\n"
            "  brew install hidapi\n"
            "  pip install hidapi\n"
        )


# Strings that suggest a device is the console. Monogram bought the Palette
# Gear line, so firmware may identify as either.
NAME_HINTS = ("monogram", "palette")


def parse_id_pair(text):
    """Parse "0x16d0:0x0e1a" or "16d0:0e1a" into (vid, pid)."""
    if ":" not in text:
        raise argparse.ArgumentTypeError(
            f"expected VID:PID, got {text!r} (e.g. 0x16d0:0x0e1a)"
        )
    left, right = text.split(":", 1)
    try:
        return int(left, 16), int(right, 16)
    except ValueError:
        raise argparse.ArgumentTypeError(
            f"VID and PID must be hexadecimal, got {text!r}"
        )


def scan(show_all=False):
    """List HID devices, flagging anything that looks like the console."""
    hid = _require_hid()
    devices = hid.enumerate()
    if not devices:
        sys.exit("No HID devices found at all. Is anything plugged in?")

    likely = []
    for info in devices:
        haystack = " ".join(
            str(info.get(key, "")) for key in
            ("manufacturer_string", "product_string")
        ).lower()
        if any(hint in haystack for hint in NAME_HINTS):
            likely.append(info)

    if likely:
        print("Likely console interfaces:\n")
        _print_devices(likely)
        print("\nA modular console usually exposes several interfaces (one per")
        print("function: HID, keyboard, MIDI). Try each with --watch; the one")
        print("carrying module data is the one whose bytes change when you")
        print("turn a dial.")
    else:
        print("Nothing matched a Monogram/Palette name string.")
        print("The device may report a generic name, so scan the full list")
        print("with --scan --all and look for an unfamiliar entry that")
        print("appears only when the console is plugged in.\n")

    if show_all or not likely:
        print(f"\nAll {len(devices)} HID devices:\n")
        _print_devices(devices)


def _print_devices(devices):
    for info in devices:
        vid = info.get("vendor_id", 0)
        pid = info.get("product_id", 0)
        print(f"  {vid:#06x}:{pid:#06x}  "
              f"{info.get('manufacturer_string') or '?'} / "
              f"{info.get('product_string') or '?'}")
        print(f"      usage_page={info.get('usage_page')} "
              f"usage={info.get('usage')} "
              f"interface={info.get('interface_number')}")
        path = info.get("path")
        if isinstance(path, bytes):
            path = path.decode("utf-8", "replace")
        print(f"      path={path}")


def format_report(data, previous=None):
    """Hex-format a report, marking bytes that changed since the last one."""
    parts = []
    for index, byte in enumerate(data):
        changed = previous is not None and index < len(previous) \
            and previous[index] != byte
        parts.append(f"[{byte:02x}]" if changed else f" {byte:02x} ")
    return "".join(parts)


def offsets_ruler(width):
    return "".join(f" {i:02d} " for i in range(width))


def watch(vid, pid, record_path=None, label=None, timeout_ms=500):
    """Read reports continuously, highlighting what changes."""
    hid = _require_hid()

    device = hid.device()
    try:
        device.open(vid, pid)
    except (OSError, IOError) as exc:
        sys.exit(
            f"Could not open {vid:#06x}:{pid:#06x}: {exc}\n\n"
            "Common causes:\n"
            "  - Monogram Creator is running and holding the device. Quit it.\n"
            "  - macOS has claimed the interface; try running with sudo.\n"
            "  - Wrong interface; run --scan and try another one."
        )

    device.set_nonblocking(True)
    print(f"Opened {vid:#06x}:{pid:#06x}")
    try:
        print(f"  manufacturer: {device.get_manufacturer_string()}")
        print(f"  product:      {device.get_product_string()}")
    except (OSError, IOError):
        pass  # Some interfaces refuse string descriptors; not fatal.

    if label:
        print(f"  label:        {label}")
    print("\nMove ONE control at a time. Changed bytes are [bracketed].")
    print("Press Ctrl-C to stop.\n")

    sink = open(record_path, "a") if record_path else None
    previous = None
    count = 0
    ruler_shown = False

    try:
        while True:
            data = device.read(64, timeout_ms=timeout_ms)
            if not data:
                continue

            if not ruler_shown:
                print("        " + offsets_ruler(len(data)))
                ruler_shown = True

            count += 1
            print(f"  {count:>5} {format_report(data, previous)}")

            if sink:
                sink.write(json.dumps({
                    "t": time.time(),
                    "label": label,
                    "data": list(data),
                }) + "\n")
                sink.flush()

            previous = data
    except KeyboardInterrupt:
        print(f"\nStopped after {count} reports.")
    finally:
        device.close()
        if sink:
            sink.close()
            print(f"Recorded to {record_path}")


def analyse(path):
    """Report which byte offsets vary, grouped by the label being recorded.

    Offsets that move only while one control was being touched are almost
    certainly that control's field.
    """
    try:
        with open(path) as handle:
            rows = [json.loads(line) for line in handle if line.strip()]
    except FileNotFoundError:
        sys.exit(f"No such recording: {path}")
    except json.JSONDecodeError as exc:
        sys.exit(f"{path} is not valid JSONL: {exc}")

    if not rows:
        sys.exit(f"{path} is empty.")

    by_label = defaultdict(list)
    for row in rows:
        by_label[row.get("label") or "(unlabelled)"].append(row["data"])

    print(f"{len(rows)} reports across {len(by_label)} label(s).\n")

    varying_by_label = {}
    for label, reports in sorted(by_label.items()):
        width = max(len(r) for r in reports)
        values = defaultdict(set)
        for report in reports:
            for index in range(width):
                values[index].add(report[index] if index < len(report) else None)

        varying = {i: v for i, v in values.items() if len(v) > 1}
        varying_by_label[label] = set(varying)

        print(f"--- {label} ({len(reports)} reports, {width} bytes) ---")
        if not varying:
            print("  No bytes changed. Was the control actually moved?\n")
            continue

        for index in sorted(varying):
            seen = sorted(v for v in varying[index] if v is not None)
            preview = ", ".join(f"{v:02x}" for v in seen[:12])
            if len(seen) > 12:
                preview += f", ... ({len(seen)} distinct)"
            print(f"  byte {index:>2}: {preview}")
        print()

    if len(varying_by_label) > 1:
        print("--- cross-label comparison ---")
        shared = set.intersection(*varying_by_label.values())
        if shared:
            print(f"  Offsets varying under every label: "
                  f"{sorted(shared)}")
            print("  These are likely counters, timestamps or checksums "
                  "rather than\n  control data.")
        for label, offsets in sorted(varying_by_label.items()):
            unique = offsets - shared
            if unique:
                print(f"  Unique to {label!r}: {sorted(unique)}")
        print("\n  Offsets unique to one label are that control's payload.")


def main():
    parser = argparse.ArgumentParser(
        description="Discover the Monogram Console's raw HID protocol.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument("--scan", action="store_true",
                        help="list HID devices and flag likely candidates")
    parser.add_argument("--all", action="store_true",
                        help="with --scan, show every device")
    parser.add_argument("--watch", type=parse_id_pair, metavar="VID:PID",
                        help="stream reports from a device, e.g. 0x16d0:0x0e1a")
    parser.add_argument("--record", metavar="FILE",
                        help="append the watched reports to a JSONL file")
    parser.add_argument("--label", metavar="NAME",
                        help="tag recorded reports, e.g. 'dial-1-clockwise'")
    parser.add_argument("--analyse", "--analyze", dest="analyse",
                        metavar="FILE",
                        help="report which byte offsets vary, by label")
    args = parser.parse_args()

    if args.scan:
        scan(show_all=args.all)
    elif args.watch:
        watch(*args.watch, record_path=args.record, label=args.label)
    elif args.analyse:
        analyse(args.analyse)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
