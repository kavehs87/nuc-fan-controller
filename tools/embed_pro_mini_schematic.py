#!/usr/bin/env python3
"""Replace the Nano stand-in on the sheet with the Pro Mini that is now on the board.

This is a one-shot migration, kept because it is the record of what happened to
the drawing:

  * the Arduino_Nano_v2.x symbol goes, together with the library copy KiCad had
    cached, and with the no-connects and net labels that hung off its pins;
  * J2 goes too - that header existed to carry four signals down to a Nano that
    was not on the board.  The module is on the board now;
  * U1 becomes mosfet-fan-switch:Arduino_Pro_Mini_328, the 35-hole hole map from
    pcb/pro_mini.py.  Pin number == footprint pad number == the hole's silkscreen
    name, and every hole the board does not use gets a no-connect;
  * J5 (the FTDI programming row), J6 (the 2x3 ICSP header), and D2/D3 (spare
    flyback diodes, unpopulated) are drawn in;
  * U1's programming-row GND pin is wired to the existing GND rail, which is also
    what keeps that rail's left-hand end from ending in mid-air.

Run it once, then refresh the junction dots and rebuild the board so the board's
footprint uuids follow the sheet's:

    python3 tools/embed_pro_mini_schematic.py
    python3 tools/fix_schematic_junctions.py --rebuild mosfet-fan-switch.kicad_sch
    python3 pcb/build_board.py && python3 tools/skeleton_board.py
"""
from __future__ import annotations

import math
import re
import sys
import uuid
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "pcb"))
from fix_schematic_junctions import _blocks, _lib_pins, _text  # noqa: E402
import pro_mini                                                # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
SCH = ROOT / "mosfet-fan-switch.kicad_sch"
TOL = 1e-4

# Where the new parts stand.  Every anchor is a multiple of 1.27 mm - KiCad's
# connection grid - so that the pins, which sit 2.54 and 5.08 mm from the anchor,
# land on the grid too and ERC has nothing to complain about.
U1_AT = (62.23, 158.75)
J5_AT = (27.94, 158.75)                 # 1x06, straight across U1's programming row
J6_AT = (27.94, 121.92)                 # 2x03 ICSP; pin 2 stays a dead pad
D2_AT = (228.6, 152.4)                  # parallel with D1, same 270-degree stance
D3_AT = (254.0, 175.26)

# The uuid the Nano instance already carried: reusing it is what lets the board's
# U1 keep its identity across the change.
U1_UUID = "7bec43cf-c164-4b3d-b4c6-040f301cac80"
SHEET_PATH = "/70af4f7e-8b7a-484f-96e0-6ca2b9e2231e"
KICAD_SYMBOLS = Path("/Applications/KiCad/KiCad.app/Contents/SharedSupport/symbols")

# pad number -> net label.  Everything else on the module is a no-connect, which
# is exactly what the board does: the spare holes are there to solder into, not to
# wire up.  Pad 29 is the exception - it gets a wire to the GND rail instead.
U1_NETS = {3: "RST", 4: "GND", 12: "PWM", 13: "P12V", 15: "RST", 16: "P3V3",
           20: "DEMAND", 21: "SCK", 22: "MISO", 23: "MOSI", 24: "TACH_PWM",
           25: "DTR", 26: "TX0", 27: "RX1", 28: "P3V3", 30: "BLK", 31: "GND"}
U1_WIRED = {29: (97.79, 210.82)}        # programming-row GND -> the sheet's GND rail

J5_NETS = {1: "DTR", 2: "TX0", 3: "RX1", 4: "P3V3", 5: "GND", 6: "BLK"}
J6_NETS = {1: "MISO", 3: "SCK", 4: "MOSI", 5: "RST", 6: "GND"}

BOARD = {"exclude_from_sim": "yes", "in_bom": "yes", "on_board": "yes",
         "in_pos_files": "yes", "dnp": "no"}
SPARE = dict(BOARD, dnp="yes")          # on the board, but nobody solders it


