"""Build the single-sided (home-etchable) board: nuc-fan-controller.kicad_pcb

One copper layer (F.Cu).  Every part sits on that same face, GND is a copper pour over
the whole board, and the two fan rails are 1.8 mm bars 2.54 mm apart so the three fan
headers straddle them with no routing at all.  No vias, no jumpers, no track under 0.7 mm.

Run from the repository root:   python3 logs/build1l.py
Then check it:                 sh logs/drc.sh

The rules this build is written to:
  track, gap, pour clearance   0.70 mm
  power rails                  1.80 mm  (12 V and the switched fan rail; 0.3 A measured)
  copper to board edge         0.50 mm
  drill                        0.90 signal, 1.00 headers, 3.20 mounting holes
  grid                         everything lands on a 2.54 mm grid; the router steps 0.635
"""
import heapq
import math
import re
import sys
import uuid

SRC = 'nuc-fan-controller.kicad_pcb'          # the board this writes
TPL = 'logs/fp-templates.inc'                 # footprint templates (see logs/getfp.py)

BOARD_W, BOARD_H = 88.90, 83.82
GRID = 0.635
CLEAR = 0.70
TRACE = 0.70
POWER = 1.80
EDGE_CLEAR = 0.50
SLACK = 0.06              # the router leaves a hair more than the rule asks for
ROUTE_WIN = 6.0           # how far outside a leg's own pads its route may wander
POUR_GAP = 2.20           # trace-to-trace/rail gap: 2*CLEAR + the pour's min_thickness
MIN_DRILL = 0.90
ANNULAR = 0.25
MIN_PAD = 1.40
MAX_PAD = 1.80        # 2.54 grid: two pads this wide still leave 0.74 mm of gap

NETS = ['+12V', '+3V3', '19V', 'BASE', 'FAN_GATE', 'FAN_PWM', 'FAN_SW', 'GATE', 'GND',
        'NUC_PWM', 'NUC_TACH', 'PWM_DIV', 'PWM_IN', 'TACH_BASE', 'TACH_OUT',
        'unconnected-(J2-Pin_4-Pad4)']

HDR2 = 'Connector_PinHeader_2.54mm:PinHeader_1x02_P2.54mm_Vertical'
HDR4 = 'Connector_PinHeader_2.54mm:PinHeader_1x04_P2.54mm_Vertical'
HDR5 = 'Connector_PinHeader_2.54mm:PinHeader_1x05_P2.54mm_Vertical'
RES = 'Resistor_THT:R_Axial_DIN0204_L3.6mm_D1.6mm_P5.08mm_Horizontal'
TO92 = 'Package_TO_SOT_THT:TO-92_Inline_Wide'
TO220 = 'Package_TO_SOT_THT:TO-220-3_Vertical'
SOT223 = 'Package_TO_SOT_SMD:SOT-223-3_TabPin2'
DISC38 = 'Capacitor_THT:C_Disc_D3.8mm_W2.6mm_P2.50mm'
DISC30 = 'Capacitor_THT:C_Disc_D3.0mm_W2.0mm_P2.50mm'
RAD10 = 'Capacitor_THT:CP_Radial_D10.0mm_P5.00mm'
RAD8 = 'Capacitor_THT:CP_Radial_D8.0mm_P3.50mm'
RAD63 = 'Capacitor_THT:CP_Radial_D6.3mm_P2.50mm'
DIODE = 'Diode_THT:D_DO-41_SOD81_P10.16mm_Horizontal'
TP = 'TestPoint:TestPoint_Pad_D1.5mm'
MH = 'MountingHole:MountingHole_3.2mm_M3'

# (ref, template, new name, x, y, rotation, pad nets in pad order, pad-at overrides in pad order)
# Rotations are KiCad's counter-clockwise degrees; Y points down the page.
# --------------------------------------------------------------------------
# The board: one copper layer, every part on it, no jumpers, no jump wires.
#
# The two power nets run as 1.8 mm bars 2.54 mm apart across the middle of the
# board (+12 V at y=48.26, FAN_SW at y=50.8).  That spacing is not arbitrary: a
# 2-pin 2.54 header plugged straight across them lands pin 1 on +12 V and pin 2
# on FAN_SW with zero routing, which is exactly what J3/J4/J7 (fan) and D2 (the
# fan's flyback clamp) need.  The bars do not run the same distance: +12 V stops
# at x=12 and FAN_SW at x=124.46, so at either end there is a clear column where
# a trace can cross from one side of the slot to the other without touching the
# other bar.
# --------------------------------------------------------------------------
GRID = 2.54
BAR_W = 1.8
Y12, YSW = 25.40, 27.94
X12_A, X12_B = 13.97, 81.28          # the +12 V bar, and its riser up the right edge
YS_RISER = 68.58
XSW_A, XSW_B = 13.97, 71.12

