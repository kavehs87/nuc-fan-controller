#!/usr/bin/env python3
"""Build the single-layer PCB for the MOSFET fan switch.

Everything on this board is meant to be made at home: toner transfer or UV
photoresist, one copper side (B.Cu), no vias, wide tracks, generous spacing.
Crossings are avoided by placement; where one is unavoidable it is a 0 ohm
resistor standing on end (see JUMPERS below), never a via.

The script writes the board file, prints the pad table it used, and reports
any place where two different nets cross.

    python3 pcb/build_board.py
"""
from __future__ import annotations

import math
import re
import uuid
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BOARD = ROOT / "mosfet-fan-switch.kicad_pcb"
SCHEMATIC = ROOT / "mosfet-fan-switch.kicad_sch"
FP_DIR = Path("/Applications/KiCad/KiCad.app/Contents/SharedSupport/footprints")

# ---------------------------------------------------------------- geometry --
# Home-etch rules of thumb for a 35 um copper board.
CLEARANCE = 0.50     # mm between two different nets
TRACK = 0.80         # signal traces
TRACK_POWER = 2.00   # 12 V and GND buses (~1 A safe at this width)
DRILL_MIN = 0.80

W, H = 56.0, 44.0    # board outline
RAIL_GND_Y = 3.0     # GND bus along the top edge
RAIL_12V_Y = 41.0    # +12 V bus along the bottom edge
SPINE_X = 5.5        # GND return lane down the left edge

# Reference labels sit just outside each part's courtyard, horizontal on the
# board.  REF_AT overrides the default spot when that spot is taken; REF_NONE
# suppresses the label (mounting holes).
REF_AT = {"Q3": (30.5, 26.0), "R2": (18.5, 6.8), "R5": (41.5, 6.0)}
REF_NONE = {"MK1", "MK2", "MK3", "MK4"}


# ------------------------------------------------------------------ nets --
NETS = ["/P12V", "/GND", "/PWM", "/LGATE", "/BOOT", "/HIGATE", "/GATE", "/DRAIN"]
NET_ID = {n: i + 1 for i, n in enumerate(NETS)}


# ------------------------------------------------------------- footprints --
class Quoted(str):
    """a string that was written with quotes in the source file"""


def sexpr(s: str):
    """Minimal s-expression reader: nested lists of strings."""
    tok = re.findall(r'\([^()]*\)|[^\s()]+', s)  # not used; see below
    out, stack = [], []
    i = 0
    while i < len(s):
        c = s[i]
        if c == '(':
            stack.append([])
            i += 1
        elif c == ')':
            done = stack.pop()
            (stack[-1] if stack else out).append(done)
            i += 1
        elif c.isspace():
            i += 1
        elif c == '"':
            j = s.index('"', i + 1)
            (stack[-1] if stack else out).append(Quoted(s[i + 1:j]))
            i = j + 1
        else:
            j = i
            while j < len(s) and not s[j].isspace() and s[j] not in '()':
                j += 1
            (stack[-1] if stack else out).append(s[i:j])
            i = j
    return out


def load_footprint(lib_name: str):
    lib, name = lib_name.split(':')
    txt = (FP_DIR / f"{lib}.pretty" / f"{name}.kicad_mod").read_text()
    tree = sexpr(txt)[0]
    fp = {'name': tree[1], 'pads': [], 'items': [], 'texts': []}
    for it in tree[3:]:
        tag = it[0]
        if tag == 'pad':
            pad = {'num': it[1], 'type': it[2], 'shape': it[3], 'at': None,
                   'size': None, 'drill': None, 'layers': None, 'rest': []}
            for sub in it[4:]:
                if sub[0] == 'at':
                    pad['at'] = [float(sub[1]), float(sub[2]), float(sub[3]) if len(sub) > 3 else 0.0]
                elif sub[0] == 'size':
                    pad['size'] = [float(sub[1]), float(sub[2])]
                elif sub[0] == 'drill':
                    pad['drill'] = [float(sub[1]), float(sub[2]) if len(sub) > 2 else float(sub[1]),
                                    float(sub[3]) if len(sub) > 3 else None]
                elif sub[0] == 'layers':
                    pad['layers'] = sub[1:]
                else:
                    pad['rest'].append(sub)
            if pad['at'] is None:
                pad['at'] = [0.0, 0.0, 0.0]
            fp['pads'].append(pad)
        elif tag == 'fp_text':
            fp['texts'].append(it)
        elif tag in ('fp_line', 'fp_rect', 'fp_poly', 'fp_circle'):
            fp['items'].append(it)
    return fp


