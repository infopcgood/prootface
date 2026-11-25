"""Offline speaking example, independent of avatar animation/phoneme keys.

Synthesized-phone TIMES schedule continuous semantic gestures for a review
clip. Live operation still uses OpenSeeFace, never these phone labels. This is
an authored demonstration, not learned lip sync or a naturalness benchmark.
"""
import math
from .model import NEUTRAL

# Opening, rounding and spreading are independently overlapped. These targets
# never select an avatar viseme or stored mouth pose.
_TARGETS = {
    'aa':(.72,0,.05), 'ae':(.62,0,.3), 'ah':(.52,0,.05),
    'aw':(.60,.3,0), 'ax':(.28,0,0), 'eh':(.45,0,.35),
    'er':(.32,.35,0), 'ey':(.47,0,.52), 'ih':(.31,0,.3),
    'iy':(.24,0,.70), 'ow':(.42,.85,0), 'oy':(.48,.65,0),
    'uh':(.34,.70,0), 'uw':(.32,1,0), 'w':(.23,1,0),
    'sh':(.22,.55,0), 'zh':(.22,.5,0), 'ch':(.24,.45,0),
    'jh':(.25,.35,0), 's':(.16,0,.35), 'z':(.16,0,.3),
    'f':(.16,0,.15), 'v':(.18,0,.15), 'r':(.28,.35,0),
    'l':(.28,0,.12), 'm':(.16,0,0), 'b':(.16,0,0),
    'p':(.16,0,0), 'pau':(0,0,0), 'sil':(0,0,0),
}


def _ease(x):
    x = max(0.0, min(1.0, x))
    return x*x*(3-2*x)


def _window(t, start, end, lead, attack, release):
    start -= lead
    end -= lead
    return _ease((t-start+attack)/attack)*_ease((end+release-t)/release)


class SpeakingExample:
    def __init__(self, data):
        self.text = data['text']
        self.segments = data['segments']
        previous = 0.0
        for segment in self.segments:
            a, b = segment['start'], segment['end']
            if not (math.isfinite(a) and math.isfinite(b) and previous <= a < b):
                raise ValueError('Speech segments must be finite, ordered and nonoverlapping')
            if not isinstance(segment['phone'], str):
                raise ValueError('Invalid speech segment')
            previous = b
        if not self.segments:
            raise ValueError('No speech segments')
        self.duration = previous

    def controls(self, seconds):
        if not math.isfinite(seconds):
            raise ValueError('Invalid example time')
        controls = dict(NEUTRAL)
        # Expression carries through the sentence and the return to rest.
        controls.update(corner_left=.24, corner_right=.20)
        if seconds < 0 or seconds > self.duration:
            return controls
        for column, key in enumerate(('opening','rounding','spread')):
            lead = .075 if key == 'rounding' else .028
            weighted, total = 0.0, 0.0
            for segment in self.segments:
                weight = _window(seconds, segment['start'], segment['end'], lead, .045, .045)
                target = _TARGETS.get(segment['phone'], (.25,0,.1))[column]
                weighted += weight*target
                total += weight
            controls[key] = weighted/total if total > 1e-9 else 0.0
        # Closures dominate the vowel interpolation instead of being averaged
        # away. Contact timing has a much shorter response than jaw opening.
        closures = [_window(seconds, s['start'], s['end'], .018, .022, .025)
                    for s in self.segments if s['phone'] in ('m','b','p','pau','sil')]
        controls['seal'] = max(closures, default=0.0)
        return controls

    def word(self, seconds):
        for segment in self.segments:
            if segment['start'] <= seconds < segment['end']:
                word = segment.get('word', '')
                return '' if word == '0' else word
        return ''
