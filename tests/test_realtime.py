import unittest

from prootface.model import Animator,NEUTRAL
from prootface.timing import FRAME_SECONDS


class RealtimeAnimationTests(unittest.TestCase):
    def test_shape_family_gets_two_frames_but_jaw_keeps_following_input(self):
        a=Animator()
        first=a.step(dict(opening=.4,rounding=1,seal=0),0)
        self.assertEqual(a.family_index,1)
        second=a.step(dict(opening=.8,spread=1,seal=0),FRAME_SECONDS)
        self.assertEqual(a.family_index,1)
        self.assertGreater(second['aperture'],first['aperture'])
        a.step(dict(opening=.8,spread=1,seal=0),2*FRAME_SECONDS)
        self.assertEqual(a.family_index,2)

    def test_contact_interrupts_pose_hold_and_has_readable_exposure(self):
        a=Animator();a.step(dict(opening=.8,seal=0),0)
        closed=a.step(dict(opening=.8,seal=1),FRAME_SECONDS)
        held=a.step(dict(opening=.8,seal=0),2*FRAME_SECONDS)
        reopened=a.step(dict(opening=.8,seal=0),3*FRAME_SECONDS)
        self.assertEqual(closed['aperture'],0)
        self.assertEqual(held['aperture'],0)
        self.assertGreater(reopened['aperture'],0)

    def test_prefix_does_not_depend_on_future_input(self):
        prefix=[dict(opening=.5,rounding=1,seal=0),dict(opening=.8,spread=1,seal=0),NEUTRAL]
        outputs=[]
        for suffix in ([NEUTRAL]*5,[dict(opening=1,spread=1,seal=0)]*5):
            a=Animator();poses=[a.step(target,i*FRAME_SECONDS) for i,target in enumerate(prefix+suffix)]
            outputs.append(poses[:len(prefix)])
        self.assertEqual(outputs[0],outputs[1])

    def test_opening_hit_reaches_extreme_and_tightens_promptly(self):
        a=Animator()
        a.step(dict(opening=.18,seal=0),0)
        hit=a.step(dict(opening=.72,seal=0),FRAME_SECONDS)
        held=a.step(dict(opening=.72,seal=0),2*FRAME_SECONDS)
        tight=a.step(dict(opening=.18,seal=0),3*FRAME_SECONDS)
        amount=lambda p:sum(p['blend_'+k] for k in ('open','round','wide'))
        self.assertGreaterEqual(amount(hit),.99)
        self.assertGreaterEqual(amount(held),.99)
        self.assertLess(amount(tight),.08)
        self.assertEqual(tight['accent'],0)

    def test_gradual_large_opening_can_accent_without_lookahead(self):
        a=Animator();poses=[]
        for i,value in enumerate((.3,.35,.4,.45,.5,.55)):
            poses.append(a.step(dict(opening=value,seal=0),i*FRAME_SECONDS))
        self.assertEqual(poses[-2]['accent'],0)
        self.assertGreater(poses[-1]['accent'],0)

    def test_contact_and_tracking_loss_cancel_opening_accents(self):
        for tracked in (True,False):
            a=Animator();a.step(dict(opening=.8,seal=0),0)
            p=a.step(dict(opening=.8,seal=1),FRAME_SECONDS,tracked)
            self.assertEqual(p['accent'],0)