def rot(a: float, x: float, y: float):
    """KiCad placement rotation (Y axis points down on the board)."""
    r = math.radians(a)
    return x * math.cos(r) - y * math.sin(r), x * math.sin(r) + y * math.cos(r)


def did(*parts) -> str:
    """A stable uuid for a generated item, so re-running the script reproduces
    the same file instead of churning every id on every build."""
    return str(uuid.uuid5(uuid.NAMESPACE_URL, 'mosfet-fan-switch:' + ':'.join(map(str, parts))))


# ------------------------------------------------------------- components --
#   ref, footprint, x, y, rotation, side, {pad number: net}
#
# Pad numbers are the REAL package pin numbers, not the schematic symbol's
# SPICE pin order.  See docs/pcb-notes.md for the mapping table.
PARTS = [
    # 12 V in, PWM in, fans out
    ("J1", "Connector_PinHeader_2.54mm:PinHeader_1x02_P2.54mm_Vertical",
     9.0, 37.0, 90, "F.Cu", {"1": "/P12V", "2": "/GND"}),
    ("J2", "Connector_PinHeader_2.54mm:PinHeader_1x02_P2.54mm_Vertical",
     11.0, 20.0, 90, "F.Cu", {"1": "/PWM", "2": "/GND"}),
    # each row of J3 is one fan: pin 1 (odd) = +12 V, pin 2 (even) = the switched side
    ("J3", "Connector_PinHeader_2.54mm:PinHeader_2x03_P2.54mm_Vertical",
     48.54, 31.08, 180, "F.Cu",
     {"1": "/P12V", "2": "/DRAIN", "3": "/P12V", "4": "/DRAIN", "5": "/P12V", "6": "/DRAIN"}),

    # 1. level shifter : 3.3 V PWM -> 12 V logic
    ("R1", "Resistor_THT:R_Axial_DIN0207_L6.3mm_D2.5mm_P7.62mm_Horizontal",
     14.0, 20.0, 0, "F.Cu", {"1": "/PWM", "2": "/LGATE"}),
    ("R2", "Resistor_THT:R_Axial_DIN0207_L6.3mm_D2.5mm_P7.62mm_Horizontal",
     21.62, 10.62, 270, "F.Cu", {"1": "/LGATE", "2": "/GND"}),
    ("Q2", "Package_TO_SOT_SMD:SOT-23",
     25.0, 20.0, 0, "B.Cu", {"1": "/LGATE", "2": "/GND", "3": "/BOOT"}),

    # 2. gate booster : 12 V pull-up + P-channel switch
    ("R3", "Resistor_THT:R_Axial_DIN0207_L6.3mm_D2.5mm_P7.62mm_Horizontal",
     26.0, 32.0, 90, "F.Cu", {"1": "/BOOT", "2": "/P12V"}),
    ("Q3", "Package_SO:SO-8_3.9x4.9mm_P1.27mm",
     30.5, 21.0, 270, "B.Cu",
     {"1": "/P12V", "2": "/P12V", "3": "/P12V", "4": "/BOOT",
      "5": "/HIGATE", "6": "/HIGATE", "7": "/HIGATE", "8": "/HIGATE"}),
    ("R4", "Resistor_THT:R_Axial_DIN0207_L6.3mm_D2.5mm_P7.62mm_Horizontal",
     27.0, 12.0, 0, "F.Cu", {"1": "/HIGATE", "2": "/GATE"}),
    ("R5", "Resistor_THT:R_Axial_DIN0207_L6.3mm_D2.5mm_P7.62mm_Horizontal",
     38.0, 10.0, 270, "F.Cu", {"1": "/GATE", "2": "/GND"}),

    # 3. the switch and its flyback diode
    ("Q1", "Package_TO_SOT_THT:TO-220-3_Vertical",
     42.0, 22.0, 270, "F.Cu", {"1": "/GATE", "2": "/DRAIN", "3": "/GND"}),
    ("D1", "Diode_THT:D_DO-41_SOD81_P10.16mm_Horizontal",
     34.0, 36.0, 0, "F.Cu", {"1": "/P12V", "2": "/DRAIN"}),

    # decoupling at the 12 V input
    ("C3", "Capacitor_THT:C_Disc_D5.0mm_W2.5mm_P5.00mm",
     13.0, 36.0, 270, "F.Cu", {"1": "/P12V", "2": "/GND"}),
    ("C4", "Capacitor_THT:CP_Radial_D6.3mm_P2.50mm",
     20.0, 36.0, 270, "F.Cu", {"1": "/P12V", "2": "/GND"}),

    # mechanical
    ("MK1", "MountingHole:MountingHole_3.2mm_M3", 2.5, 2.5, 0, "F.Cu", {}),
    ("MK2", "MountingHole:MountingHole_3.2mm_M3", 53.5, 2.5, 0, "F.Cu", {}),
    ("MK3", "MountingHole:MountingHole_3.2mm_M3", 2.5, 41.5, 0, "F.Cu", {}),
    ("MK4", "MountingHole:MountingHole_3.2mm_M3", 53.5, 41.5, 0, "F.Cu", {}),
]

