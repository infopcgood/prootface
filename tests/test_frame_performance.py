import unittest

from prootface.model import Style,pose_from_controls
from prootface.performance import SpeakingExample
from prootface.timing import ANIMATION_FPS


class FramePerformanceTests(unittest.TestCase):
    def setUp(self):
        phones=[('pau',0,.2),('m',.2,.23),('ey',.23,.40),('b',.40,.44),
                ('iy',.44,.55),('w',.55,.62),('uw',.62,.70),('v',.70,.80),('pau',.80,1)]
        self.example=SpeakingExample(dict(text='Timing test',segments=[
            dict(phone=p,start=a,end=b,word='test') for p,a,b in phones]))

    def test_working_rate_is_24_and_short_closures_get_two_frames(self):
        self.assertEqual(ANIMATION_FPS,24)
        controls,events=self.example.keyed_frames()
        for event in events:
            if event['phone'] in ('m','b'):
                self.assertGreaterEqual(len(event['exposed_frames']),2)
                for frame in event['exposed_frames']:
                    p=pose_from_controls(controls[frame],Style())
                    self.assertEqual(p['aperture'],0)
                    self.assertEqual(p['blend_closed'],1)

    def test_vowel_key_pose_is_held_and_lip_bite_is_distinct(self):
        controls,events=self.example.keyed_frames()
        event=next(e for e in events if e['phone']=='ey')
        self.assertGreaterEqual(len(event['exposed_frames']),2)
        weights=[]
        for frame in event['exposed_frames']:
            p=pose_from_controls(controls[frame],Style())
            weights.append((p['blend_open'],p['blend_wide'],p['blend_round']))
        self.assertTrue(all(w==weights[0] for w in weights))
        self.assertGreater(weights[0][1],.9)
        bite=next(e for e in events if e['phone']=='v')
        p=pose_from_controls(controls[bite['exposed_frames'][0]],Style())
        self.assertEqual(p['blend_bite'],1)
        self.assertEqual(p['blend_round'],0)

    def test_authoring_is_repeatable_and_bounded(self):
        first=self.example.keyed_frames();self.assertEqual(first,self.example.keyed_frames())
        for controls in first[0]:
            for key,value in controls.items():
                self.assertTrue((-1 if key.startswith(('corner','brow')) else 0)<=value<=1)
