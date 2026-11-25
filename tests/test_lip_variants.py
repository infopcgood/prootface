import copy
import unittest

from prootface.model import NEUTRAL, Style, pose_from_controls
from prootface.rig import add_mouth_variants


def fixture():
    # Two roots, rest tip, upper feature, and a coincident material/UV split.
    return dict(positions=[0,0,0, 2,0,0, 1,-1,0, 1,2,0, 1,-1,0],
                targets={'open':dict(indices=[0,1,2,4],deltas=[0,0,0, 0,0,0, 0,.8,0, 0,.8,0]),
                         'round':dict(indices=[0,1,2,4],deltas=[0,0,0, 0,0,0, 0,.8,0, 0,.8,0]),
                         'wide':dict(indices=[0,1,2,4],deltas=[0,0,0, 0,0,0, 0,.6,0, 0,.6,0])})


def dense(target, count):
    result = [[0,0,0] for _ in range(count)]
    for j,i in enumerate(target['indices']):
        result[i] = target['deltas'][j*3:j*3+3]
    return result


class LipVariantTests(unittest.TestCase):
    def test_spike_restores_relief_and_preserves_coincident_splits_and_roots(self):
        rig = fixture();before = copy.deepcopy(rig)
        add_mouth_variants(rig,dict(spike=dict(anchors=[0,1],tip=2)))
        delta = dense(rig['targets']['spike_open'],5)
        self.assertAlmostEqual(-1+.8+delta[2][1],-1)
        self.assertEqual(delta[2],delta[4])
        self.assertEqual(delta[0],[0,0,0]);self.assertEqual(delta[1],[0,0,0])
        self.assertEqual(delta[3],[0,0,0])
        self.assertEqual(rig['positions'],before['positions'])
        self.assertEqual(rig['targets']['open'],before['targets']['open'])

    def test_round_reach_moves_layers_together_and_keeps_upper_features_fixed(self):
        rig = fixture();add_mouth_variants(rig,dict(round_reach_fraction=.25))
        delta = dense(rig['targets']['round_reach'],5)
        self.assertEqual(delta[2],[-.5,0,0]);self.assertEqual(delta[2],delta[4])
        self.assertEqual(delta[3],[0,0,0])
        self.assertTrue(all(d[1:]==[0,0] for d in delta))

    def test_optional_spike_uses_same_articulation_and_contact_suppresses_variants(self):
        control=dict(opening=.8,rounding=1,seal=0)
        a=pose_from_controls(control,Style(lower_lip_spike=0))
        b=pose_from_controls(control,Style(lower_lip_spike=1))
        self.assertEqual(a['blend_round'],b['blend_round'])
        self.assertEqual(a['blend_spike_round'],0)
        self.assertEqual(b['blend_spike_round'],b['blend_round'])
        self.assertEqual(b['blend_round_reach'],1)
        closed=pose_from_controls(dict(control,seal=1),Style(lower_lip_spike=1))
        self.assertEqual(closed['blend_round_reach'],0)
        self.assertTrue(all(v==0 for k,v in closed.items() if k.startswith('blend_spike_')))
        neutral=pose_from_controls(NEUTRAL,Style(lower_lip_spike=1))
        self.assertEqual(neutral['blend_spike_open'],0)

    def test_missing_private_guide_preserves_existing_rig(self):
        rig=fixture();before=copy.deepcopy(rig);add_mouth_variants(rig,None)
        self.assertEqual(rig,before)
        with self.assertRaises(ValueError):
            add_mouth_variants(rig,dict(round_reach_fraction=float('nan')))


if __name__=='__main__':unittest.main()