# ref, KiCad footprint, x, y, rot, nets in pad order, pad offsets (default: the template's)
PARTS = [
    # ---- power entry, bottom right: the module's socket and the 19 V in ----
    ("J6",  "Connector_PinHeader_2.54mm:PinHeader_1x04_P2.54mm_Vertical",
     78.74, 17.78, 0, ["GND", "GND", "19V", "+12V"],
     [(0, 0), (0, 2.54), (0, 5.08), (0, 7.62)]),
    ("J1",  "Connector_PinHeader_2.54mm:PinHeader_1x02_P2.54mm_Vertical",
     71.12, 17.78, 90, ["19V", "GND"]),
    ("C3",  "Capacitor_THT:CP_Radial_D8.0mm_P3.50mm",
     48.26, 20.32, 90, ["+12V", "GND"], [(0, 0), (5.08, 0)]),
    ("C4",  "Capacitor_THT:C_Disc_D6.0mm_W2.5mm_P5.00mm",
     58.42, 22.86, 0, ["+12V", "GND"], [(0, 0), (2.54, 0)]),
    # ---- the three fan connectors, plugged straight across the two bars ----
    ("J3",  "Connector_PinHeader_2.54mm:PinHeader_1x02_P2.54mm_Vertical",
     13.97, Y12, 0, ["+12V", "FAN_SW"], [(0, 0), (0, 2.54)]),
    ("J4",  "Connector_PinHeader_2.54mm:PinHeader_1x02_P2.54mm_Vertical",
     19.05, Y12, 0, ["+12V", "FAN_SW"], [(0, 0), (0, 2.54)]),
    ("J7",  "Connector_PinHeader_2.54mm:PinHeader_1x02_P2.54mm_Vertical",
     24.13, Y12, 0, ["+12V", "FAN_SW"], [(0, 0), (0, 2.54)]),
    # ---- D2 clamps the fans' flyback into +12 V; C12 bypasses the switched rail
    ("D2",  "Diode_THT:D_DO-41_SOD81_P10.16mm_Horizontal",
     73.66, Y12, 270, ["+12V", "FAN_SW"]),
    ("C12", "Capacitor_THT:C_Disc_D6.0mm_W2.5mm_P5.00mm",
     35.56, YSW, 270, ["FAN_SW", "GND"], [(0, 0), (5.08, 0)]),
    # ---- the low-side fan switch, its gate divider, and Q2 which drives it ----
    ("Q3",  "Package_TO_SOT_THT:TO-220-3_Vertical",
     63.50, 33.02, 0, ["GATE", "FAN_SW", "GND"]),
    ("R10", "Resistor_THT:R_Axial_DIN0204_L3.6mm_D1.6mm_P5.08mm_Horizontal",
     68.58, 38.10, 180, ["GATE", "GND"]),
    # R11 is not in the schematic.  It is the bridge that lets FAN_PWM cross the divider
    # row on a board with one copper layer; see BARS.
    ("R11", "Resistor_THT:R_Axial_DIN0204_L3.6mm_D1.6mm_P5.08mm_Horizontal",
     53.34, 55.87, 270, ["FAN_PWM", "FAN_PWM"]),
    ("R9",  "Resistor_THT:R_Axial_DIN0204_L3.6mm_D1.6mm_P5.08mm_Horizontal",
     58.42, 45.72, 0, ["FAN_GATE", "GATE"]),
    ("R8",  "Resistor_THT:R_Axial_DIN0204_L3.6mm_D1.6mm_P5.08mm_Horizontal",
     63.50, 50.80, 0, ["+12V", "FAN_GATE"], [(5.08, 0), (0, 0)]),
    ("Q2",  "Package_TO_SOT_THT:TO-92_Inline_Wide",
     48.26, 45.72, 0, ["GND", "BASE", "FAN_GATE"]),
    ("R6",  "Resistor_THT:R_Axial_DIN0204_L3.6mm_D1.6mm_P5.08mm_Horizontal",
     45.72, 38.10, 0, ["FAN_PWM", "BASE"]),
    ("R7",  "Resistor_THT:R_Axial_DIN0204_L3.6mm_D1.6mm_P5.08mm_Horizontal",
     55.88, 38.10, 0, ["BASE", "GND"]),
    # ---- the 3.3 V regulator and its caps, hung on the +12 V riser ----------
    ("U3",  "Package_TO_SOT_SMD:TO-252-3_TabPin2",
     76.20, 66.04, 90, ["GND", "+3V3", "+12V"]),
    ("C7",  "Capacitor_THT:CP_Radial_D6.3mm_P2.50mm",
     60.96, 76.20, 90, ["+3V3", "GND"], [(0, 0), (5.08, 0)]),
    ("C8",  "Capacitor_THT:C_Disc_D3.8mm_W2.6mm_P2.50mm",
     71.12, 76.20, 90, ["+3V3", "GND"], [(0, 0), (5.08, 0)]),
    # ---- the NUC interface, top left: GND, tach, PWM, pin 4 not fitted -----
    ("J2",  "Connector:FanPinHeader_1x04_P2.54mm_Vertical",
     12.70, 78.74, 0, ["GND", "NUC_TACH", "NUC_PWM", ""]),
    # ---- tach front end: Q1 buffers the NUC's open-collector tach, R2 pulls
    #      it up, C9 and TP1 tap the line
    ("Q1",  "Package_TO_SOT_THT:TO-92_Inline_Wide",
     22.86, 66.04, 0, ["GND", "TACH_BASE", "NUC_TACH"]),
    ("R2",  "Resistor_THT:R_Axial_DIN0204_L3.6mm_D1.6mm_P5.08mm_Horizontal",
     30.48, 71.12, 270, ["TACH_BASE", "TACH_OUT"]),
    ("C9",  "Capacitor_THT:C_Disc_D3.8mm_W2.6mm_P2.50mm",
     35.56, 71.12, 90, ["NUC_TACH", "GND"], [(0, 0), (5.08, 0)]),
    ("TP1", "TestPoint:TestPoint_Pad_D1.5mm",
     45.72, 68.58, 0, ["NUC_TACH"]),
    # ---- the PWM divider: NUC_PWM - R3 - PWM_DIV - R4 - PWM_IN - R5 - GND --
    ("R3",  "Resistor_THT:R_Axial_DIN0204_L3.6mm_D1.6mm_P5.08mm_Horizontal",
     20.32, 58.42, 0, ["NUC_PWM", "PWM_DIV"]),
    ("R4",  "Resistor_THT:R_Axial_DIN0204_L3.6mm_D1.6mm_P5.08mm_Horizontal",
     30.48, 58.42, 0, ["PWM_DIV", "PWM_IN"]),
    ("R5",  "Resistor_THT:R_Axial_DIN0204_L3.6mm_D1.6mm_P5.08mm_Horizontal",
     45.72, 58.42, 90, ["PWM_IN", "GND"]),
    ("C10", "Capacitor_THT:CP_Radial_D6.3mm_P2.50mm",
     58.42, 58.42, 90, ["PWM_IN", "GND"], [(0, 0), (5.08, 0)]),
    ("C11", "Capacitor_THT:C_Disc_D3.8mm_W2.6mm_P2.50mm",
     68.58, 58.42, 90, ["PWM_IN", "GND"], [(0, 0), (5.08, 0)]),
    # ---- the Pro Mini plugs in along the top edge --------------------------
    ("J5",  "Connector_PinHeader_2.54mm:PinHeader_1x05_P2.54mm_Vertical",
     48.26, 81.28, 90, ["GND", "TACH_OUT", "FAN_PWM", "PWM_IN", "+3V3"]),
    # ---- mounting holes, M3 ------------------------------------------------
    ("MK1", "MountingHole:MountingHole_3.2mm_M3",  5.08, 12.70, 0, []),
    ("MK2", "MountingHole:MountingHole_3.2mm_M3", 83.82, 12.70, 0, []),
    ("MK3", "MountingHole:MountingHole_3.2mm_M3", 83.82, 76.20, 0, []),
    ("MK4", "MountingHole:MountingHole_3.2mm_M3",  5.08, 76.20, 0, []),

]

