# Runtime API reference

Version 0.1.0. Import from the modules below; render dependencies are optional and
are not imported by the pure controller. Command-line tools and browser helper
modules are implementation details. No ROS installation is needed for the core.

## Measurements and normalization

| Python API | Contract |
| --- | --- |
| `prootface.openseeface.decode_packet(packet: bytes, received_at: float) -> list[Measurement]` | Decode 1–39 complete 1785-byte OpenSeeFace records. Malformed/non-finite used fields raise `ValueError`. `received_at` is local monotonic seconds. |
| `prootface.openseeface.Measurement` | Decoded observation: `received_at`, `sender_time`, `face_id`, `features`, `aperture_ratio`, `confidence`, `valid`, `eye_left`, `eye_right`. Treat it as read-only, including its feature dictionary. |
| `Measurement.signals() -> dict[str, float]` | Six signed raw signals: `open`, `width`, `corner_left`, `corner_right`, `brow_left`, `brow_right`. |
| `prootface.ros_input.measurement_from_ros(message, received_at) -> Measurement` | Duck-typed adapter for `interface_pkg/OSFData`; no rclpy import. Same aperture/validity rules as UDP. Raises `ValueError` for malformed input. |
| `prootface.model.retarget(measurement, profile) -> dict[str, float]` | Convert a valid observation into normalized semantic controls. This function does not check freshness or filter time; the caller or `Application` does. |

`aperture_ratio` is mean inner-lip separation divided by mouth width, or `None`
when width/confidence cannot establish it. `confidence` is the minimum confidence
of mouth landmarks 58–65. Validity requires the tracker success flag and mouth
confidence of at least 0.5. The sender's timestamp is metadata, never a freshness
clock. Anatomical left/right is independent of image/display mirroring.

`observation(...)` is the lower-level keyword-only constructor used by both
adapters. It takes `received_at`, `sender_time`, `face_id`, `resolution` (2 values),
`right_eye`, `left_eye`, `success`, `confidence` (68 values), `xy` (68 image-space
2D points), and `features` (all names in `openseeface.FEATURES`). Invalid shapes,
missing features, and non-finite values raise `ValueError`. It does not consume
3D landmarks or infer phonemes.

## Calibration

Import these from `prootface.calibration`:

| API | Behavior |
| --- | --- |
| `Range(rest=0, positive=1, negative=-1)` | Signed range; each span must be at least 0.02. |
| `Range.normalize(value) -> float` | Normalize a finite value to [-1, 1], independently above/below rest. |
| `Profile()` | Default uncalibrated profile. Contains six `ranges`, `closed_aperture`, `open_aperture`, `calibrated`, and `schema_version=1`. |
| `Profile.to_dict()` / `Profile.from_dict(data)` | JSON-compatible schema-1 serialization; malformed/unsupported profiles raise `ValueError`. |
| `Profile.save(path: Path)` | Create parents and atomically replace the profile file. Filesystem errors raise `OSError`. |
| `CalibrationSession.begin(stage)` | Begin/reset one of `neutral`, `open`, `wide`, `narrow`, `smile`. Other stages' samples remain. |
| `CalibrationSession.add(signals, aperture)` | Add a finite six-signal sample to the active stage. Does nothing when stopped. Caller must exclude invalid tracking. |
| `CalibrationSession.finish() -> Profile` | Require at least eight samples per stage and usable motion ranges; construct a profile and stop capture on success. `ValueError` leaves the active capture and samples intact. Does not save a file. |
| `CalibrationSession.status()` | `{"stage": null, "counts": {"neutral": 0, ...}}`. |

Set `session.stage = None` to pause capture without losing samples. Capturing
about two seconds per stage is recommended; eight samples is the actual minimum.
The five stages do not calibrate independent protrusion, phoneme identity, blink
ranges, or frowns. See [CALIBRATION.md](CALIBRATION.md) for baseline consistency
and the default-threshold fallback when aperture samples are insufficient.

## Controls, style and timed poses

Import `NEUTRAL`, `Style`, `STYLE_BOUNDS`, `retarget`, `pose_from_controls`, and
`Animator` from `prootface.model`.

| Control | Range | Meaning |
| --- | --- | --- |
| `opening`, `rounding`, `spread` | 0–1 | Aperture drive and mouth family selection |
| `seal` | 0–1 | 1 closes the mouth; overrides opening |
| `corner_left`, `corner_right` | -1–1 | Independent frown/smile drive |
| `eye_left`, `eye_right` | 0–1 | 1 is open; 0 is blink |
| `brow_left`, `brow_right` | -1–1 | Semantic brow controls; no schema-2 brow target is emitted currently |
| `tension` | 0–1 | Semantic value retained in the pose; no independent schema-2 tension target |
| `bite`, `sibilant`, `postalveolar`, `rhotic`, `lip_press` | 0–1 | Optional explicit articulation channels; not inferred by the OpenSeeFace adapter |

