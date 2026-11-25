import unittest

from prootface.model import Animator,NEUTRAL,Style,pose_from_controls


class MorphPoseTests(unittest.TestCase):
    def test_authored_mouth_basis_is_convex_and_contact_suppresses_opening(self):
        for opening in (0,.1,.5,1):
            for rounding in (0,.5,1):
                for spread in (0,.5,1):
                    for seal in (0,.5,1):
                        p=pose_from_controls(dict(opening=opening,rounding=rounding,spread=spread,seal=seal),Style())
                        weights=[p['blend_'+key] for key in ('open','round','wide')]
                        self.assertTrue(all(0<=w<=1 for w in weights))
                        self.assertLessEqual(sum(weights),1+1e-12)
                        if seal==1:
                            self.assertEqual(sum(weights),0)

    def test_articulation_response_preserves_endpoints_and_readable_middle(self):
        rest=pose_from_controls(NEUTRAL,Style())
        full=pose_from_controls(dict(opening=1,seal=0),Style())
        middle=pose_from_controls(dict(opening=.4,seal=0),Style())
        self.assertEqual(rest['blend_open'],0)
        self.assertEqual(full['blend_open'],1)
        self.assertGreater(middle['blend_open'],middle['aperture'])
        self.assertLessEqual(middle['blend_open'],1)

    def test_contact_release_does_not_swallow_short_opening(self):
        animator=Animator()
        for i in range(60):animator.step(dict(opening=.6,seal=1),i/60)
        expected=pose_from_controls(dict(opening=.6,seal=0),Style())['aperture']
        first=animator.step(dict(opening=.6,seal=0),1)
        second=animator.step(dict(opening=.6,seal=0),1+1/60)
        self.assertGreater(first['aperture'],expected*.85)
        self.assertGreater(second['aperture'],expected*.97)

    def test_family_contrast_pushes_dominant_shape_without_exceeding_basis(self):
        p=pose_from_controls(dict(opening=.6,spread=.7,seal=0),Style())
        self.assertGreater(p['blend_wide']/(p['blend_open']+p['blend_wide']),.88)
        for seal in (0,.3,.7,1):
            p=pose_from_controls(dict(opening=.8,rounding=1,bite=.7,sibilant=.8,
                                     lip_press=1,seal=seal),Style())
            total=sum(p['blend_'+key] for key in ('open','round','wide','bite',
                                                'sibilant','postalveolar','rhotic','closed'))
            self.assertLessEqual(total,1+1e-12)
