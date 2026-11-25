# Character model and animation rules

## Current direction

The user selected Triwave as the visual reference. The latest instruction is
to use authored phoneme poses as a starting point, superseding the earlier
request to ignore them. Preserve the selected rest identity, curate the pose
basis, and improve the response and transitions. No tongue, tooth rows or
metallic lip tubes. Private asset details and inspection notes are excluded.

## Boundaries

1. OpenSeeFace measures facial features and landmarks.
2. Wearer calibration learns signed usable movement and contact aperture.
3. Retargeting estimates opening, rounding proxy, spreading, corners and seal.
4. Temporal rules stabilize motion and prioritize contact.
5. Semantic controls continuously blend a configured authored pose basis.
6. Mesh projection, emission texture and occlusion create each flat side view.
7. Physical panel mapping remains a separate, later calibration.

Style changes must not require repeating wearer calibration. Both anatomical
sides share one timed pose; projection mirrors only once.

## Private authored basis

The generic morph importer reads source-specific names, target mapping and
projection from ignored private settings. It disables nonselected animation
and exports indexed rest geometry, UVs, sparse target deltas and a texture.
No source asset, private settings or derived data is committed. Schema 2 is
the current authored-mesh path; schema 1 is the legacy silhouette study.

The configured mouth samples represent open, rounded, spread and closed shapes.
Expressions and blinks are smaller independent channels. These names describe
a semantic interface, not identifiers from any particular source asset.

## Blendspace and contact

After filtering, visible opening is:

`v = opening^gamma * (1 - seal)`

Opening strength maps it to a bounded authored response:

`s = clamp(v * opening_strength / .36)`

`a = s * (2 - s)`

This increases readability in the middle of the calibrated feature range and
preserves exact closed/full endpoints. The input feature is not a physical
percentage of a mesh's jaw travel. Default gamma is .85.

Normalize rounding and spread by `max(1, rounding + spread)` to obtain `r` and
`w`. The primary mouth weights are:

- Open: `a * (1-r-w)`.
- Rounded: `a * r`.
- Spread: `a * w`.

They are nonnegative and sum to at most one. Thus articulation remains inside
the configured mouth basis. At seal=1 all opening weights are zero. A bounded
closed-pose contribution can follow latent opening during contact; it must be
mapped to an actually closed sample. Mild pucker, smile/frown and blink channels
remain separate, so expression persists across articulation.

The authored geometry supplies lower-contour curvature and recession. Do not
also stretch a closed 2D ribbon or uniformly squash the whole mouth. Opening
strength is adjustable; an independent recession slider is hidden for this
basis because that motion is authored into its samples.

An automatic spatial-decomposition experiment produced edge tearing and was
discarded. Any future intermediate-pose correction needs actual visual review;
non-finite checks and triangle counts cannot establish appeal or naturalness.

## Timing

Opening/width use a speed-adaptive low-pass. Contact can attach promptly and
uses an 8 ms release time constant, preventing the previous sticky closure.
Do not apply both a slow contact filter and a squared seal gate: that swallowed
short openings in the review performance. Lost tracking eases toward rest.
Freshness uses monotonic receive time, never sender wall time.

The offline example uses synthesized segment times to schedule semantic controls.
Rounding prepares ahead of its sound, adjacent gestures overlap, and contact
overrides the vowel trajectory. It also includes a brief preparatory blink.
This is a synthetic demonstration; live controls still come from OpenSeeFace.

## Rendering and framing

Sparse authored deltas deform the mesh. Its original UVs and emission texture
preserve appearance, while opaque surfaces resolve visibility. Separate
anatomical side projections preserve asymmetric expressions. A fixed view is
bounded across the configured mouth basis with margin; it never auto-zooms
between syllables. Do not hide large openings by clipping the display frame.

The review renderer consumes the same compiled mesh and Python blend weights
as WebGL. It is a native offline render, not a browser or hardware benchmark.
The WS35 mask remains a schematic, opt-in study until physical mapping is
measured; it must not silently clip an animation review.

## Film-animation transfer and limits

The goal remains controlled muzzle identity, a readable lower contour, receding
opening, persistent expression and clear closures. These adapt principles from
animation research; they do not reproduce Disney's undisclosed character rig.

OpenSeeFace supplies signed adaptive features and landmarks, not a full set of
muscle controls. Rounding is a narrowing proxy and seal is inferred from visible
aperture. Do not imply independent pucker or lip-pressure measurement.

Higher LED density improves sampling, not emitting area, physical silhouette
or observer-dependent parallax. Physical Sigma WS35 panel angles, pitch and
LED coordinates remain unmeasured. Perceptual acceptance requires actual motion
review and wearer recordings, then browser and real-visor evaluation.
