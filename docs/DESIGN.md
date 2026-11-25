# Character model and animation rules

## Accepted direction

The user's priority is natural animation. Hardware output and transport
integration come later. A CM4 + Hailo-8 is the target host, but OpenSeeFace owns
measurement and this project does not change or compile its neural models.
Use a shaded, dimensional, restrained muzzle-like mouth. No tongue, gums or
tooth rows. Exactly one V point per side, continuous with the posterior lip.
Its attachment is geometric, not a detached tooth positioned over an image.

## Layer boundaries

1. Measurement: OpenSeeFace features and optional inner-lip landmarks.
2. Wearer calibration: neutral offsets and usable positive/negative movement.
3. Retargeting: opening, narrowing proxy, spreading, corners and contact.
4. Time: motion-dependent response, contact priority, tracking-loss recovery.
5. Character pose: bounded opening curve, jaw angle, recession, width and
   independent anatomical corners.
6. Appearance: continuous upper/lower profile surfaces, recessed cavity,
   posterior V and a restrained eye marker for orientation.
7. Display: side projection, mirroring, panel mask and eventual pixel sampling.

Wearer calibration must not store display dimensions or decide the character's
appearance. A style change must not require repeating wearer calibration.

## Transfer of film-animation findings

- Nick's animators described a receding jaw opening to avoid a crocodile-like
  hinge. Here the lower contour follows a rotational arc around a posterior
  hinge, with a separate bounded recession term. This is our adaptation, not
  Disney's undisclosed rig implementation.
- Judy's narrowed mouth corners preserved appeal and tooth visibility. Here
  the width envelope and corner motion are bounded separately from opening.
- Speech continues inside a persistent expression. Rounding modifies central
  articulation while corner lift remains independent.
- Real speech coarticulates. Live camera measurements already contain much of
  that preparation and overlap. Avoid snapping between phoneme labels.
- A real closure is more important than a noisy opening estimate. Visible
  contact is enforced, including around the attached V, after smoothing.

## Current geometry

This first model is 2.5D: original deformable profile strips with surface depth
and lighting, not an anatomically complete shared 3D skull. Both sides share
articulation and time; each has its own anatomical corner.

The upper contour remains comparatively stable. The lower lip rotates down
and back, the rear corner stays restrained, and a corrective lower contour
maintains contact around the V when closing. The cavity recedes behind both
lips. At complete closure both contours coincide. No text or third-party art
is baked into the face mesh.

The V is evaluated directly within the upper contour using a compact triangular
basis. Samples include its exact two roots and tip, so it cannot detach when
the mouth changes shape. Its position and depth are editable character rules.

## Physical limits and WS35 layout

Sigma's WS35 photograph/CAD render shows paired shaped planar boards around a
central nose gap, behind a curved outer visor. The reference is NOT two frontal
LCDs and NOT the rectangular HUB75 variant. Higher density improves shading
and curve sampling; it does not create additional emitting area, change panel
normals, remove the nose gap or move the physical visor's silhouette.

The preview's polygon and optional panel tilt are clearly marked schematics.
They are not measured fits to Sigma. Physical panel pose and virtual rendering
camera are different calibrations. No exact mounting angle has been extracted.

## Honest input capabilities

OpenSeeFace's 14 features are signed adaptive measurements. They are not
ARKit/Babble blendshapes. Current rounding is derived from negative mouth width;
it is not a dedicated pucker measurement, a phoneme identity, or an emotion.
Contact uses the ratio between three inner-lip pairs and mouth width when those
landmarks are usable. That infers contact, not pressure or true independent
jaw-plus-lip muscle activation. Do not claim otherwise in the UI or docs.

## Naturalness acceptance criteria

- Rest is stable; closing returns to the same character-specific contour.
- Contact remains closed during a smile or a deliberately conflicting jaw input.
- The lower contour recedes smoothly rather than dropping like a sliding flap.
- The V remains part of the rear contour; one per side and no tooth duplication.
- Spreading, rounding and speech preserve identifiable expression.
- No frame-rate-dependent overshoot or random idle mouth motion.
- Lost input eases to rest; stale sender wall clocks cannot drive time.
- Final acceptance needs real wearer recordings and visual review on the actual
  visor. Synthetic performance tests cannot establish perceptual naturalness.