# 0 ohm jumpers used to cross a wire.  Not in the schematic on purpose.
JUMPERS: list[tuple[str, str, float, float, float]] = []


# ------------------------------------------------------------- placement --
class Comp:
    def __init__(self, ref, fp_name, x, y, a, side, nets):
        self.ref, self.x, self.y, self.a, self.side = ref, x, y, a, side
        self.fp = load_footprint(fp_name)
        self.fp_name = fp_name
        self.nets = nets
        self.mirror = side == "B.Cu"
        self.pads = {}          # pad number -> absolute (x, y)
        for p in self.fp['pads']:
            lx, ly, la = p['at']
            if self.mirror:
                ly, la = -ly, -la
            ax, ay = rot(a, lx, ly)
            self.pads[p['num']] = (x + ax, y + ay)

    def pad(self, ref: str) -> tuple[float, float]:
        num = ref.split('.')[1]
        return self.pads[num]


PART = {c.ref: c for c in (Comp(*p) for p in PARTS)}
for ref, fp_name, x, y, a, side, nets in JUMPERS:
    PART[ref] = Comp(ref, fp_name, x, y, a, side, nets)


# ----------------------------------------------------------------- tracks --
SEGMENTS: list[dict] = []


def resolve(pt):
    if isinstance(pt, str):
        ref = pt.split('.')[0]
        return PART[ref].pad(pt)
    return (float(pt[0]), float(pt[1]))


def track(net: str, pts, width=TRACK):
    """Polyline.  Points are pad references ('Q1.2') or explicit (x, y)."""
    a = [resolve(p) for p in pts]
    for (x1, y1), (x2, y2) in zip(a, a[1:]):
        SEGMENTS.append(dict(net=net, x1=x1, y1=y1, x2=x2, y2=y2, width=width))


def bus(net, x1, x2, y, width=TRACK_POWER):
    track(net, [(x1, y), (x2, y)], width)


def T(net, pts, width=TRACK):
    """Orthogonal polyline: inserts the corner between consecutive points."""
    a = [resolve(p) for p in pts]
    out = [a[0]]
    for (x1, y1), (x2, y2) in zip(a, a[1:]):
        if abs(x1 - x2) > 1e-6 and abs(y1 - y2) > 1e-6:
            out.append((x2, y1))          # horizontal first, then vertical
        out.append((x2, y2))
    track(net, out, width)