`NEUTRAL` is the full default control dictionary. Copy it before changing it.
Unspecified controls use these defaults; notably, `seal` defaults to **1**.
A manually opened mouth must also set `seal` to 0. Values outside a channel's
range are clamped. Unknown names, non-numeric values, booleans, NaN and infinity
raise `ValueError`.

```python
from prootface.model import Animator, NEUTRAL, Style

animator = Animator(Style())
target = {**NEUTRAL, 'opening': 0.8, 'rounding': 0.9, 'seal': 0.0}
pose = animator.step(target, now=10.0, tracked=True)
# Repeat at 24 Hz with increasing local monotonic timestamps.
```

- `pose_from_controls(controls, style, family_index=None, accent=0.0) -> dict`
  evaluates a pose immediately, without temporal filtering. Optional
  `family_index` is 0 (normal), 1 (round) or 2 (wide); `None` blends families.
  `accent` is an explicit additive articulation accent in [0, 0.5]. Usually let
  `Animator` manage both values.
- `Animator(style=None).step(target, now, tracked=True) -> dict` applies causal
  filtering, contact holds, family commitment and observed-motion accents.
  Times must be finite and nondecreasing; invalid targets do not advance its
  state. Use `tracked=False` to ease toward rest and cancel accents.
- A pose includes normalized controls, `blend_<target>` weights,
  `front_motion_scale`, and diagnostic values such as `aperture`, `accent`,
  `jaw_angle`, `jaw_recession`, and `width_scale`. Render the returned pose as a
  whole. Blend weights drive the compiled mesh; diagnostics are not extra mesh
  transforms. Missing targets in a character simply have no visual effect.

Style fields are validated at construction; HTTP applies the same bounds.
Replace `animator.style` with a new `Style(...)` to change it. These settings are
character direction, separate from wearer calibration.

| Style field | Default | Bounds | Effect |
| --- | --- | --- | --- |
| `max_jaw_angle` | 0.36 | 0.1–0.65 | Opening drive scale and contour jaw angle |
| `opening_gamma` | 1 | 0.6–2 | Opening response |
| `asymmetry` | 0.7 | 0–1 | Left/right corner difference |
| `pose_contrast` | 2.5 | 1–4 | Family separation |
| `opening_contrast` | 3.2 | 1–4 | Small/large opening separation |
| `key_pose_strength` | 0.95 | 0–1 | Timed family commitment |
| `accent_gain` | 0.45 | 0–0.5 | Observed opening onset accent |
| `front_motion_scale` | 0.8 | 0–1 | Restrict compiled anterior motion |
| `rounding_reach` | 1 | 0–1 | Optional compiled forward-rounding correction |
| `lower_lip_spike` | 0 | 0–1 | Optional compiled lower-lip correction |
| `recession` | 0.12 | 0–0.35 | Contour-study/diagnostic recession |
| `max_corner_lift` | 0.2 | 0–0.35 | Contour study only |
| `v_depth` | 0.11 | 0.02–0.30 | Contour study only |
| `v_position` | 0.88 | 0.65–0.92 | Contour study only |
| `v_width` | 0.045 | 0.02–0.10 | Contour study only |
| `lip_thickness` | 0.016 | 0.005–0.04 | Contour study only |

Changing contour-only fields does not redraw an imported schema-2 character.
Its lip silhouette comes from the private compiled mesh and authored targets.

## Stateful application and HTTP

`prootface.server.Application(profile_path: Path, face_id=0)` owns a profile,
calibration session, animator and latest valid selected-face observation. Initial
mode is `demo`; the ROS node switches it to `live`.

| Method/property | Contract |
| --- | --- |
| `receive(packet, now)` | Decode and ingest UDP bytes; malformed datagrams increment `rejected`. |
| `ingest(measurement)` | Shared ROS/UDP path. Ignore other faces, invalid tracking and older receipt times for the latest state. Selected-face arrivals increment `received`. |
| `tick(now)` | Advance the controller and replace `snapshot`; returns `None`. Call at 24 Hz on a monotonic clock. |
| `command(path, data)` | Apply one HTTP command below directly. Invalid commands preserve prior settings; a failed calibration file write preserves the old profile and permits retry. |
| `lock` | RLock; hold it while copying `snapshot` from another thread. |
| `stop` | Event used to stop HTTP event streams and standalone loops. |

Freshness requires local input age between 0 and 250 ms. Tracking loss relaxes
the pose and clears queued contact so old closures are not replayed on recovery.
A closure observed between ticks is latched, preserving brief contacts. Ingest
only measurements produced by the validated adapters or equivalent trusted code.