def key(p) -> tuple[float, float]:
    return (round(p[0], 2), round(p[1], 2))


def instances(lines) -> dict[str, tuple[int, int, str]]:
    """ref -> (start, end, text) for every symbol instance on the sheet."""
    out = {}
    for a, b in _blocks(lines, "symbol"):
        if re.match(r'^\t\(symbol "', lines[a]):
            continue
        t = _text(lines, a, b)
        out[re.search(r'\(property "Reference" "([^"]*)"', t).group(1)] = (a, b, t)
    return out


def instance_pins(body, libpins) -> list[tuple[float, float]]:
    """Sheet point of every pin of one instance (the junction tool's maths)."""
    lib = re.search(r'\(lib_id "([^"]+)"', body).group(1)
    X, Y, ang = (float(v) for v in
                 re.search(r'\(at ([-\d.]+) ([-\d.]+) ([-\d.]+)\)', body).groups())
    fx, fy = bool(re.search(r'\(mirror y\)', body)), bool(re.search(r'\(mirror x\)', body))
    pts = []
    for px, py in libpins[lib]:
        if fx:
            px, py = -px, py
        if fy:
            px, py = px, -py
        r = math.radians(ang)
        pts.append((round(X + px * math.cos(r) - py * math.sin(r), 4),
                    round(Y - px * math.sin(r) - py * math.cos(r), 4)))
    return pts


# ------------------------------------------------------------- new entities --
def block_symbol(lib_id, at, rot, ref, value, footprint, descr, pins, flags,
                 note=None, offs=((0, -2.54), (0, 2.54))):
    x, y = at
    out = ['\t(symbol',
           f'\t\t(lib_id "{lib_id}")',
           f'\t\t(at {x:g} {y:g} {rot})',
           '\t\t(unit 1)',
           '\t\t(body_style 1)']
    for k, v in flags.items():
        out.append(f'\t\t({k} {v})')
    out.append(f'\t\t(uuid "{uuid.uuid4()}")')
    for name, text, (dx, dy) in zip(("Reference", "Value"), (ref, value), offs):
        out.append(f'\t\t(property "{name}" "{text}"\n'
                   f'\t\t\t(at {x + dx:g} {y + dy:g} 0)\n'
                   '\t\t\t(show_name no)\n\t\t\t(do_not_autoplace no)\n'
                   '\t\t\t(effects\n\t\t\t\t(font\n\t\t\t\t\t(size 1.27 1.27)\n\t\t\t\t)\n'
                   '\t\t\t)\n\t\t)')
    for name, text in (("Footprint", footprint), ("Datasheet", ""),
                       ("Description", descr)):
        out.append(f'\t\t(property "{name}" "{text}"\n\t\t\t(at {x:g} {y:g} 0)\n'
                   '\t\t\t(hide yes)\n\t\t\t(show_name no)\n\t\t\t(do_not_autoplace no)\n'
                   '\t\t\t(effects\n\t\t\t\t(font\n\t\t\t\t\t(size 1.27 1.27)\n\t\t\t\t)\n'
                   '\t\t\t)\n\t\t)')
    if note:
        out.append(f'\t\t(property "Note" "{note}"\n\t\t\t(at {x:g} {y:g} 0)\n'
                   '\t\t\t(effects\n\t\t\t\t(font\n\t\t\t\t\t(size 1.27 1.27)\n\t\t\t\t)\n'
                   '\t\t\t\t(hide yes)\n\t\t\t)\n\t\t)')
    for p in pins:
        out.append(f'\t\t(pin "{p}"\n\t\t\t(uuid "{uuid.uuid4()}")\n\t\t)')
    out += ['\t\t(instances',
            '\t\t\t(project "mosfet-fan-switch"',
            f'\t\t\t\t(path "{SHEET_PATH}"',
            f'\t\t\t\t\t(reference "{ref}")',
            '\t\t\t\t\t(unit 1)',
            '\t\t\t\t)',
            '\t\t\t)',
            '\t\t)',
            '\t)']
    return '\n'.join(out)


