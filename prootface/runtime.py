"""Bounded latest-pose handoff; the graphics context belongs to its worker."""
from dataclasses import dataclass
import threading


@dataclass(frozen=True)
class RenderedFrame:
    sequence: int
    pose_time: float
    pixels: object


class RenderWorker:
    """Create/render/close on one thread, with one pending and one ready frame."""

    def __init__(self, renderer_factory):
        self._condition = threading.Condition()
        self._pending = None
        self._completed = None
        self._stopping = False
        self._error = None
        self.info = {}
        self.dropped_pending = 0
        self._ready = threading.Event()
        self._thread = threading.Thread(
            target=self._run, args=(renderer_factory,), daemon=True,
            name='prootface-render',
        )
        self._thread.start()
        if not self._ready.wait(15):
            self.close()
            raise RuntimeError('Offscreen renderer did not initialize')
        try:
            self.check()
        except RuntimeError:
            self.close()
            raise

    def check(self):
        """Raise RuntimeError, chained to the original renderer failure."""
        with self._condition:
            if self._error is not None:
                raise RuntimeError('Offscreen render worker failed') from self._error

    def submit(self, sequence, pose_time, pose):
        """Replace queued work; pose_time must use the caller's monotonic clock."""
        with self._condition:
            self.check()
            if self._stopping:
                raise RuntimeError('Render worker is closed')
            if self._pending is not None:
                self.dropped_pending += 1
            self._pending = (sequence, pose_time, dict(pose))
            self._condition.notify()

    def poll(self):
        """Take the latest completed frame once, or return None without waiting."""
        with self._condition:
            self.check()
            result = self._completed
            self._completed = None
            return result

    def _fail(self, error):
        with self._condition:
            if self._error is None:
                self._error = error

    def _run(self, factory):
        renderer = None
        try:
            renderer = factory()
            self.info = dict(renderer.info)
            self._ready.set()
            while True:
                with self._condition:
                    self._condition.wait_for(
                        lambda: self._stopping or self._pending is not None
                    )
                    if self._stopping:
                        break
                    sequence, now, pose = self._pending
                    self._pending = None
                frame = RenderedFrame(sequence, now, renderer.render_atlas(pose))
                with self._condition:
                    if not self._stopping:
                        self._completed = frame
        except BaseException as exc:
            self._fail(exc)
            self._ready.set()
        finally:
            if renderer is not None:
                try:
                    renderer.close()
                except BaseException as exc:
                    self._fail(exc)

    def close(self):
        """Discard pending work and join the worker; safe to call repeatedly.

        Render/cleanup failures remain available through check(). A join timeout
        raises RuntimeError because graphics calls cannot be safely interrupted.
        """
        with self._condition:
            self._stopping = True
            self._pending = None
            self._completed = None
            self._condition.notify_all()
        self._thread.join(10)
        if self._thread.is_alive():
            raise RuntimeError('Graphics worker did not stop')

    def __enter__(self):
        return self

    def __exit__(self, *_):
        self.close()
