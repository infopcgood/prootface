"""Replay real OpenSeeFace packets through the existing live Application.

Only an earlier, disjoint section estimates sample normalization. This is an
approximation for existing footage, not the guided wearer calibration. The
evaluation frames cannot affect normalization or earlier animation frames.
"""
import argparse
import base64
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from prootface.calibration import Profile, Range, SIGNALS, percentile
from prootface.openseeface import decode_packet
from prootface.server import Application
from prootface.timing import ANIMATION_FPS


def estimate_sample_profile(measurements):
    good = [m for m in measurements if m.valid and m.aperture_ratio is not None]
    if len(good) < 48:
        raise ValueError('Need at least two seconds of valid earlier measurements')
    apertures = [m.aperture_ratio for m in good]
    low = percentile(apertures, .15)
    resting = [m for m in good if m.aperture_ratio <= low]
    ranges = {}
    for key in SIGNALS:
        values = [m.signals()[key] for m in good]
        rest = percentile([m.signals()[key] for m in resting], .5)
        if key == 'width':
            rest = percentile(values, .5)
        positive = max(rest + .15, percentile(values, .98))
        negative = min(rest - .15, percentile(values, .02))
        if key == 'open':
            negative = rest - 1
        ranges[key] = Range(rest, positive, negative)
    closed = percentile(apertures, .05) + .003
    opened = max(closed + .05, percentile(apertures, .98))
    return Profile(ranges, closed, opened, calibrated=False)


def replay(records, profile, start, end, warmup_start, lower_lip_spike=0.0):
    if not 0 <= warmup_start <= start < end:
        raise ValueError('Invalid replay interval')
    # No profile is read or written; all packet validation, staleness, contact
    # latching, retargeting and animation use the same Application as live UDP.
    app = Application(Path('/nonexistent/prootface-replay-profile'))
    app.profile = profile
    app.mode = 'live'
    app.animator.style.lower_lip_spike = lower_lip_spike
    output = []
    for row in records:
        timestamp = row['time']
        if timestamp < warmup_start:
            continue
        if timestamp >= end:
            break
        packet = base64.b64decode(row['packet'], validate=True)
        if packet:
            app.receive(packet, timestamp)
        app.tick(timestamp)
        if timestamp >= start:
            output.append(dict(frame=row['frame'], time=timestamp,
                               pose=app.snapshot['pose'],
                               tracking=app.snapshot['tracking'],
                               raw=app.snapshot['raw'],
                               aperture_ratio=app.snapshot['aperture_ratio']))
    return output


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--packets', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--calibration-start', type=float, default=4)
    parser.add_argument('--calibration-end', type=float, default=14)
    parser.add_argument('--start', type=float, default=16)
    parser.add_argument('--end', type=float, default=22)
    parser.add_argument('--lower-lip-spike', type=float, default=0.0)
    args = parser.parse_args()
    if not 0 <= args.lower_lip_spike <= 1:
        parser.error('Lower lip spike strength must be between zero and one')
    if not 0 <= args.calibration_start < args.calibration_end <= args.start:
        parser.error('Calibration must end before the evaluation interval')
    records = [json.loads(line) for line in args.packets.read_text().splitlines()]
    measurements = []
    for row in records:
        if args.calibration_start <= row['time'] < args.calibration_end and row['packet']:
            measurements.extend(decode_packet(base64.b64decode(row['packet']), row['time']))
    profile = estimate_sample_profile(measurements)
    frames = replay(records, profile, args.start, args.end, args.calibration_end,args.lower_lip_spike)
    expected = round((args.end - args.start) * ANIMATION_FPS)
    if len(frames) != expected:
        raise ValueError('Recording does not cover the complete evaluation interval')
    args.output.mkdir(parents=True, exist_ok=True)
    (args.output / 'profile.json').write_text(json.dumps(profile.to_dict(), indent=2))
    (args.output / 'poses.json').write_text(json.dumps([r['pose'] for r in frames]))
    (args.output / 'measurements.json').write_text(json.dumps(frames))
    summary = dict(fps=ANIMATION_FPS, frames=len(frames),
                   calibration=[args.calibration_start, args.calibration_end],
                   evaluation=[args.start, args.end],
                   tracked_frames=sum(r['tracking'] for r in frames),
                   lower_lip_spike=args.lower_lip_spike,
                   note='Real video measurements; earlier-section estimated calibration; causal live Application.')
    (args.output / 'replay.json').write_text(json.dumps(summary, indent=2))
    print(json.dumps(summary))


if __name__ == '__main__':
    main()
