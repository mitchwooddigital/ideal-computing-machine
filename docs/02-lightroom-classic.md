# Lightroom Classic

This is the best-supported case. [MIDI2LR](https://github.com/rsjaffe/MIDI2LR)
is a mature, actively maintained open-source bridge that talks directly to
Lightroom's develop controls. It replaces the dead Monogram plugin completely.

## Important: Classic only

MIDI2LR works with **Lightroom Classic**. Cloud Lightroom (the one that just
says "Lightroom") has no control-surface or plugin API for this, so there is
no equivalent bridge and nothing this project can do about it. If you use
both, the console will work in Classic and not in cloud.

## Setup

**1. Set the modules to MIDI in Creator**, per
[the base setup](01-route-a-setup.md):

- Type: **CC (Control Change)**
- Dials: **Relative**
- Sliders: **Absolute**
- Unique CC number per control

**2. Install MIDI2LR** from the
[releases page](https://github.com/rsjaffe/MIDI2LR/releases) (6.2.1.0 or
later). It installs as a Lightroom plugin plus a companion app.

**3. Map each control.** In the MIDI2LR panel, click the Lightroom parameter
you want (Exposure, Contrast, Temperature...), then move the console control
you want bound to it. It learns the pairing.

**4. The step everyone misses.** Right-click each *dial* mapping and select
**"Two's Complement"**. Without this, MIDI2LR misreads the relative encoder
values and the dial will only ever move one direction, or jump wildly. If a
dial behaves strangely, this is almost always why.

**5. Save the profile** as XML so it reloads automatically.

## Suggested mapping

Dials suit the continuous develop parameters:

| Control | Parameter |
|---|---|
| Dial 1 | Exposure |
| Dial 2 | Contrast |
| Dial 3 | Highlights |
| Dial 4 | Shadows |
| Dial 5 | Temperature |
| Dial 6 | Vibrance |

Buttons suit discrete actions:

| Control | Action |
|---|---|
| Button 1 | Next photo |
| Button 2 | Previous photo |
| Button 3 | Set flag / pick |
| Button 4 | Reject |
| Button 5 | Copy settings |
| Button 6 | Paste settings |
| Button 7 | Before/after toggle |
| Button 8 | Reset all |

## Troubleshooting

**A dial only moves one way.** Two's Complement is not set on that mapping.
See step 4.

**A dial moves in huge jumps.** The module is in Absolute mode in Creator, not
Relative. Change it there.

**Nothing responds at all.** Check MIDI2LR is actually receiving: its panel
shows incoming messages. If it sees nothing, the problem is upstream in
Creator, so go back to `companion.py --monitor` and confirm MIDI is leaving
the console.

**It broke after a Lightroom update.** Unlike the Monogram plugin, MIDI2LR is
maintained, so update it. This is the whole reason for using it.

## Credit

This recipe follows the approach documented by Rob Futrell in
[Fix Broken Monogram Creative Console in
Lightroom](https://robfutrell.com/monogram-creative-console-lightroom-fix/).
