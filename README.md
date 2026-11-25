# Prootface

Character-mouth animation downstream of OpenSeeFace, for two flat side displays
in a denser Sigma WS35-style wearable head.

Triwave is the selected visual reference. The latest user direction is to use
authored phoneme poses as a starting point and improve their blending and timing.
The current path uses a privately configured authored mesh basis. It preserves
rest identity, supports clear closures and persistent expression, and avoids
the rejected raster-ribbon swelling and sideways squash. No tongue or tooth rows.

**Working rate: 24 fps.** Mouth-shape changes are deliberately exaggerated:
stronger silhouette contrast, short readable holds and fast transitions.
The live controller uses only current/past measurements, keeps jaw motion
responsive during shape holds and preserves brief contacts between output frames.
Browser refresh does not generate extra interpolated poses.

## Run

Python 3.10+ and a WebGL browser:

```sh
python -m prootface
```

Open http://127.0.0.1:8080. Private runtime data consists of
`local/character.json` and its `.png` texture sidecar. If no character is loaded,
the UI labels the older contour study as a fallback; that is not the target rig.
Output-only pages: `/?side=left&display=1` and `/?side=right&display=1`.

For live input, OpenSeeFace normally sends UDP to 127.0.0.1:11573. Select another
port if the existing ROS receiver owns it:

```sh
python -m prootface --udp-port 11574 --face-id 0
```

## Private authored-basis import

Keep reference assets and settings private. Configuration specifies the mesh,
emission image/material, side-view calibration and a `targets` map from semantic
channels to source keys. Semantic channels include open, round, wide, closed,
side-specific smile/frown/pucker and blink. Nonselected animation is disabled.
No source-specific names or projection values are embedded in reusable code.

```sh
blender --background --factory-startup --disable-autoexec --python tools/import_morph_character.py -- /path/to/model.blend --settings local/character-settings.json --output local/character.json
```

The output is private indexed geometry, UVs, sparse target deltas and a texture.
Do not commit it. The older rest-mask importer/compiler remain for legacy studies.

## Audible speaking review

The example sentence is “Maybe we should move a little closer.” Optional tools
use local CMU Flite shared libraries, Blender, ffmpeg, NumPy and Pillow:

```sh
python tools/synthesize_example.py local/sentence
python tools/render_morph_sentence.py --character local/character.json --output local/review
```

The native review renderer consumes the same compiled mesh and Python-generated
blend weights as WebGL. It uses a fixed camera with room for the pose basis.
The default `--input-mode tracking` sends synthetic camera-supported controls
through the actual causal controller. Unmeasured consonant hints are disabled.
The optional `--input-mode authored` is a full scripted pose reference; it is
not live tracking. Output is exactly 24 fps. Neither mode is a camera recording,
browser capture or CM4 performance benchmark.

## Model boundaries

Measurement, wearer calibration, character style, time and display projection
remain separate. Open/round/spread samples use contrasted, bounded weights. A mouth family gets
a brief minimum exposure while jaw motion continues; contact interrupts it.
Contact attaches immediately and receives a two-frame minimum exposure. Corner expression holds
through articulation; lost tracking eases toward rest. Both side displays share
one timed anatomical state and mirror only at projection.

OpenSeeFace narrowing is a rounding proxy; seal is inferred from lip aperture.
These are not independent muscle measurements. Specialized consonant controls
are accepted by the model but are not currently inferred from OpenSeeFace. Actual panel geometry, LED map
and CM4 performance remain unmeasured. No changes have been made to proto-ros2.

## Development

Read [AGENTS.md](AGENTS.md), [design](docs/DESIGN.md), [research](docs/RESEARCH.md),
[pipeline](docs/PIPELINE.md) and [status](docs/STATUS.md).

```sh
python -m unittest discover -s tests -v
node --test tests/test_geometry.mjs tests/test_character.mjs tests/test_morph_mesh.mjs
```

Publish reusable code and generic notes only. Private reference files, mappings,
inspection notes, derived geometry and review clips remain outside version control.
