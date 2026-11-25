# Mouth and display reference research

Research snapshot: 2026-11-25. Separate observations from design choices. The
linked artist images/CAD were inspected as references; none is redistributed.

## Original visual references

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
- [OpenSeeFace sender](https://github.com/emilianavt/OpenSeeFace/blob/205b2fbc8ba2615c70a7029a9248082ca65627d9/facetracker.py)
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

