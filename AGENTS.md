# Prootface working instructions

## Product goal and accepted constraints
- Target: wearable protogen head, CM4 + Hailo-8; one flat display on each side of the muzzle.
- OpenSeeFace owns facial measurement. This repository owns calibration, retargeting, temporal animation and display geometry. Do not replace the tracker or require Hailo to render.
- The goal is a dimensional, restrained, Nick-in-Zootopia-like mouth: plausible lip contact, lower-jaw opening with backward recession, controlled rear corners and a shaded cavity.
- Latest user correction: NO tongue and NO tooth rows. Use ONE V-shaped sharp point integrated with the rear/eye-side lip line of EACH side view. It is part of the lip contour, not a floating tooth.
- Do not revert to a luminous zigzag/emoji mouth as the default.
- Latest hardware choice: Sigma WS35 version with a denser LED display. Use WS35 layout as the physical reference, NOT the rectangular HUB75 variant. Pixel pitch/density and actual LED coordinates remain configurable and unmeasured. Do not assume the original WS2812 protocol or original LED count.
- Two flat displays cannot reproduce actual silhouette deformation, a continuous curved display, or viewpoint-correct parallax for every observer. Make two calibrated views of one shared anatomical state; do not claim those physical limitations are solved.

## Research and provenance
- Read docs/RESEARCH.md and docs/DESIGN.md before changing mouth rules.
- Study original artist references and implementation techniques; do not copy character meshes, artwork, or firmware assets into this repository.
- OpenSeeFace source is authoritative for input semantics. It exports 14 signed features plus 2D/3D landmarks, NOT ARKit/Babble's full blendshape set. There is no directly measured tongue, pucker or lip-seal channel. Mark inferred controls explicitly.
- Preserve links, upstream commit hashes, observed evidence, deductions and unverified assumptions in research notes.

## Implementation boundaries
- Keep the character model deterministic and independently testable without a camera, browser, Hailo or external ML packages.
- Separate tracker input, wearer calibration, character style, temporal rules and rendering.
- Use monotonic receive timestamps for staleness. Sender wall time must not control animation time.
- Both displays consume the same frame/state. Anatomical left/right is distinct from screen mirroring.
- A closed mouth must keep lip contact regardless of smile/rounding. Preserve silent expressions; do not gate camera-driven mouths on microphone activity.
- Do not interpret mouth narrowing as a reliably measured phoneme or emotion.
- Keep future adaptation of the native display backend possible. First prototype may use WebGL with a small local server.
- Document CM4 frame-rate/latency as unverified until measured on the real hardware.

## Continuity
- Update docs/STATUS.md whenever a meaningful milestone completes or work is interrupted. It must record implemented behavior, test commands/results, repository/branch state, limitations and ordered next steps.
- Add useful tests for packet decoding, signed calibration, pose combinations, lip contact, V-point attachment, side consistency and stale-input behavior.
- Keep commits reviewable, preserve user changes and never force-push over concurrent work.

## Sigma reference update
- Creator repository: coelacant1/Protogen-3D-Prints, SigmaProtogen/.
- Pictures/WS35.png is the selected layout reference: two shaped planar boards behind a curved visor, with a central non-emissive nose gap. HUB75.png describes another variant and must not set this project's panel shape.
- Keep physical panel placement separate from virtual mouth camera yaw. Do not infer exact mounting angles from pictures or print-oriented STLs.


## Latest integration boundary
- User asked to prioritize natural animation and leave transport/hardware technicalities until later.
- Existing pipeline lives in infopcgood/proto-ros2; consult its current files before integrating. Keep this first character model independently previewable and document its future insertion point. Do not modify proto-ros2 without a task requiring that work.

## Critical visual rejection / latest reference
- User rejected the first rendered sample as terrifying. The thick metallic/ribbed lip strips and severe floating eye shapes are NOT accepted and must not become the target design.
- Stop equating natural Nick-like movement with literal detached sculpted human lips. User now explicitly requests Triwave's protogen model as the mouth-shape reference. Inspect original/public model previews before rebuilding the appearance.
- Preserve the constraints: Sigma WS35 placement with denser LEDs; OpenSeeFace measurement; no tongue or tooth rows; one small attached posterior V point per side.
- Do not declare naturalness achieved based on code tests or synthetic renders. Get a visually acceptable shape direction first.
- Latest clarification: Triwave's mouth SHAPE is the reference. Its limited animation for light VRChat use is not the motion target. Keep the static contour design separate from the richer live articulation rules; do not reduce this project to the reference avatar's limited animation set.
- The Triwave mesh has not been obtained or inspected locally. Public creator pages/previews were located, but precise contour coordinates and rig details are unverified. Do not invent an extracted or matched shape.