# ------------------------------------------------------------------ build --
def build_tracks():
    # the two buses, and the GND return lane down the left edge
    bus("/GND", SPINE_X, 42.0, RAIL_GND_Y)
    bus("/P12V", 9.0, 48.54, RAIL_12V_Y, 3.0)
    track("/GND", [(SPINE_X, RAIL_GND_Y), (SPINE_X, 37.0)], 1.5)

    # 12 V in, PWM in, decoupling
    T("/P12V", ["J1.1", (9.0, RAIL_12V_Y)])
    T("/GND", ["J1.2", (SPINE_X, 37.0)])
    T("/GND", ["J2.2", (SPINE_X, 20.0)])
    T("/P12V", ["C3.1", (13.0, RAIL_12V_Y)])
    T("/P12V", ["C4.1", (20.0, RAIL_12V_Y)])
    T("/GND", ["C3.2", (SPINE_X, 31.0)])
    T("/GND", ["C4.2", (SPINE_X, 33.5)])

    # 1. level shifter
    T("/PWM", ["J2.1", "R1.1"])
    T("/LGATE", ["R1.2", "R2.1"])
    T("/LGATE", ["R1.2", (21.62, 22.5), (24.06, 22.5), "Q2.1"])
    T("/GND", ["Q2.2", (24.06, RAIL_GND_Y)])

    # 2. gate booster.  BOOT runs down x=26 and only reaches Q3's gate pad from
    # the left, so its copper never squeezes into the 1.27 mm gap between the
    # gate pad and the source pads.
    T("/BOOT", ["Q2.3", (26.0, 20.0), (26.0, 32.0)])
    track("/BOOT", [(26.0, 23.575), (28.4, 23.575)])
    track("/P12V", [(29.865, 23.575), (32.405, 23.575)])
    track("/P12V", [(32.405, 23.575), (32.405, RAIL_12V_Y)], 2.0)
    track("/HIGATE", [(27.0, 12.0), (27.0, 16.0), (32.405, 16.0), (32.405, 18.425)])
    track("/HIGATE", [(28.595, 18.425), (28.595, 16.0)])
    track("/HIGATE", [(29.865, 18.425), (29.865, 16.0)])
    track("/HIGATE", [(31.135, 18.425), (31.135, 16.0)])

    # 3. gate pull-down, the big FET, and the switched side
    T("/GATE", ["R4.2", (34.62, 22.0), "Q1.1"])
    T("/GATE", ["R4.2", (38.0, 12.0), "R5.1"])
    T("/GND", ["Q1.3", (42.0, RAIL_GND_Y)])
    track("/DRAIN", [(42.0, 19.46), (46.0, 19.46), (46.0, 31.08)], 1.5)
    track("/DRAIN", [(44.16, 36.0), (44.16, 31.08), (46.0, 31.08)], 1.5)
    T("/P12V", ["D1.1", (34.0, RAIL_12V_Y)])
    T("/P12V", ["J3.1", "J3.3", "J3.5", (48.54, RAIL_12V_Y)])


# ------------------------------------------------------- courtyard geometry --
def comp_bbox(c):
    """absolute bounding box of a footprint's courtyard (its pads if it has none)"""
    pts = []
    for it in c.fp['items']:
        layer = next((s2[1] for s2 in it[3:] if s2[0] == 'layer'), '')
        if 'CrtYd' not in layer:
            continue
        if it[0] in ('fp_line', 'fp_rect'):
            pts += [(float(it[1][1]), float(it[1][2])), (float(it[2][1]), float(it[2][2]))]
        elif it[0] == 'fp_poly':
            pts += [(float(p[1]), float(p[2])) for p in it[1][1:]]
        elif it[0] == 'fp_circle':
            cx, cy = float(it[1][1]), float(it[1][2])
            r = math.hypot(float(it[2][1]) - cx, float(it[2][2]) - cy)
            pts += [(cx - r, cy - r), (cx + r, cy + r)]
    if not pts:
        pts = list(c.pads.values()) or [(0.0, 0.0)]
    out = []
    for (x, y) in pts:
        if c.mirror:
            y = -y
        ax, ay = rot(c.a, x, y)
        out.append((c.x + ax, c.y + ay))
    xs = [p[0] for p in out]
    ys = [p[1] for p in out]
    return min(xs), min(ys), max(xs), max(ys)


def courtyard_clashes():
    boxes = {c.ref: comp_bbox(c) for c in PART.values() if not c.ref.startswith('MK')}
    clash = []
    keys = list(boxes)
    for i, a in enumerate(keys):
        for b in keys[i + 1:]:
            ax1, ay1, ax2, ay2 = boxes[a]
            bx1, by1, bx2, by2 = boxes[b]
            ox = min(ax2, bx2) - max(ax1, bx1)
            oy = min(ay2, by2) - max(ay1, by1)
            if ox > 0 and oy > 0:
                clash.append((a, b, round(ox, 2), round(oy, 2)))
    return boxes, clash


# ------------------------------------------------------------ crossing check
def seg_intersect(a, b):
    def cross(o, p, q):
        return (p[0] - o[0]) * (q[1] - o[1]) - (p[1] - o[1]) * (q[0] - o[0])
    p1, p2 = (a['x1'], a['y1']), (a['x2'], a['y2'])
    p3, p4 = (b['x1'], b['y1']), (b['x2'], b['y2'])
    d1, d2 = cross(p3, p4, p1), cross(p3, p4, p2)
    d3, d4 = cross(p1, p2, p3), cross(p1, p2, p4)
    if ((d1 > 0) != (d2 > 0)) and ((d3 > 0) != (d4 > 0)):
        return True
    def on(o, p, q):
        return min(o[0], q[0]) - 1e-9 <= p[0] <= max(o[0], q[0]) + 1e-9 and \
               min(o[1], q[1]) - 1e-9 <= p[1] <= max(o[1], q[1]) + 1e-9
    if abs(d1) < 1e-9 and on(p3, p1, p4):
        return True
    if abs(d2) < 1e-9 and on(p3, p2, p4):
        return True
    if abs(d3) < 1e-9 and on(p1, p3, p2):
        return True
    if abs(d4) < 1e-9 and on(p1, p4, p2):
        return True
    return False


