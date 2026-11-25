# Prootface working instructions

## Product goal and accepted constraints
- Target: wearable protogen head, CM4 + Hailo-8; one flat display on each side of the muzzle.
- OpenSeeFace owns facial measurement. This repository owns calibration, retargeting, temporal animation and display geometry. Do not replace the tracker or require Hailo to render.
- The goal is a dimensional, restrained, Nick-in-Zootopia-like mouth: plausible lip contact, lower-jaw opening with backward recession, controlled rear corners and a shaded cavity.
- Latest user correction: NO tongue and NO tooth rows. Use ONE V-shaped sharp point integrated with the rear/eye-side lip line of EACH side view. It is part of the lip contour, not a floating tooth.
- Do not revert to a luminous zigzag/emoji mouth as the default.
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
- Creator repository is coelacant1/Protogen-3D-Prints, SigmaProtogen/. Inspect its Pictures/HUB75.png and SigmaBottom.png. The paired flat panels form canted sides behind a curved visor, with a non-emissive central nose gap. Keep physical panel geometry separate from virtual mouth camera orientation; do not invent measured mounting angles from marketing images or print-oriented STLs.
