"""Generic spatial rig guides; all reference-specific geometry stays private."""

import math

FRONT_TARGETS = frozenset(('open','round','wide','bite','sibilant','postalveolar','rhotic'))


def front_motion_weights(character):
    """Smooth restraint at the anterior opening edge, full motion farther back.

    Canonical rig X runs front-to-rear. Use affected rest vertices to locate
    the mouth, not the full visor bounds. No authored rest position is changed.
    """
    base=character['positions'];count=len(base)//3
    indices={i for name in ('open','round','wide')
             for i in character['targets'].get(name,{}).get('indices',[])}
    if not indices:return [0.0]*count
    front=min(base[3*i] for i in indices);rear=max(base[3*i] for i in indices)
    if rear-front<1e-8:return [0.0]*count
    result=[]
    for i in range(count):
        t=(base[3*i]-front)/(rear-front)
        u=max(0.0,min(1.0,(t-.10)/.25))
        result.append(1-u*u*(3-2*u))
    return result


def add_mouth_variants(character, settings):
    """Compile optional art-directed corrections from a private landmark guide.

    A private rest landmark guide supplies spike relief. An optional posed-edge
    landmark locates the exposed lower contour. Continuous fields affect skin,
    occluders and coincident UV splits together. Corrections are compiled at
    authored endpoints; runtime only blends sparse targets.
    """
    if not settings:
        return
    base = [character['positions'][i:i+3] for i in range(0, len(character['positions']), 3)]
    targets = character['targets']
    indices = {i for name in ('open', 'round', 'wide')
               for i in targets.get(name, {}).get('indices', [])}
    if not indices:
        return
    reach = settings.get('round_reach_fraction', 0)
    if not math.isfinite(reach) or not 0 <= reach <= .5:
        raise ValueError('Round reach fraction must be between zero and one half')
    if reach:
        distance = reach * (max(base[i][0] for i in indices)-min(base[i][0] for i in indices))
        top = max(base[i][1] for i in indices)
        falloff = max(1e-5, (top-min(base[i][1] for i in indices))*.04)
        # One continuous shear field moves emitting and occluding surfaces
        # together, including stationary and UV-split vertices. Selecting only
        # vertices in a source morph can leave exposed slivers behind.
        selected, deltas = [], []
        for i, (_, y, _) in enumerate(base):
            u = max(0, min(1, (top+falloff-y)/falloff))
            weight = u*u*(3-2*u)
            if weight > 1e-6:
                selected.append(i);deltas.extend((-distance*weight, 0, 0))
        targets['round_reach'] = dict(indices=selected, deltas=deltas)
    guide = settings.get('spike')
    if not guide:
        return
    a, b = guide['anchors']
    tip = guide['tip']
    ax, ay = base[a][:2];bx, by = base[b][:2];tx, ty = base[tip][:2]
    dx, dy = bx-ax, by-ay
    length = math.hypot(dx, dy)
    if length < 1e-6:
        raise ValueError('Spike guide anchors must be distinct')
    along = ((tx-ax)*dx+(ty-ay)*dy)/length**2
    depth = ((tx-ax)*-dy+(ty-ay)*dx)/length
    if not .05 < along < .95 or abs(depth) < 1e-5:
        raise ValueError('Spike guide needs a tip away from its anchor chord')
    for semantic in ('open', 'round', 'wide', 'bite', 'sibilant', 'postalveolar', 'rhotic'):
        if semantic not in targets:
            continue
        posed = [p[:] for p in base]
        target = targets[semantic]
        for j, i in enumerate(target['indices']):
            for k in range(3):
                posed[i][k] += target['deltas'][j*3+k]
        pax, pay = posed[a][:2];pbx, pby = posed[b][:2]
        pdx, pdy = pbx-pax, pby-pay
        plen = math.hypot(pdx, pdy)
        if plen < 1e-6:
            continue
        # Preserve vertical spike relief while keeping the authored horizontal
        # trajectory. Rotating the entire rest chevron can turn it into a fin.
        if abs(dx) < 1e-6 or abs(pdx) < 1e-6:
            continue
        relief = ty-(ay+(tx-ax)/dx*dy)
        current_chord = pay+(posed[tip][0]-pax)/pdx*pdy
        sign = 1 if relief > 0 else -1
        remaining = max(0, (posed[tip][1]-current_chord)*sign)
        boost = max(0, abs(relief)-remaining)
        left, right = abs(tx-ax), abs(bx-tx)
        band = max(1e-6, abs(relief)*.6)
        center, edge = posed[guide.get('posed_tip', tip)][:2]
        top = edge-sign*band
        selected, deltas = [], []
        for i, (x, y, _) in enumerate(posed):
            horizontal = max(0, 1-abs(x-center)/(left if x < center else right))
            u = max(0, min(1, (y-top)*sign/band))
            vertical = u*u*(3-2*u)
            displacement = sign*boost*horizontal*vertical
            if abs(displacement) > 1e-8:
                selected.append(i);deltas.extend((0, displacement, 0))
        targets['spike_'+semantic] = dict(indices=selected, deltas=deltas)
