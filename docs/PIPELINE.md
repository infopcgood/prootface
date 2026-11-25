# Existing proto-ros2 pipeline: integration reference

Re-inspected `infopcgood/proto-ros2` master commit
`6110aa90568b796e18188dd3104e273d1e30c9f0` on 2026-11-25. The user has now
asked how Prootface would integrate. This is a source-checked integration
contract; ROS wiring and a live offscreen renderer are not implemented here.

## Observed current path

1. OpenSeeFace sends UDP; `osf_receiver_pkg` binds port 11573 and publishes
   `interface_pkg/OSFData` on `osf_data`.
2. `face_renderer_pkg` currently consumes categorical `FacialExpression` on
   `facial_expression`, composites PNG eye/mouth assets, and publishes custom
   `Image` messages on `request_screen_display`.
3. `screen_dispatcher_pkg` accepts frames only from the owner selected by the
   `request_screen_control` service, then republishes on `screen_display`.
4. Existing display backends consume those custom image messages.

The `osf_expression_detector_pkg` directory currently contains packaging and
tests but no detector implementation file. Do not describe it as an existing
continuous retargeting layer.

## Message details that matter later

- OSFData has signed mouth/corner features plus eye data, confidences, 2D and
  3D points. Field suffixes are `_left`/`_right`, unlike upstream `_l`/`_r`.
- Custom Image fields are `sender`, `height`, `width`, `flip_second_screen`,
  `data`. There is no encoding field or separate anatomical side payload.
- Existing face renderer flattens OpenCV BGR uint8 data and sets
  `flip_second_screen=True`.
- Current proto_panel_display hard-codes 50x34, 8 strips x 150 LEDs, loads
  coordinates from `id.txt`, samples BGR pixels and reverses channels to RGB.
  Those are existing backend assumptions, NOT defaults for the denser panel.

## Intended insertion point

`osf_data` -> Prootface calibration + continuous character state -> renderer ->
`request_screen_display` -> existing dispatcher -> chosen backend.

Use an adapter into the pure core instead of another UDP receiver in production.
Retain the dispatcher's ownership protocol. Decide explicitly how two distinct
anatomical views are transported: a single mirrored image cannot preserve an
asymmetric smirk or wink. An atlas or an extended interface may be appropriate,
but must be agreed with the user's actual display backend later. Avoid silently
mirroring an already side-specific render twice.

No changes to proto-ros2 have been made by this task. End-to-end ROS operation,
Hailo inference and hardware LED output are not implemented or tested here.

## Concrete integration proposal

Add a `prootface_node` in the ROS workspace. It owns the shared calibrated
character state and the realtime rendering output, replacing the PNG face
renderer in the active launch. OpenSeeFace and the existing UDP receiver stay
upstream. Do not run the standalone Prootface UDP listener alongside it on the
same port, and do not route continuous measurements through expression names.

### Input and calibration

Subscribe to `interface_pkg/OSFData` on `osf_data`. The message already carries
the required features and landmarks; no additional inference model is needed
for retargeting. A thin adapter constructs the core Measurement:

| OSFData | Core use |
| --- | --- |
| id | Selected face ID |
| mouth_open / mouth_wide | Signed opening/width features |
| mouth_corner_updown_left/right | Core `_l`/`_r` feature names |
| eyebrow_updown_left/right | Core `_l`/`_r` feature names |
| left_eye_open / right_eye_open | Blink openness; do not substitute signed eye features |
| confidence / got_3d_points | Same validity checks as standalone input |
| points[58..65] | Normalized inner-lip aperture and contact |

Use local monotonic receipt time for freshness. Keep the callback short, retain
the latest valid measurement, and latch brief contacts as the current live
Application does. Run the same calibration, retargeter and Animator at 24 Hz.
Rendering may hold that state at a lower chosen cadence without slowing the
controller or changing contact timers. Use small/latest-only queues to prevent
a slow renderer from replaying old expressions.

Refactor the Application's decoded-measurement ingestion and HTTP/calibration
hosting away from socket creation. The ROS adapter can then reuse the same
state and calibration buttons without binding UDP. Expose profile path, selected
face, private character path, style and presentation rate as configuration.
Calibration remains specific to wearer/camera/tracker baseline, independent
of ROS transport and panel mapping.

### Live renderer and screen ownership

The current working renderer is the WebGL viewer. Blender is an offline review
tool. Production ROS output still needs a realtime offscreen renderer that
consumes the same compiled mesh/texture and authored weights, projects both
anatomical sides, and returns BGR uint8 pixels. That is a substantive remaining
implementation item; the existing PNG compositor cannot produce these poses.
Keep a latest-pose handoff between controller and renderer instead of a growing
render queue. Validate the renderer against the native reference frames.

The node calls `request_screen_control` with sender `prootface_node`, then
publishes Image messages to `request_screen_display` with exactly that sender.
The existing dispatcher forwards them to `screen_display`. Its current service
simply changes the accepted sender; it is not a timed lease or automatic crash
failover. The old face renderer must not simultaneously reclaim ownership.
Existing expression commands can later become timed expression overlays while
tracked jaw/contact remain continuous; this mapping does not exist yet.

### Two side displays: use one synchronized atlas

For the first integration, retain the existing Image and dispatcher. Package
left and right side renders in a side-by-side BGR atlas: width `2*side_width`,
height `side_height`, row-major data, `flip_second_screen=False`. The dispatcher
already forwards dimensions and bytes without interpreting them. This carries
both sides from the same animation tick and preserves asymmetric corners and
winks. Each image must be projected/mirrored once; do not then duplicate/flip a
side-specific view in the backend.

Update the dense-WS display backend to understand this atlas and sample the
correct half using each panel's own LED coordinates, strip order and orientation.
Separate virtual frame dimensions from per-side dimensions and physical LED
counts. The current panel code hard-rejects sizes other than 50x34 and assumes
8 strips of 150 LEDs, so changing only a resolution parameter is insufficient.
Its mapping also does not implement the generic flip flag. Preserve the BGR
message convention and perform the final BGR-to-RGB conversion once.

`opencv2_display_pkg` can validate the atlas first, using matching configured
atlas dimensions. Physical WS geometry, denser LED locations, strip counts and
driver throughput must come from the actual panels, not the existing constants.

### Launch and completion sequence

The current `launch.sh` starts only screen_dispatcher, the PNG face renderer and
mic_input. It does not start the parameter server, OSF receiver or display node.
Create an explicit launch configuration for the parameter server, existing OSF
receiver, new Prootface node, dispatcher and selected backend; OpenSeeFace startup
remains part of the measurement pipeline.

1. Validate OSFData-to-Measurement parity against the same packet recording.
2. Wire the calibrated controller and its UI into the ROS node.
3. Implement realtime BGR frame output; compare it with approved A renders.
4. Exercise screen ownership and the two-view atlas through the OpenCV backend.
5. Parameterize/map the actual dense WS panels, then measure CM4 latency and
   sustained output. Keep hardware measurements separate from offline previews.

Hailo deployment, if used by the measurement stage, remains upstream. This
animation layer itself is deterministic retargeting and morph blending.
