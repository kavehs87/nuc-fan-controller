#!/usr/bin/env python3
"""A small single-copper-layer maze router with 0 ohm jumper support.

The board is rasterised on a 0.254 mm (10 mil) grid.  Pads, holes, the board
edge and already routed copper of *other* nets are obstacles.  A* walks the
grid in eight directions and may take a "jumper" move: a straight 5.08 mm hop
over an obstacle, which the caller turns into a 0 ohm resistor standing on the
board.  The jumper is the single-layer answer to a track that has to cross
another track; there are no vias.

The router is deliberately conservative: it keeps `CLEARANCE` millimetres
between copper of different nets and `EDGE` millimetres from the board edge.
"""
from __future__ import annotations

import heapq
import math
from dataclasses import dataclass, field

GRID = 0.254                 # 10 mil raster
JUMP_MM = 5.08               # 0 ohm jumper pitch (0204)
JUMP_CELLS = round(JUMP_MM / GRID)
JUMP_COST = 120.0            # cell units; a jumper is the last resort


@dataclass
class Pad:
    x: float
    y: float
    sx: float
    sy: float
    shape: str = "circle"
    drill: float = 0.0


@dataclass
class Obstacle:
    kind: str                # 'rect' | 'circle' | 'seg'
    x: float = 0.0
    y: float = 0.0
    sx: float = 0.0
    sy: float = 0.0
    x2: float = 0.0
    y2: float = 0.0
    width: float = 0.0


