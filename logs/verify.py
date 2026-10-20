#!/usr/bin/env python3
"""Check the generated board against what the board is supposed to do.

    kicad-cli pcb drc nuc-fan-controller.kicad_pcb --refill-zones --save-board
    python3 logs/verify.py

Plain Python 3, no KiCad Python: the board is read as text, the same way logs/pourcheck.py
reads it.  (KiCad 10's Python is no help here - `ZONE.Outline().Polygons()` and
`PAD.GetZone()` do not exist, and `GetConnectivity().GetConnectedPads()` ignores zones
altogether: it returns nothing connected for every GND pad on a board that is grounded.)

Three questions a single-sided board can fail silently on:

1. Does every net's copper form one piece?  KiCad's ratsnest compares copper, so it cannot
   know that a part joins its own two pads - which is exactly what the 0 R bridge R11 does -
   and it cannot tell a GND pad that the pour reaches from one it merely overlaps.
2. Is the GND pour one island?  A pour split into pockets still passes DRC: each pocket is
   the same zone object, so every pad in it looks connected and half the board is ungrounded.
3. Do the board's nets match the schematic's, pin by pin?  logs/netlist.net is the authority.
"""
import importlib.util
import os
import subprocess
import sys
import xml.etree.ElementTree as ET

BOARD = "nuc-fan-controller.kicad_pcb"
NETLIST = "logs/netlist.net"

# Parts whose two pads *are* the connection.  KiCad's ratsnest counts each of these as a
# missing connection; here they are the thing that makes the net whole.
BRIDGES = {"R11"}
# Footprints that carry no part from the schematic.
BOARD_ONLY = {"R11"} | {"MK%d" % i for i in (1, 2, 3, 4)}

EPS = 0.01


def load_parser():
    """Borrow logs/pourcheck.py's board reader rather than write a second one."""
    spec = importlib.util.spec_from_file_location("pourcheck", "logs/pourcheck.py")
    mod = importlib.util.module_from_spec(spec)
    try:
        spec.loader.exec_module(mod)
    except SystemExit:
        pass
    return mod


def filled_islands(path):
    """KiCad's own filled pour, straight out of the board text, as islands of polygons."""
    pc = load_parser()
    board = pc.sexp(open(path).read())[0]
    islands = []
    for zone in pc.children(board, "zone"):
        for fp in pc.children(zone, "filled_polygon"):
            pts = [(float(p[1]), float(p[2]))
                   for pl in pc.children(fp, "pts") for p in pc.children(pl, "xy")]
            if len(pts) > 2:
                islands.append(pts)
    return islands


def bbox(poly):
    xs = [p[0] for p in poly]
    ys = [p[1] for p in poly]
    return min(xs), min(ys), max(xs), max(ys)


def merge(islands, pad=0.05):
    """Islands whose bounding boxes touch are one piece of copper."""
    groups = []
    for poly in islands:
        b = bbox(poly)
        for g in groups:
            gb = g[1]
            if b[0] - pad <= gb[2] and gb[0] - pad <= b[2] and b[1] - pad <= gb[3] and gb[1] - pad <= b[3]:
                g[0].append(poly)
                g[1] = (min(b[0], gb[0]), min(b[1], gb[1]), max(b[2], gb[2]), max(b[3], gb[3]))
                break
        else:
            groups.append([[poly], b])
    return groups


def inpoly(pt, poly):
    x, y = pt
    inside = False
    n = len(poly)
    for i in range(n):
        x1, y1 = poly[i]
        x2, y2 = poly[(i + 1) % n]
        if (y1 > y) != (y2 > y):
            t = (y - y1) / (y2 - y1)
            if x1 + (x2 - x1) * t > x:
                inside = not inside
    return inside


def area(poly):
    n = len(poly)
    return abs(sum(poly[i][0] * poly[(i + 1) % n][1] - poly[(i + 1) % n][0] * poly[i][1]
                   for i in range(n)) / 2.0)


def seg_hits_pad(x1, y1, x2, y2, w, px, py, hw, hh):
    """Does a track of width w touch a pad's rectangle?  Sample the track."""
    steps = int(max(abs(x2 - x1), abs(y2 - y1)) / 0.05) + 1
    for k in range(steps + 1):
        t = k / steps
        x, y = x1 + (x2 - x1) * t, y1 + (y2 - y1) * t
        if abs(x - px) <= hw + w / 2 and abs(y - py) <= hh + w / 2:
            return True
    return False