VALUES = {
    'C3': '470uF 25V', 'C4': '100n', 'C7': '10uF', 'C8': '100n', 'C9': '100p',
    'C10': '1uF', 'C11': '100n', 'C12': '100n', 'D2': '1N5819',
    'J1': '19V IN', 'J2': 'NUC fan header', 'J3': 'FAN 2', 'J4': 'FAN 3',
    'J5': 'Pro Mini', 'J6': 'BUCK MODULE', 'J7': 'FAN 1',
    'Q1': 'BC547B', 'Q2': 'BC547B', 'Q3': 'IRFZ44N',
    'R2': '1k', 'R3': '4.7k', 'R4': '2.2k', 'R5': '10k', 'R6': '1k',
    'R7': '10k', 'R8': '1k', 'R9': '120R', 'R10': '10k', 'R11': '0R bridge',
    'TP1': 'TACH', 'U3': 'AMS1117-3.3',
    'MK1': 'M3', 'MK2': 'M3', 'MK3': 'M3', 'MK4': 'M3',
}

# Copper drawn by hand rather than routed: the rails, their feeds, the stubs that land
# a pad on a rail.  A pad sitting on a rail is connected by the rail itself.
# Every power net is drawn, not routed: a 1.8 mm bar to each of its pads.  On a board
# this size that is how a single-sided supply is actually laid out, and it takes the four
# fattest nets out of the router's way so the thin signal nets get the lanes.
BARS = [
    # +12 V: the rail under the fan connectors, a riser up the right edge, and a stub
    # to each pad that hangs off them
    ("+12V", (X12_A, Y12), (81.28, Y12)),
    ("+12V", (81.28, Y12), (81.28, 71.08)),
    ("+12V", (78.48, 71.08), (81.28, 71.08), 1.20),    # U3 pad 3
    ("+12V", (68.58, 50.80), (81.28, 50.80)),        # R8 pad 1
    ("+12V", (58.42, 22.86), (58.42, Y12)),           # C4 pad 1
    ("+12V", (48.26, 20.32), (48.26, Y12)),           # C3 pad 1
    # FAN_SW: the rail, and the two stubs that lift it to D2 and to Q3's drain
    ("FAN_SW", (XSW_A, YSW), (73.66, YSW)),
    ("FAN_SW", (66.04, YSW), (66.04, 33.02)),
    ("FAN_SW", (73.66, YSW), (73.66, 35.56)),
    # 19 V: the short run from the brick's header to the module's socket
    ("19V", (71.12, 17.78), (71.12, 22.86)),
    ("19V", (71.12, 22.86), (78.74, 22.86)),
    # +3V3: from the regulator's tab out to the Pro Mini's VCC pin
    # The 3.3 V rail sits 5.08 mm above the Pro Mini's row, not 2.54.  A bar 2.54 above a
    # header row walls the row off: the bar's clearance band and the pads' clearance band
    # meet with nothing left between them, so no trace can come down onto any pad but the
    # one the bar's own stub lands on.
    ("+3V3", (76.20, 64.78), (76.20, 76.20)),         # tab -> pin 2 -> rail, one straight run
    ("+3V3", (60.96, 76.20), (76.20, 76.20)),         # C7 and C8 hang off this stretch
    # The VCC feed comes down at x=60.96, not straight down at the pin's own x.  The gap
    # between the FAN_PWM bar (x=53.34) and a stub at x=58.42 is 5.08 mm, and after the
    # trace's own clearance on both sides 0.13 mm is left: no lane.  Moving the stub one
    # pitch right opens the lane every other net on that row needs.
    ("+3V3", (60.96, 76.20), (60.96, 81.28)),
    ("+3V3", (60.96, 81.28), (58.42, 81.28)),         # into the Pro Mini's VCC pin
    # FAN_PWM, drawn.  It climbs from the Pro Mini's D11 pin up the one column that is
    # clear all the way (x=53.34), crosses under the fan-drive row at y=50.8, and comes
    # up the left of the divider to R6.  Routed, the A* sent it the long way round the
    # board instead, and a trace on the perimeter walls the ground pour off.
    # The one crossing this board cannot route around.  The divider's row lies between
    # the Pro Mini's row and the fan drive, and FAN_PWM has to get from one to the other,
    # so it crosses the divider row at x=53.34 under R11, a 0 R bridge.  The bridge is a
    # board part only: the schematic has no such component, and the BOM lists it.
    ("FAN_PWM", (53.34, 81.28), (53.34, 60.95), 0.90),
    ("FAN_PWM", (53.34, 55.87), (53.34, 50.80), 0.90),
    ("FAN_PWM", (53.34, 50.80), (43.18, 50.80), 0.90),
    ("FAN_PWM", (43.18, 50.80), (43.18, 38.10), 0.90),
    ("FAN_PWM", (43.18, 38.10), (45.72, 38.10), 0.90),
    # The NUC interface and the tach line, drawn for the same reason.  Their four ends
    # interleave on the board: J2's tach pin and its PWM pin sit side by side on the
    # header, and the parts they lead to sit on the other side of everything else, so
    # one of the two would have to cross the other.  Sending the tach line around the
    # bottom of the row untangles it, and the untangled version is what leaves the
    # ground pour in one piece.
    ("NUC_TACH", (15.24, 78.74), (15.24, 81.28), 0.90),
    ("NUC_TACH", (15.24, 81.28), (27.94, 81.28), 0.90),
    ("NUC_TACH", (27.94, 81.28), (27.94, 66.04), 0.90),
    ("NUC_TACH", (27.94, 73.66), (35.56, 73.66), 0.90),
    ("NUC_TACH", (35.56, 73.66), (35.56, 71.12), 0.90),
    ("NUC_PWM", (17.78, 78.74), (17.78, 58.42), 0.90),
    ("NUC_PWM", (17.78, 58.42), (20.32, 58.42), 0.90),
    ("TACH_OUT", (30.48, 76.20), (50.80, 76.20), 0.90),
    ("TACH_OUT", (50.80, 76.20), (50.80, 81.28), 0.90),
    # TACH_BASE and the divider's own row, drawn for the same reason as above: left to
    # the router TACH_BASE took an 18 mm fence and came back through the fan drive,
    # which then walled BASE and FAN_GATE in.
    ("TACH_BASE", (25.40, 66.04), (25.40, 63.50), 0.90),
    ("TACH_BASE", (25.40, 63.50), (30.48, 63.50), 0.90),
    ("TACH_BASE", (30.48, 63.50), (30.48, 71.12), 0.90),
    ("PWM_IN", (35.56, 58.42), (68.58, 58.42), 0.90),     # R4 - R5 - C10 - C11, one bar
    ("PWM_IN", (55.88, 81.28), (55.88, 58.42), 0.90),     # down to the Pro Mini's A0
]