class Router:
    def __init__(self, w: float, h: float, clearance: float = 0.5,
                 edge: float = 0.5, grid: float = GRID):
        self.w, self.h = w, h
        self.clearance = clearance
        self.edge = edge
        self.g = grid
        self.nx = int(w / grid) + 1
        self.ny = int(h / grid) + 1
        self.pads: dict[str, list[Pad]] = {}
        self.obstacles: list[tuple[str, Obstacle]] = []   # (net, obstacle)
        self.segments: list[dict] = []                    # routed tracks
        self.jumpers: list[dict] = []
        self.failed: list[tuple[str, tuple, tuple]] = []
        self.keepout: list[tuple[float, float, float, float]] = []

    # ------------------------------------------------------------- geometry --
    def add_pad(self, net: str, p: Pad):
        self.pads.setdefault(net, []).append(p)

    def add_obstacle(self, net: str, ob: Obstacle):
        self.obstacles.append((net, ob))

    def add_keepout(self, x1, y1, x2, y2):
        """no jumper pads in here (component courtyards)"""
        self.keepout.append((x1, y1, x2, y2))

    def add_mounting_hole(self, x, y, dia):
        self.obstacles.append(("", Obstacle("circle", x, y, dia, dia)))

    def _mark_rect(self, blocked, cx, cy, sx, sy, value=1):
        g = self.g
        x1 = int(math.floor((cx - sx) / g))
        x2 = int(math.ceil((cx + sx) / g))
        y1 = int(math.floor((cy - sy) / g))
        y2 = int(math.ceil((cy + sy) / g))
        for iy in range(max(0, y1), min(self.ny - 1, y2) + 1):
            base = iy * self.nx
            for ix in range(max(0, x1), min(self.nx - 1, x2) + 1):
                blocked[base + ix] = value

    def _mark_disc(self, blocked, cx, cy, r, value=1):
        g = self.g
        x1 = int(math.floor((cx - r) / g))
        x2 = int(math.ceil((cx + r) / g))
        y1 = int(math.floor((cy - r) / g))
        y2 = int(math.ceil((cy + r) / g))
        r2 = (r + g) ** 2
        for iy in range(max(0, y1), min(self.ny - 1, y2) + 1):
            dy = iy * g - cy
            base = iy * self.nx
            for ix in range(max(0, x1), min(self.nx - 1, x2) + 1):
                dx = ix * g - cx
                if dx * dx + dy * dy <= r2:
                    blocked[base + ix] = value

    def _mark_segment(self, blocked, x1, y1, x2, y2, width, value=1):
        length = math.hypot(x2 - x1, y2 - y1)
        n = max(1, int(length / (self.g * 0.5)) + 1)
        for k in range(n + 1):
            t = k / n
            self._mark_disc(blocked, x1 + (x2 - x1) * t, y1 + (y2 - y1) * t,
                            width / 2, value)

    def blocked_grid(self, net: str, width: float) -> bytearray:
        """Everything another net must not touch while routing `net`."""
        blocked = bytearray(self.nx * self.ny)
        infl = self.clearance + width / 2
        # board edge
        edge_cells = int(math.ceil((self.edge + width / 2) / self.g))
        for iy in range(self.ny):
            for ix in range(self.nx):
                if ix < edge_cells or ix >= self.nx - edge_cells or \
                   iy < edge_cells or iy >= self.ny - edge_cells:
                    blocked[iy * self.nx + ix] = 1
        for onet, ob in self.obstacles:
            if onet == net:
                continue
            if ob.kind == "circle":
                self._mark_disc(blocked, ob.x, ob.y, ob.sx / 2 + infl)
            elif ob.kind == "rect":
                self._mark_rect(blocked, ob.x, ob.y,
                                ob.sx / 2 + infl, ob.sy / 2 + infl)
            else:
                self._mark_segment(blocked, ob.x, ob.y, ob.x2, ob.y2,
                                   ob.width + 2 * infl)
        for s in self.segments:
            if s["net"] == net:
                continue
            self._mark_segment(blocked, s["x1"], s["y1"], s["x2"], s["y2"],
                               s["width"] + 2 * infl)
        for j in self.jumpers:
            if j["net"] == net:
                continue
            self._mark_disc(blocked, j["x1"], j["y1"], 0.8 + infl)
            self._mark_disc(blocked, j["x2"], j["y2"], 0.8 + infl)
        return blocked

    def copper_grid(self, net: str) -> bytearray:
        """other nets' copper, inflated by clearance + jumper pad radius"""
        blocked = bytearray(self.nx * self.ny)
        infl = self.clearance + 0.8
        for onet, ob in self.obstacles:
            if onet == net:
                continue
            if ob.kind == "circle":
                self._mark_disc(blocked, ob.x, ob.y, ob.sx / 2 + infl)
            elif ob.kind == "rect":
                self._mark_rect(blocked, ob.x, ob.y, ob.sx / 2 + infl,
                                ob.sy / 2 + infl)
            else:
                self._mark_segment(blocked, ob.x, ob.y, ob.x2, ob.y2,
                                   ob.width + 2 * infl)
        for s in self.segments:
            if s["net"] == net:
                continue
            self._mark_segment(blocked, s["x1"], s["y1"], s["x2"], s["y2"],
                               s["width"] + 2 * infl)
        for j in self.jumpers:
            if j["net"] == net:
                continue
            self._mark_disc(blocked, j["x1"], j["y1"], 0.8 + infl)
            self._mark_disc(blocked, j["x2"], j["y2"], 0.8 + infl)
        return blocked

    def pad_grid(self, net: str) -> bytearray:
        """pads and holes only, used to sanity check a jumper landing"""
        blocked = bytearray(self.nx * self.ny)
        for onet, ob in self.obstacles:
            if onet == net:
                continue
            if ob.kind == "circle":
                self._mark_disc(blocked, ob.x, ob.y, ob.sx / 2 + 0.3)
            elif ob.kind == "rect":
                self._mark_rect(blocked, ob.x, ob.y, ob.sx / 2 + 0.3,
                                ob.sy / 2 + 0.3)
        return blocked

    # ---------------------------------------------------------------- routing --
    def cell(self, x, y):
        return (max(0, min(self.nx - 1, int(round(x / self.g)))),
                max(0, min(self.ny - 1, int(round(y / self.g)))))

    def free_near(self, blocked, ix, iy, radius=6):
        if not blocked[iy * self.nx + ix]:
            return ix, iy
        for r in range(1, radius + 1):
            for dx in range(-r, r + 1):
                for dy in range(-r, r + 1):
                    if max(abs(dx), abs(dy)) != r:
                        continue
                    jx, jy = ix + dx, iy + dy
                    if 0 <= jx < self.nx and 0 <= jy < self.ny and \
                       not blocked[jy * self.nx + jx]:
                        return jx, jy
        return None

    def astar(self, blocked, start, goal, allow_jumps=True, padgrid=None,
              copper=None):
        nx, ny = self.nx, self.ny
        g = self.g
        sx, sy = start
        gx, gy = goal
        start_i = sy * nx + sx
        goal_i = gy * nx + gx
        INF = float("inf")
        dist = {start_i: 0.0}
        prev = {}
        jumped = {}
        h = lambda ix, iy: math.hypot(ix - gx, iy - gy)
        pq = [(h(sx, sy), 0.0, sx, sy)]
        dirs = [(1, 0, 1.0), (-1, 0, 1.0), (0, 1, 1.0), (0, -1, 1.0),
                (1, 1, 1.4142), (1, -1, 1.4142), (-1, 1, 1.4142), (-1, -1, 1.4142)]
        jumps = [(1, 0), (-1, 0), (0, 1), (0, -1)]
        while pq:
            f, d, ix, iy = heapq.heappop(pq)
            i = iy * nx + ix
            if d > dist.get(i, INF):
                continue
            if i == goal_i:
                path = []
                cur = i
                while cur in prev:
                    path.append((cur % nx, cur // nx, jumped.get(cur)))
                    cur = prev[cur]
                path.append((sx, sy, None))
                path.reverse()
                return path
            for dx, dy, c in dirs:
                jx, jy = ix + dx, iy + dy
                if not (0 <= jx < nx and 0 <= jy < ny):
                    continue
                if blocked[jy * nx + jx]:
                    continue
                if dx and dy:
                    # no cutting the corner between two blocked cells
                    if blocked[iy * nx + jx] or blocked[jy * nx + ix]:
                        continue
                nd = d + c
                ni = jy * nx + jx
                if nd < dist.get(ni, INF):
                    dist[ni] = nd
                    prev[ni] = i
                    jumped.pop(ni, None)
                    heapq.heappush(pq, (nd + h(jx, jy), nd, jx, jy))
            if allow_jumps:
                for dx, dy in jumps:
                    jx, jy = ix + dx * JUMP_CELLS, iy + dy * JUMP_CELLS
                    if not (0 <= jx < nx and 0 <= jy < ny):
                        continue
                    if blocked[jy * nx + jx]:
                        continue
                    if self.in_keepout(jx * g, jy * g) or \
                       self.in_keepout(ix * g, iy * g):
                        continue
                    # the pads themselves must sit on free copper
                    if copper[jy * nx + jx] or copper[iy * nx + ix]:
                        continue
                    # the body may bridge tracks, but never a pad or a hole
                    body_ok = True
                    for k in range(4, JUMP_CELLS - 3):
                        cx, cy = ix + dx * k, iy + dy * k
                        if padgrid[cy * nx + cx]:
                            body_ok = False
                            break
                    if not body_ok:
                        continue
                    crossed = False
                    for k in range(3, JUMP_CELLS - 2):
                        cx, cy = ix + dx * k, iy + dy * k
                        if blocked[cy * nx + cx]:
                            crossed = True
                            break
                    if not crossed:
                        continue
                    nd = d + JUMP_COST
                    ni = jy * nx + jx
                    if nd < dist.get(ni, INF):
                        dist[ni] = nd
                        prev[ni] = i
                        jumped[ni] = (ix, iy, jx, jy)
                        heapq.heappush(pq, (nd + h(jx, jy), nd, jx, jy))
        return None

    def simplify(self, pts):
        out = []
        for p in pts:
            if len(out) >= 2:
                a, b = out[-2], out[-1]
                if (a[0] == b[0] == p[0]) or (a[1] == b[1] == p[1]) or \
                   (abs(a[0] - b[0]) == abs(a[1] - b[1]) and
                        abs(b[0] - p[0]) == abs(b[1] - p[1]) and
                        (b[0] - a[0]) * (p[1] - b[1]) ==
                        (b[1] - a[1]) * (p[0] - b[0])):
                    out[-1] = p
                    continue
            out.append(p)
        return out

    def in_keepout(self, x, y):
        for x1, y1, x2, y2 in self.keepout:
            if x1 <= x <= x2 and y1 <= y <= y2:
                return True
        return False

    def route_edge(self, net: str, width: float, a, b, blocked, allow_jumps):
        sx, sy = self.cell(*a)
        gx, gy = self.cell(*b)
        s = self.free_near(blocked, sx, sy)
        t = self.free_near(blocked, gx, gy)
        if s is None or t is None:
            return None
        path = self.astar(blocked, s, t, allow_jumps=allow_jumps,
                          padgrid=self.pad_grid(net),
                          copper=self.copper_grid(net))
        if path is None:
            return None
        # build runs of copper, splitting at every jumper hop
        runs = [[]]
        for idx, (ix, iy, jump) in enumerate(path):
            p = (ix * self.g, iy * self.g)
            if idx == 0:
                runs[-1].append(p)
                continue
            if jump is not None:
                src = (path[idx - 1][0] * self.g, path[idx - 1][1] * self.g)
                runs[-1].append(src)
                cand = dict(net=net, x1=src[0], y1=src[1], x2=p[0], y2=p[1])
                dup = False
                for j in self.jumpers:
                    if j['net'] == net and \
                       min(abs(j['x1'] - cand['x1']) + abs(j['y1'] - cand['y1']),
                           abs(j['x1'] - cand['x2']) + abs(j['y1'] - cand['y2'])) < 1e-6 and \
                       min(abs(j['x2'] - cand['x2']) + abs(j['y2'] - cand['y2']),
                           abs(j['x2'] - cand['x1']) + abs(j['y2'] - cand['y1'])) < 1e-6:
                        dup = True
                        break
                if not dup:
                    self.jumpers.append(cand)
                runs.append([p])
            else:
                runs[-1].append(p)
        if runs and runs[0]:
            runs[0][0] = (a[0], a[1])
        if runs and runs[-1]:
            runs[-1][-1] = (b[0], b[1])
        for run in runs:
            run = self.simplify(run)
            for (x1, y1), (x2, y2) in zip(run, run[1:]):
                if abs(x1 - x2) < 1e-9 and abs(y1 - y2) < 1e-9:
                    continue
                self.segments.append(dict(net=net, x1=x1, y1=y1, x2=x2, y2=y2,
                                          width=width))
        return True

    def route_net(self, name: str, width: float, allow_jumps=False, only=None):
        pads = self.pads.get(name, [])
        if len(pads) < 2:
            return []
        blocked = self.blocked_grid(name, width)
        pts = [(p.x, p.y) for p in pads]
        used = [0]
        left = list(range(1, len(pts)))
        edges = []
        while left:
            best = None
            for i in used:
                for j in left:
                    d = math.hypot(pts[i][0] - pts[j][0], pts[i][1] - pts[j][1])
                    if best is None or d < best[0]:
                        best = (d, i, j)
            _, i, j = best
            edges.append((pts[i], pts[j]))
            used.append(j)
            left.remove(j)
        edges.sort(key=lambda e: math.hypot(e[0][0] - e[1][0], e[0][1] - e[1][1]))
        failed = []
        for a, b in edges:
            if only is not None and (a, b) not in only:
                continue
            if self.route_edge(name, width, a, b, blocked, allow_jumps) is None:
                failed.append((a, b))
            else:
                # keep the working grid in step with the copper we just laid
                blocked = self.blocked_grid(name, width)
        return failed

    def route_all(self, order, allow_jumps=True):
        pending = []
        for name, width in order:
            failed = self.route_net(name, width, allow_jumps=False)
            if failed:
                pending.append((name, width, failed))
        # second pass: only the connections that failed, now allowed to hop
        for name, width, failed in pending:
            again = self.route_net(name, width, allow_jumps=True, only=set(failed))
            for a, b in again:
                self.failed.append((name, a, b))
        return self.segments, self.jumpers, self.failed