def crossings():
    out = []
    for i, a in enumerate(SEGMENTS):
        for b in SEGMENTS[i + 1:]:
            if a['net'] == b['net']:
                continue
            if seg_intersect(a, b):
                out.append((a, b))
    return out


# ------------------------------------------------------------- emit board --
def fmt(v: float) -> str:
    s = f"{v:.4f}".rstrip('0').rstrip('.')
    return s if s not in ('-0', '') else '0'


def map_layer(layer: str, side: str) -> str:
    if side == "F.Cu":
        return layer
    return layer.replace("F.Cu", "B.Cu").replace("F.Mask", "B.Mask") \
                .replace("F.Paste", "B.Paste").replace("F.SilkS", "B.SilkS") \
                .replace("F.Fab", "B.Fab").replace("F.CrtYd", "B.CrtYd")


def emit_items(fp, side, mirror, out, indent):
    pad = "  " * indent
    for it in fp['items'] + fp['texts']:
        tag = it[0]

        def tp(x, y):
            x, y = float(x), float(y)
            if mirror:
                y = -y
            return fmt(x), fmt(y)

        def flip_ang(a):
            a = float(a)
            return fmt(-a if mirror else a)

        # item layout is (tag start end stroke [fill] layer) - tag is it[0]
        if tag == 'fp_line':
            x1, y1 = tp(it[1][1], it[1][2])
            x2, y2 = tp(it[2][1], it[2][2])
            layer = next(s[1] for s in it[3:] if s[0] == 'layer')
            stroke = next(s for s in it[3:] if s[0] == 'stroke')
            out.append(f'{pad}(fp_line (start {x1} {y1}) (end {x2} {y2}) '
                       f'(stroke (width {stroke[1][1]}) (type {stroke[2][1]})) '
                       f'(layer "{map_layer(layer, side)}"))')
        elif tag == 'fp_rect':
            x1, y1 = tp(it[1][1], it[1][2])
            x2, y2 = tp(it[2][1], it[2][2])
            stroke = next(s for s in it[3:] if s[0] == 'stroke')
            fill = next((s[1] for s in it[3:] if s[0] == 'fill'), 'no')
            layer = next(s[1] for s in it[3:] if s[0] == 'layer')
            out.append(f'{pad}(fp_rect (start {x1} {y1}) (end {x2} {y2}) '
                       f'(stroke (width {stroke[1][1]}) (type {stroke[2][1]})) '
                       f'(fill {fill}) (layer "{map_layer(layer, side)}"))')
        elif tag == 'fp_poly':
            pts = ' '.join(f'(xy {tp(p[1], p[2])[0]} {tp(p[1], p[2])[1]})' for p in it[1][1:])
            stroke = next(s for s in it[2:] if s[0] == 'stroke')
            fill = next((s[1] for s in it[2:] if s[0] == 'fill'), 'no')
            layer = next(s[1] for s in it[2:] if s[0] == 'layer')
            out.append(f'{pad}(fp_poly (pts {pts}) '
                       f'(stroke (width {stroke[1][1]}) (type {stroke[2][1]})) '
                       f'(fill {fill}) (layer "{map_layer(layer, side)}"))')
        elif tag == 'fp_circle':
            cx, cy = tp(it[1][1], it[1][2])
            ex, ey = tp(it[2][1], it[2][2])
            stroke = next(s for s in it[3:] if s[0] == 'stroke')
            layer = next(s[1] for s in it[3:] if s[0] == 'layer')
            out.append(f'{pad}(fp_circle (center {cx} {cy}) (end {ex} {ey}) '
                       f'(stroke (width {stroke[1][1]}) (type {stroke[2][1]})) (fill no) '
                       f'(layer "{map_layer(layer, side)}"))')
        elif tag == 'fp_text':
            kind, text = it[1], it[2]
            x, y = tp(it[3][1], it[3][2])
            ang = flip_ang(it[3][3] if len(it[3]) > 3 else 0)
            layer = next(s[1] for s in it[4:] if s[0] == 'layer')
            eff = next((s for s in it[4:] if s[0] == 'effects'), None)
            size, thick = '1', '0.15'
            if eff:
                font = next((s for s in eff[1:] if s[0] == 'font'), None)
                if font:
                    size = font[2][1]
                    thick = next((s[1] for s in font[1:] if s[0] == 'thickness'), '0.15')
            if float(size) < 0.8:
                continue          # library polarity marks are too small to etch
            mirror_note = ' (justify mirror)' if map_layer(layer, side).startswith('B.') else ''
            out.append(f'{pad}(fp_text {kind} "{text}" (at {x} {y} {ang}) '
                       f'(layer "{map_layer(layer, side)}") (effects (font (size {size} {size}) '
                       f'(thickness {thick})){mirror_note}))')


