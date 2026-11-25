# Status — 2026-11-25

## Latest direction

Triwave is the static shape reference. Preserve the chosen rest identity and
improve natural articulation independently. The user explicitly instructed us
to IGNORE avatar phoneme animation keys and requested an audible animated
sentence preview after the motion work. A temporary pause to locate a reference
was superseded by that instruction.

Target: CM4 + Hailo-8, denser Sigma WS35 side displays, OpenSeeFace measurement.
Prioritize motion; defer hardware/transport integration. No tongue or tooth rows.

## Privacy boundary

Reference source files, identifiers, structural details, inspection observations,
private settings, masks, derived contours and rendered user previews are kept
out of this public repository. Reusable tooling accepts private configuration;
it must not embed source-specific object/material names or camera calibration.
Keep configuration and generated character data under ignored local/.

## Implemented

- Generic configured rest-shape importer, with non-rest animation disabled.
  No avatar animation poses/deltas are exported.
- Rest-mask compiler for one visible eye, nose and mouth per side. It derives
  normalized front/rear and lower-ribbon coordinates for procedural deformation.
- web/character.mjs: independently developed opening, backward recession,
  rounding, corner lift and contact priority. Concave silhouettes triangulate
  after deformation. Full contact restores the selected rest design.
- WebGL unlit rendering through /api/character and --character. If no private
  character file exists, the original contour fallback is explicitly labeled.
- performance.py: independent overlapping semantic gestures for an offline
  example. Speech TIMESTAMPS schedule controls; avatar phoneme SHAPES are unused.
- Optional speech synthesis and 60 fps video-review tools. They use the actual
  Python Animator and JS deformation, with software rasterization. A speaking
  example was generated and saved privately for user review.

## Earlier core retained

OpenSeeFace 1785-byte decoding, face selection, robust signed calibration,
contact-aware retargeting, adaptive temporal filtering, monotonic staleness and
tracking-loss relaxation. Both displays share one timed semantic pose and retain
independent anatomical corner expression.

Existing infopcgood/proto-ros2 was inspected without modifications. See
PIPELINE.md for its existing topics/messages and intended insertion point.

## Verification

- Python unittest: 19 passed.
- Node geometry/character tests: 10 passed.
- Syntax/compile checks and CLI/HTTP smoke passed.
- The review output contains H.264 video and AAC audio and was visually inspected.
- Browser execution and physical-panel appearance remain unverified. A working
  browser executable is unavailable here. CM4 performance is unmeasured.
- These checks do not establish perceptual naturalness; user review is required.

## Repository

https://github.com/infopcgood/prootface, branch master. Previous checkpoint:
e405a6d5bd3273153f4877f0499ccf407db04fb3. This revision publishes reusable tools,
animation code, tests and generic documentation only. Reference-derived data
and private inspection notes must not be copied into a public update.

## Next

1. Review the actual speaking animation while preserving the chosen rest shape.
2. Refine continuous opening/rounding/contact and corner timing from feedback.
   Never reintroduce avatar phoneme keys as a shortcut.
3. Capture real wearer speech through OpenSeeFace and tune calibration separately.
4. Exercise both sides in a real browser, then on the visor.
5. Only then add proto-ros2 adaptation, measured LED mapping and CM4 profiling.
