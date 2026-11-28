"""Expression selection, context-dependent geometry and speech independence."""
from copy import deepcopy
import importlib.util
import json
from pathlib import Path
import tempfile
import time
import unittest
import urllib.error
import urllib.request

from prootface.expression_rig import compile_expression_sets
from prootface.expressions import ExpressionController, ExpressionRig, EXPRESSIONS
from prootface.model import Animator, NEUTRAL, Style, pose_from_controls
from prootface.server import Application, start_http
from test_core import packet

RENDER_DEPS = bool(importlib.util.find_spec('numpy') and importlib.util.find_spec('PIL'))


def character_fixture():
    return dict(schema=2, positions=[0,0,0, 1,0,0, 0,1,0, 0,2,0], uvs=[0,0]*4,
        parts=[dict(indices=[0,1,2],textured=True)],
        front_weights=[1,.5,0,0],
        targets=dict(open=dict(indices=[1],deltas=[0,-.5,0]),
                     round=dict(indices=[1],deltas=[-.2,-.2,0]),
                     wide=dict(indices=[1],deltas=[.2,-.25,0]),
                     smile=dict(indices=[1],deltas=[0,.1,0]),
                     eye_left=dict(indices=[3],deltas=[0,-.2,0]),
                     eye_right=dict(indices=[3],deltas=[0,-.2,0])),
        view=dict(zoom=1,offset=[0,0]))


def rig_fixture():
    c = character_fixture()
    # Include an additional upper mouth point to establish nonzero field extent.
    c['targets']['open'] = dict(indices=[1,2], deltas=[0,-.5,0, 0,.1,0])
    definitions = {}
    for name in EXPRESSIONS[1:]:
        definitions[name] = dict(eyes=dict(left='eye_left',right='eye_right'), mouth={
            'rest': dict(sources=dict(smile=.5)),
            'open': dict(sources=dict(smile=.8)),
            'round': dict(sources=dict(smile=.1)),
            'wide': dict(sources=dict(smile=1.)),
        })
    compile_expression_sets(c, definitions)
    return c


