# Prootface

Continuous character-mouth animation downstream of OpenSeeFace, with wearer
calibration, causal articulation and two anatomical views for flat displays.

The pure Python controller runs at 24 Hz. Character style controls opening
contrast, observed-motion accents, expression and rounded forward reach.
Contact interrupts articulation; lost tracking relaxes toward rest. Narrowing
is a rounding proxy, not independent protrusion or phoneme recognition.

[Runtime API reference](docs/API.md) covers Python calls, controls, style bounds,
HTTP endpoints, frame layout and worker lifecycle.

## Standalone preview and calibration

Python 3.10+:

```sh
python -m prootface --character /path/to/private/character.json
```

Open http://127.0.0.1:8080. The standalone receiver listens on UDP 11573 by
default. Do not run it on the same port as an existing ROS receiver. Use the
five calibration stages to capture neutral, open, wide, narrow and closed smile;
[calibration details](docs/CALIBRATION.md) explain ranges and tracker baselines.

The browser uses WebGL. `/?side=left&display=1` and
`/?side=right&display=1` expose individual side views. Schema-2 characters have
a private JSON mesh plus a PNG texture sidecar. The older contour fallback is
only a development study, not a replacement for a configured character.

## Headless EGL rendering

Install NumPy and Pillow through the optional extra:

```sh
python -m pip install -e '.[render]'
```

Linux also needs EGL, a GLES driver and access to its render device. On a typical
Mesa system the packages are `libegl1`, `libgles2` and `libgl1-mesa-dri`.

```python
from prootface.offscreen import OffscreenRenderer
from prootface.model import NEUTRAL, Style, pose_from_controls

with OffscreenRenderer('/path/to/private/character.json', 256, 144) as renderer:
    pose = pose_from_controls(NEUTRAL, Style())
    atlas = renderer.render_atlas(pose)  # (144, 512, 3), top-left BGR uint8
    print(renderer.info)                # inspect the actual graphics driver
```

Create, render and close on the same thread. The renderer uses the compiled
schema-2 mesh, original UVs, sparse targets, depth and separate side projections.
It requires neither Blender nor a browser. Mesa may choose a software renderer;
its availability does not establish performance on another device.

## ROS integration

The implementation is in
[proto-ros2/prootface_pkg](https://github.com/infopcgood/proto-ros2/tree/master/src/prootface_pkg).
It consumes the shared `osf_data`, hosts this same calibration UI and publishes
a synchronized BGR atlas through the existing screen dispatcher. See its README
for installation, launch arguments and dense-WS LED-map requirements.

[Integration contract](docs/PIPELINE.md) documents input, ownership, frame layout
and validation. The ROS path does not create a second UDP listener.

## Private character import

Keep model files, source mappings and all generated character data private:

```sh
blender --background --factory-startup --disable-autoexec --python tools/import_morph_character.py -- /path/to/model.blend --settings local/character-settings.json --output local/character.json
```

Private settings map semantic channels to source targets. Optional art-direction
corrections compile at import time. Runtime only blends sparse targets; it does
not run Blender, inspect source models or access private import settings.

## Development

```sh
python -m unittest discover -s tests -v
node --test tests/test_geometry.mjs tests/test_character.mjs tests/test_morph_mesh.mjs
```

Render tests need the optional dependencies and a working EGL driver. ROS tests
run under Jazzy in the integration repository, using original synthetic fixtures.
Recorded-video tools are offline diagnostics; a scripted or offline preview is
not a hardware latency measurement. See [status](docs/STATUS.md).
