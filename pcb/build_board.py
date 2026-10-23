#!/usr/bin/env python3
"""Build the two-layer PCB for the MOSFET fan switch.

Two copper layers, normal fab rules, solid ground pour on the back and a solid
+12 V pour over the switching stage.  Vias are allowed, so nothing needs a 0 ohm
jumper: the single-layer tricks in the archived board are gone.

    python3 pcb/build_board.py            # write the board, report the checks
    python3 pcb/build_board.py --pads     # pad table only (used to plan tracks)

Everything here is generated from the parts table below plus the footprint
libraries, so the board can be re-laid-out by editing coordinates and re-running.
"""
from __future__ import annotations

import math
import re
import sys
import uuid
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BOARD = ROOT / "mosfet-fan-switch.kicad_pcb"
SCHEMATIC = ROOT / "mosfet-fan-switch.kicad_sch"
FP_DIR = Path("/Applications/KiCad/KiCad.app/Contents/SharedSupport/footprints")

sys.path.insert(0, str(ROOT / "pcb"))
import pro_mini                                   # the Pro Mini hole map and socket
FOOTPRINT_LIB = "mosfet-fan-switch"              # pcb/footprints/mosfet-fan-switch.pretty

# ---------------------------------------------------------------- geometry --
# Prototype fab rules: JLCPCB two-layer takes 0.15 mm, so 0.30 mm everywhere is
# comfortable and still leaves room for hand re-routing in KiCad.
CLEARANCE = 0.30         # mm between two different nets
TRACK = 0.30             # signal traces
TRACK_SMALL = 0.30       # the microcontroller stubs
TRACK_POWER = 1.50       # 12 V, GND and the switched side (~3 A safe at 1.5 mm)
VIA_DRILL = 0.40
VIA_SIZE = 0.80
EDGE = 0.50              # copper to board edge

W, H = 50.0, 62.0        # 12 V stage, NUC interface band, microcontroller deck
BAND_12V = 30.0          # below this y is the +12 V pour on F.Cu

# Reference labels sit just outside each part's courtyard, horizontal on the
# board.  REF_AT overrides the default spot when that spot is taken; REF_NONE
# suppresses the label (mounting holes).
REF_AT = {}
REF_NONE = {"MK1", "MK2", "MK3", "MK4"}

# ------------------------------------------------------------------ nets --
NETS = ["/P12V", "/GND", "/PWM", "/LGATE", "/BOOT", "/HIGATE", "/GATE", "/DRAIN",
        "/NUC_PWM", "/DEMAND", "/TACH_PWM", "/TBASE", "/NUC_TACH",
        # the microcontroller deck
        "/P3V3", "/RST", "/DTR", "/BLK", "/TX0", "/RX1", "/MOSI", "/MISO", "/SCK"]
NET_ID = {n: i + 1 for i, n in enumerate(NETS)}

# Net classes for the .kicad_pro: the wide nets get their own clearance rules.
POWER_NETS = ["/P12V", "/GND", "/DRAIN"]


# ------------------------------------------------------------- footprints --
class Quoted(str):
    """a string that was written with quotes in the source file"""


