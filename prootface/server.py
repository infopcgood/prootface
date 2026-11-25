"""Local-only preview, calibration endpoints and OpenSeeFace receiver."""

from dataclasses import asdict
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
import math
import mimetypes
from pathlib import Path
import socket
import threading
import time
from urllib.parse import urlsplit

from .calibration import CalibrationSession, Profile
from .model import Animator, NEUTRAL, Style, demo_controls, pose_from_controls, retarget
from .openseeface import decode_packet
from .timing import ANIMATION_FPS,FRAME_SECONDS

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

    def receive(self, packet: bytes, now: float):
        try:
            records = decode_packet(packet, now)
        except ValueError:
            with self.lock:
                self.rejected += 1
            return
        with self.lock:
            for m in records:
                if m.face_id == self.face_id:
                    # Only valid fresh records replace the last usable sample.
                    self.received += 1
                    if m.valid:
                        self.latest = m
                        if self.mode == "live":
                            contact=retarget(m,self.profile)['seal']>=.98
                            if contact and not self.measurement_contact:self.contact_pending=True
                            self.measurement_contact=contact
                            self.session.add(m.signals(), m.aperture_ratio)

    def tick(self, now: float):
        with self.lock:
            age = now - self.latest.received_at if self.latest else None
            fresh = age is not None and age <= 0.25
            label = "Manual character controls"
            target = self.manual
            active = True
            if self.mode == "demo":
                target, label = demo_controls(now - self.started)
            elif self.mode == "live":
                label = "OpenSeeFace live" if fresh else "Tracking unavailable — easing to rest"
                target = retarget(self.latest, self.profile) if fresh else NEUTRAL
                if fresh and self.contact_pending:
                    target={**target,'seal':1}
                    self.contact_pending=False
                active = fresh
            pose = self.animator.step(target, now, active)
            self.sequence += 1
            self.snapshot = dict(
                sequence=self.sequence, mode=self.mode, label=label, pose=pose,animation_fps=ANIMATION_FPS,
                style=asdict(self.animator.style), age_ms=None if age is None else round(age*1000),
                tracking=fresh, calibrated=self.profile.calibrated,
                calibration=self.session.status(), received=self.received, rejected=self.rejected,
                raw=self.latest.signals() if self.latest else None,
                aperture_ratio=self.latest.aperture_ratio if self.latest else None,
                limitations=["rounding is a narrowing proxy", "seal is inferred from lip aperture",
                             "specialized consonant channels are not inferred from OpenSeeFace"],
            )

    def command(self, path: str, data: dict):
        with self.lock:
            if path == "/api/control":
                mode = data.get("mode", self.mode)
                if mode not in ("manual", "live", "demo"):
                    raise ValueError("Unknown mode")
                proposed = {**self.manual, **data.get("controls", {})}
                if any(k not in NEUTRAL for k in proposed):
                    raise ValueError("Unknown control")
                pose_from_controls(proposed, self.animator.style)
                self.manual = {k: float(proposed[k]) for k in NEUTRAL}
                self.mode = mode
                if mode!='live':self.contact_pending=False
            elif path == "/api/style":
                allowed = {
                    "max_jaw_angle": (.1, .65), "recession": (0, .35),
                    "opening_gamma": (.6, 2), "max_corner_lift": (0, .35),
                    "asymmetry": (0, 1), "v_depth": (.02, .30),
                    "v_position": (.65, .92), "v_width": (.02, .10),
                    "lip_thickness": (.005, .04),
                    "pose_contrast": (1,4),
                    "opening_contrast": (1,4),"key_pose_strength": (0,1),"accent_gain": (0,.5),
                    "front_motion_scale": (0,1),
                }
                proposed = asdict(self.animator.style)
                for k, v in data.items():
                    if k not in allowed or not isinstance(v, (float, int)):
                        raise ValueError("Unknown style parameter")
                    if not math.isfinite(v) or not allowed[k][0] <= v <= allowed[k][1]:
                        raise ValueError("Style parameter outside safe geometric bounds")
                    proposed[k] = v
                self.animator.style = Style(**proposed)
            elif path == "/api/calibration/start":
                self.mode = "live"
                self.session.begin(data["stage"])
            elif path == "/api/calibration/stop":
                self.session.stage = None
            elif path == "/api/calibration/save":
                profile = self.session.finish()
                profile.save(self.profile_path)
                self.profile = profile
            else:
                raise ValueError("Unknown command")


def serve(args):
    app = Application(Path(args.profile), args.face_id)
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
            start = time.monotonic()
            app.tick(start)
            app.stop.wait(max(0.001, FRAME_SECONDS - (time.monotonic() - start)))

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
                texture = Path(getattr(args, 'character', 'local/character.json')).with_suffix('.png')
                self.respond(200, texture.read_bytes(), 'image/png') if texture.is_file() else self.respond(404, '{"error":"No character texture"}')
            elif path == "/api/character":
                character = Path(getattr(args, 'character', 'local/character.json'))
                self.respond(200, character.read_bytes() if character.is_file() else b'null')
            elif path == "/api/state":
                with app.lock:
                    self.respond(200, json.dumps(app.snapshot))
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

    server = ThreadingHTTPServer((args.host, args.port), Handler)
    server.daemon_threads = True
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

