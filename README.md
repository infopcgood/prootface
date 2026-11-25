# Prootface

Natural character-mouth animation downstream of OpenSeeFace, for two flat
side displays in a Sigma WS35-style wearable head with denser LEDs.

**Triwave is the selected static mouth-shape reference.** Preserve the chosen
rest identity while developing natural opening, backward recession, rounding,
expression and contact independently. The user explicitly instructed us to
**ignore avatar phoneme animation keys**. Import tools disable non-rest
animation and export no animation poses or deltas. No tongue or tooth rows.
Private reference details, files and derived geometry are not published here.

## Run

Python 3.10+ and a WebGL browser:

```sh
python -m prootface
```

Open http://127.0.0.1:8080. If `local/character.json` exists, both anatomical
sides use the imported rest shape and procedural animation. If absent, the UI
labels the older original contour study as a fallback. It is not the target
character. No ML packages, ROS, camera or Hailo runtime are needed for preview.

Output-only pages: `/?side=left&display=1` and `/?side=right&display=1`.
OpenSeeFace normally sends to 127.0.0.1:11573; select another port if the existing
ROS receiver owns it:

```sh
python -m prootface --udp-port 11574 --face-id 0
```

## Import a rest shape privately

Keep user reference assets and configuration private. The generic importer
requires a private JSON settings file specifying the mesh object, emission
image/material, orthographic camera and anatomical side mapping. It embeds no
asset-specific object names or projection values. Blender is required; NumPy,
SciPy, contourpy and Pillow are optional import-tool dependencies.

```sh
blender --background --factory-startup --disable-autoexec --python tools/import_character.py -- /path/to/model.blend --settings local/character-settings.json --output local/character-source
python tools/compile_character.py local/character-source local/character.json
python -m prootface --character local/character.json
```

The compiler expects visible eye, nose and mouth regions per side. This is a
face-silhouette adapter, not a general avatar converter. Source assets, private
settings, masks and derived outlines belong under ignored local/ or outside the
repository. Commit reusable code and generic instructions only.

## Render an audible speaking example

The review sentence is **“Maybe we should move a little closer.”** It includes
clear closures and rounded sounds. Optional tools use locally installed CMU
Flite shared libraries, Node, ffmpeg and Pillow:

```sh
python tools/synthesize_example.py local/sentence
python tools/render_sentence.py --character local/character.json --output local/preview
```

Output: `local/preview/speaking-example.mp4` (720p, 60 fps, synthesized audio),
review frames and timing metadata. This runs the actual Python Animator and JS
character deformation, with software rasterization. It is an authored timing
example, not captured live tracking or a browser/hardware benchmark. Phone
TIMES schedule our own overlapping controls; no avatar phoneme shapes are used.

## Current behavior

- Verified OpenSeeFace binary decoding, signed calibration and local profiles.
- Separate measurement, wearer normalization, character style and animation.
- Contact priority, receding opening and persistent independent corner expression.
- Continuous rest-ribbon deformation and an unlit display rendering path.
- Speed-adaptive smoothing and tracking-loss relaxation.
- Shared anatomical state for both displays; mirror only at projection.
- Schematic WS35 mask and density study. Actual LED map and angles are unmeasured.

Rounding is inferred from narrowing; seal is inferred from visible lip aperture.
These are not independently measured muscle controls. Naturalness still needs
visual review and real wearer recordings. CM4 performance is unmeasured.

## Continue development

Read [AGENTS.md](AGENTS.md), [design](docs/DESIGN.md),
[research](docs/RESEARCH.md), [existing pipeline](docs/PIPELINE.md), and
[status / next steps](docs/STATUS.md).

```sh
python -m unittest discover -s tests -v
node --test tests/test_geometry.mjs tests/test_character.mjs
```

The existing `infopcgood/proto-ros2` pipeline was inspected and left unchanged.
Future integration should consume its `/osf_data` and preserve screen ownership.
Prioritize the animation before transport or hardware changes.
