# Working instructions

- This repository owns deterministic calibration, retargeting, temporal animation
  and rendering downstream of OpenSeeFace. Keep measurement, wearer normalization,
  character style, presentation cadence and physical LED mapping separate.
- Keep current style defaults unless directed otherwise. Preserve rest identity,
  readable closures, expression during speech and fast contact interruption.
- The controller uses current/past measurements only at 24 Hz. Presentation can
  hold poses at 24/12/6 fps. Do not add future phonemes or browser interpolation.
- Both anatomical side views share one timed pose. Keep side selection distinct
  from display mirroring, and mirror once. Output atlases use top-left BGR bytes.
- Source assets, textures, compiled geometry, source-specific settings, reference
  identifiers, private inspection notes and user-specific observations stay under
  ignored local/. Publish reusable code, original synthetic tests and generic
  setup instructions only. Do not copy private continuity notes into public docs.
- Preserve original landmark indices when refining imported geometry. Deformation
  boundaries must not move stationary features through coarse masking triangles.
  Validate sparse blending and side/depth behavior in native and offscreen paths.
- ROS integration lives in infopcgood/proto-ros2. Consume its OSFData topic,
  screen ownership and interface messages. The standalone server must not bind
  UDP when the ROS receiver owns the port. Calibration HTTP hosts shared state.
- EGL contexts belong to the render worker thread. Keep one latest pending pose
  and one latest completed frame; no unbounded queues of old expressions.
- Read README.md, docs/PIPELINE.md and docs/STATUS.md for public interfaces and
  validation status. Private continuity belongs in local/private-notes/.
- Use meaningful input, contact, concurrency, rendering and ROS integration tests.
  Distinguish software Mesa/CI results from actual CM4, Hailo and LED measurements.
- Never fabricate a panel map. Validate physical strip order/count against the
  installed driver and use actual panel coordinates. Legacy backends remain usable.
- Publish with an expected branch SHA, inspect concurrent changes and never
  force-push over another change. No private assets enter public CI artifacts.

- User boundary: leave existing ROS packages unchanged except for adding
  parameters in param_server_pkg or new definitions in interface_pkg. Keep all
  Prootface input/output adapters, tests and dependencies in prootface_pkg.

- Expression selection comes from external commands/buttons. Keep the speech
  controller independent, use expression-specific speech banks, preserve full
  contact and blinks, and keep expression selections during tracking loss.
- Anchor expression banks in authored mouth targets. Do not replace their
  identity with curve-only fields to hide blending artifacts. Review mouths
  with neutral eyes and compare rest endpoints to the authored references.
  Keep emotion corrections independent of anterior articulation restraint.
