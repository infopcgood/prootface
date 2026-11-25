"""Compile private rest masks into a flat-screen character (no avatar keys).

Optional import-only dependencies: numpy, scipy, contourpy, Pillow.
python tools/compile_character.py local/character-source local/character.json
Generated outlines are derived from the user's asset; keep them under local/.
"""
import argparse
import json
from pathlib import Path

import contourpy
import numpy as np
from PIL import Image
from scipy import ndimage


def simplify(points, tolerance=1.5):
    """Ramer-Douglas-Peucker simplification, retaining the original silhouette."""
    if len(points) <= 2:
        return points
    start, end = points[0], points[-1]
    direction = end-start
    length = np.linalg.norm(direction)
    distances = (np.linalg.norm(points-start, axis=1) if length < 1e-9 else
                 np.abs(direction[0]*(points[:,1]-start[1])-
                        direction[1]*(points[:,0]-start[0]))/length)
    index = int(np.argmax(distances))
    if distances[index] <= tolerance:
        return np.array([start, end])
    return np.concatenate((simplify(points[:index+1], tolerance)[:-1],
                           simplify(points[index:], tolerance)))


def compile_side(path, flip):
    image = np.array(Image.open(path).convert('RGB'))
    if flip:
        image = image[:, ::-1].copy()
    height, width = image.shape[:2]
    labels, _ = ndimage.label(image.max(axis=2) > 40)
    candidates = []
    for label, box in enumerate(ndimage.find_objects(labels), 1):
        if box is not None:
            area = int(np.count_nonzero(labels[box] == label))
            if area > 100:
                candidates.append((area, label, box))
    if len(candidates) != 3:
        raise ValueError(f'Expected visible eye, mouth and nose; found {len(candidates)} in {path}')
    # This face adapter expects one visible eye, nose and mouth per side mask.
    ordered = sorted(candidates, key=lambda c: c[2][0].start)
    names = {ordered[0][1]: 'eye', ordered[-1][1]: 'mouth', ordered[1][1]: 'nose'}
    parts = []
    for _, label, box in candidates:
        mask = labels == label
        lines = contourpy.contour_generator(z=mask.astype(float)).lines(.5)
        line = max(lines, key=len)
        outline = simplify(line)[:-1]
        left, right = box[1].start, box[1].stop-1
        top, bottom = np.zeros(width), np.zeros(width)
        for x in range(left, right+1):
            rows = np.flatnonzero(mask[:, x])
            if len(rows):
                top[x], bottom[x] = rows[0]-.5, rows[-1]+.5
        points = []
        for x, y in outline:
            column = int(np.clip(round(x), left, right))
            lower = np.clip((y-top[column])/max(1, bottom[column]-top[column]), 0, 1)
            points.append([round((x/(width-1)-.5)*3.76, 7),
                           round((.5-y/(height-1))*2.32-.14, 7),
                           round(float(np.clip((x-left)/max(1,right-left),0,1)), 7),
                           round(float(lower), 7)])
        parts.append(dict(name=names[label], points=points))
    return dict(parts=parts)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('source', type=Path)
    parser.add_argument('output', type=Path)
    parser.add_argument('--color', type=float, nargs=3, default=[.2,.8,1])
    args = parser.parse_args()
    if any(not 0<=v<=1 for v in args.color):
        parser.error('Color channels must be between zero and one')
    character = dict(schema=1, name='User-provided rest face',
                     provenance='Private projection of supplied rest geometry. No avatar animation keys.',
                     color=args.color+[1],
                     sides={side:compile_side(args.source/(side+'.png'), side=='right')
                            for side in ('left','right')})
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(character, separators=(',',':'))+'\n')
    print(args.output)
    for side, data in character['sides'].items():
        print(side, {p['name']:len(p['points']) for p in data['parts']})


if __name__ == '__main__':
    main()
