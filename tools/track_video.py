"""Run upstream OpenSeeFace on chronological video frames and retain real packets.

Requires an external OpenSeeFace checkout and its dependencies/models. Neither
video nor measurement output belongs in version control. Audio is never input.
"""
import argparse
import base64
import json
from pathlib import Path
import struct
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from prootface.openseeface import FEATURES, HEADER, decode_packet
from prootface.timing import ANIMATION_FPS


def pack_face(face, timestamp, width, height):
    """Upstream facetracker.py wire layout; landmarks are stored as row/column."""
    eyes = face.eye_blink if face.eye_blink is not None else [1, 1]
    header = HEADER.pack(timestamp, face.id, width, height, *eyes,
                         int(face.success), face.pnp_error, *face.quaternion,
                         *face.euler, *face.translation)
    confidence = [float(point[2]) for point in face.lms]
    xy = [float(v) for row, col, _ in face.lms for v in (col, row)]
    xyz = [float(v) for x, y, z in face.pts_3d for v in (x, -y, -z)]
    features = [float((face.current_features or {}).get(k, 0)) for k in FEATURES]
    values = confidence + xy + xyz + features
    return header + struct.pack(f'<{len(values)}f', *values)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--osf-root', type=Path, required=True)
    parser.add_argument('--video', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--model', type=int, default=3)
    args = parser.parse_args()
    sys.path.insert(0, str(args.osf_root.resolve()))
    import cv2
    from tracker import Tracker

    capture = cv2.VideoCapture(str(args.video))
    fps = capture.get(cv2.CAP_PROP_FPS)
    if not capture.isOpened() or abs(fps - ANIMATION_FPS) > .01:
        raise ValueError('Prepare a constant 24 fps video before tracking')
    width = int(capture.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(capture.get(cv2.CAP_PROP_FRAME_HEIGHT))
    tracker = Tracker(width, height, model_type=args.model, max_faces=1,
                      max_threads=2, silent=True, no_gaze=False,
                      static_model=True, max_feature_updates=0,
                      model_dir=str(args.osf_root.resolve() / 'models'))
    args.output.mkdir(parents=True, exist_ok=True)
    count = valid = 0
    inference_seconds = 0
    with (args.output / 'packets.jsonl').open('w') as output:
        while True:
            ok, frame = capture.read()
            if not ok:
                break
            start = time.perf_counter()
            faces = tracker.predict(frame)
            inference_seconds += time.perf_counter() - start
            timestamp = count / ANIMATION_FPS
            packet = b''.join(pack_face(f, timestamp, width, height) for f in faces)
            measurements = decode_packet(packet, timestamp) if packet else []
            valid += int(any(m.valid for m in measurements))
            output.write(json.dumps(dict(frame=count, time=timestamp,
                                         packet=base64.b64encode(packet).decode())) + '\n')
            count += 1
    capture.release()
    revision = subprocess.check_output(['git', '-C', str(args.osf_root),
                                       'rev-parse', 'HEAD'], text=True).strip()
    summary = dict(frames=count, valid_frames=valid, fps=ANIMATION_FPS,
                   model=args.model, osf_revision=revision,
                   inference_seconds=inference_seconds,
                   inference_fps=count / max(inference_seconds, 1e-9),
                   note='Offline chronological inference; throughput is not device latency.')
    (args.output / 'tracking.json').write_text(json.dumps(summary, indent=2) + '\n')
    print(json.dumps(summary))
    if valid < 48:
        raise RuntimeError('Fewer than two seconds of usable face tracking; choose a clearer clip.')


if __name__ == '__main__':
    main()