# The nets the router has to finish.  The tight two-pad nets go first: they are the ones
# a long trace can wall off, and they have nowhere else to go.
# GND is not in the list: the pour under everything connects it.  Routing it pad to pad
# first would wall the board off with a chain of 0.7 mm traces.
# Short and tight first, the long ones last: a long trace routed early wanders wherever
# the A* likes and walls off the lanes a tight net has nowhere else to use.
ROUTE_ORDER = ['NUC_PWM', 'NUC_TACH', 'TACH_BASE', 'TACH_OUT', 'PWM_DIV', 'PWM_IN',
               'BASE', 'FAN_GATE', 'GATE']   # drawn nets seed the chain; only stubs get routed

# Holes that carry no pad: the router has to know about them.
HOLES = [(5.08, 12.70, 1.6), (83.82, 12.70, 1.6), (83.82, 76.20, 1.6), (5.08, 76.20, 1.6),
         (78.74, 17.78, 0.55), (78.74, 20.32, 0.55)]      # holes with no pad: a track must stay off them

# Silk text that is not part of a footprint
# Silkscreen that says what each row is for.  The footprints already print pin numbers;
# these are the functions, so the board can be built without going back to the schematic.
LABELS = [
    ('19V in', 66.04, 15.24),
    ('module: 1 2 GND  3 19V  4 12V', 58.42, 13.97),
    ('12V', 6.35, 24.60),
    ('fan SW', 6.35, 29.20),
    ('1N5819', 73.66, 39.37),
    ('GND  TACH  PWM  NC', 12.70, 82.55),
    ('GND  TACH  PWM  PWM  3V3', 48.26, 78.74),
    ('3.3V', 71.12, 73.66),
]

# Nothing lives above the 19 V row at y=17.78 but the mounting holes, and 17.78 mm of empty
# board is a fifth of the panel.  Lift the whole layout 7.62 mm and close the outline on it.
Y0 = 7.62
BOARD_H -= Y0
PARTS = [(p[0], p[1], p[2], p[3] - Y0, p[4], p[5]) + tuple(p[6:]) for p in PARTS]
BARS = [(b[0], (b[1][0], b[1][1] - Y0), (b[2][0], b[2][1] - Y0)) + tuple(b[3:]) for b in BARS]
HOLES = [(h[0], h[1] - Y0, h[2]) for h in HOLES]
LABELS = [(t, x, y - Y0) for t, x, y in LABELS]


def U():
    return str(uuid.uuid4())


# ------------------------------------------------------------------ templates
def blocks(src, head):
    """Spans of every block that starts with `head` (matched at any depth)."""
    for m in re.finditer(re.escape(head), src):
        i = src.index('(', m.start())
        depth = 0
        while i < len(src):
            c = src[i]
            if c == '(':
                depth += 1
            elif c == ')':
                depth -= 1
                if depth == 0:
                    yield (m.start(), i + 1)
                    break
            i += 1


def templates(src):
    out = {}
    for s, e in blocks(src, '\t(footprint "'):
        b = src[s:e]
        name = re.match(r'\t\(footprint "([^"]+)"', b).group(1)
        out.setdefault(name, b)
    return out


PAD_RE = re.compile(r'\t\t\(pad "[^"]+" .*?\n\t\t\)', re.S)


def strip_graphics(b):
    """Drop every fp_* graphic from a footprint block (used for the re-drawn diode)."""
    out, last = [], 0
    for s, e in blocks(b, '\t\t(fp_'):
        out.append(b[last:s])
        last = e
    out.append(b[last:])
    return ''.join(out)


def pad_block(pid, shape, at, size, drill, net, mask='*.Cu'):
    drill_line = '\n\t\t\t(drill %.2f)' % drill if drill else ''
    return ('\t\t(pad "%s" %s\n\t\t\t(at %.2f %.2f)\n\t\t\t(size %.2f %.2f)%s\n'
            '\t\t\t(layers "%s" "*.Mask")\n\t\t\t(net "%s")\n\t\t\t(uuid "%s")\n\t\t)'
            % (pid, shape, at[0], at[1], size[0], size[1], drill_line, mask, net, U()))


