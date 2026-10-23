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
# Home-etch rules of thumb for a 35 um copper board.
CLEARANCE = 0.50     # mm between two different nets
TRACK = 0.80         # signal traces
TRACK_POWER = 2.00   # 12 V and GND buses (~1 A safe at this width)
DRILL_MIN = 0.80

W, H = 56.0, 92.0    # fan driver (top), NUC interface band, microcontroller strip
RAIL_GND_Y = 3.0     # GND bus along the top edge
RAIL_12V_Y = 41.0    # +12 V bus, bottom edge of the fan driver
SPINE_X = 5.5        # GND return lane down the left edge, old part of the board
BAND_GND_Y = 58.0    # GND bus along the bottom edge, through the NUC band
DEMAND_Y = 49.0      # the divider's output rail in the NUC band

# Reference labels sit just outside each part's courtyard, horizontal on the
# board.  REF_AT overrides the default spot when that spot is taken; REF_NONE
# suppresses the label (mounting holes).
REF_AT = {"Q3": (30.5, 26.0), "R2": (18.5, 6.8), "R5": (41.5, 6.0),
          "J3": (47.3, 34.2)}
REF_NONE = {"MK1", "MK2", "MK3", "MK4"}


# ------------------------------------------------------------------ nets --
NETS = ["/P12V", "/GND", "/PWM", "/LGATE", "/BOOT", "/HIGATE", "/GATE", "/DRAIN",
        "/NUC_PWM", "/DEMAND", "/TACH_PWM", "/TBASE", "/NUC_TACH",
        # the microcontroller strip
        "/P3V3", "/RST", "/DTR", "/BLK", "/TX0", "/RX1", "/MOSI", "/MISO", "/SCK"]
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
# Pad numbers are the REAL package pin numbers, not the schematic symbol's
# SPICE pin order.  See docs/pcb-notes.md for the mapping table.
PARTS = [
    # 12 V in, PWM in, fans out
    ("J1", "Connector_PinHeader_2.54mm:PinHeader_1x02_P2.54mm_Vertical",
     9.0, 37.0, 90, "F.Cu", {"1": "/P12V", "2": "/GND"}),
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
    # Two spare flyback diodes, in parallel with D1, standing at the fan end of
    # the board.  Neither is populated as built: 3 A of fan current is D1's job.
    # D2 (1N5822, 3 A) covers about 12-20 fans; D3 (MBR10100CT, 10 A dual
    # Schottky, common cathode) covers anything this driver can switch.  See
    # sim/fan_count.py.  D3's pads 1 and 3 are the two anodes, pad 2 the cathode.
    ("D2", "Diode_THT:D_DO-27_P15.24mm_Horizontal",
     47.5, 6.0, 90, "F.Cu", {"1": "/P12V", "2": "/DRAIN"}),
    ("D3", "Package_TO_SOT_THT:TO-220-3_Vertical",
     52.2, 30.0, 90, "F.Cu", {"1": "/DRAIN", "2": "/P12V", "3": "/DRAIN"}),

    # decoupling at the 12 V input
    ("C3", "Capacitor_THT:C_Disc_D5.0mm_W2.5mm_P5.00mm",
     13.0, 36.0, 270, "F.Cu", {"1": "/P12V", "2": "/GND"}),
    ("C4", "Capacitor_THT:CP_Radial_D6.3mm_P2.50mm",
     20.0, 36.0, 270, "F.Cu", {"1": "/P12V", "2": "/GND"}),

    # 4. the NUC fan-header interface, in the band below the 12 V rail.
    #    J4 is the NUC's own 4-pin fan socket; the divider turns the NUC's 5 V
    #    PWM request into the 3.3 V the Pro Mini expects, and Q4 is the open
    #    collector that answers with the fan-drive carrier on the tach line.
    ("J4", "Connector_PinHeader_2.54mm:PinHeader_1x04_P2.54mm_Vertical",
     47.0, 44.0, 0, "F.Cu",
     {"1": "/NUC_PWM", "2": "/NUC_TACH", "4": "/GND"}),          # pin 3 = no connect
    ("R7", "Resistor_THT:R_Axial_DIN0207_L6.3mm_D2.5mm_P7.62mm_Horizontal",
     34.7, 49.0, 180, "F.Cu", {"1": "/NUC_PWM", "2": "/DEMAND"}),
    ("R8", "Resistor_THT:R_Axial_DIN0207_L6.3mm_D2.5mm_P7.62mm_Horizontal",
     22.5, 49.0, 90, "F.Cu", {"1": "/DEMAND", "2": "/GND"}),
    ("C5", "Capacitor_THT:CP_Radial_D8.0mm_P3.50mm",
     16.5, 49.0, 90, "F.Cu", {"1": "/DEMAND", "2": "/GND"}),
    ("C6", "Capacitor_THT:C_Disc_D3.8mm_W2.6mm_P2.50mm",
     10.5, 49.0, 90, "F.Cu", {"1": "/DEMAND", "2": "/GND"}),
    ("R9", "Resistor_THT:R_Axial_DIN0207_L6.3mm_D2.5mm_P7.62mm_Horizontal",
     23.5, 46.0, 0, "F.Cu", {"1": "/TACH_PWM", "2": "/TBASE"}),
    ("Q4", "Package_TO_SOT_THT:TO-92_Inline_Wide",
     33.96, 55.5, 0, "F.Cu", {"1": "/GND", "2": "/TBASE", "3": "/NUC_TACH"}),

    # 5. the microcontroller strip, below the NUC band.  U1 is the Pro Mini
    # sitting on three female headers; its pad numbers are the hole numbers of
    # the clone hole map in pcb/pro_mini.py, so a pad name on the board and the
    # pin number in the schematic are the same thing.  U1 stands at 270 degrees:
    # row B (RAW .. D10) is the upper row nearest the band, with RAW at its
    # band end and D10 at the far end; row A (TX0 .. D9) is the lower row, with
    # D9 at the far end.  The programming row stands at the band end of the
    # module and GND/A6/A7 at the far end, between the two rows.
    ("U1", f"{FOOTPRINT_LIB}:{pro_mini.FOOTPRINT}",
     14.0, 87.0, 270, "F.Cu",
     {"3": "/RST", "4": "/GND", "12": "/PWM", "13": "/P12V", "15": "/RST",
      "16": "/P3V3", "20": "/DEMAND", "21": "/SCK", "22": "/MISO",
      "23": "/MOSI", "24": "/TACH_PWM", "25": "/DTR", "26": "/TX0",
      "27": "/RX1", "28": "/P3V3", "29": "/GND", "30": "/BLK", "31": "/GND"}),
    # J5 mirrors U1's own programming row pad for pad, so an FTDI/CH340 adapter
    # can plug in beside the module instead of on top of it.  Placed at 180
    # degrees so that J5 pin n sits straight across from U1 pin 24+n: pin 1
    # (DTR) at the bottom end of the board, pin 6 (BLK) at the band end.  One
    # column left of the GND descent, so MK4's courtyard stays clear of it.
    ("J5", "Connector_PinHeader_2.54mm:PinHeader_1x06_P2.54mm_Vertical",
     48.5, 85.73, 180, "F.Cu",
     {"1": "/DTR", "2": "/TX0", "3": "/RX1", "4": "/P3V3", "5": "/GND",
      "6": "/BLK"}),
    # J6 is the plain 2x3 ICSP header for programming the 328 with another
    # Arduino.  It sits in the band corner freed by MK4, directly above D11,
    # D12 and D13, so the six-way ribbon is a handfull of short stubs.
    # Pin 2 (the programmer's VCC) is deliberately a dead pad: the Pro Mini
    # powers itself from /P12V, and feeding an Uno's 5 V into a 3.3 V board is
    # how boards get destroyed.  Use five wires, not six.
    ("J6", "Connector_PinHeader_2.54mm:PinHeader_2x03_P2.54mm_Vertical",
     22.54, 67.08, 180, "F.Cu",
     {"1": "/MISO", "3": "/SCK", "4": "/MOSI", "5": "/RST", "6": "/GND"}),

    # mechanical
    ("MK1", "MountingHole:MountingHole_3.2mm_M3", 2.5, 2.5, 0, "F.Cu", {}),
    ("MK2", "MountingHole:MountingHole_3.2mm_M3", 53.5, 2.5, 0, "F.Cu", {}),
    ("MK3", "MountingHole:MountingHole_3.2mm_M3", 2.5, 89.5, 0, "F.Cu", {}),
    ("MK4", "MountingHole:MountingHole_3.2mm_M3", 53.5, 89.5, 0, "F.Cu", {}),
]

