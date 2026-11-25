import copy
import unittest

from prootface.rig import split_at_horizontal_boundaries


def square():
    return dict(positions=[-1,-1,-1, 1,-1,1, 1,1,1, -1,1,-1],
                uvs=[0,0, 1,0, 1,1, 0,1], front_weights=[0,1,1,0],
                parts=[dict(textured=False,indices=[0,1,2,0,2,3])],
                targets={'open':dict(indices=[0,1,2,3],
                                     deltas=[-2,-1,0, 2,-1,0, 2,1,0, -2,1,0])})


class RigBoundaryTests(unittest.TestCase):
    def test_cut_preserves_surface_area_winding_and_original_guide_ids(self):
        rig=square();original=rig['positions'][:]
        split_at_horizontal_boundaries(rig,[0])
        self.assertEqual(rig['positions'][:len(original)],original)
        area=0
        p=rig['positions'];indices=rig['parts'][0]['indices']
        for j in range(0,len(indices),3):
            a,b,c=[p[3*i:3*i+3] for i in indices[j:j+3]]
            signed=((b[0]-a[0])*(c[1]-a[1])-(b[1]-a[1])*(c[0]-a[0]))/2
            self.assertGreater(signed,0);area+=signed
            self.assertFalse(min(a[1],b[1],c[1])<0<max(a[1],b[1],c[1]))
        self.assertAlmostEqual(area,4)
        # The shared diagonal intersects once, with a vertex reused on both sides.
        center=[i for i in range(len(p)//3) if p[i*3:i*3+2]==[0,0]]
        self.assertEqual(len(center),1)
        self.assertGreater(indices.count(center[0]),2)

    def test_new_vertices_interpolate_uv_depth_front_weight_and_source_delta(self):
        rig=square();split_at_horizontal_boundaries(rig,[0,.2])
        target=rig['targets']['open'];deltas=dict(zip(target['indices'],
                [target['deltas'][j:j+3] for j in range(0,len(target['deltas']),3)]))
        for i in range(4,len(rig['positions'])//3):
            x,y,z=rig['positions'][i*3:i*3+3]
            u,v=rig['uvs'][i*2:i*2+2]
            self.assertAlmostEqual(z,x)
            self.assertAlmostEqual(u,(x+1)/2);self.assertAlmostEqual(v,(y+1)/2)
            self.assertAlmostEqual(rig['front_weights'][i],u)
            for value,expected in zip(deltas.get(i,[0,0,0]),[2*x,y,0]):
                self.assertAlmostEqual(value,expected)

    def test_upper_partition_can_remain_exactly_fixed_under_lower_only_motion(self):
        rig=square();split_at_horizontal_boundaries(rig,[0,.2])
        before=copy.deepcopy(rig)
        for i in range(len(rig['positions'])//3):
            y=rig['positions'][i*3+1]
            rig['positions'][i*3]-=max(0,min(1,(.2-y)/.2))
        indices=rig['parts'][0]['indices'];upper=0
        for j in range(0,len(indices),3):
            triangle=indices[j:j+3]
            if all(before['positions'][i*3+1]>=.2-1e-10 for i in triangle):
                upper+=1
                for i in triangle:
                    self.assertEqual(rig['positions'][i*3:i*3+3],before['positions'][i*3:i*3+3])
        self.assertGreater(upper,0)


if __name__=='__main__':unittest.main()
