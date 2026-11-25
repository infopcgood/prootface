"""Deterministic human-to-character rules; renderer receives semantic controls."""

from dataclasses import asdict, dataclass
import math
from .calibration import Profile, clamp
from .openseeface import Measurement


@dataclass
class Style:
    max_jaw_angle: float = 0.44
    recession: float = 0.12
    opening_gamma: float = 1.22
    max_corner_lift: float = 0.20
    asymmetry: float = 0.70
    v_depth: float = 0.18
    v_position: float = 0.84
    v_width: float = 0.08
    lip_thickness: float = 0.065


NEUTRAL = dict(opening=0.0, rounding=0.0, spread=0.0, seal=1.0,
               corner_left=0.0, corner_right=0.0, tension=0.0,
               eye_left=1.0, eye_right=1.0, brow_left=0.0, brow_right=0.0)


def retarget(m: Measurement, profile: Profile) -> dict[str, float]:
    x = {k: profile.ranges[k].normalize(v) for k, v in m.signals().items()}
    opening = max(0.0, x["open"])
    if m.aperture_ratio is not None:
        # An observed contact gap is stronger evidence than adaptive jaw-feature drift.
        gap = clamp((m.aperture_ratio - profile.closed_aperture) /
                    (profile.open_aperture - profile.closed_aperture))
        opening = 0.55 * opening + 0.45 * gap
        seal = 1.0 - clamp(gap / 0.12)
    else:
        seal = 1.0 - clamp(opening / 0.08)
    return dict(
        opening=opening, rounding=max(0.0, -x["width"]),
        spread=max(0.0, x["width"]), seal=seal,
        corner_left=x["corner_left"], corner_right=x["corner_right"],
        tension=clamp(abs(x["width"]) * 0.4), eye_left=m.eye_left,
        eye_right=m.eye_right, brow_left=x["brow_left"], brow_right=x["brow_right"],
    )


def pose_from_controls(controls: dict[str, float], style: Style) -> dict:
    c = dict(NEUTRAL)
    for k, v in controls.items():
        if k in c:
            if not math.isfinite(v):
                raise ValueError("Non-finite character control")
            c[k] = clamp(v, -1.0 if k.startswith(("corner", "brow")) else 0.0, 1.0)
    # Rounding acts on central articulation; it does not erase emotional corner lift.
    average = (c["corner_left"] + c["corner_right"]) / 2
    rendered_corners = {
        f"corner_{side}_render": average + style.asymmetry * (c[f"corner_{side}"] - average)
        for side in ("left", "right")
    }
    visible = c["opening"] ** style.opening_gamma * (1 - c["seal"]) ** 2
    return {**c, **rendered_corners, "aperture": visible, "jaw_angle": style.max_jaw_angle * visible,
            "jaw_recession": style.recession * visible,
            "width_scale": clamp(1 + 0.10 * c["spread"] - 0.28 * c["rounding"], 0.65, 1.10)}


class Animator:
    def __init__(self, style: Style | None = None):
        self.style = style or Style()
        self.controls = dict(NEUTRAL)
        self.last_time: float | None = None

    def step(self, target: dict[str, float], now: float, tracked: bool = True) -> dict:
        if not math.isfinite(now) or (self.last_time is not None and now < self.last_time):
            raise ValueError("Animation time must be finite and monotonic")
        dt = 1 / 60 if self.last_time is None else min(0.1, now - self.last_time)
        self.last_time = now
        clean = pose_from_controls(target, self.style)  # validate before modifying state
        for k, old in self.controls.items():
            value = clean[k] if tracked else NEUTRAL[k]
            tau = 0.022 if k in ("opening", "rounding", "spread", "seal") else 0.055
            if not tracked:
                tau = 0.14
            self.controls[k] += (value - old) * (1 - math.exp(-dt / tau))
        if tracked and clean["seal"] >= 0.98:
            # Contact priority prevents filtering or smile correctives leaking a gap.
            self.controls["seal"] = 1.0
        return pose_from_controls(self.controls, self.style)


def demo_controls(seconds: float) -> tuple[dict, str]:
    """Synthetic articulation demonstration, not a phoneme recognizer or recorded speech."""
    scenes = (
        ("Rest / contact", dict()),
        ("Conversational opening", dict(opening=.5, seal=0)),
        ("Rounded opening — inferred proxy", dict(opening=.55, rounding=.9, seal=0)),
        ("Smile while speaking", dict(opening=.48, spread=.4, corner_left=.8, corner_right=.8, seal=0)),
        ("Closed smile / contact wins", dict(opening=.6, corner_left=.8, corner_right=.8, seal=1)),
        ("Asymmetric restrained opening", dict(opening=.35, corner_left=.85, corner_right=.1, seal=0)),
        ("Emphatic opening / recession", dict(opening=.95, tension=.6, seal=0)),
    )
    label, values = scenes[int(seconds / 2.5) % len(scenes)]
    return {**NEUTRAL, **values}, label