# 0 ohm jumpers used to cross a wire.  Not in the schematic on purpose.
# JP1 flies over the GND spine so /PWM can cross the return lane.  JP2 flies
# over the band rail so /P12V can reach the module's RAW pad.  JP3 flies over
# the /P3V3 link so /RST can reach pad 3.  JP4 flies over the SCK lane so
# /MISO can get back to D12.  Each is a 0 ohm link, not a component with a
# value, and each crosses exactly one foreign track.
JUMPERS: list[tuple] = [
    ("JP1", "Resistor_THT:R_Axial_DIN0207_L6.3mm_D2.5mm_P7.62mm_Horizontal",
     2.0, 14.0, 0, "F.Cu", {"1": "/PWM", "2": "/PWM"}),
    ("JP2", "Resistor_THT:R_Axial_DIN0207_L6.3mm_D2.5mm_P7.62mm_Horizontal",
     50.5, 52.88, 90, "F.Cu", {"1": "/P12V", "2": "/P12V"}),
    ("JP3", "Resistor_THT:R_Axial_DIN0207_L6.3mm_D2.5mm_P7.62mm_Horizontal",
     36.86, 76.2, 90, "F.Cu", {"1": "/RST", "2": "/RST"}),
    ("JP4", "Resistor_THT:R_Axial_DIN0207_L6.3mm_D2.5mm_P5.08mm_Vertical",
     26.4, 70.98, 90, "F.Cu", {"1": "/MISO", "2": "/MISO"}),
    ("JP5", "Resistor_THT:R_Axial_DIN0207_L6.3mm_D2.5mm_P7.62mm_Horizontal",
     9.5, 55.75, 90, "F.Cu", {"1": "/DEMAND", "2": "/DEMAND"}),
    ("JP6", "Resistor_THT:R_Axial_DIN0411_L9.9mm_D3.6mm_P7.62mm_Vertical",
     6.0, 66.5, 90, "F.Cu", {"1": "/GND", "2": "/GND"}),
    ("JP7", "Resistor_THT:R_Axial_DIN0204_L3.6mm_D1.6mm_P5.08mm_Vertical",
     16.4, 66.0, 90, "F.Cu", {"1": "/MOSI", "2": "/MOSI"}),
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
    # ---- /GND: one continuous return.  Top bus -> jog inside MK2 -> right-edge
    # descent -> band rail -> module deck.  The bus stops at x=50.5 so its
    # rounded cap clears the top-right mounting hole, then drops below the hole
    # before turning right onto x=51.5.
    bus("/GND", SPINE_X, 50.5, RAIL_GND_Y)
    track("/GND", [(50.5, RAIL_GND_Y), (50.5, 5.5)], 1.5)
    track("/GND", [(50.5, 5.5), (54.75, 5.5)], 1.5)
    track("/GND", [(54.75, 5.5), (54.75, BAND_GND_Y)], 1.5)
    bus("/GND", 6.0, 54.75, BAND_GND_Y, 1.5)
    bus("/P12V", 9.0, 48.54, RAIL_12V_Y, 3.0)
    track("/GND", [(SPINE_X, RAIL_GND_Y), (SPINE_X, 37.0)], 1.5)

    # 12 V in, decoupling
    T("/P12V", ["J1.1", (9.0, RAIL_12V_Y)])
    T("/GND", ["J1.2", (SPINE_X, 37.0)])
    T("/P12V", ["C3.1", (13.0, RAIL_12V_Y)])
    T("/P12V", ["C4.1", (20.0, RAIL_12V_Y)])
    T("/GND", ["C3.2", (SPINE_X, 31.0)])
    T("/GND", ["C4.2", (SPINE_X, 33.5)])

    # 1. level shifter.  /PWM leaves U1's D9 pad, runs left past the far end of
    # the module and up the free left edge: x = 2.0 is the one lane that clears
    # the +12 V bus (whose rounded end reaches x = 7.5), the band rail (7.25)
    # and the GND spine (4.75).  JP1 then flies over the spine.
    T("/PWM", ["U1.12", (2.0, 87.0)])
    track("/PWM", [(2.0, 87.0), "JP1.1"])
    T("/PWM", ["JP1.2", "R1.1"])
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

    # 4. the NUC interface band.  Its return arrives down the right edge, past
    # the end of the 12 V bus, so nothing crosses that bus to get here.
    # The divider: /DEMAND is the rail the three shunt parts hang off.
    track("/DEMAND", [(10.5, DEMAND_Y), (27.08, DEMAND_Y)])
    track("/GND", [(10.5, 51.5), (12.5, 51.5), (12.5, BAND_GND_Y)])
    track("/GND", [(16.5, 52.5), (16.5, BAND_GND_Y)])
    track("/GND", [(22.5, 56.62), (22.5, BAND_GND_Y)])

    # the tach output: 1 k series, then Q4 as an open collector.  J4 stands
    # vertical at the band's right end so /NUC_PWM and /NUC_TACH fan out left
    # and down without crossing anything; R9 lies flat left of it, Q4 below.
    track("/TACH_PWM", [(23.5, 46.0), (3.85, 46.0), (3.85, 71.76), "U1.24"])
    track("/TBASE", [(31.12, 46.0), (31.12, 53.0), (36.5, 53.0), "Q4.2"])
    track("/GND", ["Q4.1", (33.96, BAND_GND_Y)])
    track("/NUC_TACH", ["J4.2", (44.5, 46.54), (44.5, 55.5)])
    track("/NUC_PWM", ["J4.1", (34.7, 44.0), "R7.1"])
    # J4's GND pin drops straight to the band rail.
    track("/GND", ["J4.4", (47.0, BAND_GND_Y)])

    # 5. the module deck.  /P12V drops from the bus end at x=50.0 to jumper
    # JP2, which flies over the band rail; from JP2 it runs left of the
    # programming row and enters pad 13 (RAW) from above.  /GND keeps running
    # down the right edge (x=54.75) past the band rail, then turns left at
    # y=75.57 through J5 pad 5 into U1 pad 29.
    track("/P12V", [(48.54, RAIL_12V_Y), (50.5, RAIL_12V_Y), (50.5, 52.88)], 1.5)
    track("/P12V", ["JP2.2", (50.5, 66.0), (41.94, 66.0), "U1.13"], 1.0)
    track("/GND", [(54.75, BAND_GND_Y), (54.75, 75.57), (44.48, 75.57), "U1.29"], 1.5)

    # the programming row to J5: straight shots, same y on both sides.
    # (/GND pad 29 and J5 pad 5 are fed by the stub above, not across.)
    for pu, ju, net in ((25, 1, "/DTR"), (26, 2, "/TX0"), (27, 3, "/RX1"),
                        (28, 4, "/P3V3"), (30, 6, "/BLK")):
        track(net, [f"U1.{pu}", f"J5.{ju}"], 0.8)
    # U1's 3.3 V output: pad 16 (row B) down and across to pad 28 (programming
    # row), where the J5 stub continues the same net to the adapter header.
    # The lane at x=34.9 stays left of the /RST column (x=36.86) and clears
    # spare pad 35 by 0.6 mm.
    track("/P3V3", ["U1.16", (34.9, 71.76), (34.9, 78.11)], 0.8)
    track("/P3V3", [(34.9, 78.11), "U1.28"], 0.8)

    # the ICSP fan-out.  J6 stands at 180 degrees so its NC/MOSI/GND column
    # (x=20) faces the module's spare-pad column and its MISO/SCK/RST column
    # (x=22.54) faces the open deck.  Planar permutation: MOSI turns left at
    # the header and drops straight to D11.  SCK takes the outside lane down
    # x=28.5 and back left along y=73.5 into D13.  MISO drops x=26.4 to jumper
    # JP4, which flies over the SCK lane, then runs back left along y=75.98
    # and comes up into D12.  RST runs right at y=62, drops into pad 15, and
    # jumper JP3 flies it over the /P3V3 link down to pad 3; /DEMAND takes the
    # left lane down to y=81.5 and comes up into A0; J6's GND drops the far
    # left to the spare GND pad 31.
    track("/MOSI", ["J6.4", (16.4, 64.54), (16.4, 66.0)], 0.8)
    track("/MOSI", ["JP7.2", "U1.23"], 0.8)
    track("/SCK", ["J6.3", (28.5, 64.54), (28.5, 73.5), (21.62, 73.5), "U1.21"], 0.8)
    track("/MISO", ["J6.1", (26.4, 67.08), (26.4, 70.98)], 0.8)
    track("/MISO", ["JP4.2", (19.08, 76.06), (19.08, 71.76), "U1.22"], 0.8)
    track("/RST", ["J6.5", (36.86, 62.0), (36.86, 76.2)], 0.8)
    track("/RST", ["JP3.2", (36.86, 87.0)], 0.8)
    # /DEMAND leaves the divider rail at its left end, crosses the band rail on
    # jumper JP5, and comes into pad 20 from above along y=69.0, so it never
    # touches the SCK/MISO lanes below row B.  JP7 hops the /MOSI drop over that
    # /DEMAND lane and JP6 hops the spare GND pad 31 feed over the /TACH lane.
    track("/DEMAND", [(10.5, DEMAND_Y), (9.5, DEMAND_Y), (9.5, 55.75)], 0.8)
    track("/DEMAND", ["JP5.2", (9.5, 69.0), (24.16, 69.0), "U1.20"], 0.8)
    track("/GND", ["J6.6", (20.0, BAND_GND_Y)], 0.8)
    track("/GND", [(6.0, BAND_GND_Y), (6.0, 66.5)], 0.8)
    track("/GND", ["JP6.2", (6.0, 79.38), "U1.31"], 0.8)


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
    for m in fp['models']:
        out.append('\t\t' + sexpr_to_str(m))
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
        ("copper on back", 29.0, 7.0),
        ("JP1 = 0 ohm link", 6.0, 18.0),
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
