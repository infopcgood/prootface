"""Regression tests for state preservation at input and command boundaries."""
from copy import deepcopy
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import urllib.error
import urllib.request

from prootface.calibration import Profile, SIGNALS, STAGES
from prootface.model import Animator, NEUTRAL, Style, pose_from_controls
from prootface.openseeface import decode_packet, observation
from prootface.server import Application, start_http
from test_core import packet


def complete_session(session):
    for stage in STAGES:
        session.begin(stage)
        values = dict.fromkeys(SIGNALS, 0.)
        if stage == 'open':
            values['open'] = .9
        elif stage == 'wide':
            values['width'] = .9
        elif stage == 'narrow':
            values['width'] = -.9
        elif stage == 'smile':
            values['corner_left'] = values['corner_right'] = .8
        for _ in range(8):
            session.add(values, .3 if stage == 'open' else .02)


class ValidationTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.app = Application(Path(self.temp.name) / 'profile.json')

    def test_rejected_calibration_commands_preserve_mode_and_capture(self):
        self.app.session.begin('neutral')
        for command in ({'stage': 'unknown'}, {}, {'stage': []}):
            with self.assertRaises(ValueError):
                self.app.command('/api/calibration/start', command)
            self.assertEqual(self.app.mode, 'demo')
            self.assertEqual(self.app.session.stage, 'neutral')
        with self.assertRaises(ValueError):
            self.app.command('/api/calibration/save', {})
        self.assertEqual(self.app.session.stage, 'neutral')
        self.assertFalse(self.app.profile.calibrated)

    def test_failed_profile_write_keeps_profile_capture_and_retry(self):
        complete_session(self.app.session)
        original = self.app.profile
        with patch.object(Profile, 'save', side_effect=OSError('disk full')):
            with self.assertRaises(OSError):
                self.app.command('/api/calibration/save', {})
        self.assertIs(self.app.profile, original)
        self.assertEqual(self.app.session.stage, 'smile')
        self.app.command('/api/calibration/save', {})
        self.assertIsNone(self.app.session.stage)
        self.assertTrue(json.loads(self.app.profile_path.read_text())['calibrated'])

    def test_http_profile_write_failure_is_a_json_error(self):
        complete_session(self.app.session)
        server, thread = start_http(self.app, '127.0.0.1', 0, Path(self.temp.name)/'character.json')
        try:
            request = urllib.request.Request(
                f'http://127.0.0.1:{server.server_port}/api/calibration/save',
                b'{}', {'Content-Type': 'application/json'},
            )
            with patch.object(Profile, 'save', side_effect=OSError('disk full')):
                with self.assertRaises(urllib.error.HTTPError) as caught:
                    urllib.request.urlopen(request, timeout=2)
                self.assertEqual(caught.exception.code, 500)
                self.assertIn('error', json.load(caught.exception))
        finally:
            self.app.stop.set()
            server.shutdown()
            server.server_close()
            thread.join(2)

    def test_style_validation_is_shared_by_python_and_http_commands(self):
        original = self.app.animator.style
        for bad in (True, '1', float('nan'), -1, 2):
            with self.subTest(bad=bad):
                with self.assertRaises(ValueError):
                    Style(rounding_reach=bad)
                with self.assertRaises(ValueError):
                    self.app.command('/api/style', {'rounding_reach': bad})
                self.assertIs(self.app.animator.style, original)

    def test_invalid_animation_target_does_not_advance_time_or_state(self):
        animator = Animator()
        animator.step(NEUTRAL, 1)
        original = deepcopy(animator.__dict__)
        for target in ({'opening': float('nan')}, {'opening': 'wide'}, {'typo': 1}):
            with self.assertRaises(ValueError):
                animator.step(target, 2)
            self.assertEqual(animator.__dict__, original)
        animator.step(NEUTRAL, 1.5)

    def test_invalid_profiles_cannot_reach_retargeting(self):
        for changes in ({'open_aperture': 0}, {'ranges': {}},
                        {'closed_aperture': float('nan')}, {'schema_version': 2}):
            with self.subTest(changes=changes), self.assertRaises(ValueError):
                Profile(**changes)
        for data in ({'schema_version': 1}, None):
            with self.assertRaises(ValueError):
                Profile.from_dict(data)

    def test_invalid_direct_family_and_accent_are_rejected(self):
        for kwargs in ({'family_index': 3}, {'family_index': True},
                       {'accent': float('nan')}, {'accent': 2}):
            with self.assertRaises(ValueError):
                pose_from_controls(NEUTRAL, Style(), **kwargs)

    def test_tracking_gap_does_not_replay_an_old_contact(self):
        self.app.mode = 'live'
        self.app.receive(packet(gap=25), 10)
        self.app.tick(10)
        self.app.receive(packet(gap=0), 10.01)
        self.assertTrue(self.app.contact_pending)
        self.app.receive(packet(gap=25), 11)
        self.app.tick(11)
        self.assertFalse(self.app.contact_pending)
        self.assertGreater(self.app.snapshot['pose']['aperture'], 0)

    def test_stale_tick_discards_contact_and_future_receipt_is_not_fresh(self):
        self.app.mode = 'live'
        self.app.receive(packet(gap=25), 10)
        self.app.tick(10)
        self.app.receive(packet(gap=0), 10.01)
        self.app.tick(11)
        self.assertFalse(self.app.contact_pending)
        self.app.receive(packet(gap=25), 12)
        self.app.tick(11.5)
        self.assertFalse(self.app.snapshot['tracking'])

    def test_older_measurement_cannot_replace_newer_selected_face(self):
        self.app.mode = 'live'
        self.app.receive(packet(gap=25), 10)
        newest = self.app.latest
        self.app.receive(packet(gap=0), 9)
        self.assertIs(self.app.latest, newest)
        self.assertFalse(self.app.contact_pending)

    def test_observation_shape_and_missing_features_report_value_error(self):
        measurement = decode_packet(packet(), 1)[0]
        args = dict(received_at=1, sender_time=2, face_id=0, resolution=(640, 480),
                    right_eye=1, left_eye=1, success=True, confidence=[1]*68,
                    xy=[(0, 0)]*68, features=measurement.features)
        for changes in ({'xy': [None]*68}, {'features': {}}, {'resolution': None},
                        {'success': 3}, {'face_id': True}):
            with self.subTest(changes=changes), self.assertRaises(ValueError):
                observation(**{**args, **changes})
