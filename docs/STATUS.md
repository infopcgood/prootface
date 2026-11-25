# Status — 2026-11-25

## Current direction and user feedback

Build the character model downstream of OpenSeeFace. Target: CM4 + Hailo-8,
Sigma WS35 head with denser LEDs, one flat display per muzzle side. Prioritize
natural animation; defer hardware and ROS plumbing. No tongue or tooth rows.
One V-shaped point must join the posterior/eye-side lip contour of each side.

The user rejected the first sample as terrifying. Its thick metallic/ribbed
lip strips are not accepted. The current revision removes that appearance,
uses thin clean contours, and rounds the opening instead of a rigid wedge.
**This replacement has not been approved and naturalness is not established.**

Triwave's protogen is now the mouth-SHAPE reference. The user explicitly
clarified that its limited animation for light VRChat use is not the desired
animation limit. Preserve natural contact, restrained corners, overlapping
articulation and backward jaw recession from the film-animation research.

## Implemented

- Standard-library Python application and dependency-free WebGL motion study.
  Run `python -m prootface`, open http://127.0.0.1:8080.
- OpenSeeFace 1785-byte record decoder, multiple-face selection, validation,
  confidence checks, anatomical features, inner-lip aperture and receive time.
- Robust staged wearer calibration, signed normalization and local JSON save.
- Separate wearer profile, character style, retargeting, temporal filtering and
  geometry. Rounding is explicitly a narrowing proxy; seal is inferred.
- Deterministic shared character pose, independent anatomical corners, bounded
  receding opening, persistent smile, geometric contact and attached rear V.
- Speed-adaptive smoothing, immediate measured contact, tracking-loss relaxation
  and a synthetic phrase with overlapping controls. This is not audio lip sync.
- Dual displays, manual controls, output-only views and schematic WS35 mask and
  LED-density study. Density options do not specify the future physical panel.
- Original software-render tool (`tools/render_study.py`) for actual geometry
  review; optional NumPy/Pillow and Node are needed only for this tool.

## Research and provenance

- OpenSeeFace source inspected at sender blob
  `205b2fbc8ba2615c70a7029a9248082ca65627d9`. Features are 14 signed adaptive
  channels, not an ARKit blendshape set. No independently measured seal/pucker.
- Disney animation interviews, Disney facial-rig papers, JALI, visual speech
  research and the One Euro filter informed the rules. See RESEARCH.md; do not
  misrepresent a general Disney paper as the actual Zootopia rig.
- Sigma creator repository `coelacant1/Protogen-3D-Prints`, commit
  `bc19f4185c104a6d147133a1f943bb8daf7fd5e7`: WS35, HUB75 and bottom render
  images inspected. WS35 is selected. Actual assembly angles and LED map are
  unmeasured. Print-oriented HUB75 reference STL does not establish WS35 pose.
- Triwave's original creator page/public preview URLs located and opened.
  Neither its Blender/FBX mesh nor clear local mouth close-ups were obtained.
  Current contour coordinates are original placeholders, not extracted from or
  validated against that model. Do not claim a faithful visual match.
- Existing `infopcgood/proto-ros2` pipeline read at tree
  `6110aa90568b796e18188dd3104e273d1e30c9f0`; see PIPELINE.md. No changes made
  there. Future adapter should consume existing `/osf_data` and preserve screen
  dispatcher ownership. Existing display dimensions are not this panel's spec.

## Verification

- `python -m unittest discover -s tests -q`: **15 passed**.
- `node --test tests/test_geometry.mjs`: **6 passed**.
- CLI/HTTP smoke passed: startup, static assets, both output routes, manual
  control and current model defaults. JavaScript syntax checks passed.
- Checks cover packet layout/rejection, calibration, contact priority,
  persistent expression, time behavior, shared-side consistency, finite mixed
  poses, front/rear contact, V attachment and LED-map orientation.
- Software renders inspected. A working browser executable is unavailable in
  the current environment; browser execution and physical display appearance
  are **unverified**. No CM4 latency or frame-rate measurements yet.

## Repository and continuity

Public repository: https://github.com/infopcgood/prootface, branch `master`.
The user updated GitHub permissions; connector writes now work. The first
implementation was published at
`50950781bcd3070bf7f70e23107343d3fbf20b67`. The following revision replaces the
rejected appearance and records the Triwave clarification. GitHub connector
Git Data APIs are the working publication route; direct Git HTTPS failed in
this environment. Do not force-push over concurrent changes.

Read AGENTS.md and this file before continuing. Original research, design and
pipeline notes are committed; wearer calibration and review renders under
`local/` are ignored. Third-party art, CAD and avatar assets are not bundled.

## Next steps, in order

1. Obtain a clear profile close-up or inspect an authorized Triwave model asset.
   Establish the rest contour, corner return and attached V proportions with
   visual feedback. Do not assume this provisional contour is accepted.
2. Preserve that approved rest identity through closed smile, slight opening,
   conversational opening, rounding, broad opening and one-sided expression.
   Art-direct corrective curves; do not imitate the reference's limited motion.
3. Review a short motion sequence against real wearer speech. Tune opening
   gain, closure timing, rounding shape and corner response separately. Current
   width-only rounding and simple eye markers are incomplete appearance work.
4. Run the WebGL UI in a real browser; check both mirrored sides, shading,
   temporal smoothness and controls. Then review on the actual visor.
5. Only after shape/motion agreement, add the proto-ros2 adapter, measured WS35
   panel mapping and real hardware performance work. Keep tracker, calibration,
   animation and pixel-output boundaries separate.
