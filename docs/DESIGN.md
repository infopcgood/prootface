# Character model and animation rules

## Current target

The user selected Triwave as the static visual reference and explicitly asked
us to ignore avatar phoneme animation keys. Develop natural Nick/Zootopia-informed
articulation independently, preserving the selected rest identity. No tongue,
tooth rows, detached fangs or metallic lip tubes. Private reference details and
inspection notes are excluded from this public document.

## Boundaries

1. OpenSeeFace measures features and landmarks.
2. Wearer calibration learns signed usable movement and contact aperture.
3. Retargeting estimates opening, narrowing, spread, corners and seal.
4. Time filtering stabilizes rest, follows deliberate motion and honors contact.
5. A shared semantic pose drives both anatomical sides.
6. Character-specific deformation expands the imported rest silhouette.
7. Display projection handles mirroring, mask and eventual LED sampling.

Style changes do not require repeating wearer calibration. Physical panel
placement is distinct from the camera used to project the character.

## Rest-shape import

The generic Blender adapter reads private import settings from an ignored file.
It opens a user-provided asset with scripts disabled and zeros every non-rest
animation key. The configured emission source and opaque occlusion produce two
orthographic rest masks. No reference animation delta is exported. Source
identity, internal object/material names and projection calibration are never
embedded in reusable code.

The compiler identifies visible eye, nose and mouth components and simplifies
their boundaries. The private compiled file contains rest polygons, not a
viseme library. It also stores normalized front-to-rear position `t` and a
lower-ribbon weight `v`, determined from the rest mask's vertical envelope.
The selected concave silhouette is retained without copying its data into code.
Both side projections are canonicalized to front-left; each display mirrors
only once. Source asset and derived outlines are not committed.

## Independent deformation

The Python model filters semantic controls and computes visible aperture:

`a = opening^gamma * (1 - seal)^2`

A measured closure has priority over jaw drift. In the filled-ribbon design,
contact means returning to the supplied closed ribbon, not extinguishing the
entire luminous mouth. The original contour study remains an explicitly labeled
fallback when the private character file is absent.

For a mouth span `L`, normalized position `t`, lower weight `v`, corner `c` and
rounding `r`, the imported-character path uses:

- Smooth opening envelope `e = sin(pi*t)^0.72`, retaining both returns.
- Lower expansion `dy = -.32*L*a*e*v*(jaw_gain/.36)*(1+.18*r)`.
- Backward recession `dx = .09*L*a*e*v*(recession/.12)`.
- Persistent corner lift `.16*L*c*smoothstep((t-.30)/.70)` with style gain.
- Bounded narrowing/spreading about the posterior anchor, plus a small central
  upper-contour rounding correction. These changes do not replace the rest
  shape or switch between discrete drawings.

Upper contour vertices remain comparatively stable; the lower band expands
and recedes. At contact, opening displacement is exactly zero. Expression and
width remain independent, so a closed smile or rounded closure retains character.
The concave outline is triangulated after deformation, avoiding a convex fan
that would incorrectly fill the hooked corner. The display uses unlit emission;
it does not invent sculpted human lips to suggest natural motion.

The eye keeps the supplied rest outline; blink compresses it vertically and a
small cheek lift follows positive corner expression. Eye animation is secondary
to the mouth in this study. The source's eye/viseme animation keys are not used.

## Temporal and speech rules

Live OpenSeeFace controls already contain much of real coarticulation. Do not
classify phonemes or gate silent expressions with microphone activity. The
speed-adaptive low-pass follows deliberate mouth movement quickly and suppresses
rest noise; contact can close immediately. Tracking loss eases toward rest.
Use monotonic receive time, never sender wall time, for freshness.

For the audible offline example only, CMU Flite segment times schedule our own
semantic gestures. Opening/spreading overlap across roughly 45 ms windows;
rounding prepares about 75 ms early, while contact has a shorter response.
Closure is a dominating constraint, so averaging adjacent vowels cannot erase
an M/B/P closure. A slower corner expression persists through the whole phrase.
The same Python Animator and JS deformation render the review clip. This is
not a live tracker recording or an evaluation of the avatar's phoneme keys.

## Film-animation transfer

Nick's animators discussed a receding opening to avoid a crocodile-like jaw;
this design adapts that principle as bounded lower-ribbon recession. Controlled
corners retain appeal and expression during articulation. Actual closures and
relaxed returns to rest are more useful here than a one-picture-per-phoneme
mouth chart. These are our adaptations, not a disclosure of Disney's rig.

## Physical and measurement limits

The selected Sigma WS35 layout has two shaped flat side boards and a nose gap
behind a curved visor. Higher LED density improves sampling, not emitting area,
physical silhouette or observer-dependent parallax. Current panel mask/tilt are
schematics; no assembly angle or custom LED map has been measured. The video
shows the two flat projected face views, not a verified fit to physical panels.

OpenSeeFace exports signed adaptive features, not a full ARKit/Babble set.
Rounding is a narrowing proxy and contact is inferred from inner-lip aperture.
Do not claim direct pucker, pressure or independent jaw-muscle measurement.

## Acceptance

Require stable rest identity, full closures, restrained corners, no detached
points, persistent expression, smooth receding opening and safe loss recovery.
Tests and software frames verify geometry and timing invariants. Perceptual
naturalness needs user review of the speaking clip and real captured wearer
speech, followed by browser and actual-visor review.