def schematic_parts() -> dict[str, tuple[str, str]]:
    """ref -> (uuid, value) read from the sheet.

    KiCad links a footprint to its symbol by UUID, so reusing the symbol's uuid
    is what makes cross-probing and "Update PCB from Schematic" work between the
    two files instead of KiCad thinking the board is full of unknown parts.
    """
    out: dict[str, tuple[str, str]] = {}
    if not SCHEMATIC.exists():
        return out
    lines = SCHEMATIC.read_text().split('\n')
    i = 0
    while i < len(lines):
        if re.match(r'^\t\(symbol\b', lines[i]):
            depth, j = 0, i
            while j < len(lines):
                depth += lines[j].count('(') - lines[j].count(')')
                j += 1
                if depth <= 0:
                    break
            body = '\n'.join(lines[i:j])
            ref = re.search(r'\(property "Reference" "([^"]*)"', body)
            uid = re.search(r'^\t\t\(uuid "([^"]+)"', body, re.M)
            val = re.search(r'\(property "Value" "([^"]*)"', body)
            if ref and uid:
                out[ref.group(1)] = (uid.group(1), val.group(1) if val else '')
            i = j
        else:
            i += 1
    return out


SCH_PARTS = schematic_parts()


def emit_footprint(c: Comp, out):
    side = c.side
    mirror = c.mirror
    fp = c.fp

    def field(kind):
        """where the library puts this field, in the footprint's local frame"""
        for it in fp['texts']:
            if it[1] == kind or (kind == 'Reference' and 'REFERENCE' in str(it[2])):
                a = it[3]
                x, y = float(a[1]), float(a[2])
                ang = float(a[3]) if len(a) > 3 else 0.0
                if mirror:
                    y, ang = -y, -ang
                return x, y, ang
        return 0.0, 0.0, 0.0

    def local_for(X, Y):
        """board point -> footprint local frame, upright on the board.
        KiCad treats a text angle as absolute (board-relative), so 0 keeps the
        label horizontal no matter how the footprint is rotated."""
        ax, ay = rot(-c.a, X - c.x, Y - c.y)
        if mirror:
            ay = -ay
        return ax, ay, 0.0

    vx, vy, va = field('Value')
    if c.ref in REF_NONE:
        rx = ry = ra = None
    else:
        x1, y1, x2, y2 = comp_bbox(c)
        tx, ty = REF_AT.get(c.ref, ((x1 + x2) / 2, y1 - 1.4))
        rx, ry, ra = local_for(tx, ty)
    suid, sval = SCH_PARTS.get(c.ref, (None, ''))
    if suid is None:                      # mounting holes: no symbol to match
        suid = did('footprint', c.ref)
    out.append(f'\t(footprint "{fp["name"]}" (version 20260206) (generator "pcbnew")'
               f' (generator_version "10.0")')
    out.append(f'\t\t(layer "{side}")')
    out.append(f'\t\t(uuid "{suid}")')
    # KiCad rotates a footprint by -theta relative to the maths convention used
    # in this script (Y axis points down), so the placement angle is negated.
    out.append(f'\t\t(at {fmt(c.x)} {fmt(c.y)} {fmt(-c.a)})')
    mir = ' (justify mirror)' if side == "B.Cu" else ''
    if c.ref not in REF_NONE:
        out.append(f'\t\t(property "Reference" "{c.ref}" (at {fmt(rx)} {fmt(ry)} {fmt(ra)})'
                   f' (layer "{map_layer("F.SilkS", side)}")'
                   f' (effects (font (size 1 1) (thickness 0.15)){mir}))')
    out.append(f'\t\t(property "Value" "{sval or fp["name"].split("_")[0]}" '
               f'(at {fmt(vx)} {fmt(vy)} {fmt(va)})'
               f' (layer "{map_layer("F.Fab", side)}") (hide yes)'
               f' (effects (font (size 1 1) (thickness 0.15)){mir}))')
    attr = 'smd' if side == "B.Cu" else 'through_hole'
    out.append(f'\t\t(attr {attr})')
    emit_items(fp, side, mirror, out, 2)
    for p in fp['pads']:
        lx, ly, la = p['at']
        if mirror:
            ly, la = -ly, -la
        # KiCad 10 rotates a footprint's *positions* by the placement angle but
        # rotates each pad's *copper* only by that pad's own angle.  KiCad itself
        # bakes the placement angle into every pad when it places a footprint, so
        # we do the same; without it a rotated SO-8 has overlapping pads.
        la = (la - c.a) % 360.0
        layers = ' '.join(f'"{map_layer(l, side)}"' for l in (p['layers'] or []))
        out.append(f'\t\t(pad "{p["num"]}" {p["type"]} {p["shape"]} '
                   f'(at {fmt(lx)} {fmt(ly)} {fmt(la)}) (size {fmt(p["size"][0])} {fmt(p["size"][1])})'
                   + (f' (drill {fmt(p["drill"][0])})' if p['drill'] else '')
                   + f' (layers {layers})')
        for sub in p['rest']:
            out.append('\t\t\t' + sexpr_to_str(sub))
        net = c.nets.get(p['num'])
        if net:
            out.append(f'\t\t\t(net {NET_ID[net]} "{net}")')
        out.append('\t\t)')
    out.append('\t)')


