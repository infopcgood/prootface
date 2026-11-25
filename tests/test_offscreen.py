import ctypes.util
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest

AVAILABLE=bool(importlib.util.find_spec('numpy') and importlib.util.find_spec('PIL') and ctypes.util.find_library('EGL'))
if AVAILABLE:
    import numpy as np
    from PIL import Image
    from prootface.offscreen import CompiledMesh, OffscreenRenderer
    from unittest.mock import patch


def write_fixture(root):
    # Original test geometry: two colored anatomical surfaces sharing a silhouette.
    points=[[-.6,-.6,.8],[.9,-.6,.8],[-.6,.6,.8],
            [-.6,-.6,-.8],[.9,-.6,-.8],[-.6,.6,-.8]]
    rig=dict(schema=2,positions=[v for p in points for v in p],uvs=[.25,.5]*3+[.75,.5]*3,
             parts=[dict(name='test',textured=True,indices=[0,1,2,3,4,5])],
             targets={'open':dict(indices=[0,1,2],deltas=[0,-.2,0]*3)},
             view=dict(zoom=1,offset=[0,0]),anatomical_left_sign=1)
    path=Path(root)/'character.json';path.write_text(json.dumps(rig))
    image=Image.new('RGB',(2,1));image.putdata([(255,0,0),(0,255,0)]);image.save(path.with_suffix('.png'))
    return path


@unittest.skipUnless(AVAILABLE,'Optional EGL/NumPy/Pillow renderer dependencies unavailable')
class OffscreenTests(unittest.TestCase):
    def test_invalid_sparse_indices_and_front_weights_are_rejected(self):
        with tempfile.TemporaryDirectory() as root:
            original = json.loads(write_fixture(root).read_text())
            for indices in ([.5, 1, 2], [True, 1, 2], [0, 0, 2], [0, 1, 99]):
                character = {**original, 'targets': {
                    'open': {'indices': indices, 'deltas': [0, -.2, 0]*3}}}
                with self.subTest(indices=indices), self.assertRaises(ValueError):
                    CompiledMesh(character)
            with self.assertRaises(ValueError):
                CompiledMesh({**original, 'front_weights': [-1]*6})

    def test_context_is_released_even_when_make_current_fails_during_close(self):
        with tempfile.TemporaryDirectory() as root:
            renderer = OffscreenRenderer(write_fixture(root), 16, 16)
            display = renderer.display
            with patch.object(renderer, '_current', side_effect=RuntimeError('context lost')):
                with self.assertRaisesRegex(RuntimeError, 'context lost'):
                    renderer.close()
            self.assertTrue(renderer.closed)
            self.assertNotIn(display, OffscreenRenderer._display_refs)
            renderer.close()

    def test_depth_anatomical_sides_one_mirror_and_bgr_output(self):
        with tempfile.TemporaryDirectory() as root:
            with OffscreenRenderer(write_fixture(root),64,64) as renderer:
                frame=renderer.render_atlas({})
                self.assertEqual(frame.shape,(64,128,3));self.assertEqual(frame.dtype,np.uint8)
                left,right=frame[:,:64],frame[:,64:]
                red=(left[:,:,2]>240)&(left[:,:,1]<10);green=(right[:,:,1]>240)&(right[:,:,2]<10)
                self.assertGreater(red.sum(),50);self.assertGreater(green.sum(),50)
                self.assertFalse((left[:,:,1]>240).any());self.assertFalse((right[:,:,2]>240).any())
                self.assertAlmostEqual(np.where(red)[1].mean()+np.where(green)[1].mean(),63,delta=1)
                self.assertAlmostEqual(np.where(red)[0].mean(),np.where(green)[0].mean(),delta=1)
                moved=renderer.render_atlas({'blend_open':1})
                moved_green=(moved[:,64:,1]>240)&(moved[:,64:,2]<10)
                self.assertTrue(np.array_equal(green,moved_green))
                self.assertFalse(np.array_equal(left,moved[:,:64]))
            renderer.close()
            with self.assertRaises(RuntimeError):renderer.render_atlas({})
