#!/usr/bin/env python3
"""Model the GND pour on the generated board and say which GND pads it can reach.

Why this exists: KiCad's DRC treats a zone as one object.  If routed traces and the
power rails wall the pour into pockets, a GND pad sitting in a pocket still counts as
"connected to the GND zone" — the board passes DRC and does not work.  KiCad's own fill
agrees: it fills each pocket separately and never says they are islands.

The model is KiCad's own fill rule, read straight off the board text:
  * copper of another net keeps the zone's clearance (0.70) from the pour;
  * copper of the pour's own net (a GND pad, a GND track) is absorbed by the pour —
    verified against a test board: a same-net track does not split a pour, so a GND
    track can stitch two pockets together;
  * the pour stops 0.5 mm short of the board edge.
So the pour is exactly the flood-filled region of a grid in which only foreign copper,
inflated by its clearance, is blocked.

  python3 logs/pourcheck.py            # report + logs/pour.png
"""
import re
import sys
from collections import deque

import numpy as np

BOARD = sys.argv[1] if len(sys.argv) > 1 else "nuc-fan-controller.kicad_pcb"
PNG = "logs/pour.png"
CELL = 0.10            # grid, mm
CLEAR = 0.70           # zone clearance to foreign copper
EDGE = 0.50            # pour standoff from Edge.Cuts


# --- the board is a nested list of tokens; read it as one -------------------------
def sexp(text):
    out, stack = [], []
    i, n = 0, len(text)
    while i < n:
        c = text[i]
        if c == "(":
            stack.append(out)
            out = []
            i += 1
        elif c == ")":
            top = stack.pop()
            top.append(out)
            out = top
            i += 1
        elif c in " \t\r\n":
            i += 1
        elif c == '"':
            j = i + 1
            while text[j] != '"':
                j += 1
            out.append(text[i + 1:j])
            i = j + 1
        else:
            j = i
            while j < n and text[j] not in " \t\r\n()":
                j += 1
            out.append(text[i:j])
            i = j
    return out


def num(x):
    return float(x)


def children(node, name):
    return [c for c in node if isinstance(c, list) and c and c[0] == name]


def args(node, name, default=()):
    """The arguments of a child node: (at 1 2 3) -> ["1", "2", "3"]."""
    for c in node:
        if isinstance(c, list) and c and c[0] == name:
            return c[1:]
    return default


def value(node, name, default=None):
    """The single value of a child node: (net "GND") -> "GND"."""
    a = args(node, name)
    return a[0] if a else default


def parse(path):
    board = sexp(open(path).read())
    board = board[0] if board and isinstance(board[0], list) else board
    pads, rails, tracks, edge = [], [], [], []

    for fp in children(board, "footprint"):
        lib = fp[1]
        at = args(fp, "at")
        ox, oy, rot = num(at[0]), num(at[1]), num(at[2]) if len(at) > 2 else 0.0
        ref = next((c[2] for c in children(fp, "property") if c[1] == "Reference"), lib)
        for pad in children(fp, "pad"):
            pnum, kind, shape = pad[1], pad[2], pad[3]
            xy = args(pad, "at") or args(pad, "xy") or ("0", "0")
            size = args(pad, "size") or ("1", "1")
            net = value(pad, "net")
            if not net:
                continue
            lx, ly = num(xy[0]), num(xy[1])
            a = int(round(rot)) % 360
            lx, ly = {0: (lx, ly), 90: (ly, -lx), 180: (-lx, -ly), 270: (-ly, lx)}[a]
            pads.append((ref, pnum, net, ox + lx, oy + ly, num(size[0]) / 2, num(size[1]) / 2))

    for g in children(board, "gr_line"):
        s, e = args(g, "start"), args(g, "end")
        layer = value(g, "layer")
        net = value(g, "net")
        stroke = next((c for c in g if isinstance(c, list) and c and c[0] == "stroke"), None)
        w = num(args(stroke, "width")[0]) if stroke else 0.1
        if layer == "Edge.Cuts":
            edge.append((num(s[0]), num(s[1]), num(e[0]), num(e[1])))
        elif layer == "F.Cu":
            rails.append((w, net, num(s[0]), num(s[1]), num(e[0]), num(e[1])))

    for seg in children(board, "segment"):
        if value(seg, "layer") != "F.Cu":
            continue
        s, e = args(seg, "start"), args(seg, "end")
        tracks.append((num(args(seg, "width")[0]), value(seg, "net"),
                       num(s[0]), num(s[1]), num(e[0]), num(e[1])))

    for gr in children(board, "gr_rect"):
        if value(gr, "layer") == "Edge.Cuts":
            s, e = args(gr, "start"), args(gr, "end")
            edge += [(num(s[0]), num(s[1]), num(e[0]), num(s[1])),
                     (num(e[0]), num(s[1]), num(e[0]), num(e[1])),
                     (num(e[0]), num(e[1]), num(s[0]), num(e[1])),
                     (num(s[0]), num(e[1]), num(s[0]), num(s[1]))]
    return pads, rails, tracks, edge


