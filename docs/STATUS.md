# Integration status

## Implemented

- Shared validated observation construction for UDP and ROS OSFData.
- Decoded-measurement ingestion and calibration HTTP hosting without a UDP socket.
- Headless EGL/GLES schema-2 atlas renderer, depth/texture handling and BGR readback.
- Latest-only render worker with graphics-thread ownership and bounded handoff.
- ROS node, startup screen-control request, 24 Hz controller and 24/12/6 fps output.
- Existing Image transport carrying synchronized, independently projected sides.
- Atlas-aware WS backend with explicit coordinate mapping and RGB conversion.
- Optional package-owned input adapter: datagram validation, multi-face support
  and clean shutdown; existing receiver code remains unchanged.
- Explicit ROS launch configuration; legacy renderer/backends remain available.

## Validation checkpoint

Local core suite: 78 tests passed. Browser geometry suite: 16 tests passed.
Pure LED-map suite: 3 tests passed. Package
wheel creation succeeded and includes only the public Python package. EGL tests
exercise original synthetic geometry, side selection, one mirror, depth and BGR.

The initial ROS Jazzy build covered seven packages; the isolated integration
now builds only the unchanged interface/dispatcher packages and prootface_pkg. The real
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

## Existing-package boundary

The ROS integration restores all pre-existing package trees to their revision
before Prootface work. Its optional input, preview, atlas modules and associated
tests now live in prootface_pkg. The only permitted future changes to existing
packages are adding parameters in param_server_pkg or adding new interface
definitions in interface_pkg. Existing behavior and definitions remain intact.

## Externally selected expressions

Implemented expression-specific closed/open/wide/round banks, independent eye
and mouth selection, 24 Hz preset transitions, latched external commands and
optional timed returns. Both generic renderers consume the same sparse context
weights. New tests cover bank reconstruction, front restraint, contact, blinks,
interruption, persistence, invalid commands and HTTP selection. Non-neutral
expressions require a newly compiled private character; geometry and source
mappings are not distributed by this public repository.

Expression compilation now requires an authored mouth source. Authored shape
corrections and their rest cancellation remain independent of anterior speech
restraint; optional articulation scaling uses separate motion targets. Endpoint
tests cover that separation at multiple restraint values. The review tool keeps
eyes neutral in the comparison by default so mouth identity can be judged.
