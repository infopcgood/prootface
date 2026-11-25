# Existing proto-ros2 pipeline: integration reference

Inspected `infopcgood/proto-ros2` master tree
`6110aa90568b796e18188dd3104e273d1e30c9f0` on 2026-11-25. The user asked
to prioritize natural animation; this document preserves integration context
without rebuilding the existing pipeline or adding ROS dependencies here.

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