def diode_footprint(x, y, nets):
    """D2 lies across the two rails: pad 1 (cathode) on the 12 V bar, pad 2 (anode) on
    the fan rail, 5.08 across and 2.54 down.  Body drawn along that diagonal."""
    ux, uy = 5.08 / 5.657, 2.54 / 5.657
    vx, vy = -uy, ux                      # across the body
    cx, cy = 2.54, 1.27
    hl, hw = 2.60, 1.30                   # DO-41 is 5.3 x 2.7 mm
    corners = [(cx + hl * ux + hw * vx, cy + hl * uy + hw * vy),
               (cx + hl * ux - hw * vx, cy + hl * uy - hw * vy),
               (cx - hl * ux - hw * vx, cy - hl * uy - hw * vy),
               (cx - hl * ux + hw * vx, cy - hl * uy + hw * vy)]
    band = ((0 + 1.0 * ux + hw * vx, 0 + 1.0 * uy + hw * vy),
            (0 + 1.0 * ux - hw * vx, 0 + 1.0 * uy - hw * vy))

    def line(pts, layer, width=0.15):
        return ('\t\t(fp_poly\n\t\t\t(pts %s)\n\t\t\t(stroke\n\t\t\t\t(width %.2f)\n'
                '\t\t\t\t(type solid)\n\t\t\t)\n\t\t\t(fill none)\n\t\t\t(layer "%s")\n'
                '\t\t\t(uuid "%s")\n\t\t)'
                % (' '.join('(xy %.3f %.3f)' % p for p in pts), width, layer, U()))

    body = line(corners + [corners[0]], 'F.Fab', 0.1)
    silk = line([corners[1], corners[2]], 'F.SilkS') + \
        line([corners[3], corners[0]], 'F.SilkS') + \
        line([band[0], band[1]], 'F.SilkS')
    yard = line([(-1.2, -1.2), (6.2, -1.2), (6.2, 3.74), (-1.2, 3.74), (-1.2, -1.2)], 'F.CrtYd', 0.05)

    return '\n'.join([
        '\t(footprint "nucfan:D_DO-41_P5.08x2.54"',
        '\t\t(layer "F.Cu")',
        '\t\t(uuid "%s")' % U(),
        '\t\t(at %.2f %.2f 0)' % (x, y),
        '\t\t(property "Reference" "D2"\n\t\t\t(at 1.0 -2.2 0)\n\t\t\t(layer "F.SilkS")'
        '\n\t\t\t(uuid "%s")\n\t\t\t(effects\n\t\t\t\t(font\n\t\t\t\t\t(size 1.1 1.1)'
        '\n\t\t\t\t\t(thickness 0.15)\n\t\t\t\t)\n\t\t\t)' % U(),
        '\t\t(property "Value" "1N5819"\n\t\t\t(at 1.0 4.2 0)\n\t\t\t(layer "F.Fab")'
        '\n\t\t\t(uuid "%s")\n\t\t\t(effects\n\t\t\t\t(font\n\t\t\t\t\t(size 1.1 1.1)'
        '\n\t\t\t\t\t(thickness 0.1)\n\t\t\t\t)\n\t\t\t)' % U(),
        '\t\t(property "Datasheet" ""\n\t\t\t(at 0 0 0)\n\t\t\t(layer "F.Fab")'
        '\n\t\t\t(uuid "%s"))' % U(),
        '\t\t(property "Description" "40V 1A Schottky rectifier, body laid across the '
        'two rails"\n\t\t\t(at 0 0 0)\n\t\t\t(layer "F.Fab")\n\t\t\t(uuid "%s"))' % U(),
        silk, body, yard,
        pad_block('1', 'thru_hole rect', (0, 0), (1.8, 1.8), 0.9, nets[0]),
        pad_block('2', 'thru_hole rect', (5.08, 2.54), (1.8, 1.8), 0.9, nets[1]),
        '\t)',
    ])


def rot_pt(lx, ly, deg):
    """KiCad's footprint rotation, in board coordinates (y runs *down* the panel).

    Verified against pcbnew: a pad 5.08 mm to the right of a footprint placed at 90
    ends up 5.08 mm above it, and at 270 it ends up below.  Getting this backwards is
    how a board ends up with its stubs pointing into the wrong rail.
    """
    a = math.radians(deg)
    c, sn = math.cos(a), math.sin(a)
    return (lx * c + ly * sn, -lx * sn + ly * c)


def make_part(tpl, ref, value, fpname, x, y, rot, nets, pad_at):
    """Clone a template footprint: move it, re-pitch it, name its pads' nets.

    Nets and pad offsets are matched to the footprint's *pad numbers*, in the order they
    appear, not to its pad blocks: a TO-252 has two pads numbered 2 (the leads and the
    tab), and a fan header carries an unnamed peg hole.  Counting blocks instead of
    numbers silently shifts every net one pad to the left.
    """
    b = tpl
    if fpname:
        b = re.sub(r'\(footprint "[^"]+"', '(footprint "%s"' % fpname, b, count=1)
    # A .kicad_mod carries no placement of its own; a footprint in a board does, and it
    # sits right after the footprint's layer.  Appending it there is what actually moves
    # the part — rewriting "the first (at ...) in the block" instead hits a pad.
    if rot:
        b = rotate_block(b, rot)
        if rot in (90, 270):
            b = re.sub(r'\(size ([\d.]+) ([\d.]+)\)',
                       lambda m: '(size %s %s)' % (m.group(2), m.group(1)), b)
    if ref == 'J2':
        # The library's fan header carries an unnamed NPTH peg at (5.08, -2.16) that
        # centres a fan's plug.  It sits exactly on the lane that leaves the header's
        # PWM pin, and nothing electrically depends on it, so this board drops it and
        # holds the plug with the two screws at either end of the case instead.
        b = re.sub(r'\t\t\(pad "" np_thru_hole circle[\s\S]*?\n\t\t\)\n', '', b, count=1)
    b = re.sub(r'(\n\t\t)\(layer "[FB]\.Cu"\)',
               r'\g<1>(layer "F.Cu")\n\g<1>(at %.2f %.2f 0)' % (x, y), b, count=1)

    pads = list(PAD_RE.finditer(b))
    nums = [re.match(r'\t\t\(pad "([^"]*)"', m.group(0)).group(1) for m in pads]
    order = []
    for n in nums:
        if n and n not in order:
            order.append(n)
    net_of = dict(zip(order, nets))
    at_of = dict(zip(order, pad_at))

    new, last = [], 0
    for m, num in zip(pads, nums):
        new.append(b[last:m.start()])
        p = m.group(0)
        if num in at_of:
            px, py = rot_pt(*at_of[num], rot)
            p = re.sub(r'\(at -?[\d.]+ -?[\d.]+(?: -?[\d.]+)?\)',
                       '(at %.2f %.2f)' % (px, py), p, count=1)
        p = fit_hole(p)
        if num in net_of:
            if re.search(r'\(net "[^"]*"\)', p):
                p = re.sub(r'\(net "[^"]*"\)', '(net "%s")' % net_of[num], p, count=1)
            else:
                p = p.replace('\n\t\t)', '\n\t\t\t(net "%s")\n\t\t)' % net_of[num])
        new.append(p)
        last = m.end()
    new.append(b[last:])
    b = ''.join(new)

    b = re.sub(r'(\(property "Reference" ")[^"]*(")', r'\g<1>%s\g<2>' % ref, b, count=1)
    if value:
        b = re.sub(r'(\(property "Value" ")[^"]*(")', r'\g<1>%s\g<2>' % value, b, count=1)
    b = re.sub(r'\(uuid "[^"]*"\)', lambda m: '(uuid "%s")' % U(), b)
    return b


