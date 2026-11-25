# Prootface working instructions

## Goal and current direction

- Wearable protogen head: CM4 + Hailo-8, one flat display per muzzle side.
- Selected physical reference: Sigma WS35 with denser LEDs. Do not substitute
  rectangular HUB75 panels or invent density, coordinates or mounting angles.
- OpenSeeFace owns measurement. This repository owns wearer calibration,
  retargeting, temporal animation and display geometry.
- The user selected Triwave as the visual mouth-shape reference, while retaining
  natural Nick/Zootopia-informed articulation as the motion goal.
- Latest explicit instruction: IGNORE avatar phoneme animation keys. Preserve
  the chosen rest design and develop continuous motion independently.
- No tongue, tooth rows or detached fangs. Do not return to the rejected thick
  metallic/ribbed lip strips. The supplied rest identity takes precedence over
  earlier provisional geometry and approximate notch-placement descriptions.
- Prioritize natural motion. Leave transport and hardware integration for later.

## Asset privacy

- User reference files and inspection notes are private. Never commit source
  archives, models, textures, masks, derived contours, file identifiers, private
  object/material names, projection settings or asset inspection observations.
- Put private import settings and generated character data under ignored local/.
  Reusable code must accept settings instead of embedding private-source details.
- Public research notes may cite public sources and record general techniques.
  Do not copy private inspection notes into them.
- The generic importer zeros every non-rest animation key and exports no avatar
  animation deltas. Offline speech timestamps may schedule our independent
  semantic gestures, but must never select avatar phoneme shapes.

## Animation boundaries

- Keep tracker input, wearer calibration, character style, time and display
  projection separate. A style change must not require wearer recalibration.
- Core behavior stays deterministic and testable without camera, Hailo or ML.
- OpenSeeFace has signed adaptive features and landmarks, not a complete ARKit
  blendshape set. Rounding is a narrowing proxy; seal is inferred from aperture.
- Preserve silent expressions. Do not gate facial motion with microphone activity.
- Contact takes priority over noisy opening and must preserve the closed design.
- Both sides share one timed semantic pose and independent anatomical corners.
  Anatomical left/right is distinct from display mirroring; mirror only once.
- Use monotonic receive time for staleness, not sender wall time. Ease to rest
  on lost tracking; avoid random idle mouth motion and frame-dependent overshoot.
- Two flat screens cannot provide continuous curved emission, physical jaw
  silhouette changes or correct parallax for every observer.

## Existing integration and continuity

- Read docs/DESIGN.md, docs/RESEARCH.md and docs/STATUS.md before changing rules.
- Existing integration is infopcgood/proto-ros2. See docs/PIPELINE.md; do not
  modify that repository without a task requiring it. Preserve screen ownership.
- The user requested a real animated, audible sentence preview. A static image
  or passing test count is not a replacement. Naturalness requires visual review.
- Keep private preview outputs outside version control. Do not claim CM4 or
  browser performance was measured until it actually is.
- Update docs/STATUS.md at milestones/interruption. Add useful tests for protocol,
  signed calibration, contact, corner persistence, concave geometry and time.
- Publish only reusable code and generic documentation. Use an expected branch
  SHA, preserve concurrent work and never force-push over another change.
