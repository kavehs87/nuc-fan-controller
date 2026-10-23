#!/usr/bin/env python3
"""Put back the junction dots that KiCad-side editing drops.

Why this exists
---------------
A junction dot in a .kicad_sch is not decoration: it is what tells KiCad that a
wire ending in the middle of another wire, or a component pin sitting on a wire,
is *joined* to it.  Without the dot ERC reports `unconnected_wire_endpoint` on
every stub, the two PWR_FLAG symbols look disconnected, and U1's GND pin reports
`power_pin_not_driven` - a dozen violations that all trace back to missing dots,
not to a wiring mistake.

Schematic edits made through the KiCad MCP server (add/delete component, add/
delete wire) silently remove some of them.  This script recomputes every point
where three or more of {wire ends, wires passing straight through, component
pins, net labels} meet, and appends the dots that are missing with fresh uuids.
It never moves or deletes a symbol, wire, or label.

Pin positions are recomputed from the schematic's own embedded library symbols:
a pin's connection point is its library `at` coordinate, mirrored if the
instance is mirrored, rotated by the instance angle, then added to the instance
origin - with the y axis flipped, because library symbols are drawn y-up and
sheets are stored y-down.  (Checked against Device:R, MCU_Module:Arduino_Nano,
Connector_Generic:Conn_01x04 and Transistor_BJT:BC547 instances in this project.)

    python3 tools/fix_schematic_junctions.py [file.kicad_sch]     # repair in place
    python3 tools/fix_schematic_junctions.py --check [file]       # report only
    python3 tools/fix_schematic_junctions.py --rebuild [file]     # throw all dots away,
                                                                  # redraw from the wiring
"""
from __future__ import annotations

import math
import re
import sys
import uuid
from pathlib import Path

TOL = 1e-4


def _blocks(lines: list[str], token: str) -> list[tuple[int, int]]:
    """Line ranges (start, end-exclusive) of top-level blocks named `token`."""
    out, i = [], 0
    while i < len(lines):
        if re.match(r"^\t\(%s\b" % re.escape(token), lines[i]):
            depth, j = 0, i
            while j < len(lines):
                depth += lines[j].count("(") - lines[j].count(")")
                j += 1
                if depth <= 0:
                    break
            out.append((i, j))
            i = j
        else:
            i += 1
    return out


def _text(lines: list[str], a: int, b: int) -> str:
    return "\n".join(lines[a:b])


def _segments(lines: list[str]) -> list[tuple[tuple[float, float], tuple[float, float]]]:
    segs = []
    for a, b in _blocks(lines, "wire"):
        pts = [tuple(map(float, p)) for p in
               re.findall(r"\(xy ([-\d.]+) ([-\d.]+)\)", _text(lines, a, b))]
        segs += list(zip(pts, pts[1:]))
    return segs


def _wire_arms(p, segs) -> int:
    n = 0
    for (x1, y1), (x2, y2) in segs:
        ends = [(ex, ey) for (ex, ey) in ((x1, y1), (x2, y2))
                if abs(p[0] - ex) < TOL and abs(p[1] - ey) < TOL]
        if ends:
            n += len(ends)
            continue
        straight = (abs(x1 - x2) < TOL and abs(p[0] - x1) < TOL) or \
                   (abs(y1 - y2) < TOL and abs(p[1] - y1) < TOL)
        inside = (min(x1, x2) - TOL <= p[0] <= max(x1, x2) + TOL and
                  min(y1, y2) - TOL <= p[1] <= max(y1, y2) + TOL)
        if straight and inside:
            n += 2
    return n


PIN_RE = re.compile(
    r'\(pin \w+ (?:line|short|invisible)\s*'
    r'\(at ([-\d.]+) ([-\d.]+) ([-\d.]+)\)\s*\(length ([-\d.]+)\)'
)


def _lib_pins(lines: list[str]) -> dict[str, list[tuple[float, float]]]:
    """symbol lib_id -> every pin connection offset drawn by that library symbol.

    The library definitions live inside the top-level (lib_symbols ...) block as
    (symbol "Library:Name" ... (symbol "Name_0_1" ... (pin ...) ...)), so pins are
    collected per top-level library entry, across all of its sub-symbols/units.
    """
    out: dict[str, list[tuple[float, float]]] = {}
    top = _blocks(lines, "lib_symbols")
    if not top:
        return out
    a0, b0 = top[0]
    starts = [i for i in range(a0, b0) if re.match(r'^\t\t\(symbol "', lines[i])]
    for k, i in enumerate(starts):
        head = re.match(r'^\t\t\(symbol "([^"]+)"', lines[i])
        end = starts[k + 1] if k + 1 < len(starts) else b0
        pins = [(float(m.group(1)), float(m.group(2)))
                for m in PIN_RE.finditer(_text(lines, i, end))]
        out.setdefault(head.group(1), []).extend(dict.fromkeys(pins))
    return out


