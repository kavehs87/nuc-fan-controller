"""Layout for nuc-fan-controller: placements, net wiring, and a geometry check.

Checks three things before the schematic is written:
  * cross-net wire crossings
  * wires passing through a symbol body
  * symbol bodies overlapping each other
"""
import sys
sys.path.insert(0, ".")
from pins import place, body_box

# ref, lib, footprint, value, X, Y, angle, mirrorY
COMPS = [
    # ---- block A: 19 V in, buck to 12 V -------------------------------------
    ("J1", "Connector_Generic:Conn_01x02", "Connector_PinHeader_2.54mm:PinHeader_1x02_P2.54mm_Vertical", "19V IN", 35.00, 44.45, 180, False),
    ("C1", "Device:C_Polarized", "Capacitor_THT:CP_Radial_D10.0mm_P5.00mm", "220uF 35V", 48.26, 48.26, 0, False),
    ("C2", "Device:C", "Capacitor_THT:C_Disc_D3.8mm_W2.6mm_P2.50mm", "100n", 55.88, 48.26, 0, False),
    ("U1", "Regulator_Switching:LM2596T-ADJ", "Package_TO_SOT_THT:TO-220-5_P3.4x3.7mm_StaggerOdd_Lead3.8mm_Vertical", "LM2596T", 75.00, 46.99, 0, False),
    ("D1", "Diode:1N5822", "Diode_THT:D_DO-201AD_P15.24mm_Horizontal", "1N5822", 91.44, 53.34, 270, False),
    ("L1", "Device:L_Ferrite", "Inductor_THT:L_Toroid_Horizontal_D16.8mm_P14.70mm_Vishay_TJ3", "100uH 6A", 100.33, 49.53, 90, False),
    ("C3", "Device:C_Polarized", "Capacitor_THT:CP_Radial_D10.0mm_P5.00mm", "470uF 25V", 114.30, 53.34, 0, False),
    ("C4", "Device:C", "Capacitor_THT:C_Disc_D3.8mm_W2.6mm_P2.50mm", "100n", 121.92, 53.34, 0, False),
    ("R1", "Device:R", "Resistor_THT:R_Axial_DIN0204_L3.6mm_D1.6mm_P5.08mm_Horizontal", "1k", 127.05, 48.26, 0, False),
    ("RV1", "Device:R_Potentiometer_Trim", "Potentiometer_THT:Potentiometer_Bourns_3296W_Vertical", "10k", 137.16, 44.45, 90, False),

    # ---- block B: 12 V to 5 V to 3.3 V --------------------------------------
    ("U2", "Regulator_Linear:AMS1117-5.0", "Package_TO_SOT_SMD:SOT-223-3_TabPin2", "AMS1117-5.0", 170.00, 44.45, 0, False),
    ("C5", "Device:C_Polarized", "Capacitor_THT:CP_Radial_D6.3mm_P2.50mm", "10uF", 185.10, 48.26, 0, False),
    ("C6", "Device:C", "Capacitor_THT:C_Disc_D3.8mm_W2.6mm_P2.50mm", "100n", 192.72, 48.26, 0, False),
    ("U3", "Regulator_Linear:AMS1117-3.3", "Package_TO_SOT_SMD:SOT-223-3_TabPin2", "AMS1117-3.3", 210.00, 44.45, 0, False),
    ("C7", "Device:C_Polarized", "Capacitor_THT:CP_Radial_D6.3mm_P2.50mm", "10uF", 225.04, 48.26, 0, False),
    ("C8", "Device:C", "Capacitor_THT:C_Disc_D3.8mm_W2.6mm_P2.50mm", "100n", 232.66, 48.26, 0, False),

    # ---- block C: NUC header, tach driver, PWM read -------------------------
    ("J2", "Connector_Generic:Conn_01x04", "Connector:FanPinHeader_1x04_P2.54mm_Vertical", "NUC fan header", 40.00, 104.14, 180, False),
    ("R3", "Device:R", "Resistor_THT:R_Axial_DIN0204_L3.6mm_D1.6mm_P5.08mm_Horizontal", "4.7k", 53.34, 87.63, 90, False),
    ("R4", "Device:R", "Resistor_THT:R_Axial_DIN0204_L3.6mm_D1.6mm_P5.08mm_Horizontal", "2.2k", 66.04, 87.63, 90, False),
    ("R5", "Device:R", "Resistor_THT:R_Axial_DIN0204_L3.6mm_D1.6mm_P5.08mm_Horizontal", "10k", 76.20, 91.44, 0, False),
    ("C10", "Device:C_Polarized", "Capacitor_THT:CP_Radial_D8.0mm_P3.50mm", "1uF", 88.90, 91.44, 0, False),
    ("C11", "Device:C", "Capacitor_THT:C_Disc_D3.8mm_W2.6mm_P2.50mm", "100n", 101.60, 91.44, 0, False),
    ("TP1", "Connector:TestPoint", "TestPoint:TestPoint_Pad_D1.5mm", "TACH", 60.96, 104.14, 0, False),
    ("C9", "Device:C", "Capacitor_THT:C_Disc_D3.0mm_W2.0mm_P2.50mm", "100p", 71.12, 107.95, 0, False),
    ("Q1", "Transistor_BJT:BC547", "Package_TO_SOT_THT:TO-92_Inline_Wide", "BC547B", 85.09, 109.22, 0, True),
    ("R2", "Device:R", "Resistor_THT:R_Axial_DIN0204_L3.6mm_D1.6mm_P5.08mm_Horizontal", "1k", 99.06, 109.22, 90, False),

    # ---- block D: fan speed drive -------------------------------------------
    ("R6", "Device:R", "Resistor_THT:R_Axial_DIN0204_L3.6mm_D1.6mm_P5.08mm_Horizontal", "1k", 45.72, 137.16, 90, False),
    ("R7", "Device:R", "Resistor_THT:R_Axial_DIN0204_L3.6mm_D1.6mm_P5.08mm_Horizontal", "10k", 53.34, 140.97, 0, False),
    ("Q2", "Transistor_BJT:BC547", "Package_TO_SOT_THT:TO-92_Inline_Wide", "BC547B", 66.04, 137.16, 0, False),
    ("R8", "Device:R", "Resistor_THT:R_Axial_DIN0204_L3.6mm_D1.6mm_P5.08mm_Horizontal", "1k", 81.28, 128.27, 0, False),
    ("R9", "Device:R", "Resistor_THT:R_Axial_DIN0204_L3.6mm_D1.6mm_P5.08mm_Horizontal", "120R", 91.44, 132.08, 90, False),
    ("R10", "Device:R", "Resistor_THT:R_Axial_DIN0204_L3.6mm_D1.6mm_P5.08mm_Horizontal", "10k", 104.14, 135.89, 0, False),
    ("Q3", "Transistor_FET:IRF540N", "Package_TO_SOT_THT:TO-220-3_Vertical", "IRFZ44N", 116.84, 132.08, 0, False),
    ("D2", "Diode:1N5819", "Diode_THT:D_DO-41_SOD81_P10.16mm_Horizontal", "1N5819", 124.46, 130.81, 90, False),
    ("J3", "Connector_Generic:Conn_01x02", "Connector_PinHeader_2.54mm:PinHeader_1x02_P2.54mm_Vertical", "FAN 1", 152.40, 124.46, 0, False),
    ("J4", "Connector_Generic:Conn_01x02", "Connector_PinHeader_2.54mm:PinHeader_1x02_P2.54mm_Vertical", "FAN 2", 170.18, 124.46, 0, False),
    ("C12", "Device:C", "Capacitor_THT:C_Disc_D3.8mm_W2.6mm_P2.50mm", "100n", 177.80, 130.81, 0, False),

    # ---- block E: Arduino header --------------------------------------------
    ("J5", "Connector_Generic:Conn_01x05", "Connector_PinHeader_2.54mm:PinHeader_1x05_P2.54mm_Vertical", "Pro Mini", 220.00, 97.79, 180, False),
]