def rotate_block(b, deg):
    """Turn a footprint's own artwork and pad positions about its origin.

    The board places every footprint at rot 0 and turns it here instead: one rotation
    convention in one place, and the router then reads the same numbers the board carries.
    Line-wise, because `(at ...)` means three different things in a footprint block.
    """
    out = []
    for line in b.split('\n'):
        m = re.match(r'^(\s*\(at )([-\d.]+) ([-\d.]+)(?: ([-\d.]+))?\)\s*$', line)
        if m:
            nx, ny = rot_pt(float(m.group(2)), float(m.group(3)), deg)
            extra = '' if m.group(4) is None else ' %.2f' % (float(m.group(4)) + deg)
            out.append('%s%.2f %.2f%s)' % (m.group(1), nx, ny, extra))
            continue
        m = re.match(r'^(\s*\((?:start|end|mid|center) )([-\d.]+) ([-\d.]+)\)\s*$', line)
        if m:
            nx, ny = rot_pt(float(m.group(2)), float(m.group(3)), deg)
            out.append('%s%.2f %.2f)' % (m.group(1), nx, ny))
            continue
        out.append(line)
    return '\n'.join(out)


def fit_hole(p):
    """Rescale a through-hole pad for the way this board is made.

    Nothing drilled below 0.9 mm (a hand drill wanders under that) and nothing wider
    than 1.8 mm: on a 2.54 mm grid two 1.8 mm pads still leave 0.74 mm of gap, which is
    the clearance rule.  That is what a TO-220 and a fan header need — the library draws
    them 1.9 to 2.0 mm wide, and at 2.54 mm pitch their own pads would violate the
    board's own clearance.
    """
    d = re.search(r'\(drill ([\d.]+)\)', p)
    if not d:
        return p
    drill = float(d.group(1))
    s = re.search(r'\(size ([\d.]+) ([\d.]+)\)', p)
    if not s:
        return p
    w, h = float(s.group(1)), float(s.group(2))
    drill = min(max(drill, MIN_DRILL), MAX_PAD - 2 * ANNULAR)
    w, h = min(max(w, drill + 2 * ANNULAR), MAX_PAD), min(max(h, drill + 2 * ANNULAR), MAX_PAD)
    p = re.sub(r'\(drill [\d.]+\)', '(drill %.2f)' % drill, p, count=1)
    return re.sub(r'\(size [\d.]+ [\d.]+\)', '(size %.2f %.2f)' % (w, h), p, count=1)


# --------------------------------------------------------------------- router
class Router:
    """A* on a 0.635 mm lattice over a 2.54 mm grid.

    Parts sit on 2.54 because that is what a hand-etched board forgives.  Routing on the
    same lattice does not work: two 1.5 mm pads 2.54 mm apart leave 1.04 mm of gap, and
    0.7 mm clearance on both sides of a trace needs more than that, so every lane between
    neighbouring pads reads as blocked.  A quarter-pitch lattice lets a trace slip through
    the gap diagonally, which is what a real single-sided board does.  0.635 is also the
    step the PCB router is set to, so nothing lands off-grid.
    """

    CELL = 0.635

    def __init__(self):
        self.nx = int(round(BOARD_W / self.CELL)) + 1
        self.ny = int(round(BOARD_H / self.CELL)) + 1
        self.pads = []          # (x, y, halfw, halfh, net, name)
        self.segs = []          # (x1, y1, x2, y2, width, net)
        self.routed = set()     # the thin copper among them: traces, not rails

    def cell(self, x, y):
        return (int(round(x / self.CELL)), int(round(y / self.CELL)))

    def xy(self, i, j):
        return (i * self.CELL, j * self.CELL)

    def mark(self, block, x, y, hw, hh):
        """Block the cells whose centres fall inside the rectangle (x±hw, y±hh)."""
        a, b = x - hw, x + hw
        c, d = y - hh, y + hh
        i0 = int(math.ceil(a / self.CELL - 1e-9))
        i1 = int(math.floor(b / self.CELL + 1e-9))
        j0 = int(math.ceil(c / self.CELL - 1e-9))
        j1 = int(math.floor(d / self.CELL + 1e-9))
        for i in range(max(0, i0), min(self.nx, i1 + 1)):
            for j in range(max(0, j0), min(self.ny, j1 + 1)):
                block.add((i, j))

    def mark_seg(self, block, x1, y1, x2, y2, r):
        steps = int(max(abs(x2 - x1), abs(y2 - y1)) / self.CELL) + 1
        for k in range(steps + 1):
            t = k / max(steps, 1)
            self.mark(block, x1 + (x2 - x1) * t, y1 + (y2 - y1) * t, r, r)

    def blocked(self, net, width):
        """Cells a trace of `width` on `net` may not enter."""
        block = set()
        reach = width / 2.0 + CLEAR + SLACK
        for (x, y, hw, hh, pnet, _) in self.pads:
            if pnet == net:
                continue
            self.mark(block, x, y, hw + reach, hh + reach)
        # Traces and rails are held POUR_GAP apart, not CLEAR apart.  The ground pour keeps
        # CLEAR from foreign copper on both sides of a gap, so a gap narrower than
        # 2*CLEAR + min_thickness cannot fill: the pour stops short and the board splits
        # into islands that the DRC calls unconnected ground.  2.2 = 2*0.70 + 0.80.
        # Pads keep the plain clearance: the pour reaches a pad directly, so a trace may
        # hug one without walling anything.
        pour_reach = width / 2.0 + POUR_GAP
        for (x1, y1, x2, y2, w, snet) in self.segs:
            if snet == net:
                continue
            if (x1, y1, x2, y2) in self.routed:
                self.mark_seg(block, x1, y1, x2, y2, w / 2.0 + pour_reach)
            else:
                self.mark_seg(block, x1, y1, x2, y2, w / 2.0 + reach)
        for (x, y, r) in HOLES:
            self.mark(block, x, y, r + reach, r + reach)
        # copper of this width must stay EDGE_CLEAR from the outline
        lo = int(math.ceil((EDGE_CLEAR + width / 2.0) / self.CELL))
        for i in range(self.nx):
            for j in range(self.ny):
                if i < lo or j < lo or i > self.nx - 1 - lo or j > self.ny - 1 - lo:
                    block.add((i, j))
        return block

    def route(self, a, b, block, win=None):
        """Shortest legal path from a to b.  `win` is (i0, i1, j0, j1) in lattice cells:
        a fence the search may not leave.  Without a fence a net whose direct lanes are
        congested escapes to the board's perimeter and comes back the long way round —
        235 segments for a 28 mm net — and a trace that runs the perimeter walls the
        ground pour off.  A fence keeps every net in the patch of board its own pads sit
        in, which is also what makes the pour one piece."""
        ca, cb = self.cell(*a), self.cell(*b)
        if ca == cb:
            return []
        best = {ca: 0.0}
        parent = {}
        heap = [(0.0, ca, None)]
        dirs = [(1, 0), (-1, 0), (0, 1), (0, -1),
                (1, 1), (1, -1), (-1, 1), (-1, -1)]
        while heap:
            cost, cur, par = heapq.heappop(heap)
            if cur == cb:
                break
            if cost > best.get(cur, 1e18):
                continue
            for d in dirs:
                nxt = (cur[0] + d[0], cur[1] + d[1])
                if nxt in block or not (0 <= nxt[0] < self.nx and 0 <= nxt[1] < self.ny):
                    continue
                if win and not (win[0] <= nxt[0] <= win[1] and win[2] <= nxt[1] <= win[3]):
                    continue
                step = 1.4142 if d[0] and d[1] else 1.0
                if par is not None and (cur[0] - par[0], cur[1] - par[1]) != d:
                    step += 0.35                       # a bend costs a little
                # keep away from foreign copper rather than creeping along it
                if any((nxt[0] + dx, nxt[1] + dy) in block
                       for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1))):
                    step += 0.10
                ncost = cost + step
                if ncost < best.get(nxt, 1e18):
                    best[nxt] = ncost
                    parent[nxt] = cur
                    heapq.heappush(heap, (ncost, nxt, cur))
        if cb not in parent:
            return None
        path = [cb]
        while path[-1] in parent:
            path.append(parent[path[-1]])
        path.reverse()
        pts = [self.xy(*c) for c in path]
        out = [pts[0]]
        for k in range(1, len(pts) - 1):
            if (pts[k][0] - pts[k - 1][0]) != (pts[k + 1][0] - pts[k][0]) or \
               (pts[k][1] - pts[k - 1][1]) != (pts[k + 1][1] - pts[k][1]):
                out.append(pts[k])
        out.append(pts[-1])
        return list(zip(out, out[1:]))