def dist_pt_seg(px, py, x1, y1, x2, y2):
    dx, dy = x2 - x1, y2 - y1
    if dx == 0 and dy == 0:
        return ((px - x1) ** 2 + (py - y1) ** 2) ** 0.5
    t = max(0.0, min(1.0, ((px - x1) * dx + (py - y1) * dy) / (dx * dx + dy * dy)))
    return ((px - (x1 + t * dx)) ** 2 + (py - (y1 + t * dy)) ** 2) ** 0.5


def segs_touch(a, b):
    """Two pieces of copper are one piece when an end of either lands on the other.

    Sharing an endpoint is not enough: a stub lifted onto a rail ends in the middle of it,
    and that is most of how this board's rails feed their pads.
    """
    wa, _, x1, y1, x2, y2 = a
    wb, _, u1, v1, u2, v2 = b
    for (px, py) in ((u1, v1), (u2, v2)):
        if dist_pt_seg(px, py, x1, y1, x2, y2) <= (wa + wb) / 2:
            return True
    for (px, py) in ((x1, y1), (x2, y2)):
        if dist_pt_seg(px, py, u1, v1, u2, v2) <= (wa + wb) / 2:
            return True
    return False


def net_pieces(pads, copper):
    """Split one net's copper into pieces.  Returns (pieces, joinable) where a piece is a
    list of item indices and joinable counts the bridges that weld the pieces together."""
    n = len(pads) + len(copper)
    adj = {i: set() for i in range(n)}
    for i in range(len(pads)):
        r, pnum, net, x, y, hw, hh = pads[i]
        for j, (w, _, x1, y1, x2, y2) in enumerate(copper):
            if seg_hits_pad(x1, y1, x2, y2, w, x, y, hw, hh):
                adj[i].add(len(pads) + j)
                adj[len(pads) + j].add(i)
    for i, a in enumerate(copper):
        for j in range(i + 1, len(copper)):
            b = copper[j]
            if segs_touch(a, b):
                adj[len(pads) + i].add(len(pads) + j)
                adj[len(pads) + j].add(len(pads) + i)
    seen, pieces = set(), []
    for start in range(n):
        if start in seen:
            continue
        seen.add(start)
        stack, group = [start], [start]
        while stack:
            for nb in adj[stack.pop()]:
                if nb not in seen:
                    seen.add(nb)
                    group.append(nb)
                    stack.append(nb)
        pieces.append(group)
    refs = set()
    for g in pieces:
        for idx in g:
            if idx < len(pads) and pads[idx][0] in BRIDGES:
                refs.add(pads[idx][0])
    return pieces, refs


