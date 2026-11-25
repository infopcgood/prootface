# ROS integration contract

Implementation:
[proto-ros2/prootface_pkg](https://github.com/infopcgood/proto-ros2/tree/master/src/prootface_pkg).
The existing shared receiver and dispatcher retain their roles. The new launch
uses Prootface instead of the named-PNG face renderer; legacy launch stays intact.

## Input

The ROS node subscribes to interface_pkg/OSFData on `osf_data`. The pure adapter
in `prootface.ros_input` maps `_left`/`_right` feature suffixes, uses raw eye-open
values and derives inner-lip aperture from original 2D points. Common validation
with UDP input prevents transport-specific changes to calibration or contact.
Sender time is metadata; freshness uses local monotonic receipt time.

No second UDP receiver is started by the ROS node. The existing OSF receiver
accepts complete datagrams, including multiple faces. One configured face ID
feeds the calibrated controller; the rest are ignored by that controller.

## Control and calibration

The same Application owns profile, calibration captures, style and Animator.
Its HTTP server can run independently from sockets and timing loops. The ROS
node provides the 24 Hz steady-time control loop. Only current/past input is
used. Input callbacks latch brief contacts, including between presentation ticks.

Presentation rate can be 24, 12 or 6 fps without retiming the controller. A
render worker owns EGL and coalesces pending poses. At most one pending pose
and one completed frame are retained; stale completed frames are discarded.
UI/manual/demo commands operate on this same state. The legacy categorical
FacialExpression topic is not an automatic continuous articulation source.

## Rendering and transport

The headless GLES renderer consumes a private compiled schema-2 mesh and texture.
It draws each anatomical side with its own depth sign and one display mirror,
using the same sparse authored weights as the viewer. It returns contiguous
uint8 BGR pixels with a top-left origin. Blender is only an offline tool.

The atlas layout is:

- width: twice the configured per-side virtual width;
- height: configured per-side virtual height;
- left half: anatomical left view;
- right half: anatomical right view;
- Image.data: row-major BGR bytes;
- flip_second_screen: false, because both views are already side-specific.

At startup the ROS node requests screen control with its fully qualified sender
name, then publishes Image messages with that same sender to
`request_screen_display`. The existing dispatcher forwards its selected producer
to `screen_display`. The node does not repeatedly reclaim ownership from another
producer. The current dispatcher is a selected-sender gate, not a timed lease.

## Outputs

The OpenCV backend can display the atlas using matching global display dimensions.
The new WS atlas backend consumes an explicit map with per-side pixel positions,
physical strip/LED order and unused slots. It converts BGR to RGB exactly once.
It validates map dimensions and driver strip count, rejects extra mirroring and
clears stale output. No physical map can be generated from virtual frame dimensions.
The existing single-image WS/HUB75 backends remain separate legacy entry points.

See the ROS package README for its launch configuration, dependencies, map schema
and test commands. Device validation remains distinct from desktop/CI execution.
