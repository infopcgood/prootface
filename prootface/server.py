"""Local-only preview, calibration endpoints and OpenSeeFace receiver."""

from dataclasses import asdict
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
import mimetypes
from pathlib import Path
import socket
import threading
import time
from urllib.parse import urlsplit

from .calibration import CalibrationSession, Profile
from .expressions import ExpressionController, ExpressionRig
from .model import Animator, NEUTRAL, Style, demo_controls, pose_from_controls, retarget
from .openseeface import decode_packet
from .timing import ANIMATION_FPS, FRAME_SECONDS

TRACKING_TIMEOUT = 0.25

WEB = Path(__file__).parent / "web"


class Application:
    def __init__(self, profile_path: Path, face_id: int = 0):
        self.lock = threading.RLock()
        self.profile_path, self.face_id = profile_path, face_id
        self.profile = Profile()
        if profile_path.exists():
            self.profile = Profile.from_dict(json.loads(profile_path.read_text()))
        self.session = CalibrationSession()
        self.animator = Animator()
        self.manual = dict(NEUTRAL)
        self.mode = "demo"
        self.latest = None
        self.rejected = 0
        self.received = 0
        self.sequence = 0
        self.started = time.monotonic()
        self.stop = threading.Event()
        self.snapshot = {}
        self.measurement_contact = True
        self.contact_pending = False
        self.expression_rig = ExpressionRig()
        self.expressions = ExpressionController(self.expression_rig.available)

    def configure_character(self, character):
        """Configure available expression banks before the first animation tick."""
        rig = ExpressionRig(character)
        with self.lock:
            if self.sequence:
                raise ValueError('Configure the character before animation starts')
            self.expression_rig = rig
            self.expressions = ExpressionController(rig.available)

    def select_expression(self, name, now=None, *, part='face', hold=0., transition=.2):
        with self.lock:
            self.expressions.select(name, time.monotonic() if now is None else now,
                                    part=part, hold=hold, transition=transition)

    def receive(self, packet: bytes, now: float):
        try:
            records = decode_packet(packet, now)
        except ValueError:
            with self.lock:
                self.rejected += 1
            return
        for measurement in records:
            self.ingest(measurement)

    def ingest(self, m):
        """Accept decoded input from either UDP or ROS, with identical rules."""
        with self.lock:
            if m.face_id == self.face_id:
                self.received += 1
                if m.valid and (self.latest is None or m.received_at >= self.latest.received_at):
                    if self.latest is None or m.received_at - self.latest.received_at > TRACKING_TIMEOUT:
                        self.contact_pending = False
                        self.measurement_contact = True
                    self.latest = m
                    if self.mode == "live":
                        contact = retarget(m, self.profile)["seal"] >= .98
                        if contact and not self.measurement_contact:
                            self.contact_pending = True
                        self.measurement_contact = contact
                        self.session.add(m.signals(), m.aperture_ratio)

    def tick(self, now: float):
        with self.lock:
            self.expressions._time(now)
            age = now - self.latest.received_at if self.latest else None
            fresh = age is not None and 0 <= age <= TRACKING_TIMEOUT
            if not fresh:
                self.contact_pending = False
                self.measurement_contact = True
            label = "Manual character controls"
            target = self.manual
            active = True
            if self.mode == "demo":
                target, label = demo_controls(now - self.started)
            elif self.mode == "live":
                label = "OpenSeeFace live" if fresh else "Tracking unavailable — easing to rest"
                target = retarget(self.latest, self.profile) if fresh else NEUTRAL
                if fresh and self.contact_pending:
                    target = {**target, "seal": 1}
                    self.contact_pending = False
                active = fresh
            pose = self.animator.step(target, now, active)
            expression_weights = self.expressions.sample(now)
            pose = self.expression_rig.compose(pose, expression_weights)
            self.sequence += 1
            self.snapshot = dict(
                sequence=self.sequence, mode=self.mode, label=label, pose=pose,animation_fps=ANIMATION_FPS,
                style=asdict(self.animator.style), age_ms=None if age is None else round(age*1000),
                tracking=fresh, calibrated=self.profile.calibrated,
                calibration=self.session.status(), received=self.received, rejected=self.rejected,
                raw=self.latest.signals() if self.latest else None,
                aperture_ratio=self.latest.aperture_ratio if self.latest else None,
                expression=self.expressions.status(expression_weights),
                limitations=["rounding is a narrowing proxy", "seal is inferred from lip aperture",
                             "specialized consonant channels are not inferred from OpenSeeFace"],
            )

    def command(self, path: str, data: dict, *, now=None):
        """Apply one validated command; invalid commands leave state unchanged."""
        if not isinstance(data, dict):
            raise ValueError("Expected command object")
        with self.lock:
            if path == "/api/expression":
                self.expressions.select(data.get('expression'), time.monotonic() if now is None else now,
                    part=data.get('part', 'face'), hold=data.get('hold', 0.),
                    transition=data.get('transition', .2))
            elif path == "/api/control":
                mode = data.get("mode", self.mode)
                if mode not in ("manual", "live", "demo"):
                    raise ValueError("Unknown mode")
                controls = data.get("controls", {})
                if not isinstance(controls, dict):
                    raise ValueError("Expected controls object")
                proposed = {**self.manual, **controls}
                if any(k not in NEUTRAL for k in proposed):
                    raise ValueError("Unknown control")
                pose_from_controls(proposed, self.animator.style)
                self.manual = {k: float(proposed[k]) for k in NEUTRAL}
                if mode != self.mode or mode != "live":
                    self.contact_pending = False
                    self.measurement_contact = True
                self.mode = mode
            elif path == "/api/style":
                proposed = asdict(self.animator.style)
                for k, v in data.items():
                    if k not in proposed:
                        raise ValueError("Unknown style parameter")
                    proposed[k] = v
                self.animator.style = Style(**proposed)
            elif path == "/api/calibration/start":
                self.session.begin(data.get("stage"))
                self.mode = "live"
                self.contact_pending = False
                self.measurement_contact = True
            elif path == "/api/calibration/stop":
                self.session.stage = None
            elif path == "/api/calibration/save":
                previous_stage = self.session.stage
                profile = self.session.finish()
                try:
                    profile.save(self.profile_path)
                except OSError:
                    self.session.stage = previous_stage
                    raise
                self.profile = profile
                self.contact_pending = False
                self.measurement_contact = True
            else:
                raise ValueError("Unknown command")