# "side" says which way the text runs away from the pin: left, right, up, down.
def block_label(net, p, side):
    x, y = p
    ang, just = {"left": (180, "right bottom"), "right": (0, "left bottom"),
                 "up": (90, "left bottom"), "down": (270, "right bottom")}[side]
    return (f'\t(label "{net}"\n\t\t(at {x:g} {y:g} {ang})\n'
            '\t\t(effects\n\t\t\t(font\n\t\t\t\t(size 1.27 1.27)\n\t\t\t)\n'
            f'\t\t\t(justify {just})\n\t\t)\n\t\t(uuid "{uuid.uuid4()}")\n\t)')


def block_no_connect(p):
    return f'\t(no_connect\n\t\t(at {p[0]:g} {p[1]:g})\n\t\t(uuid "{uuid.uuid4()}")\n\t)'


def block_wire(pts):
    """One wire block per straight piece: a .kicad_sch wire is always two points."""
    out = []
    for (x1, y1), (x2, y2) in zip(pts, pts[1:]):
        out.append(f'\t(wire\n\t\t(pts\n\t\t\t(xy {x1:g} {y1:g}) (xy {x2:g} {y2:g})\n\t\t)\n'
                   '\t\t(stroke\n\t\t\t(width 0)\n\t\t\t(type default)\n\t\t)\n'
                   f'\t\t(uuid "{uuid.uuid4()}")\n\t)')
    return '\n'.join(out)


def lib_entry(lib_id: str) -> list[str]:
    """The library's own definition of `lib_id`, renamed the way KiCad caches it.

    A library file names its symbols plainly ("Conn_01x06"); a sheet caches them
    under the library prefix ("Connector_Generic:Conn_01x06").  kicad-cli resolves
    a symbol from that cache only, so a new part has to arrive with its cache
    entry, exactly as KiCad would have written it on save.
    """
    lib, name = lib_id.split(':')
    for path in (ROOT / "mosfet-fan-switch.kicad_sym",
                 KICAD_SYMBOLS / f"{lib}.kicad_sym"):
        txt = path.read_text()
        i = txt.find(f'(symbol "{name}"\n')
        if i < 0:
            continue
        depth, j, instr, esc = 0, i, False, False
        while j < len(txt):
            c = txt[j]
            if instr:
                if esc:
                    esc = False
                elif c == '\\':
                    esc = True
                elif c == '"':
                    instr = False
            elif c == '"':
                instr = True
            elif c == '(':
                depth += 1
            elif c == ')':
                depth -= 1
                if depth == 0:
                    break
            j += 1
        body = txt[i:j + 1].replace(f'(symbol "{name}"\n', f'(symbol "{lib_id}"\n', 1)
        return ['\t' + line for line in body.rstrip('\n').split('\n')]
    raise KeyError(lib_id)


def cached_ids(lines) -> set[str]:
    a, b = _blocks(lines, 'lib_symbols')[0]
    return {m.group(1) for i in range(a, b)
            if (m := re.match(r'^\t\t\(symbol "([^"]+)"', lines[i]))}


