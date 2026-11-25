# Wearer calibration

Calibration learns the wearer's resting measurements, comfortable articulation
range and lip-contact threshold. It does not redraw the selected character or
choose the amount of exaggeration. A is the selected lower-lip contour, with
strong forward rounding and spike retention disabled.

## Capture procedure

Use the final camera position and normal wearing conditions. Let OpenSeeFace
track a few neutral and speaking movements before starting. Its internal feature
normalization needs a usable range as well as the character's own wearer profile.

Get into each pose, select its capture button, hold about two seconds, then
stop capture before changing pose. Repeat a stage if tracking is unreliable.
The current UI uses manual capture/stop buttons and sample counts; it is not
an automatic timed wizard. About two seconds is the recommended operator
procedure, not an enforced duration. The current code requires eight valid
samples per stage and rejects unusably small movement ranges.

| Stage | Wearer action | Learned quantity |
| --- | --- | --- |
| Neutral | Relaxed face, lips gently together | Rest values and closed-lip landmark noise |
| Open | Comfortable deliberate AA opening | Usable opening and landmark-gap range |
| Wide | Spread lips as for EE | Positive width range |
| Narrow | Round/purse lips as for OO | Negative width range; rounding proxy |
| Smile | Smile with lips together | Left/right positive corner-lift range |

Use a comfortable speaking range rather than forcing physical extremes. Save
only after all five stages. The existing server writes the profile atomically
and reloads it on startup. A failed calibration does not replace the prior file.

## Measurement normalization

Each stage uses medians to reduce the effect of transient or extreme samples.
For a measured feature x and resting value r, the signed normalized value is:

`(x-r)/(positive-r)` above rest, or `(x-r)/(r-negative)` below rest.

Clamp to [-1,1]. Width therefore has distinct narrow and wide ranges instead
of assuming that a wearer's movement is symmetric around rest. Each corner has
its own smile range. Brows and the negative corner/frown span retain default
unit ranges; the five poses do not claim to calibrate them. Blink openness is
currently passed through from OpenSeeFace without a separate calibration stage.

Inner-lip gap is normalized by mouth width. The neutral stage's 95th-percentile
gap plus a small margin estimates the contact/noise threshold. The open stage's
median gap supplies its usable opening range. If both stages lack enough gap
samples, current code retains default aperture thresholds; that fallback should
be checked in an actual wearer session rather than mistaken for measured contact.

The retargeter combines normalized opening feature (55%) with normalized landmark
aperture (45%) when aperture is available. Aperture also controls the contact
gate, so observed closure can override a drifting opening feature. Negative
width selects rounding/forward reach; positive width selects spreading. These
are geometric proxies, not inferred phoneme names or measured lip protrusion.

## Speech check and style tuning

After capture, check quiet rest, repeated M/B/P closures, EE-to-OO transitions
and a normal sentence with large and small syllables. Check that rest is stable,
contact reads cleanly and rounding advances the mouth without random toggling.
Repeat the relevant calibration stage if an ordinary movement saturates too
early or requires a strained pose to register. Tune opening contrast, accents
and reach as character style after the wearer measurements are credible.

The profile is independent of whether display poses are shown at 24, 12 or
6 fps. Keep tracking/control responsive even when the display holds drawings.
Existing internet footage uses an estimated earlier-section profile and has
not performed these guided poses.

## Baseline consistency and reuse

OpenSeeFace's signed features have their own adaptive median/min/max statistics.
A saved wearer profile assumes the same tracker normalization. Saving a profile
does not itself freeze or restore OpenSeeFace's internal state. Coordinating
that baseline lifecycle remains part of final tracker integration; do not claim
that restarting the external tracker preserves an identical feature baseline.
If its normalization changes, or the camera/head mounting moves, recheck the
guided poses and recalibrate as needed. Raw landmark aperture remains separate
evidence for contact, but width/corner normalization still needs a consistent
baseline. Actual wearer validation remains outstanding.
