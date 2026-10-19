"""Emit the wires, junctions, power symbols and labels for nuc-fan-controller.

Pin coordinates come from what is actually in the .kicad_sch (placed.py), so a
snap by the placement tool cannot desync the wires from the pins.
"""
import itertools
import math
import sys
import uuid

sys.path.insert(0, ".")
from layout import NETS, POWER, LABELS, NOCONECT, COMPS
from placed import placed, pinmap
from pins import body_box

SCH = "/Users/kaveh/Documents/Projects/nuc-tach-sim/nuc-fan-controller.kicad_sch"


def segs(pts):
    out = []
    prev = None
    for cur in pts:
        if prev is not None and prev != cur:
            ax, ay = prev
            bx, by = cur
            if abs(ax - bx) > 1e-6 and abs(ay - by) > 1e-6:
                out.append(((ax, ay), (bx, ay)))
                out.append(((bx, ay), (bx, by)))
            else:
                out.append(((ax, ay), (bx, by)))
        prev = cur
    return out


def points(name, P):
    out = []
    for it in NETS[name]:
        if isinstance(it[0], str):
            out.append(P[(it[0], str(it[1]))])
        elif it[0] is None:
            out.append(it[1])
        else:
            out.append(it)
    return out


def cross(s1, s2):
    (x1, y1), (x2, y2) = s1
    (x3, y3), (x4, y4) = s2
    h1 = abs(y1 - y2) < 1e-6
    h2 = abs(y3 - y4) < 1e-6
    if h1 == h2:
        return False
    if h1:
        lo, hi = sorted([x1, x2])
        return lo + 1e-6 < x3 < hi - 1e-6 and min(y3, y4) - 1e-6 < y1 < max(y3, y4) + 1e-6
    lo, hi = sorted([y1, y2])
    return min(x3, x4) - 1e-6 < x1 < max(x3, x4) + 1e-6 and lo + 1e-6 < y3 < hi - 1e-6


def main():
    P = pinmap(SCH)
    allsegs = []
    for name in NETS:
        allsegs += [(name, s) for s in segs(points(name, P))]

    bad = [(a, s1, b, s2) for (a, s1), (b, s2) in itertools.combinations(allsegs, 2)
           if a != b and cross(s1, s2)]
    print("cross-net crossings:", len(bad))
    for b in bad:
        print("   ", b)

    # a shared endpoint between two different nets would be a short
    ends = {}
    for name, s in allsegs:
        for p in s:
            ends.setdefault(p, set()).add(name)
    shorts = {p: n for p, n in ends.items() if len(n) > 1}
    print("cross-net shared endpoints:", shorts)

    boxes = []
    for ref, lib, X, Y, A, mir, unit in placed(SCH):
        bb = body_box(lib, X, Y, A, mirrorY=mir)
        if bb:
            boxes.append((ref, bb))
    hits = []
    for ref, bb in boxes:
        for name, (p, q) in allsegs:
            x1, y1, x2, y2 = bb
            if abs(p[1] - q[1]) < 1e-6:
                y = p[1]
                if y1 + 1e-6 < y < y2 - 1e-6 and min(p[0], q[0]) < x2 - 1e-6 and max(p[0], q[0]) > x1 + 1e-6:
                    hits.append((ref, name, (p, q)))
            else:
                x = p[0]
                if x1 + 1e-6 < x < x2 - 1e-6 and min(p[1], q[1]) < y2 - 1e-6 and max(p[1], q[1]) > y1 + 1e-6:
                    hits.append((ref, name, (p, q)))
    print("wires through symbol bodies:", hits)

    # A part is shorted when both of its own pins land on one net. Catch that in the net
    # table instead of waiting for the netlist: an earlier pass put R3.2 on NUC_PWM and the
    # schematic drew a wire straight through the resistor's body, which looked tidy.
    belong, dup = {}, []
    for name in NETS:
        for it in NETS[name]:
            if not isinstance(it[0], str):
                continue
            pin = (it[0], str(it[1]))
            if pin in belong and belong[pin] != name:
                dup.append((pin, belong[pin], name))
            belong[pin] = name
    for lib, items in POWER:
        net = {"power:GND": "GND", "power:+12V": "+12V", "power:+3V3": "+3V3"}.get(lib)
        for it in items:
            if not isinstance(it[0], str):
                continue
            pin = (it[0], str(it[1]))
            if net and pin in belong and belong[pin] != net:
                dup.append((pin, belong[pin], net))
            if net:
                belong[pin] = net
    print("pins on two nets:", dup)
    shorted = []
    for ref, lib, *_ in COMPS:
        nets = {belong[p] for p in belong if p[0] == ref}
        npins = sum(1 for p in belong if p[0] == ref)
        if npins == 2 and len(nets) == 1:
            shorted.append((ref, next(iter(nets))))
    print("parts with both ends on one net:", shorted)

    # every pin of every wired component must be touched by a wire end, a power
    # symbol, a label, a no-connect, or another pin
    covered = set()
    for name in NETS:
        for p in points(name, P):
            covered.add(p)
    for _, items in POWER:
        for it in items:
            covered.add(P[(it[0], str(it[1]))] if isinstance(it[0], str) else it)
    for nm, tgt, _o in LABELS:
        covered.add(P[(tgt[0], str(tgt[1]))] if isinstance(tgt[0], str) else tgt)
    for ref, pin in NOCONECT:
        covered.add(P[(ref, pin)])
    dangling = []
    for ref, lib, X, Y, A, mir, unit in placed(SCH):
        for num, nm, x, y in [(p[0], p[1], round(p[2], 4), round(p[3], 4)) for p in
                              __import__("pins").place(lib, X, Y, A, mirrorY=mir)]:
            if (x, y) not in covered:
                dangling.append((ref, num, nm, (x, y)))
    print("uncovered pins:", dangling)

    # junction dots: three or more wire ends, or a wire end meeting a pin at an angle
    ends = {}
    for name, s in allsegs:
        for i, p in enumerate(s):
            other = s[1 - i]
            d = ((0, 1) if abs(other[1] - p[1]) < 1e-6 and other[0] > p[0] else
                 (0, -1) if abs(other[1] - p[1]) < 1e-6 else
                 (1, 0) if other[1] > p[1] else (-1, 0))
            ends.setdefault(p, []).append(d)
    junctions = []
    for p, ds in sorted(ends.items()):
        dirs = set(ds)
        if len(ds) >= 3 or (len(dirs) >= 3):
            junctions.append(p)
    print("wires:", len(allsegs), " junctions:", len(junctions))
    print("  junction points:", junctions)

    lines = []
    for name, (p, q) in allsegs:
        lines.append("\t(wire\n\t\t(pts\n\t\t\t(xy %.4f %.4f) (xy %.4f %.4f)\n\t\t)\n\t\t(stroke\n\t\t\t(width 0)\n\t\t\t(type default)\n\t\t)\n\t\t(uuid \"%s\")\n\t)"
                     % (p[0], p[1], q[0], q[1], uuid.uuid4()))
    for p in junctions:
        lines.append("\t(junction\n\t\t(at %.4f %.4f)\n\t\t(diameter 0)\n\t\t(color 0 0 0 0)\n\t\t(uuid \"%s\")\n\t)"
                     % (p[0], p[1], uuid.uuid4()))
    open("wires.inc", "w").write("\n".join(lines) + "\n")
    print("wrote wires.inc")


if __name__ == "__main__":
    main()
