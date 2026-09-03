# Premiere Pro

Premiere is the easy one. Unlike Photoshop or After Effects, it has **real
control-surface support built in**, so the console can talk to it directly
with no bridge software.

## Native control surface

Premiere accepts control surfaces in **Mackie Control (MC)** mode:

**Settings > Control Surface > Add > Mackie**

Then select the console's MIDI port as the input and output device.

The catch is that Adobe's implementation is limited to what the Mackie
protocol expresses. In practice that means encoders map to audio panning and
faders to track levels, with buttons on their default transport functions.
It is genuinely useful for audio mixing passes and transport control, and
much less useful for editing operations.

See [Adobe's control surface
documentation](https://helpx.adobe.com/africa/premiere-pro/using/control-surface-support.html)
for the full mapping.

## For editing rather than mixing

Because native support is mixing-oriented, most people get more out of Premiere
by treating the console as a keyboard:

**Option 1 — keyboard shortcuts in Creator.** Set the modules to emit
keystrokes directly. No extra software at all. This covers the majority of
editing actions well:

| Control | Action | Shortcut |
|---|---|---|
| Button | Play/pause | `space` |
| Button | Cut / razor | `cmd+k` |
| Button | Ripple delete | `shift+delete` |
| Button | Mark in | `i` |
| Button | Mark out | `o` |
| Dial | Frame step | `left` / `right` |
| Dial | Timeline zoom | `-` / `=` |

Dial-driven frame stepping needs a repeated keystroke per detent, which
Creator's keyboard mode may not do smoothly. If it feels coarse, use the
bridge instead.

**Option 2 — the bridge daemon.** Set dials to MIDI and use
`bridge/companion.py` with a Premiere profile, exactly as for
[the other Adobe apps](03-keystroke-bridge.md). This gives proper `step` and
`max_repeats` control over scrub speed. Premiere's bundle id:

```bash
osascript -e 'id of app "Adobe Premiere Pro 2025"'
```

**Option 3 — PrControl.** [Peltmade's PrControl](https://peltmade.com/prcontrol.html)
is a third-party plugin offering richer MIDI mapping than Adobe's built-in
Mackie support. Worth a look if the native surface is close but not quite
enough. It is a paid product and outside this project.

## Recommendation

Combine them: native Mackie mode for audio work, keystrokes or the bridge for
editing. They coexist fine as long as you do not assign the same physical
control to both.
