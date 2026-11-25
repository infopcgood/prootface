"""Decode the individually packed OpenSeeFace UDP protocol, not ARKit OSC.

Verified against emilianavt/OpenSeeFace facetracker.py blob
205b2fbc8ba2615c70a7029a9248082ca65627d9. Native pack calls on
little-endian upstream hosts yield 1785 bytes per face, without alignment.
The 66 face landmarks + 2 pupil landmarks are not dlib's 68-face-point layout.
"""

from dataclasses import dataclass
import math
import struct

FEATURES = (
    "eye_l", "eye_r", "eyebrow_steepness_l", "eyebrow_updown_l",
    "eyebrow_quirk_l", "eyebrow_steepness_r", "eyebrow_updown_r",
    "eyebrow_quirk_r", "mouth_corner_updown_l", "mouth_corner_inout_l",
    "mouth_corner_updown_r", "mouth_corner_inout_r", "mouth_open", "mouth_wide",
)
HEADER = struct.Struct("<di4fBf4f3f3f")
RECORD_SIZE = HEADER.size + (68 + 136 + 210 + 14) * 4


@dataclass(frozen=True)
class Measurement:
    received_at: float
    sender_time: float
    face_id: int
    features: dict[str, float]
    aperture_ratio: float | None
    confidence: float
    valid: bool
    eye_left: float = 1.0
    eye_right: float = 1.0

    def signals(self) -> dict[str, float]:
        return {
            "open": self.features["mouth_open"],
            "width": self.features["mouth_wide"],
            "corner_left": self.features["mouth_corner_updown_l"],
            "corner_right": self.features["mouth_corner_updown_r"],
            "brow_left": self.features["eyebrow_updown_l"],
            "brow_right": self.features["eyebrow_updown_r"],
        }


def observation(*, received_at, sender_time, face_id, resolution, right_eye,
                left_eye, success, confidence, xy, features) -> Measurement:
    """Common validation/aperture rules for wire input and decoded ROS data."""
    numbers = [received_at, sender_time, face_id, *resolution, right_eye, left_eye,
               *confidence, *(v for point in xy for v in point),
               *(features[k] for k in FEATURES)]
    if not all(math.isfinite(v) for v in numbers):
        raise ValueError('Non-finite OpenSeeFace observation')
    if (len(resolution)!=2 or min(resolution)<=0 or face_id<0 or int(face_id)!=face_id
            or len(confidence)!=68 or len(xy)!=68 or any(len(p)!=2 for p in xy)):
        raise ValueError('Invalid OpenSeeFace observation shape')
    mouth_conf = min(confidence[i] for i in range(58,66))
    span = math.dist(xy[58],xy[62])
    aperture = None
    if span>1.0 and mouth_conf>=.5:
        aperture = sum(math.dist(xy[a],xy[b]) for a,b in
                       ((59,65),(60,64),(61,63)))/(3*span)
    return Measurement(received_at,sender_time,int(face_id),dict(features),aperture,
                       mouth_conf,bool(success) and mouth_conf>=.5,
                       min(1.0,max(0.0,left_eye)),min(1.0,max(0.0,right_eye)))


def decode_packet(packet: bytes, received_at: float) -> list[Measurement]:
    if not packet or len(packet) % RECORD_SIZE or len(packet) // RECORD_SIZE >= 40:
        raise ValueError(f"Expected 1–39 OpenSeeFace records of {RECORD_SIZE} bytes")
    if not math.isfinite(received_at):
        raise ValueError("Invalid local receive time")
    result = []
    for offset in range(0, len(packet), RECORD_SIZE):
        h = HEADER.unpack_from(packet, offset)
        if not all(math.isfinite(v) for v in h):
            raise ValueError("Non-finite OpenSeeFace header")
        sender_time, face_id, width, height, right, left, success, _error, *_ = h
        if width <= 0 or height <= 0 or face_id < 0 or success not in (0, 1):
            raise ValueError("Invalid OpenSeeFace header")
        start = offset + HEADER.size
        confidence = struct.unpack_from("<68f", packet, start)
        points = struct.unpack_from("<136f", packet, start + 68 * 4)
        values = struct.unpack_from("<14f", packet, offset + RECORD_SIZE - 56)
        if not all(math.isfinite(v) for v in (*confidence, *points, *values)):
            raise ValueError("Non-finite OpenSeeFace measurement")
        xy = list(zip(points[0::2], points[1::2]))  # sender writes image x then y
        result.append(observation(received_at=received_at,sender_time=sender_time,
                    face_id=face_id,resolution=(width,height),right_eye=right,
                    left_eye=left,success=success,confidence=confidence,xy=xy,
                    features=dict(zip(FEATURES,values))))
    return result

