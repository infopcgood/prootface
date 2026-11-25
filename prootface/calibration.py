"""Robust wearer normalization. Character appearance is configured elsewhere."""

from dataclasses import asdict, dataclass, field
import json
import math
from pathlib import Path


def clamp(x: float, low: float = 0.0, high: float = 1.0) -> float:
    return min(high, max(low, x))


def percentile(values: list[float], q: float) -> float:
    if not values:
        raise ValueError("Calibration has no samples")
    xs = sorted(values)
    index = (len(xs) - 1) * q
    lo = int(index)
    return xs[lo] + (xs[min(lo + 1, len(xs) - 1)] - xs[lo]) * (index - lo)


@dataclass
class Range:
    rest: float = 0.0
    positive: float = 1.0
    negative: float = -1.0

    def __post_init__(self):
        if not all(math.isfinite(x) for x in (self.rest, self.positive, self.negative)):
            raise ValueError("Calibration range must be finite")
        if self.positive - self.rest < 0.02 or self.rest - self.negative < 0.02:
            raise ValueError("Calibration needs a usable range on both sides of rest")

    def normalize(self, value: float) -> float:
        scale = self.positive - self.rest if value >= self.rest else self.rest - self.negative
        return clamp((value - self.rest) / scale, -1.0, 1.0)


SIGNALS = ("open", "width", "corner_left", "corner_right", "brow_left", "brow_right")
STAGES = ("neutral", "open", "wide", "narrow", "smile")


@dataclass
class Profile:
    ranges: dict[str, Range] = field(default_factory=lambda: {k: Range() for k in SIGNALS})
    closed_aperture: float = 0.025
    open_aperture: float = 0.22
    calibrated: bool = False
    schema_version: int = 1

    def __post_init__(self):
        if self.schema_version != 1:
            raise ValueError("Unsupported calibration schema")
        if (set(self.ranges) != set(SIGNALS)
                or not all(isinstance(v, Range) for v in self.ranges.values())):
            raise ValueError("Calibration needs one Range per signal")
        if (not all(math.isfinite(x) for x in (self.closed_aperture, self.open_aperture))
                or not 0 <= self.closed_aperture < self.open_aperture):
            raise ValueError("Invalid aperture calibration")

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> "Profile":
        try:
            if data.get("schema_version") != 1:
                raise ValueError("Unsupported calibration schema")
            ranges = {k: Range(**data["ranges"][k]) for k in SIGNALS}
            return cls(ranges, float(data["closed_aperture"]),
                       float(data["open_aperture"]), bool(data.get("calibrated")))
        except (AttributeError, KeyError, TypeError, OverflowError) as exc:
            raise ValueError("Malformed calibration profile") from exc

    def save(self, path: Path):
        path.parent.mkdir(parents=True, exist_ok=True)
        temp = path.with_suffix(path.suffix + ".tmp")
        temp.write_text(json.dumps(self.to_dict(), indent=2) + "\n")
        temp.replace(path)


class CalibrationSession:
    def __init__(self):
        self.stage: str | None = None
        self.samples: dict[str, list[dict]] = {k: [] for k in STAGES}

    def begin(self, stage: str):
        if stage not in STAGES:
            raise ValueError("Unknown calibration stage")
        self.stage = stage
        self.samples[stage] = []

    def add(self, signals: dict[str, float], aperture: float | None):
        if self.stage is None:
            return
        if not all(k in signals and math.isfinite(signals[k]) for k in SIGNALS):
            return
        sample = dict(signals)
        if aperture is not None and math.isfinite(aperture):
            sample["aperture"] = aperture
        self.samples[self.stage].append(sample)

    def finish(self) -> Profile:
        for stage in STAGES:
            if len(self.samples[stage]) < 8:
                raise ValueError(f"Capture at least 8 valid live frames for {stage}")
        med = lambda stage, k: percentile([s[k] for s in self.samples[stage]], 0.5)
        ranges = {}
        for k in SIGNALS:
            rest = med("neutral", k)
            positive = rest + 1.0
            negative = rest - 1.0
            if k == "open":
                positive = med("open", k)
            elif k == "width":
                positive, negative = med("wide", k), med("narrow", k)
            elif k.startswith("corner"):
                positive = med("smile", k)
            if positive - rest < 0.08 or rest - negative < 0.08:
                raise ValueError(f"Insufficient {k} movement; repeat the relevant stage")
            ranges[k] = Range(rest, positive, negative)
        # Brows/frowns retain default unit spans; these stages do not claim to calibrate them.
        neutral_gaps = [s["aperture"] for s in self.samples["neutral"] if "aperture" in s]
        open_gaps = [s["aperture"] for s in self.samples["open"] if "aperture" in s]
        closed, opened = 0.025, 0.22
        if len(neutral_gaps) >= 8 and len(open_gaps) >= 8:
            closed, opened = percentile(neutral_gaps, 0.95), percentile(open_gaps, 0.5)
            if opened - closed < 0.05:
                raise ValueError("Inner-lip landmarks did not establish a usable opening range")
            closed += min(0.01, (opened - closed) * 0.04)
        profile = Profile(ranges, closed, opened, True)
        self.stage = None
        return profile

    def status(self) -> dict:
        return {"stage": self.stage, "counts": {k: len(v) for k, v in self.samples.items()}}

