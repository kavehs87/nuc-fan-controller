#!/usr/bin/env python3
"""Two things the first pass left behind.

1. BASE's mid-run used to pass 0.20 mm under Q2's pad 1.  Pad 1 is the emitter now
   (it was the collector before the BC547 pin-order fix), so that run is a
   clearance violation against a live GND pad.  It is jogged down to y=74.75,
   which clears the pad by 0.40 mm and stays clear of R7's pad 2.
2. A stray +12V stitching via at (132.45,67.45) has copper on one layer only.
   It serves nothing and the new +12V leg to J7 runs through it, so it goes.
"""
import re

PCB = 'nuc-fan-controller.kicad_pcb'
src = open(PCB).read()

MOVE = {
    '5b29ed9a': ((84.1263, 75.1263), (89.5,   75.1263)),
    'fe3a2c33': ((89.5,    75.1263), (89.8763, 74.75)),
    'c789ad57': ((89.8763, 74.75),   (93.3,    74.75)),
    'f5572583': ((93.3,    74.75),   (94.54,   76)),
}

lines = src.split('\n')
keep, cur, kind, moved = [], None, None, 0
for l in lines:
    if cur is None:
        if l in ('\t(segment', '\t(via'):
            cur, kind = [l], l[2:]
        else:
            keep.append(l)
        continue
    cur.append(l)
    if l != '\t)':
        continue
    body = '\n'.join(cur)
    if kind == 'segment':
        u = re.search(r'\(uuid "([^"]{8})', body).group(1)
        if u in MOVE:
            (x1, y1), (x2, y2) = MOVE[u]
            body = re.sub(r'\(start [-\d.]+ [-\d.]+\)\n\t\t\(end [-\d.]+ [-\d.]+\)',
                          '(start %s %s)\n\t\t(end %s %s)' % (x1, y1, x2, y2), body, count=1)
            moved += 1
            print('moved', u, (x1, y1), (x2, y2))
    elif kind == 'via' and '(at 132.45 67.45)' in body:
        print('deleted stray via (132.45,67.45) — net +12V, copper on one layer only')
        cur, kind = None, None
        continue
    keep.extend(body.split('\n'))
    cur, kind = None, None
assert moved == 4, moved
src = '\n'.join(keep)

open(PCB, 'w').write(src)
