# Prootface working instructions

## Goal and current direction

- Wearable protogen head: CM4 + Hailo-8, one flat display per muzzle side.
- Selected physical reference: Sigma WS35 with denser LEDs. Do not substitute
  rectangular HUB75 panels or invent density, coordinates or mounting angles.
- OpenSeeFace owns measurement. This repository owns wearer calibration,
  retargeting, temporal animation and display geometry.
- The user selected Triwave as the visual mouth-shape reference, while retaining
  natural Nick/Zootopia-informed articulation as the motion goal.
- Latest explicit user correction: use the avatar's authored phoneme poses as
  a starting point. This supersedes the earlier instruction to ignore them.
  Preserve the chosen rest identity, curate an authored basis, and improve
  blending, contact timing and pose response. Use purposeful transitions and
  holds; do not wash out key shapes or treat source keys as a finished performance.
- No tongue, tooth rows or detached fangs. Do not return to the rejected thick
  metallic/ribbed lip strips. The supplied rest identity takes precedence over
  earlier provisional geometry and approximate notch-placement descriptions.
- Prioritize natural motion. Leave transport and hardware integration for later.
- Latest style instruction: exaggerate the visible mouth-shape changes like
  character animation. The chosen working rate is 24 FPS for new authoring,
  runtime presentation and previews. Do not return to 30/60 fps output or
  interpolate additional poses in the browser. Use readable brief exposures,
  strong shape contrast and purposeful fast transitions.
- This must work in REAL TIME. The live controller is causal: current/past
  OpenSeeFace measurements only, no future phonemes, audio alignment or offline
  rendering in the runtime. A scripted reference is not proof of live tracking.
  Label synthetic replay as such. Specialized consonant hints are not currently
  measured by OpenSeeFace; do not show them as tracked capabilities.

## Asset privacy

- User reference files and inspection notes are private. Never commit source
  archives, models, textures, masks, derived contours, file identifiers, private
  object/material names, projection settings or asset inspection observations.
- Put private import settings and generated character data under ignored local/.
  Reusable code must accept settings instead of embedding private-source details.
- Public research notes may cite public sources and record general techniques.
  Do not copy private inspection notes into them.
- The current generic morph importer exports only the privately configured pose
  basis and texture. Nonselected animation stays disabled. Source-specific key
  names live in private settings, never reusable code. The old rest-mask tool
  is retained as a legacy study, not the current animation method.

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
- The first ribbon animation was rejected: it inflated a closed symbol, slid
  it sideways and clipped lower openings. Do not revive it as the target rig.
  Review enlarged mouth frames and the actual motion before sharing another
  preview. Discard deformations that cause tearing or occlusion artifacts.
- Keep private preview outputs outside version control. Do not claim CM4 or
  browser performance was measured until it actually is.
- Update docs/STATUS.md at milestones/interruption. Add useful tests for protocol,
  signed calibration, contact, corner persistence, concave geometry and time.
- Publish only reusable code and generic documentation. Use an expected branch
  SHA, preserve concurrent work and never force-push over another change.