`make_http_server(app, host, port, character_path)` returns a bound
`ThreadingHTTPServer` without starting loops. `start_http(...)` returns
`(server, thread)` with its serving thread running; neither creates a UDP socket
or an animation clock. On shutdown set `app.stop`, call `server.shutdown()` and
`server.server_close()`, then join the thread. Port 0 selects an available port.
The HTTP interface is an operator control API without authentication; bind it to
loopback for local use. Browser commands must have a matching Origin host.

| HTTP method/path | Request / response |
| --- | --- |
| `GET /api/state` | Current snapshot JSON (`{}` before the first tick) |
| `GET /api/events` | Server-sent events, `data: <snapshot JSON>`, sampled at 24 Hz |
| `GET /api/character` | Compiled character JSON, or `null` if absent |
| `GET /api/character-texture` | PNG sidecar; 404 if absent |
| `POST /api/control` | `{"mode":"live"}` or `{"mode":"manual","controls":{"opening":0.8,"seal":0}}`; `mode` and partial `controls` are optional. Modes: `demo`, `manual`, `live`. |
| `POST /api/style` | Partial style object, e.g. `{"opening_contrast":3.2,"rounding_reach":1}`. Applies in memory; does not write a style file. |
| `POST /api/calibration/start` | `{"stage":"neutral"}`; resets that stage, switches to live |
| `POST /api/calibration/stop` | `{}`; pauses capture |
| `POST /api/calibration/save` | `{}`; validates all stages, saves/replaces the wearer profile, stops capture |

POST bodies must be JSON objects of 1–16384 bytes. Success is `{"ok":true}`;
validation/unknown-command errors return HTTP 400 with `{"error":"..."}`;
cross-origin browser writes return 403; calibration persistence errors return
500. An unknown POST route currently returns 400, not 404.

Snapshots contain `sequence`, `mode`, `label`, `pose`, `animation_fps`, `style`,
`age_ms`, `tracking`, `calibrated`, `calibration` (stage/counts), `received`,
`rejected`, `raw` (six latest signals), `aperture_ratio`, and `limitations`.
`age_ms` is nullable and uses receipt time. `tracking` describes measurement
freshness even when demo/manual mode is selected. These fields update on ticks;
a successful POST does not itself tick the animation.

## Rendering and worker lifecycle

`prootface.offscreen.OffscreenRenderer(character_path, side_width=256,
side_height=144, platform='auto')` loads a schema-2 JSON mesh and its matching PNG.
Install `prootface[render]` plus an EGL/GLES driver. Side dimensions must be whole
numbers in [1, 4096]. Platform choices are `auto`, `surfaceless`, `default`.

- `render_atlas(pose)` returns a new contiguous NumPy `uint8` array with shape
  `(side_height, 2 * side_width, 3)`: anatomical left, then anatomical right;
  top-left origin; interleaved **BGR**, row-major, no padding. Both views use one
  pose and have already received their required projection/mirroring.
- `info` reports graphics `vendor`, `renderer`, `version`; software Mesa is possible.
- `close()` releases graphics resources and is idempotent. Create/render/close on
  the same thread; context-manager usage is supported.
- Invalid geometry/pose weights raise `ValueError`; graphics failures raise
  `RuntimeError`; file operations can raise filesystem/JSON errors.

`prootface.runtime.RenderWorker(renderer_factory)` creates the renderer on its
worker thread. The factory returns an object with `info`, `render_atlas(pose)`
and `close()`. It waits up to 15 seconds for initialization.

| Method/property | Contract |
| --- | --- |
| `submit(sequence, pose_time, pose)` | Nonblocking latest-pending replacement; copies the flat pose dict. `pose_time` uses the caller's monotonic clock. |
| `poll() -> RenderedFrame | None` | Take the latest completion once. Fields: `sequence`, `pose_time`, `pixels`. |
| `info`, `dropped_pending` | Graphics metadata and pending replacements |
| `check()` | Raise `RuntimeError` chained to the original render/cleanup error |
| `close()` | Discard queued/completed work, finish the current render and join (10-second limit). Repeated calls are allowed. Renderer errors remain available through `check()`. |

At most one render is running, one pose is pending, and one completion is held.
The worker replaces superseded completions and does not enforce a frame-age
limit; the ROS consumer does. Context-manager usage is supported. No GPU work
can be forcibly interrupted safely by this worker.

## CLI and ROS adapter

Both `python -m prootface` and `prootface` start the standalone HTTP/UDP preview.
Run `python -m prootface --help` for host/port, UDP host/port, face ID, profile and
character options. Defaults: HTTP 127.0.0.1:8080, UDP 127.0.0.1:11573,
`local/calibration.json`, `local/character.json`.

The separate ROS package uses this API rather than launching another UDP server.
Its [ROS API reference](https://github.com/infopcgood/proto-ros2/blob/master/src/prootface_pkg/API.md)
defines topics, control service, startup parameters, atlas transport and LED maps.