class ExpressionTests(unittest.TestCase):
    def test_external_selection_latches_and_repeated_messages_do_not_restart(self):
        e = ExpressionController()
        e.select('happy', 0)
        before = e.sample(.1)['mouth']
        e.select('happy', .1)
        after = e.sample(.1)['mouth']
        self.assertEqual(before, after)
        self.assertEqual(e.sample(.2)['mouth']['happy'], 1)
        self.assertEqual(e.sample(100)['mouth']['happy'], 1)

    def test_interrupted_crossfades_are_continuous_and_convex(self):
        e = ExpressionController()
        e.select('happy', 0)
        current = e.sample(.1)
        e.select('angry', .1)
        self.assertEqual(e.sample(.1), current)
        for i in range(1, 50):
            weights = e.sample(.1+i/24)
            for values in weights.values():
                self.assertAlmostEqual(sum(values.values()), 1)
                self.assertTrue(all(0 <= value <= 1 for value in values.values()))
        self.assertEqual(weights['mouth']['angry'], 1)

    def test_parts_are_independent_and_timed_override_returns_to_latched_choice(self):
        e = ExpressionController()
        e.select('happy', 0, transition=0)
        e.select('angry', 1, part='eyes', hold=.3, transition=.1)
        e.select('angry', 1.2, part='eyes', hold=.3, transition=.1)
        weights = e.sample(1.2)
        self.assertEqual(weights['eyes']['angry'], 1)
        self.assertEqual(weights['mouth']['happy'], 1)
        self.assertEqual(e.sample(1.41)['eyes']['happy'], 1)

    def test_invalid_commands_and_backwards_time_preserve_state(self):
        e = ExpressionController()
        e.select('sad', 1)
        before = deepcopy(e.__dict__)
        for kwargs in (dict(name='typo', now=2), dict(name='happy',now=2,part='ears'),
                       dict(name='happy',now=2,hold=float('nan')),
                       dict(name='happy',now=2,transition=-1), dict(name='happy',now=.5)):
            with self.assertRaises(ValueError):
                e.select(**kwargs)
            self.assertEqual(e.__dict__, before)

    def test_old_characters_advertise_only_neutral_and_reject_missing_banks(self):
        rig = ExpressionRig(character_fixture())
        self.assertEqual(rig.available, ('neutral',))
        with self.assertRaises(ValueError):
            ExpressionController(rig.available).select('happy', 0)
        broken = rig_fixture()
        del broken['targets'][broken['expression_sets']['sad']['open']]
        with self.assertRaises(ValueError):
            ExpressionRig(broken)

    @unittest.skipUnless(RENDER_DEPS, 'Optional renderer dependencies unavailable')
    def test_banks_reconstruct_distinct_complete_endpoints(self):
        c = rig_fixture()
        from prootface.offscreen import CompiledMesh
        mesh = CompiledMesh(c)
        rig = ExpressionRig(c)
        e = ExpressionController(rig.available)
        e.select('happy', 0, part='mouth', transition=0)
        weights = e.sample(0)
        for phase, controls, lift in (
                ('rest', NEUTRAL, .05),
                ('open', dict(opening=1,seal=0), .08),
                ('round', dict(opening=1,rounding=1,seal=0), .01),
                ('wide', dict(opening=1,spread=1,seal=0), .1)):
            raw = pose_from_controls(controls, Style(front_motion_scale=1,rounding_reach=0))
            selected = mesh.vertices(rig.compose(raw, weights))
            neutral = mesh.vertices(raw)
            self.assertAlmostEqual(float(selected[1,1]-neutral[1,1]), lift, places=6, msg=phase)
            self.assertTrue((selected[3] == neutral[3]).all())
        # Endpoint-specific corrections are not one fixed smile offset.
        self.assertNotEqual(c['targets']['expr_happy_open'], c['targets']['expr_happy_round'])

    @unittest.skipUnless(RENDER_DEPS, 'Optional renderer dependencies unavailable')
    def test_authored_shapes_survive_front_restraint_and_cancel_at_each_endpoint(self):
        from prootface.offscreen import CompiledMesh
        c = rig_fixture()
        mesh = CompiledMesh(c)
        rig = ExpressionRig(c)
        e = ExpressionController(rig.available)
        e.select('happy', 0, part='mouth', transition=0)
        for restraint in (0, .8, 1):
            for phase, lift in (('open',.08), ('round',.01), ('wide',.1)):
                raw = {'blend_'+phase:1, 'front_motion_scale':restraint}
                neutral = mesh.vertices(raw)
                selected = mesh.vertices(rig.compose(raw,e.sample(0)))
                self.assertAlmostEqual(float(selected[1,1]-neutral[1,1]),lift,places=6)

    @unittest.skipUnless(RENDER_DEPS, 'Optional renderer dependencies unavailable')
    def test_only_articulation_correction_uses_front_restraint(self):
        from prootface.offscreen import CompiledMesh
        c = character_fixture()
        c['targets']['open'] = dict(indices=[1,2],deltas=[0,-.5,0,0,.1,0])
        definitions = {'happy':dict(eyes=dict(left='eye_left',right='eye_right'),mouth={
            phase:dict(sources={'smile':.5},motion_scale=[1,1.2,1])
            for phase in ('rest','open','round','wide')})}
        compile_expression_sets(c,definitions)
        bank = c['expression_sets']['happy']
        self.assertIn(bank['open_motion'],c['front_targets'])
        self.assertNotIn(bank['open'],c['front_targets'])
        rig = ExpressionRig(c)
        e = ExpressionController(rig.available)
        e.select('happy',0,transition=0)
        mesh = CompiledMesh(c)
        for restraint,expected in ((0,0),(1,-.05)):
            raw = dict(blend_open=1,front_motion_scale=restraint)
            delta = mesh.vertices(rig.compose(raw,e.sample(0)))-mesh.vertices(raw)
            self.assertAlmostEqual(float(delta[1,1]),expected,places=6)
        del c['targets'][bank['open_motion']]
        with self.assertRaises(ValueError):
            ExpressionRig(c)

    def test_curve_only_bank_cannot_silently_replace_authored_mouth_sources(self):
        c = character_fixture()
        c['targets']['open'] = dict(indices=[1,2],deltas=[0,-.5,0,0,.1,0])
        definitions = {'happy':dict(eyes=dict(left='eye_left',right='eye_right'),mouth={
            phase:dict(sources={},bend=.1)
            for phase in ('rest','open','round','wide')})}
        with self.assertRaisesRegex(ValueError,'authored mouth source'):
            compile_expression_sets(c,definitions)

    def test_neutral_preserves_existing_pose_and_closures_disable_all_context_openings(self):
        rig = ExpressionRig(rig_fixture())
        e = ExpressionController(rig.available)
        raw = pose_from_controls(dict(opening=.8,rounding=.4,corner_left=.8,seal=0), Style())
        neutral = rig.compose(raw, e.sample(0))
        self.assertEqual({k:neutral[k] for k in raw}, raw)
        for name in EXPRESSIONS[1:]:
            e.select(name, 1, transition=0)
            pose = rig.compose(pose_from_controls(dict(opening=1,seal=1), Style()), e.sample(1))
            self.assertEqual(pose['aperture'], 0)
            for bank in rig.banks.values():
                for phase in ('open','round','wide'):
                    self.assertEqual(pose['blend_'+bank[phase]], 0)

    def test_full_blinks_override_expression_eye_geometry(self):
        rig = ExpressionRig(rig_fixture())
        e = ExpressionController(rig.available)
        e.select('angry', 0, transition=0)
        pose = rig.compose(pose_from_controls(dict(eye_left=0,eye_right=1), Style()), e.sample(0))
        self.assertEqual(pose['blend_eye_left'], 0)
        self.assertEqual(pose['blend_eye_right'], 1)
        self.assertEqual(pose['blend_blink_left'], 1)

    def test_tracking_loss_keeps_latched_expression_while_mouth_relaxes(self):
        with tempfile.TemporaryDirectory() as root:
            app = Application(Path(root)/'profile.json')
            app.configure_character(rig_fixture())
            app.mode = 'live'
            app.select_expression('angry', 0, transition=0)
            for i in range(24):
                app.receive(packet(gap=25), i/24)
                app.tick(i/24)
            for i in range(24,72):
                app.tick(i/24)
            self.assertFalse(app.snapshot['tracking'])
            self.assertEqual(app.snapshot['expression']['parts']['mouth']['selected'], 'angry')
            self.assertLess(app.snapshot['pose']['aperture'], .0001)
            self.assertEqual(app.snapshot['pose']['blend_expr_angry_rest'], 1)

    def test_http_button_changes_expression_without_switching_measurement_mode(self):
        with tempfile.TemporaryDirectory() as root:
            app = Application(Path(root)/'profile.json')
            app.configure_character(rig_fixture())
            app.mode = 'live'
            server, thread = start_http(app,'127.0.0.1',0,Path(root)/'character.json')
            try:
                url = f'http://127.0.0.1:{server.server_port}/api/expression'
                for payload, expected in (({'expression':'angry'},200), ({'expression':'missing'},400)):
                    request = urllib.request.Request(url, json.dumps(payload).encode(),
                                                     {'Content-Type':'application/json'})
                    try:
                        response = urllib.request.urlopen(request,timeout=2)
                    except urllib.error.HTTPError as exc:
                        response = exc
                    with response:
                        self.assertEqual(response.status, expected)
                with app.lock:
                    app.tick(time.monotonic())
                self.assertEqual(app.mode,'live')
                self.assertEqual(app.snapshot['expression']['parts']['mouth']['selected'],'angry')
            finally:
                app.stop.set();server.shutdown();server.server_close();thread.join(2)