# nets: ordered (ref, pin) joined by drawn wire; a bare (x, y) is an explicit point
NETS = {
    "19V":      [("J1", "1"), ("C1", "1"), ("C2", "1"), ("U1", "1")],
    # every net the schematic leaves to KiCad's auto-naming gets a name tag on a
    # short stub, so the board, the netlist and the print all use the same names.
    "19V_TAG":   [(48.26, 44.45), (48.26, 41.91)],
    "SW_TAG":    [("L1", "1"), (96.52, 52.07)],
    "FAN_SW_TAG": [(138.43, 127.0), (138.43, 124.46)],
    "5V_TAG":    [("C6", "1"), (193.04, 41.91)],
    "FB_TAG":    [(121.92, 44.45), (121.92, 41.91)],
    "BASE_TAG":  [("R6", "2"), (49.53, 139.70)],
    "FAN_GATE_TAG": [("R9", "1"), (87.63, 134.62)],
    "GATE_TAG":  [("R9", "2"), (95.25, 134.62)],
    "TACH_BASE_TAG": [("Q1", "2"), (90.17, 111.76)],
    "19V_FLAG": [("J1", "1"), (40.64, 46.99)],
    "SW":       [("U1", "2"), ("D1", "1"), ("L1", "1")],
    "12V":      [("L1", "2"), ("C3", "1"), ("C4", "1"), (132.08, 49.53), (132.08, 54.61)],
    "FB":       [("U1", "4"), (121.92, 44.45), ("R1", "1"), ("RV1", "1")],
    "WIPER":    [("RV1", "2"), (133.35, 40.64), ("RV1", "1")],
    "5V":       [("U2", "2"), ("C5", "1"), ("C6", "1"), ("U3", "3")],
    "3V3":      [("U3", "2"), ("C7", "1"), ("C8", "1"), (238.76, 44.45)],
    # R3 and R4 are in series and the node between them is the divider's midpoint:
    # 10 / (4.7 + 2.2 + 10) = 0.592, so a 5 V PWM swing lands 2.96 V on A0. Wiring
    # R3's far end straight onto NUC_PWM (which the first pass did) shorts it out and
    # leaves 10 / (2.2 + 10) = 0.82 -> 4.10 V, over the AVR's VCC + 0.5 V absolute max.
    "NUC_PWM":  [("J2", "3"), (48.26, 101.60), (48.26, 87.63), ("R3", "1")],
    "PWM_DIV":  [("R3", "2"), (59.69, 87.63), ("R4", "1")],
    "PWM_DIV_TAG": [(59.69, 87.63), (59.69, 90.17)],
    "PWM_IN":   [("R4", "2"), ("R5", "1"), ("C10", "1"), ("C11", "1"), (109.22, 87.63)],
    "NUC_TACH": [("J2", "2"), (53.34, 104.14), ("TP1", "1"), ("C9", "1"), ("Q1", "1")],
    "TACH_TAG": [(53.34, 104.14), (53.34, 106.68)],
    "TACH_BASE": [("Q1", "2"), ("R2", "1")],
    "BASE":     [("R6", "2"), ("R7", "1"), ("Q2", "2")],
    "FAN_GATE": [("Q2", "1"), ("R8", "2"), ("R9", "1")],
    "GATE":     [("R9", "2"), ("R10", "1"), ("Q3", "1")],
    "FAN_SW":   [("Q3", "2"), ("D2", "2"), (138.43, 127.0), ("J3", "2"), ("J4", "2"), ("C12", "1")],
    "D2_CATH":  [("D2", "1"), (129.54, 134.62), (134.62, 134.62)],
    "GND_FLAG": [(48.26, 52.07), (43.18, 52.07)],
}

