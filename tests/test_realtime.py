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
