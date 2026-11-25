import threading
import time
import unittest

from prootface.runtime import RenderWorker


class RuntimeTests(unittest.TestCase):
    def test_latest_only_handoff_and_context_thread_ownership(self):
        entered=threading.Event();release=threading.Event();calls=[];threads=[]
        class Renderer:
            info={'renderer':'test'}
            def __init__(self):threads.append(threading.get_ident())
            def render_atlas(self,pose):
                calls.append(pose['value']);threads.append(threading.get_ident())
                if len(calls)==1:entered.set();release.wait(2)
                return pose['value']
            def close(self):threads.append(threading.get_ident())
        worker=RenderWorker(Renderer)
        try:
            worker.submit(1,0,{'value':1});self.assertTrue(entered.wait(2))
            worker.submit(2,1,{'value':2});worker.submit(3,2,{'value':3});release.set()
            deadline=time.monotonic()+2;last=None
            while time.monotonic()<deadline:
                frame=worker.poll()
                if frame:last=frame
                if last and last.sequence==3:break
                time.sleep(.005)
            self.assertEqual(calls,[1,3]);self.assertEqual(last.pixels,3)
            self.assertEqual(worker.dropped_pending,1)
        finally:release.set();worker.close()
        self.assertEqual(len(set(threads)),1)
        self.assertNotEqual(threads[0],threading.get_ident())

    def test_startup_failures_propagate(self):
        def fail():raise ValueError('bad character')
        with self.assertRaises(RuntimeError):RenderWorker(fail)

    def test_render_and_cleanup_failures_preserve_the_first_cause(self):
        closed = threading.Event()
        class Renderer:
            info = {}
            def render_atlas(self, pose):
                raise ValueError('render failure')
            def close(self):
                closed.set()
                raise OSError('cleanup failure')
        worker = RenderWorker(Renderer)
        worker.submit(1, 0, {})
        self.assertTrue(closed.wait(2))
        worker.close()
        worker.close()
        with self.assertRaises(RuntimeError) as caught:
            worker.poll()
        self.assertEqual(str(caught.exception.__cause__), 'render failure')
        with self.assertRaises(RuntimeError):
            worker.submit(2, 1, {})