def _pin_points(lines: list[str]) -> list[tuple[float, float]]:
    """Sheet-coordinate connection point of every pin of every instance."""
    libpins = _lib_pins(lines)
    pts: list[tuple[float, float]] = []
    for a, b in _blocks(lines, "symbol"):
        if re.match(r'^\t\(symbol "', lines[a]):
            continue
        body = _text(lines, a, b)
        libid = re.search(r'\(lib_id "([^"]+)"', body)
        at = re.search(r'\(at ([-\d.]+) ([-\d.]+) ([-\d.]+)\)', body)
        if not libid or not at or libid.group(1) not in libpins:
            continue
        X, Y, ang = float(at.group(1)), float(at.group(2)), float(at.group(3) or 0)
        # KiCad spells instance mirroring "(mirror x)" / "(mirror y)": the axis
        # named is the axis mirrored *about*, so "mirror y" swaps left and right
        # (that is how U1's D9 ends up on the right-hand pin column).
        flip_x = bool(re.search(r'\(mirror y\)', body, re.I))
        flip_y = bool(re.search(r'\(mirror x\)', body, re.I))
        for px, py in libpins[libid.group(1)]:
            if flip_x:
                px, py = -px, py
            if flip_y:
                px, py = px, -py
            r = math.radians(ang)
            rx = px * math.cos(r) - py * math.sin(r)
            ry = px * math.sin(r) + py * math.cos(r)
            pts.append((round(X + rx, 4), round(Y - ry, 4)))   # library y-up, sheet y-down
    return pts


def _label_points(lines: list[str]) -> list[tuple[float, float]]:
    pts = []
    for a, b in _blocks(lines, "label") + _blocks(lines, "hierarchical_label"):
        m = re.search(r'\(at ([-\d.]+) ([-\d.]+)', _text(lines, a, b))
        pts.append((float(m.group(1)), float(m.group(2))))
    return pts


def _key(p) -> tuple[float, float]:
    return (round(p[0], 2), round(p[1], 2))


def needed_junctions(lines: list[str]) -> list[tuple[float, float]]:
    """Points where three or more *conductors* actually meet.

    Wire ends and wires running straight through count, and so does a component
    pin sitting on a wire (that is how the two PWR_FLAG symbols join the rails).
    Net labels do not count: a label hanging off a wire end is not a third
    conductor, and KiCad draws no dot there.
    """
    segs = _segments(lines)
    pins = [_key(p) for p in _pin_points(lines)]
    candidates = {p for seg in segs for p in seg} | set(pins)
    out = []
    for p in candidates:
        wires = _wire_arms(p, segs)
        arms = wires + sum(1 for q in pins if q == p)
        if wires >= 2 and arms >= 3:
            out.append(p)
    return sorted(out)


def present_junctions(lines: list[str]) -> set[tuple[float, float]]:
    out = set()
    for a, b in _blocks(lines, "junction"):
        m = re.search(r"\(at ([-\d.]+) ([-\d.]+)\)", _text(lines, a, b))
        out.add((float(m.group(1)), float(m.group(2))))
    return out


def block_for(p: tuple[float, float]) -> str:
    x, y = ("%g" % p[0], "%g" % p[1])
    return ("\t(junction\n\t\t(at %s %s)\n\t\t(diameter 0)\n\t\t(color 0 0 0 0)\n"
            "\t\t(uuid \"%s\")\n\t)" % (x, y, uuid.uuid4()))


def main() -> int:
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    check = "--check" in sys.argv[1:]
    rebuild = "--rebuild" in sys.argv[1:]
    path = Path(args[0]) if args else Path("mosfet-fan-switch.kicad_sch")
    lines = path.read_text().split("\n")

    if rebuild:
        for a, b in reversed(_blocks(lines, "junction")):
            del lines[a:b]
        path.write_text("\n".join(lines))
        print(f"{path.name}: every junction dot thrown away, recomputing from the wiring")

    need = needed_junctions(lines)
    have = present_junctions(lines)
    missing = [p for p in need if p not in have]
    extra = [p for p in sorted(have) if p not in {(round(q[0], 2), round(q[1], 2)) for q in need}]
    print(f"{path.name}: {len(need)} junction points needed, {len(have)} dots present, "
          f"{len(missing)} missing")
    for p in missing:
        print("   missing:", p)
    for p in extra:
        print("   dot with nothing to join:", p)
    if missing and not check:
        anchors = _blocks(lines, "junction") or _blocks(lines, "no_connect")
        at = anchors[-1][1] if anchors else next(i for i, l in enumerate(lines)
                                                 if re.match(r"^\t\(symbol\b", l))
        lines[at:at] = [block_for(p) for p in missing]
        path.write_text("\n".join(lines))
        print(f"   wrote {len(missing)} junction dot(s) into {path.name}")
        return 0
    return 0 if not missing else 1


if __name__ == "__main__":
    raise SystemExit(main())
