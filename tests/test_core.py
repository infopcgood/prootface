import json
import math
from pathlib import Path
import struct
import tempfile
import unittest

from prootface.calibration import CalibrationSession, Profile, Range, SIGNALS
from prootface.model import Animator, NEUTRAL, Style, demo_controls, pose_from_controls, retarget
from prootface.openseeface import FEATURES, HEADER, RECORD_SIZE, decode_packet
from prootface.server import Application


def packet(face_id=0, opening=.6, gap=2.0):
    h=HEADER.pack(123456.0,face_id,640,480,.8,.9,1,.01,0,0,0,1,0,0,0,0,0,0)
    points=[(0.0,0.0)]*68
    points[58],points[62]=(100,200),(200,200)
    for a,b,x in ((59,65,120),(60,64,150),(61,63,180)):
        points[a],points[b]=(x,200-gap/2),(x,200+gap/2)
    values={k:0.0 for k in FEATURES};values['mouth_open']=opening
    return h+struct.pack('<68f',*([1.0]*68))+struct.pack('<136f',*(x for p in points for x in p))+struct.pack('<210f',*([0.0]*210))+struct.pack('<14f',*(values[k] for k in FEATURES))


class ProtocolTests(unittest.TestCase):
    def test_upstream_wire_offsets_and_landmark_pairs(self):
        data=packet(face_id=7)
        self.assertEqual(len(data),1785)
        self.assertEqual(RECORD_SIZE,1785)
        m=decode_packet(data,10.0)[0]
        self.assertEqual(m.face_id,7)
        self.assertEqual(m.received_at,10)
        self.assertAlmostEqual(m.features['mouth_open'],.6,places=6)
        self.assertAlmostEqual(m.eye_left,.9,places=6)
        self.assertAlmostEqual(m.eye_right,.8,places=6)
        self.assertAlmostEqual(m.aperture_ratio,.02,places=6)
        self.assertTrue(m.valid)

    def test_multi_face_packet(self):
        frames=decode_packet(packet(3)+packet(5),20)
        self.assertEqual([m.face_id for m in frames],[3,5])

    def test_malformed_and_nan_packets_rejected(self):
        for data in (b'',packet()[:-1],packet()+b'x'):
            with self.assertRaises(ValueError):decode_packet(data,1)
        data=bytearray(packet());struct.pack_into('<f',data,len(data)-8,float('nan'))
        with self.assertRaises(ValueError):decode_packet(data,1)


class CalibrationTests(unittest.TestCase):
    def test_signed_open_see_face_ranges(self):
        r=Range(.1,.9,-.7)
        self.assertAlmostEqual(r.normalize(.5),.5)
        self.assertAlmostEqual(r.normalize(-.3),-.5)
        self.assertEqual(r.normalize(-9),-1)
        self.assertEqual(r.normalize(9),1)

    def test_complete_session_is_robust_and_roundtrips(self):
        session=CalibrationSession()
        for stage in ('neutral','open','wide','narrow','smile'):
            session.begin(stage)
            for i in range(11):
                x={k:0.1 for k in SIGNALS}
                if stage=='open':x['open']=.9
                if stage=='wide':x['width']=.85
                if stage=='narrow':x['width']=-.75
                if stage=='smile':x['corner_left']=.8;x['corner_right']=.75
                if i==10:x['open']=99  # median and rest quantiles ignore a gross outlier
                session.add(x,.02 if stage!='open' else .3)
        profile=session.finish()
        self.assertTrue(profile.calibrated)
        self.assertAlmostEqual(profile.ranges['open'].positive,.9)
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'profile.json';profile.save(p)
            recovered=Profile.from_dict(json.loads(p.read_text()))
            self.assertEqual(recovered.to_dict(),profile.to_dict())

    def test_unusable_calibration_cannot_replace_profile(self):
        session=CalibrationSession()
        with self.assertRaises(ValueError):session.finish()
        for stage in ('neutral','open','wide','narrow','smile'):
            session.begin(stage)
            for _ in range(10):session.add({k:0.0 for k in SIGNALS},.02)
        with self.assertRaises(ValueError):session.finish()