def sexpr_to_str(node) -> str:
    if isinstance(node, list):
        return '(' + ' '.join(sexpr_to_str(x) for x in node) + ')'
    if isinstance(node, Quoted):
        return f'"{node}"'
    return node


def emit():
    out = ['(kicad_pcb', '\t(version 20260206)', '\t(generator "pcbnew")',
           '\t(generator_version "10.0")', '\t(general (thickness 1.6) (legacy_teardrops no))',
           '\t(paper "A4")',
           '\t(title_block (title "mosfet-fan-switch - 12 V fan driver")'
           ' (date "2026-10-22") (rev "v2"))']
    # layers table (copied from the project board)
    layers = [(0, "F.Cu", "signal"), (2, "B.Cu", "signal"), (9, "F.Adhes", "user", "F.Adhesive"),
              (11, "B.Adhes", "user", "B.Adhesive"), (13, "F.Paste", "user"), (15, "B.Paste", "user"),
              (5, "F.SilkS", "user", "F.Silkscreen"), (7, "B.SilkS", "user", "B.Silkscreen"),
              (1, "F.Mask", "user"), (3, "B.Mask", "user"), (17, "Dwgs.User", "user", "User.Drawings"),
              (19, "Cmts.User", "user", "User.Comments"), (21, "Eco1.User", "user", "User.Eco1"),
              (23, "Eco2.User", "user", "User.Eco2"), (25, "Edge.Cuts", "user"), (27, "Margin", "user"),
              (31, "F.CrtYd", "user", "F.Courtyard"), (29, "B.CrtYd", "user", "B.Courtyard"),
              (35, "F.Fab", "user"), (33, "B.Fab", "user"), (39, "User.1", "user"), (41, "User.2", "user"),
              (43, "User.3", "user"), (45, "User.4", "user")]
    out.append('\t(layers')
    for L in layers:
        if len(L) == 3:
            out.append(f'\t\t({L[0]} "{L[1]}" {L[2]})')
        else:
            out.append(f'\t\t({L[0]} "{L[1]}" {L[2]} "{L[3]}")')
    out.append('\t)')
    out.append('\t(setup (pad_to_mask_clearance 0) (allow_soldermask_bridges_in_footprints no)'
               ' (tenting (front yes) (back yes)) (covering (front no) (back no))'
               ' (plugging (front no) (back no)) (capping no) (filling no)')
    out.append('\t\t(pcbplotparams (layerselection 0x00000000_00000000_55555555_5755f5ff)'
               ' (plot_on_all_layers_selection 0x00000000_00000000_00000000_00000000)'
               ' (disableapertmacros no) (usegerberextensions no) (usegerberattributes yes)'
               ' (usegerberadvancedattributes yes) (creategerberjobfile yes) (dashed_line_dash_ratio 12)'
               ' (dashed_line_gap_ratio 3) (svgprecision 4) (plotframeref no) (mode 1)'
               ' (useauxorigin no) (pdf_front_fp_property_popups yes) (pdf_back_fp_property_popups yes)'
               ' (pdf_metadata yes) (pdf_single_document no) (dxfpolygonmode yes) (dxfimperialunits yes)'
               ' (dxfusepcbnewfont yes) (psnegative no) (psa4output no) (plot_black_and_white yes)'
               ' (sketchpadsonfab no) (plotpadnumbers no) (hidednponfab no) (sketchdnponfab yes)'
               ' (crossoutdnponfab yes) (subtractmaskfromsilk no) (outputformat 1) (mirror no)'
               ' (drillshape 1) (scaleselection 1) (outputdirectory "pcb/gerber"))')
    out.append('\t)')
    out.append('\t(embedded_fonts no)')

    # nets
    out.append('\t(net 0 "")')
    for n, i in sorted(NET_ID.items(), key=lambda kv: kv[1]):
        out.append(f'\t(net {i} "{n}")')

    # board outline, rounded corners
    r = 2.0
    edges = [
        ((r, 0), (W - r, 0)), ((W, r), (W, H - r)), ((W - r, H), (r, H)), ((0, H - r), (0, r)),
        ((W - r, 0), (W, r)), ((W, H - r), (W - r, H)), ((r, H), (0, H - r)), ((0, r), (r, 0)),
    ]
    for (x1, y1), (x2, y2) in edges:
        out.append(f'\t(gr_line (start {fmt(x1)} {fmt(y1)}) (end {fmt(x2)} {fmt(y2)})'
                   f' (stroke (width 0.1) (type solid)) (layer "Edge.Cuts")'
                   f' (uuid "{did("edge", x1, y1, x2, y2)}"))')

    for s in SEGMENTS:
        out.append(f'\t(segment (start {fmt(s["x1"])} {fmt(s["y1"])}) (end {fmt(s["x2"])} {fmt(s["y2"])})'
                   f' (width {fmt(s["width"])}) (layer "B.Cu") (net {NET_ID[s["net"]]})'
                   f' (uuid "{did("track", s["net"], s["x1"], s["y1"], s["x2"], s["y2"])}"))')

    for c in PART.values():
        emit_footprint(c, out)

    # silkscreen notes.  These go on the *top* silkscreen: every trace is on the
    # bottom copper, so labels here never sit on copper and read normally when
    # the board is component-side up.  KiCad centres board text on its position.
    notes = [
        ("12V FAN DRIVER", 11.0, 6.0),
        ("3 x 100 mA", 9.6, 8.5),
        ("3.3V logic in", 10.5, 11.0),
        ("copper on back", 10.7, 13.5),
        ("+12V IN", 7.7, 31.8),
        ("PWM IN", 9.6, 15.4),
        ("FAN OUT", 47.3, 33.9),
        ("Q1 G-D-S", 36.5, 26.5),
        ("D1 K +12V", 32.0, 33.5),
    ]
    for text, x, y in notes:
        out.append(f'\t(gr_text "{text}" (at {fmt(x)} {fmt(y)} 0) (layer "F.SilkS")'
                   f' (effects (font (size 0.8 0.8) (thickness 0.15)))'
                   f' (uuid "{did("note", text, x, y)}"))')

    out.append(')')
    BOARD.write_text('\n'.join(out) + '\n')


