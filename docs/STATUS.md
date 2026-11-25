# Status — 2026-11-25

## Latest user direction

Use authored mouth poses as a starting point, exaggerate the visible shape
changes like character animation, and work at a chosen 24 or 12 fps. The chosen
rate is **24 fps**. The user explicitly reiterated: this must work in REAL TIME.
No tongue or tooth rows. Preserve the selected visual identity and keep source
assets and inspection details private. Hardware/ROS work remains secondary.

## Real-video milestone and anterior refinement

The user requested internet footage through actual OpenSeeFace. A reproducible
GitHub workflow now uses upstream revision
`50c09741897010faad721a218b2bbe14ecad6251`, model 3, chronological 24 fps input,
and retains wire-format measurements. No audio or phoneme schedule drives it.
The first public-domain sample was severely backlit and yielded zero faces; it
was rejected. The replacement is a public-domain White House weekly address
dated 2016-01-23. The 28-second input has 429 valid frames out of 672, including
title/initial material. The evaluated 16–22 second section has **144/144 valid
measurements**. Earlier 4–14 second footage supplies 93 valid normalization
samples; this estimate is marked uncalibrated and frozen before evaluation.
It is not guided wearer calibration.

`tools/replay_video.py` sends later real packets through the existing live
Application, including packet validity, contact, staleness and causal Animator.
Both large and tight shapes and all three mouth families occur. The private
comparison has source footage, character and enlarged mouths, with original
audio and timing. Native offline rendering reviews the same geometry/weights;
it is not evidence of browser, CM4 or physical-display latency.

The user preferred less spread at image-left/anterior lip edge. A local guide
now scales primary articulation displacement to .8 at the front, smoothly
returning to full motion farther back. Rest, expression and timing are intact.
Native/JavaScript vertex parity on review poses is within 1.8e-7 character units.
New verification totals: 37 Python tests and 14 Node tests passed. Added checks
cover tracker packet serialization, future-independent replay, stale tracking,
approximate calibration labeling and local geometry restraint.

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
- Initial sentence previews use synthetic replay. The latest video comparison
  instead uses actual OpenSeeFace measurements from public footage.
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

- Python unittest: 37 passed.
- Node geometry/character/morph tests: 14 passed.
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
