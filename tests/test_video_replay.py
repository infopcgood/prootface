import base64
import unittest
from types import SimpleNamespace

from prootface.calibration import Profile
from prootface.openseeface import decode_packet
from prootface.rig import front_motion_weights
from test_core import packet
from tools.replay_video import estimate_sample_profile, replay
from tools.track_video import pack_face


class VideoReplayTests(unittest.TestCase):
    def test_real_tracker_serializer_preserves_coordinates_and_features(self):
        points = [[0., 0., 1.] for _ in range(68)]
        points[58], points[62] = [200., 100., 1.], [200., 200., 1.]
        for a, b, col in ((59, 65, 120), (60, 64, 150), (61, 63, 180)):
            points[a], points[b] = [195., col, 1.], [205., col, 1.]
        face = SimpleNamespace(id=0, success=True, pnp_error=.01,
                               quaternion=[0, 0, 0, 1], euler=[0]*3,
                               translation=[0]*3, eye_blink=[.3, .8],
                               lms=points, pts_3d=[[0, 0, 0]]*70,
                               current_features={'mouth_open': .7})
        measured = decode_packet(pack_face(face, 2, 640, 480), 2)[0]
        self.assertTrue(measured.valid)
        self.assertAlmostEqual(measured.aperture_ratio, .1)
        self.assertAlmostEqual(measured.features['mouth_open'], .7, places=6)
        self.assertAlmostEqual(measured.eye_left, .8, places=6)

    def test_replay_prefix_is_independent_of_later_measurements(self):
        rows = [dict(frame=i, time=i/24, packet=base64.b64encode(
            packet(opening=.8, gap=20 if i % 5 else 1)).decode()) for i in range(48)]
        prefix = replay(rows, Profile(), 0, 1, 0)
        suffix = [dict(frame=i, time=i/24, packet='') for i in range(24, 48)]
        longer = replay(rows[:24] + suffix, Profile(), 0, 2, 0)
        self.assertEqual(prefix, longer[:24])
        self.assertFalse(longer[-1]['tracking'])
        self.assertEqual(longer[-1]['pose']['accent'], 0)

    def test_sample_profile_is_labeled_approximate_and_needs_valid_input(self):
        measurements = [decode_packet(packet(gap=1+i % 20), i/24)[0] for i in range(72)]
        profile = estimate_sample_profile(measurements)
        self.assertFalse(profile.calibrated)
        self.assertGreater(profile.open_aperture, profile.closed_aperture)
        with self.assertRaises(ValueError):
            estimate_sample_profile(measurements[:10])

    def test_front_guide_uses_mouth_bounds_and_same_position_weights(self):
        rig = dict(positions=[-100,0,0, 0,0,0, .2,0,0, 1,0,0, 100,0,0, 0,0,0],
                   targets={'open': {'indices': [1,2,3,5]}})
        weights = front_motion_weights(rig)
        self.assertEqual(weights[1], 1)
        self.assertEqual(weights[1], weights[5])
        self.assertGreater(weights[2], 0)
        self.assertLess(weights[2], 1)
        self.assertEqual(weights[3], 0)


if __name__ == '__main__':
    unittest.main()