def fence(r, a, b, margin):
    """The lattice cells inside `margin` mm of a leg's bounding box."""
    i0 = int(math.floor((min(a[0], b[0]) - margin) / r.CELL))
    i1 = int(math.ceil((max(a[0], b[0]) + margin) / r.CELL))
    j0 = int(math.floor((min(a[1], b[1]) - margin) / r.CELL))
    j1 = int(math.ceil((max(a[1], b[1]) + margin) / r.CELL))
    return (max(0, i0), min(r.nx - 1, i1), max(0, j0), min(r.ny - 1, j1))


def show_map(r, block, a, b, pad_of, net):
    """ASCII view of the blocked cells around a failed leg: '#' blocked, 'o' this net's
    pads, '*' endpoints, '.' free."""
    i0 = max(0, min(r.cell(*a)[0], r.cell(*b)[0]) - 8)
    i1 = min(r.nx - 1, max(r.cell(*a)[0], r.cell(*b)[0]) + 8)
    j0 = max(0, min(r.cell(*a)[1], r.cell(*b)[1]) - 8)
    j1 = min(r.ny - 1, max(r.cell(*a)[1], r.cell(*b)[1]) + 8)
    mine = {r.cell(*p) for p in pad_of.get(net, [])}
    ends = {r.cell(*a): '*', r.cell(*b): '*'}
    print('   blocked map for %s  x %.1f..%.1f  y %.1f..%.1f'
          % (net, i0 * GRID, i1 * GRID, j0 * GRID, j1 * GRID))
    print('      ' + ''.join(str((i // 10) % 10) for i in range(i0, i1 + 1)))
    for j in range(j0, j1 + 1):
        row = []
        for i in range(i0, i1 + 1):
            row.append(ends.get((i, j), 'o' if (i, j) in mine else ('#' if (i, j) in block else '.')))
        print('%4d %s' % (j, ''.join(row)))


def order_pads(pads):
    """A nearest-neighbour walk, so a net's route stays compact."""
    rest, cur, seq = list(pads[1:]), pads[0], [pads[0]]
    while rest:
        nxt = min(rest, key=lambda p: abs(p[0] - cur[0]) + abs(p[1] - cur[1]))
        rest.remove(nxt)
        seq.append(nxt)
        cur = nxt
    return seq


def main():
    src = open(SRC).read()
    tpl = templates(open(TPL).read())
    head = src[:src.index('\t(footprint "')].rstrip('\n')

    r = Router()
    parts_out, pad_of = [], {}
    for row in PARTS:
        ref, fp, x, y, rot, nets = row[:6]
        pad_at = row[6] if len(row) > 6 else []
        body = make_part(tpl[fp], ref, VALUES.get(ref), None, x, y, rot, nets, pad_at)
        parts_out.append(body)

        local, seen = [], []
        for m in PAD_RE.finditer(body):
            p = m.group(0)
            num = re.match(r'\t\t\(pad "([^"]*)"', p).group(1)
            if not num:
                continue                       # peg holes and mounting holes carry no net
            at = re.search(r'\(at (-?[\d.]+) (-?[\d.]+)(?: -?[\d.]+)?\)', p)
            size = re.search(r'\(size ([\d.]+) ([\d.]+)\)', p)
            drill = re.search(r'\(drill ([\d.]+)\)', p)
            d = float(drill.group(1)) if drill else 0.0
            w, h = float(size.group(1)), float(size.group(2))
            if d:
                d = min(max(d, MIN_DRILL), MAX_PAD - 2 * ANNULAR)
                w, h = min(max(w, d + 2 * ANNULAR), MAX_PAD), min(max(h, d + 2 * ANNULAR), MAX_PAD)
            if num not in seen:
                seen.append(num)
            local.append((num, float(at.group(1)), float(at.group(2)), w, h))   # board-local
        net_of = dict(zip(seen, nets))
        for k, (num, lx, ly, w, h) in enumerate(local):
            px, py = x + lx, y + ly          # the block is already rotated
            net = net_of.get(num, '')
            if rot in (90, 270):
                w, h = h, w
            r.pads.append((px, py, w / 2, h / 2, net, '%s.%d' % (ref, k + 1)))
            if net:
                pad_of.setdefault(net, []).append((px, py))

    for bar in BARS:
        net, a, b = bar[:3]
        w = bar[3] if len(bar) > 3 else BAR_W
        if net == 'U3+12V':
            net = '+12V'
        r.segs.append((a[0], a[1], b[0], b[1], w, net))
        if net not in ('+12V', 'FAN_SW', '19V', '+3V3'):      # a drawn signal bar is thin copper
            r.routed.add((a[0], a[1], b[0], b[1]))
            r.routed.add((b[0], b[1], a[0], a[1]))

    tracks = [(net if net != 'U3+12V' else '+12V', a, b, bar[3] if len(bar) > 3 else BAR_W)
              for bar in BARS for (net, a, b) in [bar[:3]]]
    drawn_ends = set()
    for bar in BARS:
        bnet, a, b = bar[:3]
        drawn_ends.add((bnet if bnet != 'U3+12V' else '+12V', (round(a[0], 3), round(a[1], 3))))
        drawn_ends.add((bnet if bnet != 'U3+12V' else '+12V', (round(b[0], 3), round(b[1], 3))))

    fails = []
    for net in ROUTE_ORDER:
        pads = [(round(x, 3), round(y, 3)) for (x, y) in pad_of.get(net, [])]
        width = 1.20 if net in ('+3V3', '+12V', 'FAN_SW') else TRACE
        seeded = [p for p in pads if (net, p) in drawn_ends]
        legs = []
        if seeded:
            # A drawn bar already carries the pads it lands on: bring each loose pad of
            # the net to the nearest carried one, rather than walking a pad-to-pad chain
            # that would draw the bar over again somewhere else.
            rest = [p for p in pads if p not in seeded]
            while rest:
                a, b = min(((s, q) for s in seeded for q in rest),
                           key=lambda sp: abs(sp[0][0] - sp[1][0]) + abs(sp[0][1] - sp[1][1]))
                rest.remove(b)
                seeded.append(b)
                legs.append((a, b))
        else:
            seq = order_pads(pads)
            legs = list(zip(seq, seq[1:]))
        for a, b in legs:
            block = r.blocked(net, width)
            for p in (a, b):
                block.discard(r.cell(*p))
            path = None
            for margin in (ROUTE_WIN, 3 * ROUTE_WIN, None):
                win = None if margin is None else fence(r, a, b, margin)
                path = r.route(a, b, block, win)
                if path is not None:
                    if margin is not None and margin != ROUTE_WIN:
                        print('  note: %s leg %s->%s needed a wider fence (%.0f mm)'
                              % (net, a, b, margin))
                    break
            if path is None:
                fails.append((net, a, b))
                if 'DEBUG' in __import__('os').environ:
                    show_map(r, block, a, b, pad_of, net)
                continue
            for (p, q) in path:
                tracks.append((net, p, q, width))
                r.segs.append((p[0], p[1], q[0], q[1], width, net))
                r.routed.add((p[0], p[1], q[0], q[1]))
                r.routed.add((q[0], q[1], p[0], p[1]))

    # ------------------------------------------------------------------- write
    out = [head]
    out.extend(parts_out)

    for (net, a, b, w) in tracks:
        out.append('\t(segment\n\t\t(start %.3f %.3f)\n\t\t(end %.3f %.3f)\n\t\t(width %.2f)\n'
                   '\t\t(layer "F.Cu")\n\t\t(net "%s")\n\t\t(uuid "%s")\n\t)'
                   % (a[0], a[1], b[0], b[1], w, net, U()))

    for (a, b) in [((0, 0), (BOARD_W, 0)), ((BOARD_W, 0), (BOARD_W, BOARD_H)),
                   ((BOARD_W, BOARD_H), (0, BOARD_H)), ((0, BOARD_H), (0, 0))]:
        out.append('\t(gr_line\n\t\t(start %.2f %.2f)\n\t\t(end %.2f %.2f)\n\t\t(stroke\n'
                   '\t\t\t(width 0.1)\n\t\t\t(type default)\n\t\t)\n\t\t(layer "Edge.Cuts")\n'
                   '\t\t(uuid "%s")\n\t)' % (a[0], a[1], b[0], b[1], U()))

    for (text, x, y) in LABELS:
        out.append('\t(gr_text "%s"\n\t\t(at %.2f %.2f 0)\n\t\t(layer "F.SilkS")\n\t\t(uuid "%s")\n'
                   '\t\t(effects\n\t\t\t(font\n\t\t\t\t(size 1.0 1.0)\n\t\t\t\t(thickness 0.2)\n'
                   '\t\t\t)\n\t\t\t(justify left bottom)\n\t\t)\n\t)' % (text, x, y, U()))

    # `connect_pads yes` is the whole point of the pour.  Written without the `yes`,
    # KiCad 10 reads the block as thermal-relief mode and the fill stops 0.70 mm short
    # of every GND pad: the board fills, looks grounded, and DRC says 20 GND pads are
    # unconnected.  `yes` is solid connection, which is also what a hand-etched board
    # wants - no thin thermal spokes to over-etch.
    out.append('\t(zone\n\t\t(net "GND")\n\t\t(layer "F.Cu")\n\t\t(uuid "%s")\n\t\t(hatch edge 0.5)\n'
               '\t\t(connect_pads yes\n\t\t\t(clearance %.2f)\n\t\t)\n\t\t(min_thickness 0.80)\n'
               '\t\t(fill yes\n\t\t\t(thermal_gap 0.50)\n\t\t\t(thermal_bridge_width 0.50)\n\t\t)\n'
               '\t\t(polygon\n\t\t\t(pts\n\t\t\t\t(xy 0 0) (xy %.2f 0) (xy %.2f %.2f) (xy 0 %.2f)\n'
               '\t\t\t)\n\t\t)\n\t)' % (U(), CLEAR, BOARD_W, BOARD_W, BOARD_H, BOARD_H))

    out.append('\n\t(embedded_fonts no)\n)')
    open(SRC, 'w').write('\n'.join(out) + '\n')

    print('wrote %s: %d footprints, %d copper segments, board %.2f x %.2f mm'
          % (SRC, len(parts_out), len(tracks), BOARD_W, BOARD_H))
    if fails:
        print('UNROUTABLE:')
        for (net, a, b) in fails:
            print('  %-10s (%.2f,%.2f) -> (%.2f,%.2f)' % (net, a[0], a[1], b[0], b[1]))
        return 1
    return 0


if __name__ == '__main__':
    sys.exit(main())