def sexpr(s: str):
    """Minimal s-expression reader: nested lists of strings."""
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
    if lib == FOOTPRINT_LIB:                 # the project's own footprint library
        path = ROOT / "pcb" / "footprints" / f"{lib}.pretty" / f"{name}.kicad_mod"
    else:
        path = FP_DIR / f"{lib}.pretty" / f"{name}.kicad_mod"
    txt = path.read_text()
    tree = sexpr(txt)[0]
    # 'name' is the footprint's own name; 'id' is what the board file records, so
    # KiCad can find U1 again in pcb/footprints/ when you update from library.
    fp = {'name': tree[1], 'id': lib_name, 'pads': [], 'items': [], 'texts': [], 'models': []}
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
        elif tag == 'model':
            # the library's 3D model, so the 3D viewer and `kicad-cli pcb render`
            # show the real package on the board
            fp['models'].append(it)
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
# Pad numbers are the REAL package pin numbers, not the schematic symbol's SPICE
# pin order.  See docs/pcb-notes.md for the mapping table.  Every part stands on
# the top side; only tracks and the ground pour use the back.
#
# The board reads top to bottom: the 12 V switching stage occupies y 2..30, the
# NUC fan-header interface the band y 30..42, the Pro Mini socket the deck
# y 42..62.  U1 stands at 270 degrees, so its row B (RAW .. D10) is the upper
# row nearest the band with RAW at the programming-row end and D10 at the far
# end, and row A (TX0 .. D9) is the lower row with D9 at the far end.
PARTS = [
    # 12 V in, PWM in, fans out
    ("J1", "Connector_PinHeader_2.54mm:PinHeader_1x02_P2.54mm_Vertical",
     5.5, 9.0, 0, "F.Cu", {"1": "/P12V", "2": "/GND"}),
    # each row of J3 is one fan: pin 1 (odd) = +12 V, pin 2 (even) = the switched side
    ("J3", "Connector_PinHeader_2.54mm:PinHeader_2x03_P2.54mm_Vertical",
     47.05, 27.08, 180, "F.Cu",
     {"1": "/P12V", "2": "/DRAIN", "3": "/P12V", "4": "/DRAIN", "5": "/P12V", "6": "/DRAIN"}),

    # 1. level shifter : 3.3 V PWM -> 12 V logic
    ("R1", "Resistor_THT:R_Axial_DIN0207_L6.3mm_D2.5mm_P7.62mm_Horizontal",
     16.0, 11.0, 90, "F.Cu", {"1": "/PWM", "2": "/LGATE"}),
    ("R2", "Resistor_THT:R_Axial_DIN0207_L6.3mm_D2.5mm_P7.62mm_Horizontal",
     23.5, 19.0, 0, "F.Cu", {"1": "/LGATE", "2": "/GND"}),
    ("Q2", "Package_TO_SOT_SMD:SOT-23",
     23.5, 13.0, 0, "F.Cu", {"1": "/LGATE", "2": "/GND", "3": "/BOOT"}),

    # 2. gate booster : 12 V pull-up + P-channel switch
    ("R3", "Resistor_THT:R_Axial_DIN0207_L6.3mm_D2.5mm_P7.62mm_Horizontal",
     26.0, 23.0, 0, "F.Cu", {"1": "/BOOT", "2": "/P12V"}),
    ("Q3", "Package_SO:SO-8_3.9x4.9mm_P1.27mm",
     31.0, 13.0, 270, "F.Cu",
     {"1": "/P12V", "2": "/P12V", "3": "/P12V", "4": "/BOOT",
      "5": "/HIGATE", "6": "/HIGATE", "7": "/HIGATE", "8": "/HIGATE"}),
    ("R4", "Resistor_THT:R_Axial_DIN0207_L6.3mm_D2.5mm_P7.62mm_Horizontal",
     37.0, 8.5, 90, "F.Cu", {"1": "/HIGATE", "2": "/GATE"}),
    ("R5", "Resistor_THT:R_Axial_DIN0207_L6.3mm_D2.5mm_P7.62mm_Horizontal",
     43.0, 17.62, 270, "F.Cu", {"1": "/GATE", "2": "/GND"}),

    # 3. the switch and its flyback diodes
    ("Q1", "Package_TO_SOT_THT:TO-220-3_Vertical",
     38.5, 26.0, 270, "F.Cu", {"1": "/GATE", "2": "/DRAIN", "3": "/GND"}),
    ("D1", "Diode_THT:D_DO-41_SOD81_P10.16mm_Horizontal",
     22.0, 28.0, 0, "F.Cu", {"1": "/P12V", "2": "/DRAIN"}),
    # Two spare flyback diodes, in parallel with D1, standing at the fan end of
    # the board.  Neither is populated as built: 3 A of fan current is D1's job.
    # D2 (1N5822, 3 A) covers about 12-20 fans; D3 (MBR10100CT, 10 A dual
    # Schottky, common cathode) covers anything this driver can switch.  See
    # sim/fan_count.py.  D3's pads 1 and 3 are the two anodes, pad 2 the cathode.
    ("D2", "Diode_THT:D_DO-27_P15.24mm_Horizontal",
     14.55, 5.0, 0, "F.Cu", {"1": "/P12V", "2": "/DRAIN"}),
    ("D3", "Package_TO_SOT_THT:TO-220-3_Vertical",
     34.5, 5.0, 0, "F.Cu", {"1": "/DRAIN", "2": "/P12V", "3": "/DRAIN"}),

    # decoupling at the 12 V input
    ("C3", "Capacitor_THT:C_Disc_D5.0mm_W2.5mm_P5.00mm",
     5.5, 17.0, 90, "F.Cu", {"1": "/P12V", "2": "/GND"}),
    ("C4", "Capacitor_THT:CP_Radial_D6.3mm_P2.50mm",
     9.25, 18.25, 0, "F.Cu", {"1": "/P12V", "2": "/GND"}),

    # 4. the NUC fan-header interface.  J4 is the NUC's own 4-pin fan socket; the
    #    divider turns the NUC's 5 V PWM request into the 3.3 V the Pro Mini
    #    expects, and Q4 is the open collector that answers with the fan-drive
    #    carrier on the tach line.
    ("J4", "Connector_PinHeader_2.54mm:PinHeader_1x04_P2.54mm_Vertical",
     46.5, 33.0, 0, "F.Cu",
     {"1": "/NUC_PWM", "2": "/NUC_TACH", "4": "/GND"}),          # pin 3 = no connect
    ("R7", "Resistor_THT:R_Axial_DIN0207_L6.3mm_D2.5mm_P7.62mm_Horizontal",
     43.0, 31.0, 180, "F.Cu", {"1": "/NUC_PWM", "2": "/DEMAND"}),
    ("R8", "Resistor_THT:R_Axial_DIN0207_L6.3mm_D2.5mm_P7.62mm_Horizontal",
     37.0, 41.5, 270, "F.Cu", {"1": "/DEMAND", "2": "/GND"}),
    ("C5", "Capacitor_THT:CP_Radial_D8.0mm_P3.50mm",
     30.0, 36.0, 90, "F.Cu", {"1": "/DEMAND", "2": "/GND"}),
    ("C6", "Capacitor_THT:C_Disc_D3.8mm_W2.6mm_P2.50mm",
     24.0, 36.0, 90, "F.Cu", {"1": "/DEMAND", "2": "/GND"}),
    ("R9", "Resistor_THT:R_Axial_DIN0207_L6.3mm_D2.5mm_P7.62mm_Horizontal",
     8.0, 31.0, 0, "F.Cu", {"1": "/TACH_PWM", "2": "/TBASE"}),
    ("Q4", "Package_TO_SOT_THT:TO-92_Inline_Wide",
     15.62, 38.0, 0, "F.Cu", {"1": "/GND", "2": "/TBASE", "3": "/NUC_TACH"}),

    # 5. the microcontroller deck.  U1 is the Pro Mini sitting on three female
    # headers; its pad numbers are the hole numbers of the clone hole map in
    # pcb/pro_mini.py, so a pad name on the board and the pin number in the
    # schematic are the same thing.  J5 mirrors U1's own programming row pad for
    # pad, so an FTDI/CH340 adapter can plug in beside the module instead of on
    # top of it: J5 pin n sits straight across from U1 pad 25+n-1.  J6 is the
    # plain 2x3 ICSP header for programming the 328 with another Arduino; its pin
    # 2 (the programmer's VCC) is deliberately a dead pad, because the Pro Mini
    # powers itself from /P12V and feeding an Uno's 5 V into a 3.3 V board is how
    # boards get destroyed.  Use five wires, not six.
    ("U1", f"{FOOTPRINT_LIB}:{pro_mini.FOOTPRINT}",
     7.77, 60.0, 270, "F.Cu",
     {"3": "/RST", "4": "/GND", "12": "/PWM", "13": "/P12V", "15": "/RST",
      "16": "/P3V3", "20": "/DEMAND", "21": "/SCK", "22": "/MISO",
      "23": "/MOSI", "24": "/TACH_PWM", "25": "/DTR", "26": "/TX0",
      "27": "/RX1", "28": "/P3V3", "29": "/GND", "30": "/BLK", "31": "/GND"}),
    ("J5", "Connector_PinHeader_2.54mm:PinHeader_1x06_P2.54mm_Vertical",
     41.79, 58.73, 180, "F.Cu",
     {"1": "/DTR", "2": "/TX0", "3": "/RX1", "4": "/P3V3", "5": "/GND", "6": "/BLK"}),
    ("J6", "Connector_PinHeader_2.54mm:PinHeader_2x03_P2.54mm_Vertical",
     12.55, 41.08, 180, "F.Cu",
     {"1": "/MISO", "3": "/SCK", "4": "/MOSI", "5": "/RST", "6": "/GND"}),

    # mechanical
    ("MK1", "MountingHole:MountingHole_3.2mm_M3", 2.5, 2.5, 0, "F.Cu", {}),
    ("MK2", "MountingHole:MountingHole_3.2mm_M3", 47.5, 2.5, 0, "F.Cu", {}),
    ("MK3", "MountingHole:MountingHole_3.2mm_M3", 2.5, 59.5, 0, "F.Cu", {}),
    ("MK4", "MountingHole:MountingHole_3.2mm_M3", 47.5, 59.5, 0, "F.Cu", {}),
]


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

    def copper(self):
        """every copper pad as (x, y, w, h, net, drilled diameter)"""
        out = []
        for p in self.fp['pads']:
            lx, ly, la = p['at']
            if self.mirror:
                ly, la = -ly, -la
            ax, ay = rot(self.a, lx, ly)
            w, h = p['size']
            if self.a % 180:                      # rotated 90/270 swaps the pad
                w, h = h, w
            d = p['drill'][0] if p['drill'] else 0.0
            out.append((self.x + ax, self.y + ay, w, h, self.nets.get(p['num']), d))
        return out


