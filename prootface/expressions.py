"""Externally selected expression banks, independent of speech measurements."""
from dataclasses import dataclass
import math

EXPRESSIONS = ('neutral', 'happy', 'angry', 'sad', 'unamused')
PARTS = ('mouth', 'eyes')
PHASES = ('open', 'round', 'wide')
DEFAULT_TRANSITION = .2


def _number(value, name, low, high):
    if (isinstance(value, bool) or not isinstance(value, (int, float))
            or not low <= value <= high or not math.isfinite(value)):
        raise ValueError(f'{name} must be a finite number in [{low}, {high}]')
    return float(value)


def _vector(name):
    return {key: float(key == name) for key in EXPRESSIONS}


@dataclass
class _Channel:
    base: str = 'neutral'
    selected: str = 'neutral'
    started: float = 0.
    start: dict | None = None
    expires: float | None = None
    transition: float = DEFAULT_TRANSITION

    def _weights(self, now):
        if self.start is None:
            return _vector(self.selected)
        u = min(1., max(0., (now - self.started) / self.transition)) if self.transition else 1.
        u = u*u*(3-2*u)
        target = _vector(self.selected)
        return {key: self.start[key]*(1-u) + target[key]*u for key in EXPRESSIONS}

    def sample(self, now):
        if self.expires is not None and now >= self.expires:
            self.start = self._weights(self.expires)
            self.started = self.expires
            self.selected = self.base
            self.expires = None
        return self._weights(now)

    def select(self, name, now, hold, transition):
        current = self.sample(now)
        # Repeated button/ROS messages must not restart a fade or timed hold.
        if name == self.selected and bool(hold) == (self.expires is not None):
            return
        self.start, self.started = current, now
        self.selected, self.transition = name, transition
        self.expires = now + hold if hold else None
        if not hold:
            self.base = name


class ExpressionController:
    """Two expression channels. Zero hold latches; positive hold is temporary."""

    def __init__(self, available=EXPRESSIONS):
        self.available = tuple(name for name in EXPRESSIONS if name in available)
        if 'neutral' not in self.available:
            raise ValueError('Neutral expression is required')
        self.channels = {part: _Channel() for part in PARTS}
        self.last_time = None

    def _time(self, now):
        if (not isinstance(now, (int, float)) or not math.isfinite(now)
                or (self.last_time is not None and now < self.last_time)):
            raise ValueError('Expression time must be finite and monotonic')

    def select(self, name, now, *, part='face', hold=0., transition=DEFAULT_TRANSITION):
        self._time(now)
        if name not in self.available:
            raise ValueError(f'Expression unavailable in this character: {name}')
        if part not in ('face', *PARTS):
            raise ValueError('Expression part must be face, mouth or eyes')
        hold = _number(hold, 'hold', 0, 3600)
        transition = _number(transition, 'transition', 0, 2)
        for key in PARTS if part == 'face' else (part,):
            self.channels[key].select(name, now, hold, transition)
        self.last_time = now

    def sample(self, now):
        self._time(now)
        result = {part: channel.sample(now) for part, channel in self.channels.items()}
        self.last_time = now
        return result

    def status(self, weights):
        return dict(available=list(self.available), parts={part: dict(
            selected=channel.selected, latched=channel.base,
            expires_at=channel.expires, weights=dict(weights[part]),
        ) for part, channel in self.channels.items()})


class ExpressionRig:
    """Resolve semantic bank targets; compiled geometry remains external data."""

    def __init__(self, character=None):
        character = character or {}
        self.banks = character.get('expression_sets', {})
        if not isinstance(self.banks, dict):
            raise ValueError('expression_sets must be an object')
        targets = character.get('targets', {})
        for name, bank in self.banks.items():
            if name not in EXPRESSIONS[1:] or not isinstance(bank, dict):
                raise ValueError('Unknown expression bank')
            for channel in ('rest', *PHASES, 'eye_left', 'eye_right'):
                target = bank.get(channel)
                if not isinstance(target, str) or target not in targets:
                    raise ValueError(f'Missing expression target: {name}/{channel}')
        self.available = ('neutral', *(name for name in EXPRESSIONS[1:] if name in self.banks))

    def compose(self, pose, weights):
        output = dict(pose)
        def add(target, weight):
            key = 'blend_' + target
            output[key] = output.get(key, 0.) + weight
        neutral = weights['mouth']['neutral']
        for side in ('left', 'right'):
            # Selected mouth banks own expression; measured articulation remains.
            for key in ('smile', 'frown'):
                name = f'blend_{key}_{side}'
                output[name] = output.get(name, 0.) * neutral
        for name, bank in self.banks.items():
            mouth = weights['mouth'][name]
            add(bank['rest'], mouth)
            for phase in PHASES:
                add(bank[phase], mouth * pose.get('blend_' + phase, 0.))
            for side in ('left', 'right'):
                # Full blinks retain their clean endpoint in every expression.
                openness = 1 - pose.get('blend_blink_' + side, 0.)
                add(bank['eye_' + side], weights['eyes'][name] * openness)
        return output