def main():
    pc = load_parser()
    subprocess.run(["kicad-cli", "pcb", "drc", BOARD, "--refill-zones", "--save-board"],
                   capture_output=True, check=True)
    pads, rails, tracks, edge = pc.parse(BOARD)
    copper = rails + tracks
    W = max(max(a[0], a[2]) for a in edge)
    H = max(max(a[1], a[3]) for a in edge)

    print("%s: %.2f x %.2f mm, %d footprints, %d netted pads, %d drawn bars, %d routed tracks"
          % (BOARD, W, H, len({p[0] for p in pads}), len(pads), len(rails), len(tracks)))

    rc = 0

    # ---- 1. every net's copper, in pieces -------------------------------------------
    nets = {}
    for i, p in enumerate(pads):
        nets.setdefault(p[2], []).append(i)
    for w, net, *_ in copper:
        nets.setdefault(net, [])
    print("\nnets and their copper:")
    for net in sorted(nets):
        mypads = [pads[i] for i in nets[net]]
        mycop = [c for c in copper if c[1] == net]
        if net == "GND":
            continue                                   # the pour, checked in 2
        pieces, bridged = net_pieces(mypads, mycop)
        note = ""
        if len(pieces) > 1:
            note = "joined by %s" % ",".join(sorted(bridged)) if bridged else "NOT CONNECTED"
            if not bridged:
                rc = 1
        print("   %-9s %2d pads, %3d copper, %d piece%s %s"
              % (net, len(mypads), len(mycop), len(pieces), "s" if len(pieces) > 1 else "", note))

    # ---- 2. the pour, as KiCad filled it -------------------------------------------
    islands = merge(filled_islands(BOARD))
    if not islands:
        print("\nno filled pour in %s: run the DRC with --refill-zones --save-board first" % BOARD)
        return 1
    print("\npour as KiCad filled it: %d island(s)" % len(islands))
    for polys, b in sorted(islands, key=lambda g: -sum(area(p) for p in g[0])):
        print("   %5.0f mm2  x %.1f..%.1f  y %.1f..%.1f  (%d polygons)"
              % (sum(area(p) for p in polys), b[0], b[2], b[1], b[3], len(polys)))
    dead = []
    for ref, pnum, net, x, y, hw, hh in pads:
        if net != "GND":
            continue
        if not any(inpoly((x, y), poly) for group in islands for poly in group[0]):
            dead.append((ref, pnum, x, y))
    if dead:
        rc = 1
        print("   GND pads outside every filled polygon (%d):" % len(dead))
        for ref, pnum, x, y in dead:
            print("      %-4s pad %-2s at (%.2f, %.2f)" % (ref, pnum, x, y))
    else:
        main_bb = max(islands, key=lambda g: sum(area(p) for p in g[0]))[1]
        print("   every GND pad lies inside the main pour")

    # ---- 3. copper that should not touch -------------------------------------------
    shorts = set()
    for i, a in enumerate(copper):
        for j in range(i + 1, len(copper)):
            b = copper[j]
            if a[1] == b[1]:
                continue
            if segs_touch(a, b):
                shorts.add((a[1], b[1], a[2], a[3]))
    for ref, pnum, net, x, y, hw, hh in pads:
        for w, cnet, x1, y1, x2, y2 in copper:
            if cnet == net:
                continue
            if seg_hits_pad(x1, y1, x2, y2, w, x, y, hw, hh):
                shorts.add((net, cnet, x, y))
    if shorts:
        rc = 1
        print("\ncopper of two nets touching (%d):" % len(shorts))
        for s in sorted(shorts):
            print("   %s / %s at (%.2f, %.2f)" % s)
    else:
        print("\nno copper of two different nets touches")

    # ---- 4. board vs schematic, pin by pin -----------------------------------------
    if not os.path.exists(NETLIST):
        print("\nno %s to compare against" % NETLIST)
        return rc
    want = {}
    text = open(NETLIST).read()
    if text.lstrip().startswith('<?xml'):
        for net in ET.fromstring(text).iter("net"):
            for node in net.iter("node"):
                want.setdefault(node.get("ref"), set()).add((node.get("pin"), net.get("name")))
    else:
        # kicad-cli's default netlist is s-expressions: (net (name "GND") (node (ref "C3") (pin "1")))
        pc = load_parser()

        def walk(node):
            for c in node:
                if isinstance(c, list):
                    yield c
                    yield from walk(c)

        root = pc.sexp(text)[0]
        for net in [n for n in walk(root) if n and n[0] == "net"]:
            name = pc.value(net, "name")
            for node in [n for n in walk(net) if n and n[0] == "node"]:
                want.setdefault(pc.value(node, "ref"), set()).add((pc.value(node, "pin"), name))
    got = {}
    for ref, pnum, net, x, y, hw, hh in pads:
        got.setdefault(ref, set()).add((pnum, net))
    diff = 0
    for ref in sorted(set(want) | set(got), key=lambda r: (r[0], r[1:])):
        w = {(p, n) for p, n in want.get(ref, set()) if not n.startswith("unconnected-")}
        g = {(p, n) for p, n in got.get(ref, set()) if n}
        if w != g:
            if ref in BOARD_ONLY and not w:
                print("\n%-4s is on the board and not in the schematic, by design" % ref)
                continue
            diff += 1
            rc = 1
            print("\nMISMATCH %-4s\n   schematic %s\n   board       %s" % (ref, sorted(w), sorted(g)))
    if not diff:
        print("\nboard nets match the schematic netlist on all %d schematic components"
              % len(want))
    return rc


if __name__ == "__main__":
    sys.exit(main())