PART = {c.ref: c for c in (Comp(*p) for p in PARTS)}

# ------------------------------------------------------------- tracks --
SEGMENTS: list[dict] = []
VIAS: list[dict] = []


def resolve(pt):
    if isinstance(pt, str):
        ref = pt.split('.')[0]
        return PART[ref].pad(pt)
    return (float(pt[0]), float(pt[1]))


def track(net: str, pts, width=TRACK, layer="F.Cu"):
    """Polyline.  Points are pad references ('Q1.2') or explicit (x, y)."""
    a = [resolve(p) for p in pts]
    for (x1, y1), (x2, y2) in zip(a, a[1:]):
        SEGMENTS.append(dict(net=net, x1=x1, y1=y1, x2=x2, y2=y2, width=width,
                             layer=layer))


def T(net: str, pts, width=TRACK, layer="F.Cu"):
    """Orthogonal polyline: inserts the corner between consecutive points."""
    a = [resolve(p) for p in pts]
    out = [a[0]]
    for (x1, y1), (x2, y2) in zip(a, a[1:]):
        if abs(x1 - x2) > 1e-6 and abs(y1 - y2) > 1e-6:
            out.append((x2, y1))          # horizontal first, then vertical
        out.append((x2, y2))
    track(net, out, width, layer)