# power symbols placed straight onto a pin or a wire end (no wire needed)
POWER = [
    ("power:GND",  [("J1", "2"), ("C1", "2"), ("C2", "2"), ("U1", "3"), ("U1", "5"), ("D1", "2"),
                    ("C3", "2"), ("C4", "2"), ("R1", "2"), ("U2", "1"), ("C5", "2"), ("C6", "2"),
                    ("U3", "1"), ("C7", "2"), ("C8", "2"), ("J2", "1"), ("C9", "2"), ("Q1", "3"),
                    ("R5", "2"), ("C10", "2"), ("C11", "2"), ("R7", "2"), ("Q2", "3"),
                    ("R10", "2"), ("Q3", "3"), ("C12", "2"), ("J5", "1")]),
    ("power:+12V", [("U2", "3"), ("R8", "1"), ("RV1", "3"), (132.08, 54.61), (129.54, 134.62),
                    ("J3", "1"), ("J4", "1")]),
    ("power:+3V3", [(238.76, 44.45), ("J5", "5")]),
    # flags only where nothing else drives the net: the LDO outputs are already
    # power outputs, so a flag on 5 V or 3 V3 is an ERC "two power drivers" error.
    ("power:PWR_FLAG", [(43.18, 52.07), (40.64, 46.99), (134.62, 134.62)]),
]

NOCONECT = [("J2", "4")]

# global labels: (name, (ref,pin) or (x,y), orientation)  0 = text to the right
LABELS = [
    ("NUC_TACH", (53.34, 106.68), 90),
    ("NUC_PWM", (48.26, 101.60), 0),
    ("PWM_IN", (109.22, 87.63), 0),
    ("TACH_OUT", ("R2", "2"), 0),
    ("TACH_OUT", ("J5", "2"), 0),
    ("FAN_PWM", ("R6", "1"), 180),
    ("FAN_PWM", ("J5", "3"), 0),
    ("PWM_IN", ("J5", "4"), 0),
    ("19V", (48.26, 41.91), 90),
    ("SW", (96.52, 52.07), 270),
    ("FAN_SW", (138.43, 124.46), 90),
    ("5V", (193.04, 41.91), 90),
    ("FB", (121.92, 41.91), 90),
    ("BASE", (49.53, 139.70), 270),
    ("FAN_GATE", (87.63, 134.62), 270),
    ("GATE", (95.25, 134.62), 270),
    ("TACH_BASE", (90.17, 111.76), 270),
    ("PWM_DIV", (59.69, 90.17), 270),
]


