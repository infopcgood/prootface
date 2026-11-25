# Status — implementation checkpoint, 2026-11-25

## Current accepted target
Natural dimensional Nick-inspired mouth motion; NO tongue or tooth rows.
One attached posterior V point per side. Sigma WS35 physical layout with
a denser LED panel. Prioritize animation; hardware technicalities later.
OpenSeeFace measures the wearer; this project is the character model.

## Implemented so far
- Protocol decoder (1785 bytes), signed features and optional aperture measurement.
- Robust staged wearer calibration and persistence.
- Contact-priority retargeting, continuous corners, jaw angle/recession and smoothing.
- Original 2.5D shaded lip/cavity surfaces with an attached V point.
- Browser preview, manual pose controls, side output views, schematic WS35 mask.
- Local preview server and live OpenSeeFace receiver.

## Research preserved
See RESEARCH.md and DESIGN.md. Inspected Sigma WS35/HUB75 and bottom renders.
See PIPELINE.md for actual proto-ros2 topics/messages and future insertion point.
No external art/CAD or upstream source code has been bundled.

## Verification at checkpoint
Python compileall passes; protocol record size verified as 1785.
Node geometry smoke check produces finite vertices.
Full regression tests and visual review are still in progress.
Playwright exists but its default browser is absent; /usr/bin/chromium is a
launcher whose /usr/lib/chromium/chromium executable is absent. Find another
installed browser or document inability to complete a browser visual test.

## Persistence
GitHub write access was initially rejected, then user updated the connection.
Bootstrap commit on master: 7997536e34570b375a43f47fb88773a1425ea4d6.
This checkpoint is being published through the GitHub connector.
No repo branch was force-pushed.

## Next steps, in order
1. Improve the synthetic performance study into continuously timed articulation.
2. Add meaningful tests for protocol, calibration, naturalness invariants,
   closed contact, attached V, mirror/side consistency and stale tracking.
3. Visually inspect and tune shaded lip geometry; naturalness is not established
   by vertex finiteness or unit tests.
4. Fix bugs found by tests; update this status and README with actual checks.
5. Future: real wearer recordings, artist-authored refinements, ROS adapter at
   osf_data -> character -> request_screen_display, and actual dense-LED map.
