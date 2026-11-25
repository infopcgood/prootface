"""OSFData adapter without a ROS dependency in the character core."""
from .openseeface import FEATURES, observation


def ros_feature_name(name):
    if name.endswith('_l'):
        return name[:-2]+'_left'
    if name.endswith('_r'):
        return name[:-2]+'_right'
    return name


def measurement_from_ros(message, received_at):
    """Use original 2D points and raw eye openness, not signed eye features.

    proto-ros2 transforms its 3D axes; the core does not need those coordinates.
    Sender wall time is retained only as metadata. Freshness uses receipt time.
    """
    try:
        return observation(received_at=received_at,sender_time=float(message.time),
            face_id=message.id,resolution=tuple(message.resolution),
            right_eye=float(message.right_eye_open),left_eye=float(message.left_eye_open),
            success=message.got_3d_points,confidence=tuple(message.confidence),
            xy=[(point.x,point.y) for point in message.points],
            features={k:float(getattr(message,ros_feature_name(k))) for k in FEATURES})
    except (AttributeError,KeyError,TypeError,OverflowError) as exc:
        raise ValueError('Malformed OSFData message') from exc
