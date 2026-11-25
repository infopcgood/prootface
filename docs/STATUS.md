# Status — 2026-11-25

## Latest user direction

Use authored mouth poses as a starting point, exaggerate the visible shape
changes like character animation, and work at a chosen 24 or 12 fps. The chosen
rate is **24 fps**. The user explicitly reiterated: this must work in REAL TIME.
No tongue or tooth rows. Preserve the selected visual identity and keep source
assets and inspection details private. Hardware/ROS work remains secondary.

## Latest performance revision

The user found the prior 24 fps pass still insufficiently dramatic. The old
opening ease-out lifted quiet movement close to the accents. It was replaced
by a contrast curve (default exponent 2.4), .95 held-family commitment and
observed-opening accents. Large onsets hit the authored extreme briefly; quiet
shapes compress tightly. Closing, contact and tracking loss cancel an accent
immediately. The driver remains causal at 24 fps; there is no pose extrapolation
outside the primary authored basis.

A before/after comparison uses identical synthetic inputs, audio timing and
fixed framing. The full-face new clip and isolated-mouth comparison are private
review outputs. They are not live camera recordings or CM4 benchmarks.

## Current behavior

- The live character clock and SSE presentation target 24 fps. Browser output
  holds each frame as-is; it adds no monitor-rate pose interpolation.
- Shape contrast pushes dominant open/round/wide silhouettes apart. A causal
  hysteresis selector gives a family a two-frame minimum exposure while jaw
  motion continues to follow current input. It does not wait for future frames.
- Contact interrupts a shape hold immediately and gets two readable frames.
  Neutral closure does not continually extend the deadline on release. Brief
  contact onsets between output ticks are latched by the receiver.
- Generic optional consonant channels are supported, but the OpenSeeFace adapter
  does NOT infer them. Default tracking-mode review disables them completely.
- The native review helper uses 24 fps frame-authored synthetic control goals,
  then sends only supported channels through the same causal Animator used live.
  A separate authored reference mode can use full consonant hints and is labeled.
- Rendered MP4/GIF previews are synthetic replay, not real camera recordings.
  Offline Blender is only a review renderer and never runs in the live path.

## Architecture retained

OpenSeeFace binary decoding, signed wearer calibration, monotonic freshness,
tracking-loss relaxation and a privately configured authored morph basis remain
separate. Indexed geometry, UVs, sparse target deltas and emission rendering are
used for both anatomical side views. A fixed view covers configured mouth poses.
Old raster-ribbon inflation and an automatic tearing corrective were rejected;
do not restore either approach as the target rig.

Live path: measurements -> wearer normalization -> causal character controller
-> authored morph weights -> WebGL/side outputs. No future audio alignment,
phoneme schedule, native offline renderer or rendered-frame queue is required.
Specialized consonant inference and actual-device evaluation remain future work.

## Verification

- Python unittest: 33 passed.
- Node geometry/character/morph tests: 13 passed.
- New regressions cover tight-to-hit contrast, causal onset accents, prompt
  cancellation, 24 fps key exposures, short closures, dominant-shape
  contrast, bounded primary weights, no dependence on future inputs, continued
  jaw response during family holds, contact interruption, and brief contacts
  observed between output frames.
- Live-server smoke observed the expected 24 fps target cadence and verified
  schema-2 character/texture endpoints. This was not a CM4 test.
- Native video verified as 24/1 fps; GIF preserves all source frame exposures.
  Enlarged mouth frames were reviewed and no display-edge clipping was found.
- Browser runtime, actual OpenSeeFace wearer capture, CM4 end-to-end latency and
  physical-display performance remain unmeasured. Synthetic replay is not proof
  of camera tracking accuracy or actual hardware throughput.

## Continuity and repository

Public repository: https://github.com/infopcgood/prootface, branch master.
Previous checkpoint: b783113cb77f43357aa792b5142faa9df81ad765.
Private settings and runtime data remain under ignored local/. Publish reusable
code and generic instructions only; never include source key/object names,
reference identifiers, derived geometry, textures or private inspection notes.
Use an expected branch SHA and preserve concurrent work.

## Next

1. Review the exaggerated 24 fps tracking-mode replay and refine its shape
   response while keeping the live path causal.
2. Capture real wearer measurements and replay them through the exact controller;
   tune calibration and compare input movement, rendered response and delay.
3. Improve any missing measured features before claiming detailed consonant
   tracking. Do not fake live capability with a scripted phoneme reference.
4. Exercise the real browser and CM4, then the visor. Keep 24 fps presentation.
5. Integrate with the existing proto-ros2 pipeline only when animation is ready;
   preserve screen ownership and use measured panel coordinates.