def main():
    pads, rails, tracks, edge = parse(BOARD)
    W = max(max(a[0], a[2]) for a in edge)
    H = max(max(a[1], a[3]) for a in edge)
    nx, ny = int(round(W / CELL)) + 1, int(round(H / CELL)) + 1
    free = np.ones((ny, nx), dtype=bool)

    def block_rect(x0, y0, x1, y1):
        i0, i1 = max(0, int(np.floor(x0 / CELL))), min(nx - 1, int(np.ceil(x1 / CELL)))
        j0, j1 = max(0, int(np.floor(y0 / CELL))), min(ny - 1, int(np.ceil(y1 / CELL)))
        if i1 >= i0 and j1 >= j0:
            free[j0:j1 + 1, i0:i1 + 1] = False

    def block_seg(x1, y1, x2, y2, half):
        steps = int(max(abs(x2 - x1), abs(y2 - y1)) / (CELL / 2)) + 1
        for k in range(steps + 1):
            t = k / steps
            block_rect(x1 + (x2 - x1) * t - half, y1 + (y2 - y1) * t - half,
                       x1 + (x2 - x1) * t + half, y1 + (y2 - y1) * t + half)

    for w, net, x1, y1, x2, y2 in rails + tracks:
        if net == "GND":
            continue
        block_seg(x1, y1, x2, y2, w / 2 + CLEAR)
    for ref, num_, net, x, y, hw, hh in pads:
        if net == "GND":
            continue
        block_rect(x - hw - CLEAR, y - hh - CLEAR, x + hw + CLEAR, y + hh + CLEAR)
    e = int(np.ceil(EDGE / CELL))
    free[:e, :] = free[ny - e:, :] = False
    free[:, :e] = free[:, nx - e:] = False

    label = np.zeros((ny, nx), dtype=np.int32)
    regions = []
    nxt = 0
    for sj in range(ny):
        for si in range(nx):
            if not free[sj, si] or label[sj, si]:
                continue
            nxt += 1
            q = deque([(sj, si)])
            label[sj, si] = nxt
            n = 0
            j0 = j1 = sj
            i0 = i1 = si
            while q:
                j, i = q.popleft()
                n += 1
                j0 = min(j0, j); j1 = max(j1, j); i0 = min(i0, i); i1 = max(i1, i)
                for dj, di in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    jj, ii = j + dj, i + di
                    if 0 <= jj < ny and 0 <= ii < nx and free[jj, ii] and not label[jj, ii]:
                        label[jj, ii] = nxt
                        q.append((jj, ii))
            regions.append((nxt, n, (i0 * CELL, j0 * CELL, i1 * CELL, j1 * CELL)))
    regions.sort(key=lambda r: -r[1])
    main_id = regions[0][0]

    print("%s: %.2f x %.2f mm, %d netted pads, %d rail segments, %d routed tracks"
          % (BOARD, W, H, len(pads), len(rails), len(tracks)))
    print("pour regions (KiCad's fill rule on a %.2f mm grid):" % CELL)
    for rid, n, bb in regions:
        print("   region %d: %5.0f mm2  x %.1f..%.1f  y %.1f..%.1f%s"
              % (rid, n * CELL * CELL, bb[0], bb[2], bb[1], bb[3],
                 "   <- main" if rid == main_id else ""))

    dead = []
    for ref, pnum, net, x, y, hw, hh in pads:
        if net != "GND":
            continue
        i0, i1 = int(round((x - hw) / CELL)), int(round((x + hw) / CELL))
        j0, j1 = int(round((y - hh) / CELL)), int(round((y + hh) / CELL))
        ids = set(label[max(0, j0):j1 + 1, max(0, i0):i1 + 1].ravel())
        ids.discard(0)
        if main_id not in ids:
            dead.append((ref, pnum, x, y, sorted(ids)))
    if dead:
        print("\nGND pads the main pour cannot reach (%d):" % len(dead))
        for ref, pnum, x, y, ids in dead:
            print("   %-4s pad %-2s at (%.2f, %.2f)  only in region(s) %s" % (ref, pnum, x, y, ids))
    else:
        print("\nevery GND pad sits in the main pour")

    img = np.ones((ny, nx, 3))
    img[label == 0] = (1, 1, 1)
    img[label == main_id] = (0.78, 0.84, 0.90)
    for rid, n, bb in regions[1:]:
        if n * CELL * CELL < 0.5:
            continue
        img[label == rid] = (0.95, 0.55, 0.55)
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    fig, ax = plt.subplots(figsize=(W / 9.0, H / 9.0), dpi=140)
    ax.imshow(img, extent=(0, W, H, 0))
    for w, net, x1, y1, x2, y2 in rails + tracks:
        ax.plot([x1, x2], [y1, y2], color="black", lw=max(0.7, w * 2.0),
                ls="-" if net in ("+12V", "FAN_SW", "19V", "+3V3") else "--")
    for ref, pnum, net, x, y, hw, hh in pads:
        ax.add_patch(plt.Rectangle((x - hw, y - hh), 2 * hw, 2 * hh,
                                   facecolor="none",
                                   edgecolor="red" if net == "GND" else "black", lw=0.8))
        ax.text(x, y, "%s%s" % (ref, pnum), fontsize=4.2, ha="center", va="center")
    ax.set_xlim(0, W); ax.set_ylim(H, 0)
    ax.set_xticks(range(0, int(W) + 1, 10)); ax.set_yticks(range(0, int(H) + 1, 10))
    ax.grid(alpha=.25, lw=.4)
    fig.tight_layout()
    fig.savefig(PNG)
    print("wrote %s" % PNG)
    return 1 if dead else 0


if __name__ == "__main__":
    sys.exit(main())
