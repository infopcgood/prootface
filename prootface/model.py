"""Deterministic human-to-character rules; renderer receives semantic controls."""

from dataclasses import asdict, dataclass
import math
from .calibration import Profile, clamp
from .openseeface import Measurement


@dataclass
class Style:
    max_jaw_angle: float = 0.36
    recession: float = 0.12
    opening_gamma: float = 0.85
    max_corner_lift: float = 0.20
    asymmetry: float = 0.70
    v_depth: float = 0.11
    v_position: float = 0.88
    v_width: float = 0.045
    lip_thickness: float = 0.016


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
    visible = c["opening"] ** style.opening_gamma * (1 - c["seal"])
    # Ease into the readable part of an authored opening sample. The source
    # feature is calibrated movement, not a physical percentage of mesh travel.
    strength = clamp(visible*style.max_jaw_angle/.36)
    articulation = strength*(2-strength)
    # Authored pose samples form a convex mouth basis. Width changes select
    # articulation, rather than squashing the entire closed silhouette.
    rounding, spreading = c['rounding'], c['spread']
    total = max(1.0, rounding+spreading)
    rounded, wide = rounding/total, spreading/total
    neutral = max(0.0,1-rounded-wide)
    blends = dict(blend_open=articulation*neutral,
                  blend_round=articulation*rounded, blend_wide=articulation*wide,
                  blend_closed=c['seal']*min(.45,c['opening']*.8))
    for side in ('left','right'):
        corner=rendered_corners[f'corner_{side}_render']
        blends[f'blend_smile_{side}']=max(0,corner)*.55
        blends[f'blend_frown_{side}']=max(0,-corner)*.45
        blends[f'blend_pucker_{side}']=rounding*(1-visible)*.12
        blends[f'blend_blink_{side}']=1-c[f'eye_{side}']
    return {**c, **rendered_corners, **blends, "aperture": visible, "jaw_angle": style.max_jaw_angle * visible,
            "jaw_recession": style.recession * visible,
            "width_scale": clamp(1 + 0.10 * c["spread"] - 0.28 * c["rounding"], 0.65, 1.10)}


class Animator:
    def __init__(self, style: Style | None = None):
        self.style = style or Style()
        self.controls = dict(NEUTRAL)
        self.last_time: float | None = None
        self.last_raw = dict(NEUTRAL)
        self.derivative = {k: 0.0 for k in NEUTRAL}

    def step(self, target: dict[str, float], now: float, tracked: bool = True) -> dict:
        if not math.isfinite(now) or (self.last_time is not None and now < self.last_time):
            raise ValueError("Animation time must be finite and monotonic")
        dt = 1 / 60 if self.last_time is None else min(0.1, now - self.last_time)
        self.last_time = now
        clean = pose_from_controls(target, self.style)  # validate before modifying state
        for k, old in self.controls.items():
            value = clean[k] if tracked else NEUTRAL[k]
            # Speed-adaptive low pass: stable rest, faster deliberate articulation.
            # No prediction or overshoot. Derivative is itself filtered at 1 Hz.
            if dt > 0:
                speed = (value - self.last_raw[k]) / dt
                self.derivative[k] += (speed-self.derivative[k]) * (1-math.exp(-dt*2*math.pi))
            self.last_raw[k] = value
            mouth = k in ("opening", "rounding", "spread", "seal")
            cutoff = (5.0 if mouth else 2.8) + (.7 if mouth else .3)*abs(self.derivative[k])
            tau = 1/(2*math.pi*cutoff) if tracked else .14
            if tracked and k == 'seal':
                # Contact can attach quickly, and must detach promptly as well.
                # Reusing the jaw low-pass here swallowed short vowel openings.
                tau = .008 if value < old else .012
            self.controls[k] += (value - old) * (1 - math.exp(-dt / tau))
        if tracked and clean["seal"] >= 0.98:
            # Contact priority prevents filtering or smile correctives leaking a gap.
            self.controls["seal"] = 1.0
        return pose_from_controls(self.controls, self.style)


def _monotone_value(times: list[float], values: list[float], t: float) -> float:
    """Shape-preserving Hermite interpolation; neighboring poses flow without overshoot."""
    import bisect
    index = min(len(times)-2, max(0, bisect.bisect_right(times, t)-1))
    spans = [times[i+1]-times[i] for i in range(len(times)-1)]
    slopes = [(values[i+1]-values[i])/spans[i] for i in range(len(spans))]
    tangents = [0.0]*len(times)
    for i in range(1,len(times)-1):
        a,b=slopes[i-1],slopes[i]
        if a*b>0:
            w1,w2=2*spans[i]+spans[i-1],spans[i]+2*spans[i-1]
            tangents[i]=(w1+w2)/(w1/a+w2/b)
    h=spans[index];u=clamp((t-times[index])/h)
    value=(2*u**3-3*u*u+1)*values[index]+(u**3-2*u*u+u)*h*tangents[index]
    value+=(-2*u**3+3*u*u)*values[index+1]+(u**3-u*u)*h*tangents[index+1]
    return clamp(value,min(values[index:index+2]),max(values[index:index+2]))


# Authored synthetic phrase. Values are opening/rounding/spreading/contact.
# Contact and preparation have their own timing; this is not audio-derived speech.
_BEATS = (
    (0.0, 0,0,0,1),(.55,0,0,0,1),(.72,.06,.4,0,1),(.86,.36,.55,0,0),
    (1.08,.58,.1,.25,0),(1.25,.20,0,.5,0),(1.38,.12,.4,0,1),
    (1.48,.12,.65,0,1),(1.65,.44,.95,0,0),(1.9,.32,.9,0,0),
    (2.10,.48,.1,.4,0),(2.3,.18,0,.15,0),(2.46,.08,0,0,1),
    (2.75,.08,0,0,1),(2.9,.35,.3,0,0),(3.14,.72,.1,.2,0),
    (3.38,.3,.1,.35,0),(3.56,.12,0,0,1),(3.75,.12,0,0,1),
    (4.02,.46,.7,0,0),(4.23,.33,.3,.2,0),(4.5,.12,.1,0,0),
    (4.78,0,0,0,1),(5.4,0,0,0,1),(6.0,0,0,0,1),
)


def demo_controls(seconds: float) -> tuple[dict, str]:
    t=seconds%6.0
    times=[b[0] for b in _BEATS]
    controls=dict(NEUTRAL)
    for index,key in enumerate(("opening","rounding","spread","seal"),start=1):
        controls[key]=_monotone_value(times,[b[index] for b in _BEATS],t)
    # Expression persists over several syllables instead of changing on each vowel.
    expression=0.24+0.12*math.sin(seconds*.55)
    controls["corner_left"]=expression
    controls["corner_right"]=expression*.82
    label="Synthetic phrase · overlapping articulation" if .6<t<4.8 else "Phrase rest · expression persists"
    return controls,label