def main() -> int:
    lines = SCH.read_text().split('\n')
    libpins = _lib_pins(lines)
    inst = instances(lines)

    # ---- 1. everything that only existed to reach the old Nano or J2 ---------
    dead = {key(p) for ref in ("U1", "J2") for p in instance_pins(inst[ref][2], libpins)}
    print(f"{len(dead)} pin points become vacant (old U1 and J2)")

    edits: list[tuple[int, int, list[str] | None]] = [
        (inst['U1'][0], inst['U1'][1], None),
        (inst['J2'][0], inst['J2'][1], None)]

    for tag in ("label", "no_connect"):
        for a, b in _blocks(lines, tag):
            m = re.search(r'\(at ([-\d.]+) ([-\d.]+)', _text(lines, a, b))
            if key((float(m.group(1)), float(m.group(2)))) in dead:
                edits.append((a, b, None))

    # Wires that only existed to reach a vacant pin get trimmed from that end;
    # the GND rail itself is left alone, because U1 takes over its left end.
    for a, b in _blocks(lines, 'wire'):
        pts = [tuple(map(float, q)) for q in
               re.findall(r'\(xy ([-\d.]+) ([-\d.]+)\)', _text(lines, a, b))]
        n0 = len(pts)
        while len(pts) > 1 and (key(pts[0]) in dead or key(pts[1]) in dead):
            pts.pop(0)
        while len(pts) > 1 and (key(pts[-1]) in dead or key(pts[-2]) in dead):
            pts.pop()
        if len(pts) < 2:
            edits.append((a, b, None))
        elif len(pts) != n0:
            edits.append((a, b, block_wire(pts).split('\n')))

    top = _blocks(lines, 'lib_symbols')[0]
    starts = [i for i in range(top[0], top[1]) if re.match(r'^\t\t\(symbol "', lines[i])]
    for k, i in enumerate(starts):
        if re.match(r'^\t\t\(symbol "MCU_Module:Arduino_Nano_v2.x"', lines[i]):
            end = starts[k + 1] if k + 1 < len(starts) else top[1]
            edits.append((i, end, None))
            break

    # ...and the cached copies of everything the sheet is about to use.
    have = cached_ids(lines)
    wanted = [f"{pro_mini.LIB_NAME}:{pro_mini.SYMBOL}",
              "Connector_Generic:Conn_01x06", "Connector_Generic:Conn_02x03_Odd_Even",
              "Device:D", "Device:D_Dual_CommonCathode_AKA"]
    missing = [lid for lid in wanted if lid not in have]
    cache = [line for lid in missing for line in lib_entry(lid)]
    edits.append((top[1] - 1, top[1] - 1, cache))
    print(f"cached {', '.join(missing) if missing else 'nothing new'}")

    for a, b, rep in sorted(edits, key=lambda e: e[0], reverse=True):
        lines[a:b] = rep if rep is not None else []
    print(f"removed {sum(1 for e in edits if e[2] is None)} blocks and trimmed "
          f"{sum(1 for e in edits if e[2] is not None)} wire(s)")

    # ---- 2. the new parts ----------------------------------------------------
    new: list[str] = []

    # U1.  Left column = row A plus the GND/A6/A7/A4/A5 holes; right column =
    # row B plus the programming row.  A left-hand pin has its graphic drawn
    # rightwards, so its label runs off to the left of the pin.
    u1 = block_symbol(f"{pro_mini.LIB_NAME}:{pro_mini.SYMBOL}", U1_AT, 0, "U1",
                      "Arduino_Pro_Mini_3V3",
                      f"{pro_mini.LIB_NAME}:{pro_mini.FOOTPRINT}",
                      "Arduino Pro Mini ATmega328P (3.3 V, 8 MHz), clone hole map",
                      [str(n) for n, *_ in pro_mini.symbol_pins()], BOARD,
                      note=("the module sits on three female headers; measure its row "
                            "spacing first - 15.24 mm on the clone boards in the bins, "
                            "12.70 mm on a genuine SparkFun"),
                      offs=((0, 24.13), (0, -24.13)))
    u1 = re.sub(r'\t\t\(uuid "[0-9a-f-]{36}"\)', f'\t\t(uuid "{U1_UUID}")',
                u1, count=1)                      # keep the Nano's uuid
    new.append(u1)

    pin_at = {n: (U1_AT[0] + x, U1_AT[1] - y)
              for n, _name, x, y, _ang in pro_mini.symbol_pins()}
    for num, _name, _x, _y, ang in pro_mini.symbol_pins():
        p = pin_at[num]
        if num in U1_NETS:
            new.append(block_label(U1_NETS[num], p, "left" if ang == 0 else "right"))
        elif num in U1_WIRED:
            new.append(block_wire([p, (U1_WIRED[num][0], p[1]), U1_WIRED[num]]))
        else:
            new.append(block_no_connect(p))

    conn = "Connector_PinHeader_2.54mm:PinHeader"
    new.append(block_symbol("Connector_Generic:Conn_01x06", J5_AT, 0, "J5",
                            "FTDI HEADER", f"{conn}_1x06_P2.54mm_Vertical",
                            "Generic connector, single row, 01x06",
                            [str(i) for i in range(1, 7)], BOARD,
                            note=("mirrors U1's own programming row pin for pin; plug "
                                  "the 3.3 V FTDI or CH340 adapter with its black wire "
                                  "over the BLK end"),
                            offs=((0, 11.43), (0, -11.43))))
    j5 = {n: (J5_AT[0] - 5.08, J5_AT[1] - y) for n, y in
          zip(range(1, 7), (5.08, 2.54, 0.0, -2.54, -5.08, -7.62))}
    for n, net in J5_NETS.items():
        new.append(block_label(net, j5[n], "left"))

    new.append(block_symbol("Connector_Generic:Conn_02x03_Odd_Even", J6_AT, 0, "J6",
                            "ICSP", f"{conn}_2x03_P2.54mm_Vertical",
                            "Generic connector, double row, 02x03, odd/even numbering",
                            [str(i) for i in range(1, 7)], BOARD,
                            note=("program the 328 with another Arduino over five "
                                  "wires: pin 2 is the programmer's 5 V and must stay "
                                  "unconnected on a 3.3 V board"),
                            offs=((0, 5.08), (0, -5.08))))
    j6 = {n: (J6_AT[0] + x, J6_AT[1] - y) for n, (x, y) in
          zip(range(1, 7), ((-5.08, 2.54), (7.62, 2.54), (-5.08, 0.0),
                            (7.62, 0.0), (-5.08, -2.54), (7.62, -2.54)))}
    for n in range(1, 7):
        if n in J6_NETS:
            new.append(block_label(J6_NETS[n], j6[n], "left" if n % 2 else "right"))
        else:
            new.append(block_no_connect(j6[n]))

    new.append(block_symbol("Device:D", D2_AT, 270, "D2", "1n5822",
                            "Diode_THT:D_DO-27_P15.24mm_Horizontal",
                            "Diode, spare, unpopulated", ["1", "2"], SPARE,
                            note=("spare 3 A Schottky across D1; fit it only if this "
                                  "board drives more than about a dozen fans"),
                            offs=((-2.54, 0), (2.54, 0))))
    new.append(block_label("P12V", (D2_AT[0], D2_AT[1] - 3.81), "up"))
    new.append(block_label("DRAIN", (D2_AT[0], D2_AT[1] + 3.81), "down"))

    new.append(block_symbol("Device:D_Dual_CommonCathode_AKA", D3_AT, 0, "D3",
                            "mbr10100ct", "Package_TO_SOT_THT:TO-220-3_Vertical",
                            "Dual Schottky, common cathode, spare, unpopulated",
                            ["1", "2", "3"], SPARE,
                            note=("spare 10 A dual Schottky across D1: pins 1 and 3 are "
                                  "the anodes on /DRAIN, pin 2 the cathode on +12 V"),
                            offs=((0, -6.35), (0, -8.89))))
    new.append(block_label("DRAIN", (D3_AT[0] - 7.62, D3_AT[1]), "left"))
    new.append(block_label("DRAIN", (D3_AT[0] + 7.62, D3_AT[1]), "right"))
    new.append(block_label("P12V", (D3_AT[0], D3_AT[1] + 5.08), "down"))

    end = max(i for i, l in enumerate(lines) if l == ')')
    lines[end:end] = new
    text = '\n'.join(lines)
    assert text.count('(') == text.count(')'), "parenthesis balance lost"
    SCH.write_text(text)
    print(f"wrote {len(new)} new blocks into {SCH.name}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
