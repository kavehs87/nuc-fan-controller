#!/usr/bin/env python3
"""The GND feed that used to run from Q2's old collector pad into R7's pad 2 is
orphaned by the pad swap: its far end now sits in mid-air at (94.9092,73.8292)
and it crowds the jogged BASE run to 0.07 mm.  It goes away; R7's pad 2 is a
through-hole pad inside the GND pour and takes GND from the zone.
"""
import re

PCB = 'nuc-fan-controller.kicad_pcb'
DROP = ['2e22af3b', '979cca8a']

src = open(PCB).read()
lines = src.split('\n')
keep, cur, dropped = [], None, []
for l in lines:
    if cur is None:
        if l == '\t(segment': cur = [l]
        else: keep.append(l)
        continue
    cur.append(l)
    if l != '\t)':
        continue
    body = '\n'.join(cur)
    u = re.search(r'\(uuid "([^"]{8})', body).group(1)
    if u in DROP:
        dropped.append((u, re.search(r'\(start [^\n]*', body).group(0)))
    else:
        keep.extend(body.split('\n'))
    cur = None
assert len(dropped) == 2, dropped
for d in dropped: print('dropped segment', d)
open(PCB, 'w').write('\n'.join(keep))
