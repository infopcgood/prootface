# Real-video evaluation

Run upstream OpenSeeFace on chronological 24 fps footage, then replay its
measurements through the same Application used by the standalone live server.
Use original audio only for comparison. No transcript, phone timings or future
measurements enter the controller.

The repository's public-video workflow downloads a public-domain sample and
retains the clip and packets as a seven-day workflow artifact. The workflow
needs only repository read permission. No private character data is uploaded.
The first backlit candidate produced no valid detections and was rejected.

Locally, with an external OpenSeeFace checkout and compatible dependencies:

```sh
ffmpeg -i input.mp4 -vf fps=24 -c:v libx264 -c:a aac local/source24.mp4
python tools/track_video.py --osf-root /path/to/OpenSeeFace \
  --video local/source24.mp4 --output local/video-input
python tools/replay_video.py --packets local/video-input/packets.jsonl \
  --calibration-start 4 --calibration-end 14 --start 16 --end 22 \
  --output local/video-replay
python tools/render_video_comparison.py --source local/source24.mp4 \
  --packets local/video-input/packets.jsonl --replay local/video-replay \
  --character local/character.json
```

To compare the optional lower-lip contour, rerun replay into a separate output
directory with `--lower-lip-spike 1`, then render that directory. The privately
compiled character must include the optional targets. The default remains 0;
both runs use the same stronger rounded forward reach. Keep input, calibration,
evaluation bounds and framing identical when comparing the two contours.

Tracking needs OpenSeeFace's NumPy, OpenCV, ONNX Runtime and model dependencies;
the public workflow pins a tested combination. Comparison rendering requires
Blender, ffmpeg, NumPy and Pillow and stays outside the runtime path.

An existing video cannot perform the guided neutral/open/wide/narrow/smile
calibration. The helper therefore estimates a sample profile from an earlier
section and marks it uncalibrated. Evaluation must start after that section.
Use a few warm-up seconds between calibration and evaluation. The estimate is
frozen; evaluation frames cannot improve it retrospectively. A genuine wearer
test should load the user's guided profile instead of fitting to the test clip.

The replay retains validity, last-good-measurement behavior, staleness, contact
and the causal 24 fps Animator. Its MP4 keeps original audio timing and its GIF
keeps all 24 fps frame exposures using alternating centisecond durations.
Outputs and all private assets belong under ignored local/. The comparison is
offline review, not a measurement of CM4 inference, display timing or latency.

## Presentation-rate comparison

The user selected A and requested 12 and 6 fps reviews against the existing
24 fps presentation. `tools/render_rate_comparison.py` takes an existing frame
sequence and its matching movie with audio. It creates true-rate individual
movies plus a synchronized comparison. Optional crop coordinates focus the
review without changing the geometry or framing between cadences.

```sh
python tools/render_rate_comparison.py --frames local/video-replay/frames \
  --movie local/video-replay/real-video-24fps.mp4 --output local/rate-comparison
```

The 12 fps review holds every second source pose; 6 fps holds every fourth.
Neither selects future poses, interpolates drawings nor slows the soundtrack.
The controller still uses its 24 fps timing rules. This isolates presentation
cadence; adapting event exposure for a selected lower live cadence would be a
separate step. Short contacts or accents can fall between sparse redraws.
