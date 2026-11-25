"""Offline speaking timing for semantic character controls.

Phone times schedule opening, rounding, spreading and contact. The character
model blends a privately configured authored pose basis continuously. Live
operation still uses OpenSeeFace; this is a timed synthetic review performance.
"""
import math
from .model import NEUTRAL
from .timing import ANIMATION_FPS

# Opening, rounding and spreading are independently overlapped. These targets
# contain no source-specific key names or abrupt avatar-pose switches.
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

# Frame-authored animation goals. Important shapes are pushed toward distinct
# silhouettes; these are not literal measurements of speech amplitude.
_ANIMATED = {
    'aa':(.9,0,.05),'ae':(.85,0,.85),'ah':(.8,0,0),'aw':(.85,.8,0),
    'ax':(.34,0,0),'eh':(.72,0,.95),'er':(.36,.45,0),
    'ey':(.72,0,1),'ih':(.42,0,.85),'iy':(.46,0,1),
    'ow':(.70,1,0),'oy':(.72,.95,0),'uh':(.60,.95,0),'uw':(.56,1,0),
    'w':(.40,1,0),'sh':(.32,.85,0),'zh':(.32,.8,0),'ch':(.38,.8,0),
    'jh':(.38,.8,0),'s':(.25,0,1),'z':(.25,0,1),'f':(.22,0,.15),
    'v':(.22,0,.15),'r':(.35,.8,0),
    'm':(.22,0,0),'b':(.22,0,0),'p':(.22,0,0),'pau':(0,0,0),'sil':(0,0,0),
}
_VOWELS = set('aa ae ah aw ax eh er ey ih iy ow oy uh uw'.split())
_CLOSURES = {'m','b','p'}
_DETAILS = {'f':'bite','v':'bite','s':'sibilant','z':'sibilant',
            'sh':'postalveolar','zh':'postalveolar','ch':'postalveolar','jh':'postalveolar',
            'r':'rhotic','er':'rhotic'}


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
        blink = _window(seconds,.07,.105,0,.045,.055)
        controls['eye_left'] = controls['eye_right'] = 1-blink
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

    def keyed_frames(self, before=.65, after=.85, speed=.85):
        """Author readable holds and transitions directly on the chosen 24 fps grid.

        Source-phone timing is only a guide: mouth poses anticipate by a frame,
        closures get two frames, and strong vowels retain a readable exposure.
        Planned key poses bypass sensor-noise filtering.
        """
        if not .5<=speed<=2 or before<0 or after<0:
            raise ValueError('Invalid performance timing')
        fps=ANIMATION_FPS
        count=math.ceil((before+self.duration/speed+after)*fps)
        keys={0:(0,dict(NEUTRAL)),count-1:(0,dict(NEUTRAL))}
        closures=[]
        for segment in self.segments:
            if segment['phone'] in _CLOSURES:
                first=max(0,round((before+segment['start']/speed)*fps)-1)
                last=max(first+1,round((before+segment['end']/speed)*fps)-2)
                closures.append((segment,first,min(count-1,last)))
        events=[]
        previous=None
        for segment in self.segments:
            phone=segment['phone']
            if phone not in _ANIMATED:
                previous=segment
                continue
            opening,rounding,spread=_ANIMATED[phone]
            goal={**NEUTRAL,'opening':opening,'rounding':rounding,'spread':spread,'seal':0}
            if phone in _DETAILS:goal[_DETAILS[phone]]=1
            first=max(0,round((before+segment['start']/speed)*fps)-1)
            last=max(first,round((before+segment['end']/speed)*fps)-2)
            priority=2 if phone in _VOWELS else 1
            if phone in _CLOSURES:
                _,first,last=next(c for c in closures if c[0] is segment)
                goal.update(seal=1,lip_press=1);priority=3
            elif phone in ('pau','sil'):
                goal.update(seal=1);priority=0
            elif phone in _VOWELS:
                if previous and previous['phone'] in _CLOSURES:
                    closing=next(c for c in closures if c[0] is previous)
                    first=max(first,closing[2]+1)
                if phone not in ('ax','ih'):
                    last=max(last,first+1)
            first=min(first,count-1);last=min(max(first,last),count-1)
            for frame in range(first,last+1):
                if frame not in keys or priority>=keys[frame][0]:
                    keys[frame]=(priority,goal)
            events.append(dict(phone=phone,first=first,last=last,priority=priority,_goal=goal))
            previous=segment
        ordered=sorted(keys)
        frames=[];cursor=0
        for frame in range(count):
            while cursor+1<len(ordered) and ordered[cursor+1]<=frame:cursor+=1
            a=ordered[cursor];b=ordered[min(cursor+1,len(ordered)-1)]
            t=_ease((frame-a)/(b-a)) if b>a else 0
            left,right=keys[a][1],keys[b][1]
            controls={key:left[key]+(right[key]-left[key])*t for key in NEUTRAL}
            secondary=self.controls((frame/fps-before)*speed)
            for key in ('corner_left','corner_right','eye_left','eye_right'):
                controls[key]=secondary[key]
            frames.append(controls)
        for event in events:
            goal=event.pop('_goal')
            event['exposed_frames']=[f for f in range(event['first'],event['last']+1)
                                     if keys[f][1] is goal]
        return frames,events