def make_http_server(app, host, port, character_path):
    """Host the same UI/calibration state without creating input sockets or clocks."""
    class Handler(BaseHTTPRequestHandler):
        protocol_version = "HTTP/1.1"

        def log_message(self, fmt, *values):
            return

        def respond(self, code, content, mime="application/json"):
            body = content if isinstance(content, bytes) else content.encode()
            self.send_response(code)
            self.send_header("Content-Type", mime)
            self.send_header("Content-Length", str(len(body)))
            self.send_header("Cache-Control", "no-store")
            self.end_headers()
            self.wfile.write(body)

        def do_GET(self):
            path = urlsplit(self.path).path
            if path == "/api/character-texture":
                texture = Path(character_path).with_suffix('.png')
                self.respond(200, texture.read_bytes(), 'image/png') if texture.is_file() else self.respond(404, '{"error":"No character texture"}')
            elif path == "/api/character":
                character = Path(character_path)
                self.respond(200, character.read_bytes() if character.is_file() else b'null')
            elif path == "/api/state":
                with app.lock:
                    body = json.dumps(app.snapshot)
                self.respond(200, body)
            elif path == "/api/events":
                self.send_response(200)
                self.send_header("Content-Type", "text/event-stream")
                self.send_header("Cache-Control", "no-cache")
                self.send_header("Connection", "close")
                self.end_headers()
                try:
                    while not app.stop.is_set():
                        with app.lock:
                            body = json.dumps(app.snapshot)
                        self.wfile.write(("data: " + body + "\n\n").encode())
                        self.wfile.flush()
                        app.stop.wait(FRAME_SECONDS)
                except (BrokenPipeError, ConnectionResetError):
                    pass
                self.close_connection = True
            else:
                name = "index.html" if path == "/" else path.removeprefix("/")
                file = (WEB / name).resolve()
                if WEB.resolve() not in file.parents or not file.is_file():
                    self.respond(404, '{"error":"Not found"}')
                    return
                mime = mimetypes.guess_type(file.name)[0] or "application/octet-stream"
                self.respond(200, file.read_bytes(), mime)

        def do_POST(self):
            # Local control API: reject cross-origin browser writes, even on localhost.
            origin = self.headers.get("Origin")
            if origin and urlsplit(origin).netloc != self.headers.get("Host"):
                self.respond(403, '{"error":"Cross-origin command rejected"}')
                return
            try:
                size = int(self.headers.get("Content-Length", "0"))
                if not 0 < size <= 16384:
                    raise ValueError("Invalid request size")
                data = json.loads(self.rfile.read(size))
                if not isinstance(data, dict):
                    raise ValueError("Expected JSON object")
                app.command(urlsplit(self.path).path, data)
                self.respond(200, '{"ok":true}')
            except (ValueError, KeyError, TypeError) as exc:
                self.respond(400, json.dumps({"error": str(exc)}))
            except OSError:
                self.respond(500, '{"error":"Could not persist calibration profile"}')

    server = ThreadingHTTPServer((host, port), Handler)
    server.daemon_threads = True
    return server


def start_http(app, host, port, character_path):
    server = make_http_server(app, host, port, character_path)
    thread = threading.Thread(target=server.serve_forever, kwargs={'poll_interval': .1}, daemon=True)
    thread.start()
    return server, thread


def serve(args):
    app = Application(Path(args.profile), args.face_id)
    character_path = Path(getattr(args, 'character', 'local/character.json'))
    if character_path.is_file():
        app.configure_character(json.loads(character_path.read_text()))
    udp = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    udp.bind((args.udp_host, args.udp_port))
    udp.settimeout(0.2)

    def receive_loop():
        while not app.stop.is_set():
            try:
                packet, _ = udp.recvfrom(65535)
                app.receive(packet, time.monotonic())
            except socket.timeout:
                continue
            except OSError:
                break

    def animate_loop():
        while not app.stop.is_set():
            with app.lock:
                start = time.monotonic()
                app.tick(start)
            app.stop.wait(max(0.001, FRAME_SECONDS - (time.monotonic() - start)))

    server = make_http_server(app, args.host, args.port, getattr(args, 'character', 'local/character.json'))
    app.tick(time.monotonic())
    threading.Thread(target=receive_loop, daemon=True).start()
    threading.Thread(target=animate_loop, daemon=True).start()
    print(f"Prootface: http://{args.host}:{args.port}", flush=True)
    print(f"OpenSeeFace UDP: {args.udp_host}:{args.udp_port}; face {args.face_id}", flush=True)
    try:
        server.serve_forever(poll_interval=0.2)
    except KeyboardInterrupt:
        pass
    finally:
        app.stop.set()
        udp.close()
        server.server_close()

