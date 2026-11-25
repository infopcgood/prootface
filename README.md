# Prootface

The character model downstream of OpenSeeFace for a wearable protogen head.

The target is a **natural, dimensional mouth** with controlled lip contact,
lower-jaw recession and expression-preserving articulation. It is inspired by
the design principles discussed by Zootopia's animators, not a copy of Nick's
character or mesh. There is **no tongue or tooth row**. One V-shaped point is
integrated into the posterior/eye-side lip contour of each side.

The physical reference is **Coela Can't's Sigma WS35 layout**, adapted to a
denser LED panel. The current WS35 silhouette is a schematic placement study;
panel dimensions, pitch, LED coordinates and mount angles are not assumed.

## Try the motion study

Python 3.10+ and a browser supporting WebGL are sufficient. No ML packages,
ROS, camera, Hailo runtime, npm install or cloud service are needed for preview.

```sh
python -m prootface
```

Open http://127.0.0.1:8080. Use **Performance study**, **Pose controls**, or
**OpenSeeFace**. Output-only pages are `/?side=left&display=1` and
`/?side=right&display=1`. Both use one shared pose, with anatomical asymmetry.

For live input, configure OpenSeeFace to send its ordinary UDP output to
127.0.0.1:11573. This receiver and proto-ros2's existing receiver cannot bind
the same UDP port simultaneously. The standalone receiver is for preview;
the future ROS integration should consume existing `/osf_data` instead.

```sh
python -m prootface --udp-port 11574 --face-id 0
```

Wearer calibration captures neutral, opening, spreading, narrowing and closed
smile samples. Click each stage, hold it briefly, then stop capture. Save only
after every stage has at least eight valid frames. The profile is stored at
`local/calibration.json`, outside version control. Camera/landmark recordings
are not written by default.

## What the prototype does

- Verified OpenSeeFace binary packet decoding and signed feature mapping.
- Robust wearer normalization, contact-aware retargeting and time-based easing.
- A shaded procedural profile-surface model, independent of display density.
- A receding lower lip/jaw arc and one attached rear V point per side.
- Persistent corner lift during articulation; closure wins over opening.
- A dual-view WebGL study with a schematic WS35 mask and density preview.
- Graceful relaxation after tracking loss and manual controls for art direction.

This is an editable motion prototype, not a production-quality organic face,
an inference model, or a hardware driver. OpenSeeFace narrowing is used only
as a **rounding proxy**. Lip seal is **inferred from visible aperture**, not
independently measured pressure. Tongue tracking and phoneme classification
are outside scope. CM4 performance is not yet measured.

## Continue development

Read [AGENTS.md](AGENTS.md), [design](docs/DESIGN.md),
[research](docs/RESEARCH.md), [existing pipeline](docs/PIPELINE.md), and
[current status / next steps](docs/STATUS.md).

```sh
python -m unittest discover -s tests -v
node --test tests/test_geometry.mjs
```

All source and procedural geometry in this initial implementation are original.
Third-party art and CAD are linked as references, not bundled or traced.

