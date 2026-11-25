# Mouth and display reference research

Research snapshot: 2026-11-25. Separate observations from design choices. The
Reference access and inspection limits are recorded below; none of the linked
artist images, CAD or avatar assets is redistributed.

## Original visual references

### Latest user-specified shape reference: Triwave

[Triwave's creator page](https://triwave.carrd.co/) provides original preview
images and a public Google Drive link for the protogen avatar. The user specified
that the mouth shape is useful but the light VRChat use/limited animation must
NOT constrain this project's animation quality. Treat it as a static design
reference; retain natural speech, closure and expression work from film research.

A user-provided reference has now been processed locally. Its source files,
identity, structural details, projected masks, derived contours and inspection
notes remain private. The public implementation contains generic rest-silhouette
processing and independent deformation, not a copy of a reference asset.

The user initially asked to ignore avatar phoneme animation keys, then explicitly
revised that direction after the first animation review: authored phoneme poses
are a better starting point. The current importer accepts a privately configured
pose basis. Source-specific key names and target data remain private. Runtime
uses continuous semantic blending rather than abrupt phoneme-name switches.

The first implementation's thick, metallic/ribbed lip strips were explicitly
rejected by the user as terrifying. They are not an acceptable direction. The
subsequent original contour study was also provisional. The generic importer
preserves a selected rest shape; independently developed motion still
needs the user's perceptual review. Do not infer acceptance from code tests.

| Reference | Observation / implication |
| --- | --- |
| [Sigma WS35 placement](https://github.com/coelacant1/Protogen-3D-Prints/blob/bc19f4185c104a6d147133a1f943bb8daf7fd5e7/SigmaProtogen/Pictures/WS35.png) | Shaped side boards, canted around the snout, with a central nose gap. Use a masked side composition, not an unbroken frontal picture. |
| [Sigma bottom view](https://github.com/coelacant1/Protogen-3D-Prints/blob/bc19f4185c104a6d147133a1f943bb8daf7fd5e7/SigmaProtogen/Pictures/SigmaBottom.png) | Curved outer visor and open interior are separate from the emitting boards. A screen image cannot move the physical outline. |
| [Sigma HUB75 comparison](https://github.com/coelacant1/Protogen-3D-Prints/blob/bc19f4185c104a6d147133a1f943bb8daf7fd5e7/SigmaProtogen/Pictures/HUB75.png) | Rectangular board variant differs from the user's chosen WS35 layout. Do not silently substitute it. |
| [Creator Sigma page](https://coelacant1.gumroad.com/l/SigmaProtogenV1) | Creator confirms both WS35 and HUB75 variants. Exact physical angles cannot be read reliably from this perspective render. |
| [dont_jinxit's Jinxed Protogen](https://jinxxy.com/dont_jinxit/JinxedProto) and its Expressions product image | Repeated head proportions with distinct eyes/corners and selected mouth changes. Avatar imagery can use depth/physical openings that a fixed visor cannot reproduce. |
| [John Tobin expressions, Yushin Aurum / parallelfurr](https://www.furaffinity.net/view/40902922/) | Located an attributed side-expression sheet. Full-resolution access was blocked; do not claim a detailed visual analysis of this image. |
| [ZOR visor explanation](https://www.furaffinity.net/view/51509455/) | Official fictional visor can physically open via nanites. That lore capability is not a physical capability of two fixed panels. Full image access was blocked here. |

Artist sheets are illustrative evidence, not a statistical survey of all protogen
art. The user's explicit preference overrides the common luminous zigzag style:
target dimensional lip behaviour with a single attached rear V, no tooth rows.

## GitHub implementation references

- [ProtoTracer](https://github.com/coelacant1/ProtoTracer), inspected tree
  `15e8c3d22853bbfc9aa053c1285c9b6b7163a65c`: supports deformable face models
  and separate expression/viseme morphs. `NukudeFlat.h` includes silence,
  consonant/vowel and expression morphs. This is a technique reference; its
  AGPL code and face vertices were not copied.
- [LumiFur Controller](https://github.com/stef1949/LumiFur_Controller), README
  blob `29be1f847820ac889546bc7d1312abec8c24b2e6`: audio-reactive interpolation
  between closed/open XBM mouths is a useful baseline, but cannot independently
  recover the wearer's rounding, smile or contact.
- [OpenSeeFace sender](https://github.com/emilianavt/OpenSeeFace/blob/master/facetracker.py)
  (inspected file-blob SHA `205b2fbc8ba2615c70a7029a9248082ca65627d9`)
  and `tracker.py`: actual packet and feature semantics. Header is 73 bytes;
  68 confidences, 68 2D points, 70 3D points and 14 features give 1785 bytes per
  face. No packet-wide alignment padding. Upstream packs each scalar separately.

Sigma repository: `coelacant1/Protogen-3D-Prints` at
`bc19f4185c104a6d147133a1f943bb8daf7fd5e7`. Earlier citations to
`Coelacant/SigmaProtogen` are stale. The old coelacant1/SigmaProtogen repository
redirects to Protogen-3D-Prints.

The small HUB75PanelReference STL was inspected only to check whether it could
supply an assembly pose. It is print-oriented and flat, with bounds about
191.8 x 95.8 x 12.3 mm, so it does NOT establish the assembled display angle.
No Sigma mesh or image is included in Prootface.

## Film and animation primary sources

- [Zootopia animation panel](https://allears.net/2016/03/01/zootopia-press-day-part-4/):
  Nick's long muzzle needed a receding jaw opening; Robin Hood was a reference.
- [Interview with Zootopia's animation team](https://insidethemagic.net/2016/01/interview-zootopia-animation-team-members-explain-how-they-brought-the-movies-characters-to-life/):
  Judy's narrow corners and controlled tooth exposure; actor footage as reference.
- [Disney, A Hybrid Approach to Facial Rigging](https://media.disneyanimation.com/uploads/production/publication_asset/52/asset/hybridFacialTalk.pdf):
  deformers, blendshapes and pose-dependent interpolation, demonstrated on Bolt
  and Prep and Landing. This does not disclose Nick's exact rig.
- [Disney, A Deformer-Based Approach to Facial Rigging](https://media.disneyanimation.com/uploads/production/publication_asset/97/asset/facial.pdf):
  art-directed contours and sculpted refinements, used on Wreck-It Ralph/Frozen.
- [JALI paper](https://dgp.toronto.edu/~elf/JALISIG16.pdf): distinct jaw/lip
  contributions, coarticulation and articulation constraints.
- [Dynamic Units of Visual Speech](https://la.disneyresearch.com/publication/dynamic-units-of-visual-speech/):
  visual speech consists of temporal gestures rather than isolated still shapes.
- [Jay Jackson, dialogue animation](https://www.animationmentor.com/blog/some-tips-for-animating-dialogue/):
  readable closures, accents, anticipation, expression and relaxed phrase endings.

## Engineering deductions

Use one semantic state with separate anatomical corner controls and calibrated
side compositions. Keep the physical board mask outside the character model.
Use real lip contact as a constraint. A higher LED count improves sampling,
not motion semantics or observer-dependent parallax. Initial procedural
surfaces are a replaceable art-direction tool; convincing final naturalness
requires actual captured performances and human review.

## Speaking-review clip

The example sentence is “Maybe we should move a little closer.” CMU Flite's
SLT voice produces audio and timestamped segments through its public C API
([official headers](https://github.com/festvox/flite/blob/master/include/flite.h)).
Timestamps schedule overlapping opening, width and contact controls. The same
controls can come from the live OpenSeeFace path; the character model maps them
to a configured authored basis. Closure overrides opening without erasing
persistent corner expression.

The first raster-ribbon animation failed visual review. Its lower contour
inflated and retained a crease, uniform width scaling moved the design sideways,
and insufficient framing clipped some openings. Applying a slower jaw filter
to seal release also suppressed short vowel openings. Those are implementation
failures, not evidence that the reference design is unsuitable.

The current path blends authored mesh samples, preserves UVs and occlusion,
uses a fixed view bounded over the pose basis, and gives contact a faster detach
response. Preview rendering consumes the same private mesh and Python-generated
weights as the WebGL path. It is not a browser or CM4 capture. Automatic affine
contour corrections were rejected after they produced visible tearing; do not
revive them as an assumed improvement over authored geometry.


## Latest style and realtime requirement

The user requested exaggerated animation and a choice of 24 or 12 fps; the
selected working rate is 24 fps. The user also reiterated that this must work
in real time. Distinct key shapes, short causal exposures and fast transitions
now take precedence over broad continuous interpolation. Preplanned phoneme
timing is only a synthetic test-input source. The live controller uses no
future measurements or phoneme schedule, and unsupported consonant channels
are excluded from the default tracking-mode preview.


## Follow-up performance review

The user found the preceding 24 fps result insufficiently dramatic. Reviewing
our response curve showed that boosting nearly every opening reduced dynamic
contrast even though peak weights were already large. The revised experiment
uses small/large range expansion, a firmer dominant family, short causal
opening hits and faster compression. A matched replay isolates the effect of
those controller changes: input sequence, camera framing and audio timing stay
fixed. This records an implementation finding, not a claim about the private
reference asset or a proof of perceptual naturalness.
