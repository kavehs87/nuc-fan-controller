"""Pin geometry helper: reads KiCad 10 .kicad_sym pin coordinates and maps them to
schematic coordinates for an instance at (X, Y, angle).

Rule verified empirically against kicad-cli/MCP snap results:
    sch_offset = Rot(-angle) . (lx, -ly)
where (lx, ly) is the pin's connection point in the library symbol's own frame
(library +y is up, schematic +y is down) and Rot is the ordinary screen-space
rotation matrix.  mirrorY (KiCad "(mirror Y)") negates ly before the rotation.
"""
import math, re, os

SYM = "/Applications/KiCad/KiCad.app/Contents/SharedSupport/symbols"

def _top_symbol(text, name):
    m = re.search(r'^\t\(symbol "' + re.escape(name) + r'"', text, re.M)
    if not m:
        return None
    depth = 0
    for j in range(m.start(), len(text)):
        if text[j] == '(':
            depth += 1
        elif text[j] == ')':
            depth -= 1
            if depth == 0:
                return text[m.start():j + 1]
    return None

def pins_of(lib_id, unit=1, _seen=None):
    lib, name = lib_id.split(":")
    text = open(os.path.join(SYM, lib + ".kicad_sym"), errors="ignore").read()
    blk = _top_symbol(text, name)
    if blk is None:
        raise KeyError(lib_id)
    out = []
    ext = re.search(r'\(extends "([^"]+)"', blk)
    if ext and (lib, ext.group(1)) not in (_seen or set()):
        out += pins_of(lib + ":" + ext.group(1), unit, (_seen or set()) | {(lib, name)})
    # sub-units are named NAME_<electric>_<unit>; collect every pin in every sub-unit
    for m in re.finditer(r'\(pin\s+\w+\s+\w+', blk):
        seg = blk[m.start():m.start() + 700]
        at = re.search(r'\(at ([\d.\-]+) ([\d.\-]+) ([\d.\-]+)\)', seg)
        if not at:
            continue
        num = re.search(r'\(number "([^"]*)"', seg)
        nm = re.search(r'\(name "([^"]*)"', seg)
        out.append((num.group(1) if num else "?", nm.group(1) if nm else "",
                    float(at.group(1)), float(at.group(2))))
    return out

def place(lib_id, X, Y, angle=0, mirrorY=False, unit=1):
    a = math.radians(-angle)
    ca, sa = math.cos(a), math.sin(a)
    res = []
    for num, nm, lx, ly in pins_of(lib_id, unit):
        if mirrorY:      # KiCad left-right flip: the library x negates
            lx = -lx
        x = lx * ca - (-ly) * sa
        y = lx * sa + (-ly) * ca
        res.append((num, nm, round(X + x, 4), round(Y + y, 4)))
    return res

def _transform(lib_id, X, Y, angle, mirrorY):
    a = math.radians(-angle)
    ca, sa = math.cos(a), math.sin(a)
    def f(lx, ly):
        if mirrorY:
            lx = -lx
        return (X + lx * ca - (-ly) * sa, Y + lx * sa + (-ly) * ca)
    return f


def _body_pts(lib_id, _seen=None):
    lib, name = lib_id.split(":")
    text = open(os.path.join(SYM, lib + ".kicad_sym"), errors="ignore").read()
    blk = _top_symbol(text, name)
    if blk is None:
        raise KeyError(lib_id)
    pts = []
    ext = re.search(r'\(extends "([^"]+)"', blk)
    if ext and (lib, ext.group(1)) not in (_seen or set()):
        pts += _body_pts(lib + ":" + ext.group(1), (_seen or set()) | {(lib, name)})
    for m in re.finditer(r'\((?:polyline|rectangle|circle|arc)', blk):
        for p in re.finditer(r'\(xy ([\d.\-]+) ([\d.\-]+)\)', blk[m.start():m.start() + 400]):
            pts.append((float(p.group(1)), float(p.group(2))))
    return pts


def body_box(lib_id, X, Y, angle=0, mirrorY=False):
    """Bounding box (x1,y1,x2,y2) of a symbol instance's drawn body."""
    pts = _body_pts(lib_id)
    if not pts:
        return None
    f = _transform(lib_id, X, Y, angle, mirrorY)
    tp = [f(px, py) for px, py in pts]
    xs = [p[0] for p in tp]; ys = [p[1] for p in tp]
    return (round(min(xs), 3), round(min(ys), 3), round(max(xs), 3), round(max(ys), 3))


if __name__ == "__main__":
    import sys
    for lib_id, X, Y, ang in [
        ("Device:R", 60, 100, 0), ("Device:R", 80, 100, 90),
        ("Connector_Generic:Conn_01x04", 210, 100, 0),
        ("Connector_Generic:Conn_01x02", 250, 100, 90),
        ("Transistor_BJT:BC547", 200, 50, 0),
        ("Transistor_FET:IRF540N", 160, 50, 0),
        ("Regulator_Switching:LM2596T-ADJ", 60, 50, 0),
        ("Regulator_Linear:AMS1117-3.3", 110, 50, 0),
        ("Diode:1N5822", 240, 50, 90),
        ("Device:C", 110, 100, 0),
        ("Device:C_Polarized", 140, 100, 0),
        ("Device:L_Ferrite", 150, 150, 90),
        ("Device:R_Potentiometer_Trim", 170, 100, 90),
        ("Connector:TestPoint", 110, 150, 0),
    ]:
        print(lib_id, (X, Y, ang))
        for p in place(lib_id, X, Y, ang):
            print("   ", p)