def main():
    build_tracks()
    print("pad positions (mm, KiCad board coordinates, Y down):")
    for c in PART.values():
        for num, (x, y) in sorted(c.pads.items(), key=lambda kv: int(kv[0]) if kv[0].isdigit() else 99):
            net = c.nets.get(num, '')
            print(f"  {c.ref:4}.{num:<2} ({x:6.2f}, {y:6.2f})  {net}")
    boxes, clash = courtyard_clashes()
    print("\ncourtyard boxes (mm):")
    for ref, (x1, y1, x2, y2) in sorted(boxes.items()):
        print(f"  {ref:4} x {x1:6.2f}..{x2:6.2f}   y {y1:6.2f}..{y2:6.2f}")
    if clash:
        print("\nCOURTYARD OVERLAPS (spread the parts):")
        for a, b, ox, oy in clash:
            print(f"  {a} x {b}   overlap {ox} x {oy} mm")
    bad = crossings()
    if bad:
        print("\nCROSSINGS between different nets (fix placement or add a 0 ohm jumper):")
        for a, b in bad:
            print(f"  {a['net']:8} ({a['x1']:.2f},{a['y1']:.2f})-({a['x2']:.2f},{a['y2']:.2f})")
            print(f"  {b['net']:8} ({b['x1']:.2f},{b['y1']:.2f})-({b['x2']:.2f},{b['y2']:.2f})")
    else:
        print("\nno net crossings - the board is planar, no jumpers needed")
    emit()
    print(f"\nwrote {BOARD}")


if __name__ == '__main__':
    main()