def pinmap():
    P = {}
    for ref, lib, fp, val, X, Y, a, mir in COMPS:
        for num, nm, x, y in place(lib, X, Y, a, mirrorY=mir):
            P[(ref, num)] = (x, y)
    return P


def net_points(name, P):
    out = []
    for it in NETS[name]:
        if isinstance(it[0], str):
            out.append(P[(it[0], str(it[1]))])
        elif it[0] is None:
            out.append(it[1])
        else:
            out.append(it)
    return out


def segs_from_points(pts):
    segs = []
    prev = None
    for cur in pts:
        if prev is not None and prev != cur:
            ax, ay = prev; bx, by = cur
            if abs(ax - bx) > 1e-6 and abs(ay - by) > 1e-6:
                segs.append(((ax, ay), (bx, ay)))
                segs.append(((bx, ay), (bx, by)))
            else:
                segs.append(((ax, ay), (bx, by)))
        prev = cur
    return segs


def main():
    P = pinmap()
    for ref, lib, fp, val, X, Y, a, mir in COMPS:
        print(f"{ref:4s} {lib:32s} ({X},{Y}) rot {a}{'' if not mir else ' mirY'}")
        for num, nm, x, y in place(lib, X, Y, a, mirrorY=mir):
            print(f"      pin {num} {nm:9s} ({x},{y})")

    allsegs = []
    print("\n--- nets ---")
    for name in NETS:
        segs = segs_from_points(net_points(name, P))
        print(f"{name:9s} " + "  ".join(f"({a[0]},{a[1]})-({b[0]},{b[1]})" for a, b in segs))
        allsegs += [(name, s) for s in segs]

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

    bad = []
    for i in range(len(allsegs)):
        for j in range(i + 1, len(allsegs)):
            n1, s1 = allsegs[i]; n2, s2 = allsegs[j]
            if n1 != n2 and cross(s1, s2):
                bad.append((n1, s1, n2, s2))
    print("\ncross-net crossings:", len(bad))
    for b in bad:
        print("   ", b)

    boxes = []
    for ref, lib, fp, val, X, Y, a, mir in COMPS:
        bb = body_box(lib, X, Y, a, mirrorY=mir)
        if bb:
            boxes.append((ref, bb))
    hits = []
    for ref, bb in boxes:
        for name, (p, q) in allsegs:
            x1, y1, x2, y2 = bb
            if abs(p[1] - q[1]) < 1e-6:
                y = p[1]
                if y1 + 1e-6 < y < y2 - 1e-6:
                    lo, hi = sorted([p[0], q[0]])
                    if lo < x2 - 1e-6 and hi > x1 + 1e-6:
                        hits.append((ref, bb, name, (p, q)))
            else:
                x = p[0]
                if x1 + 1e-6 < x < x2 - 1e-6:
                    lo, hi = sorted([p[1], q[1]])
                    if lo < y2 - 1e-6 and hi > y1 + 1e-6:
                        hits.append((ref, bb, name, (p, q)))
    print("wires through symbol bodies:", len(hits))
    for h in hits:
        print("   ", h)

    ov = []
    for i in range(len(boxes)):
        for j in range(i + 1, len(boxes)):
            (a1, (x1, y1, x2, y2)) = boxes[i]
            (b1, (x3, y3, x4, y4)) = boxes[j]
            if x1 < x4 - 1e-6 and x3 < x2 - 1e-6 and y1 < y4 - 1e-6 and y3 < y2 - 1e-6:
                ov.append((a1, b1, (x1, y1, x2, y2), (x3, y3, x4, y4)))
    print("body-body overlaps:", len(ov))
    for o in ov:
        print("   ", o)

    xs = [c[4] for c in COMPS] + [p[0] for _, s in allsegs for p in s]
    ys = [c[5] for c in COMPS] + [p[1] for _, s in allsegs for p in s]
    print(f"\nsheet extent: x {min(xs):.2f}..{max(xs):.2f}   y {min(ys):.2f}..{max(ys):.2f}")


if __name__ == "__main__":
    main()
