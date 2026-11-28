"""Offline construction of expression-specific speech endpoints and correctives.

Settings supply artistic choices. No source-asset mappings or geometry are built
into this module. Rest plus a shape correction reconstructs authored expression;
optional articulation corrections independently receive front motion restraint.
"""
import math

from .expressions import EXPRESSIONS, PHASES
from .rig import split_at_horizontal_boundaries


def _smooth(value):
    value = min(1., max(0., value))
    return value*value*(3-2*value)


def compile_expression_sets(character, definitions):
    if not definitions:
        return
    positions = character['positions']
    targets = character['targets']
    active = {i for name in PHASES for i in targets.get(name, {}).get('indices', [])}
    if not active:
        raise ValueError('Expression speech banks require a mouth basis')
    front, rear = min(positions[3*i] for i in active), max(positions[3*i] for i in active)
    bottom, top = min(positions[3*i+1] for i in active), max(positions[3*i+1] for i in active)
    span, height = rear-front, top-bottom
    if min(span, height) <= 1e-8:
        raise ValueError('Expression speech basis has no usable extent')
    feather = height*.04
    # Keep features above the deformation field stationary even on coarse faces.
    split_at_horizontal_boundaries(character, (top, top+feather))
    positions = character['positions']
    count = len(positions)//3

    def dense(name):
        if name not in targets:
            raise ValueError('Unknown expression source target: ' + name)
        result = [[0., 0., 0.] for _ in range(count)]
        target = targets[name]
        for j, i in enumerate(target['indices']):
            result[i] = target['deltas'][3*j:3*j+3]
        return result

    basis = {phase: dense(phase) for phase in PHASES}
    zeros = [[0., 0., 0.] for _ in range(count)]

    def endpoint(specification, phase):
        scales = specification.get('motion_scale', [1., 1., 1.])
        if (len(scales) != 3 or not all(math.isfinite(v) and .5 <= v <= 1.5 for v in scales)):
            raise ValueError('Expression motion_scale must have three values in [0.5,1.5]')
        bend, slope = specification.get('bend', 0.), specification.get('slope', 0.)
        if not all(math.isfinite(v) and abs(v) <= .5 for v in (bend, slope)):
            raise ValueError('Expression curvature exceeds bounds')
        speech = basis.get(phase, zeros)
        motion = [[delta[k]*(scales[k]-1) for k in range(3)] for delta in speech]
        result = [[0., 0., 0.] for _ in range(count)]
        for source, weight in specification.get('sources', {}).items():
            if not math.isfinite(weight) or not -1 <= weight <= 1:
                raise ValueError('Expression source weight outside [-1,1]')
            for point, delta in zip(result, dense(source)):
                for k in range(3):
                    point[k] += weight*delta[k]
        for i, delta in enumerate(result):
            x, y = positions[3*i:3*i+2]
            t = (x-front)/span
            envelope = (_smooth((top+feather-y)/feather)
                        * _smooth(t/.3) * (1-_smooth((t-1)/.15)))
            u = min(1., max(0., t))
            delta[1] += height * envelope * (bend*4*u*(1-u) + slope*u)
        return result, motion

    def sparse(values):
        indices, deltas = [], []
        for i, delta in enumerate(values):
            if max(map(abs, delta)) > 1e-9:
                indices.append(i)
                deltas.extend(delta)
        return dict(indices=indices, deltas=deltas)

    banks = {}
    front_targets = set(character.get('front_targets', []))
    for name, definition in definitions.items():
        if name not in EXPRESSIONS[1:]:
            raise ValueError('Unsupported expression: ' + name)
        mouth = definition['mouth']
        if not any(weight != 0 for spec in mouth.values()
                   for weight in spec.get('sources', {}).values()):
            raise ValueError('Expression bank requires an authored mouth source: ' + name)
        rest, _ = endpoint(mouth['rest'], 'rest')
        bank = {}
        rest_name = 'expr_' + name + '_rest'
        targets[rest_name] = sparse(rest)
        bank['rest'] = rest_name
        for phase in PHASES:
            shape, motion = endpoint(mouth[phase], phase)
            correction = [[shape[i][k]-rest[i][k]
                           for k in range(3)] for i in range(count)]
            target_name = 'expr_' + name + '_' + phase
            targets[target_name] = sparse(correction)
            # Emotion is a shape change, independent of anterior speech restraint.
            # Scaling its rest cancellation would leave a residual smile/frown.
            front_targets.discard(target_name)
            bank[phase] = target_name
            if any(any(delta) for delta in motion):
                motion_name = target_name + '_motion'
                targets[motion_name] = sparse(motion)
                front_targets.add(motion_name)
                bank[phase + '_motion'] = motion_name
        for side in ('left', 'right'):
            target_name = definition['eyes'][side]
            if target_name not in targets:
                raise ValueError('Missing authored eye target: ' + target_name)
            bank['eye_' + side] = target_name
        banks[name] = bank
    character['expression_sets'] = banks
    character['front_targets'] = sorted(front_targets)
