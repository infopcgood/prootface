# Integration status

## Implemented

- Shared validated observation construction for UDP and ROS OSFData.
- Decoded-measurement ingestion and calibration HTTP hosting without a UDP socket.
- Headless EGL/GLES schema-2 atlas renderer, depth/texture handling and BGR readback.
- Latest-only render worker with graphics-thread ownership and bounded handoff.
- ROS node, startup screen-control request, 24 Hz controller and 24/12/6 fps output.
- Existing Image transport carrying synchronized, independently projected sides.
- Atlas-aware WS backend with explicit coordinate mapping and RGB conversion.
- Shared receiver datagram validation, multi-face support and clean shutdown.
- Explicit ROS launch configuration; legacy renderer/backends remain available.

## Validation checkpoint

Local core suite: 65 tests passed. Pure LED-map suite: 3 tests passed. Package
wheel creation succeeded and includes only the public Python package. EGL tests
exercise original synthetic geometry, side selection, one mirror, depth and BGR.

ROS Jazzy build completed for all seven selected integration packages. The real
runtime suite passed UDP/message conversion, EGL rendering, calibration HTTP and
profile saving, dispatcher ownership, driver-byte output and an installed-launch
smoke test. It uses original synthetic geometry and a recording hardware driver.
See the [integration workflow](https://github.com/infopcgood/proto-ros2/actions/workflows/prootface-integration.yml)
for pinned core revisions and the status of each ROS commit.

Review hardening adds transactional command validation, shared Python/HTTP style
bounds, stale-contact clearing, monotonic measurement selection, strict sparse
indices, and cleanup after graphics/ROS failures. Runtime interfaces are listed
in [API.md](API.md). Startup-only ROS settings are explicitly read-only; shared
input queues retain a multi-face burst before filtering. Additional Jazzy tests
cover that burst and steady watchdog progress while simulated ROS time is paused.

## Device-dependent work

The actual dense panel coordinate file and a matching smileds driver build are
required for physical WS output. No physical coordinates are inferred or bundled.
CM4 performance, Hailo deployment, wearer tracking and LED output still require
on-device validation. Software Mesa and synthetic-driver tests do not establish
those results. Private continuity and asset details are not part of public docs.