def via(net: str, x: float, y: float):
    VIAS.append(dict(net=net, x=x, y=y))


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
    """Crossings only matter between two tracks on the same layer."""
    out = []
    for i, a in enumerate(SEGMENTS):
        for b in SEGMENTS[i + 1:]:
            if a['net'] == b['net'] or a['layer'] != b['layer']:
                continue
            if seg_intersect(a, b):
                out.append((a, b))
    return out


def build_tracks():
    """Filled in once the pad table is known; see docs/pcb-notes.md."""


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
    out.append(f'\t(footprint "{fp["id"]}" (version 20260206) (generator "pcbnew")'
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
    attr = 'smd' if any(p['type'] == 'smd' for p in fp['pads']) else 'through_hole'
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
        # KiCad 10 names nets instead of numbering them: (net "/GND") is how the
        # saved file spells it, and the number is only in older boards.
        out.append(f'\t\t(pad "{p["num"]}" {p["type"]} {p["shape"]} '
                   f'(at {fmt(lx)} {fmt(ly)} {fmt(la)}) (size {fmt(p["size"][0])} {fmt(p["size"][1])})'
                   + (f' (drill {fmt(p["drill"][0])})' if p['drill'] else '')
                   + f' (layers {layers})')
        for sub in p['rest']:
            out.append('\t\t\t' + sexpr_to_str(sub))
        net = c.nets.get(p['num'])
        if net:
            out.append(f'\t\t\t(net "{net}")')
        out.append('\t\t)')
    for m in fp['models']:
        out.append('\t\t' + sexpr_to_str(m))
    out.append('\t)')


def sexpr_to_str(node) -> str:
    if isinstance(node, list):
        return '(' + ' '.join(sexpr_to_str(x) for x in node) + ')'
    if isinstance(node, Quoted):
        return f'"{node}"'
    return node


def zone(net: str, layer: str, pts, out):
    """A filled copper pour.  KiCad 10 wants (net "name") and (name "name") both;
    a numeric net here gives a zone with no net, which plots as bare outline."""
    out.append('\t(zone')
    out.append(f'\t\t(net "{net}")')
    out.append(f'\t\t(layer "{layer}")')
    out.append(f'\t\t(uuid "{did("zone", net, layer)}")')
    out.append(f'\t\t(name "{net}")')
    out.append('\t\t(hatch none 0.5)')
    out.append('\t\t(connect_pads')
    out.append(f'\t\t\t(clearance {fmt(CLEARANCE)})')
    out.append('\t\t)')
    out.append('\t\t(min_thickness 0.25)')
    # A solid pour in KiCad 10's text format is a hatch with zero gap: 'solid' is
    # not a word the zone parser accepts, and hatch_gap 0 fills the whole polygon.
    out.append('\t\t(fill yes')
    out.append('\t\t\t(mode hatch)')
    out.append(f'\t\t\t(thermal_gap {fmt(CLEARANCE)})')
    out.append(f'\t\t\t(thermal_bridge_width {fmt(0.5)})')
    out.append('\t\t\t(island_removal_mode 0)')
    out.append('\t\t\t(hatch_thickness 0.25)')
    out.append('\t\t\t(hatch_gap 0)')
    out.append('\t\t\t(hatch_orientation 0)')
    out.append('\t\t\t(hatch_border_algorithm hatch_thickness)')
    out.append('\t\t\t(hatch_min_hole_area 0.05)')
    out.append('\t\t)')
    out.append('\t\t(polygon')
    out.append('\t\t\t(pts')
    for i in range(0, len(pts), 4):
        out.append('\t\t\t\t' + ' '.join(f'(xy {fmt(x)} {fmt(y)})' for x, y in pts[i:i + 4]))
    out.append('\t\t\t)')
    out.append('\t\t)')
    out.append('\t)')


def emit():
    out = ['(kicad_pcb', '\t(version 20260206)', '\t(generator "pcbnew")',
           '\t(generator_version "10.0")', '\t(general (thickness 1.6) (legacy_teardrops no))',
           '\t(paper "A4")',
           '\t(title_block (title "mosfet-fan-switch - 12 V fan driver")'
           ' (date "2026-10-23") (rev "v3"))']
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

    for c in PART.values():
        emit_footprint(c, out)

    for s in SEGMENTS:
        out.append(f'\t(segment (start {fmt(s["x1"])} {fmt(s["y1"])}) (end {fmt(s["x2"])} {fmt(s["y2"])})'
                   f' (width {fmt(s["width"])}) (layer "{s["layer"]}") (net "{s["net"]}")'
                   f' (uuid "{did("track", s["net"], s["layer"], s["x1"], s["y1"], s["x2"], s["y2"])}"))')

    for v in VIAS:
        out.append(f'\t(via (at {fmt(v["x"])} {fmt(v["y"])}) (size {fmt(VIA_SIZE)})'
                   f' (drill {fmt(VIA_DRILL)}) (layers "F.Cu" "B.Cu") (net "{v["net"]}")'
                   f' (remove_unused_layers no) (keep_orphan no) (free_length no)'
                   f' (uuid "{did("via", v["net"], v["x"], v["y"])}"))')

    # copper pours.  B.Cu is the ground plane; F.Cu carries the +12 V over the
    # switching stage, which also gives every gate-drive loop a return directly
    # underneath it.
    zone("/GND", "B.Cu", [(EDGE, EDGE), (W - EDGE, EDGE), (W - EDGE, H - EDGE),
                          (EDGE, H - EDGE)], out)
    zone("/P12V", "F.Cu", [(EDGE, EDGE), (W - EDGE, EDGE), (W - EDGE, BAND_12V),
                           (EDGE, BAND_12V)], out)

    # silkscreen notes.  KiCad centres board text on its position.
    notes = [
        ("12V FAN DRIVER", 12.0, 29.0),
        ("3 x 100 mA", 9.6, 8.5),
        ("gnd plane on back", 25.0, 29.0),
        ("+12V IN", 7.7, 31.8),
        ("FAN OUT", 47.3, 23.4),
        ("Q1 G-D-S", 36.5, 26.5),
        ("D1 K +12V", 32.0, 33.5),
        ("D2 D3 spare", 31.5, 43.5),
        ("NUC FAN HEADER", 49.0, 43.6),
        ("NUC INTERFACE", 27.0, 61.0),
        ("ICSP: no 5V wire", 27.0, 64.5),
        ("PRO MINI 328 SOCKET", 41.0, 68.5),
        ("J5: 1=DTR 6=BLK", 43.0, 90.5),
    ]
    for text, x, y in notes:
        out.append(f'\t(gr_text "{text}" (at {fmt(x)} {fmt(y)} 0) (layer "F.SilkS")'
                   f' (effects (font (size 0.8 0.8) (thickness 0.15)))'
                   f' (uuid "{did("note", text, x, y)}"))')

    out.append(')')
    BOARD.write_text('\n'.join(out) + '\n')


def main():
    print(f"wrote {pro_mini.write_footprint()}")     # regenerate U1's socket
    build_tracks()
    if '--pads' in sys.argv:
        for c in PART.values():
            for num, (x, y) in sorted(c.pads.items(), key=lambda kv: int(kv[0]) if kv[0].isdigit() else 99):
                print(f"  {c.ref:4}.{num:<2} ({x:6.2f}, {y:6.2f})  {c.nets.get(num, '')}")
        return
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
        print("\nCROSSINGS between different nets on the same layer:")
        for a, b in bad:
            print(f"  {a['net']:8} {a['layer']:5} ({a['x1']:.2f},{a['y1']:.2f})-({a['x2']:.2f},{a['y2']:.2f})")
            print(f"  {b['net']:8} {b['layer']:5} ({b['x1']:.2f},{b['y1']:.2f})-({b['x2']:.2f},{b['y2']:.2f})")
    else:
        print("\nno same-layer crossings")
    emit()
    print(f"\nwrote {BOARD}")


if __name__ == '__main__':
    main()
