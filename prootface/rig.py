"""Generic spatial rig guides; all reference-specific geometry stays private."""

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