class MotionTests(unittest.TestCase):
    def test_measured_contact_wins_over_drifting_open_feature(self):
        m=decode_packet(packet(opening=.9,gap=0),1)[0]
        controls=retarget(m,Profile())
        pose=pose_from_controls(controls,Style())
        self.assertEqual(controls['seal'],1)
        self.assertEqual(pose['aperture'],0)

    def test_speaking_smile_does_not_disappear_when_rounding(self):
        pose=pose_from_controls({**NEUTRAL,'opening':.6,'seal':0,'rounding':1,'corner_left':.8,'corner_right':.4},Style())
        self.assertGreater(pose['aperture'],0)
        self.assertGreater(pose['corner_left_render'],pose['corner_right_render'])
        self.assertGreater(pose['corner_right_render'],0)

    def test_asymmetry_is_applied_once(self):
        a=Animator();target={**NEUTRAL,'corner_left':1,'corner_right':0}
        for i in range(300):p=a.step(target,i/60)
        self.assertAlmostEqual(p['corner_left_render'],.85,places=3)
        self.assertAlmostEqual(p['corner_right_render'],.15,places=3)

    def test_close_is_immediate_and_reopening_does_not_overshoot(self):
        a=Animator()
        for i in range(60):a.step({**NEUTRAL,'opening':.8,'seal':0},i/60)
        closed=a.step({**NEUTRAL,'opening':.8,'seal':1},1)
        self.assertEqual(closed['aperture'],0)
        for i in range(1,30):
            p=a.step({**NEUTRAL,'opening':.4,'seal':0},1+i/60)
            self.assertTrue(0<=p['aperture']<=1)
            self.assertTrue(all(math.isfinite(v) for v in p.values()))

    def test_frame_rate_independence_and_stale_relaxation(self):
        results=[]
        for fps in (30,60,120):
            a=Animator()
            for i in range(2*fps):p=a.step({**NEUTRAL,'opening':.7,'seal':0},i/fps)
            results.append(p['aperture'])
            for i in range(2*fps,3*fps):p=a.step(NEUTRAL,i/fps,False)
            self.assertLess(p['aperture'],.001)
        self.assertLess(max(results)-min(results),.002)

    def test_synthetic_phrase_is_bounded_and_has_contact_holds(self):
        closures=0;openings=[]
        for i in range(1201):
            controls,_=demo_controls(i/200)
            self.assertTrue(all(math.isfinite(v) for v in controls.values()))
            self.assertTrue(all(0<=controls[k]<=1 for k in ('opening','seal','spread','rounding')))
            closures+=controls['seal']>.999
            openings.append(controls['opening'])
        self.assertGreater(closures,100)
        self.assertGreater(max(openings),.7)
        self.assertLess(max(abs(a-b) for a,b in zip(openings,openings[1:])),.06)

    def test_reject_backwards_time_without_mutating_state(self):
        a=Animator();a.step(NEUTRAL,2)
        with self.assertRaises(ValueError):a.step(NEUTRAL,1)


class ApplicationTests(unittest.TestCase):
    def test_live_face_selection_and_receive_clock_staleness(self):
        with tempfile.TemporaryDirectory() as d:
            app=Application(Path(d)/'cal.json',face_id=2)
            app.mode='live';app.receive(packet(1)+packet(2,gap=25),10)
            app.tick(10.1);self.assertTrue(app.snapshot['tracking'])
            app.tick(10.5);self.assertFalse(app.snapshot['tracking'])
            self.assertEqual(app.snapshot['received'],1)

    def test_manual_invalid_numeric_input_does_not_change_mode(self):
        with tempfile.TemporaryDirectory() as d:
            app=Application(Path(d)/'cal.json')
            with self.assertRaises(ValueError):app.command('/api/control',{'mode':'live','controls':{'opening':float('nan')}})
            self.assertEqual(app.mode,'demo')


if __name__=='__main__':unittest.main()
