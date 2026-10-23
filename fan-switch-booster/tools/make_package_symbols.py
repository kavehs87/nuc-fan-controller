#!/usr/bin/env python3
"""Swap the fan driver's four transistors to package-accurate symbols.

KiCad connects symbol pin N to footprint pad N.  The library symbols this sheet
used number their pins in SPICE order (D-G-S-B, C-B-E), which is not how the
real packages are wired, so an automatic "update PCB from schematic" would land
nets on the wrong legs.  `mosfet-fan-switch.kicad_sym` numbers the pins the way
the packages are; the ngspice terminal order moves into a sub-circuit wrapper in
each model file, because KiCad 10 emits device cards in symbol pin order and
ignores `Sim.Pins` for `.model` cards.

Run once.  It edits mosfet-fan-switch.kicad_sch in place:

  * replaces the four embedded library symbols with the project ones
  * re-points the instances (lib_id, Sim.Name), drops their Sim.Type
  * turns Q3 from a 4-pin SPICE PMOS into the 8-pin SO-8 package view
  * drops Q1's bulk pin, its wire stub and its label
  * labels Q3's four extra drain pins and its second source pin

Afterwards: tools/fix_schematic_junctions.py --rebuild, then the ERC.
"""
import pathlib
import re
import uuid

ROOT = pathlib.Path(__file__).resolve().parents[1]
SCH = ROOT / "mosfet-fan-switch.kicad_sch"
LIB = ROOT / "mosfet-fan-switch.kicad_sym"

# old embedded symbol -> new project symbol (and the sub-circuit that carries
# the ngspice terminal order)
SWAP = {
    "Simulation_SPICE:NMOS_Substrate": ("Q_NMOS_TO220", "mos_irfz44n"),
    "Simulation_SPICE:NMOS":           ("Q_NMOS_SOT23", "mos_2n7002"),
    "Simulation_SPICE:PMOS_Substrate": ("Q_PMOS_SO8",   "mos_irf7416"),
    "Transistor_BJT:BC547":            ("Q_NPN_TO92",   "npn_bc547"),
}
REFS = {"Q_NMOS_TO220": "Q1", "Q_NMOS_SOT23": "Q2", "Q_PMOS_SO8": "Q3", "Q_NPN_TO92": "Q4"}


def block(text, start):
    """Return (start, end) of the balanced s-expression starting at `start`."""
    d = 0
    j = start
    while True:
        if text[j] == "(":
            d += 1
        elif text[j] == ")":
            d -= 1
            if d == 0:
                return start, j
        j += 1


def top_level_blocks(text, header_re):
    """Find balanced blocks whose opening line matches header_re."""
    out = []
    for m in re.finditer(header_re, text):
        out.append(block(text, m.start()))
    return out


def new_symbol_text(name):
    """Pull one symbol out of the project library and rename it as KiCad embeds it."""
    lib = LIB.read_text()
    i = lib.index('\t(symbol "%s"' % name)
    s, e = block(lib, i)
    return lib[s:e + 1].replace('(symbol "%s"' % name,
                                 '(symbol "mosfet-fan-switch:%s"' % name, 1)


def label(net, x, y, rot, justify="left bottom"):
    return ('\t(label "%s"\n\t\t(at %s %s %s)\n\t\t(effects\n\t\t\t(font\n'
            '\t\t\t\t(size 1.27 1.27)\n\t\t\t)\n\t\t\t(justify %s)\n\t\t)\n'
            '\t\t(uuid "%s")\n\t)\n' % (net, x, y, rot, justify, str(uuid.uuid4())))


def main():
    t = SCH.read_text()

    # ---- 1. swap the embedded library symbol definitions -------------------
    for old, (new, _sub) in SWAP.items():
        i = t.index('\t\t(symbol "%s"' % old)
        s, e = block(t, i)
        t = t[:s] + new_symbol_text(new).replace('\t(symbol', '\t\t(symbol', 1) + t[e + 1:]

    # ---- 2. re-point the instances ----------------------------------------
    for new, ref in REFS.items():
        i = t.index('(property "Reference" "%s"' % ref)
        s, e = block(t, t.rfind("\t(symbol", 0, i))
        inst = t[s:e + 1]
        inst = inst.replace('(lib_id "%s")' % next(o for o, (n, _) in SWAP.items() if n == new),
                            '(lib_id "mosfet-fan-switch:%s")' % new)
        inst = inst.replace('(property "Sim.Name" "%s"' % new.replace("mos_", ""),
                            '(property "Sim.Name" "%s"' % SWAP[next(o for o, (n, _) in SWAP.items() if n == new)][1])
        # drop the Sim.Type property block: it is what made KiCad emit an M/Q card
        m = re.search(r'\t\t\(property "Sim\.Type" "[^"]*"\n(?:.*?\n)*?\t\t\)\n', inst)
        inst = inst[:m.start()] + inst[m.start():].replace(m.group(0), "", 1)
        t = t[:s] + inst + t[e + 1:]

    # Q4's Sim.Name was already bc547, so patch it by value instead of by symbol name
    i = t.index('(property "Reference" "Q4"')
    s, e = block(t, t.rfind("\t(symbol", 0, i))
    inst = t[s:e + 1].replace('(property "Sim.Name" "bc547"', '(property "Sim.Name" "npn_bc547"')
    t = t[:s] + inst + t[e + 1:]

    # ---- 3. Q3: 4-pin rotated glyph -> 8-pin package view, rotation 0 ------
    i = t.index('(property "Reference" "Q3"')
    s, e = block(t, t.rfind("\t(symbol", 0, i))
    inst = t[s:e + 1]
    inst = inst.replace("(at 184.15 170.18 180)", "(at 184.15 170.18 0)")
    inst = inst.replace("(property \"Reference\" \"Q3\"\n\t\t\t(at 177.8 168.91 0)",
                        "(property \"Reference\" \"Q3\"\n\t\t\t(at 176.53 163.5 0)")
    last_pin = inst.rindex('(pin "4"')
    p4_end = inst.index("\n\t\t)", last_pin) + len("\n\t\t)")
    extra = "".join('\n\t\t(pin "%d"\n\t\t\t(uuid "%s")\n\t\t)' % (n, str(uuid.uuid4()))
                    for n in (5, 6, 7, 8))
    inst = inst[:p4_end] + extra + inst[p4_end:]
    t = t[:s] + inst + t[e + 1:]

    # ---- 4. Q1 loses its bulk pin: delete the stub wire and its label -----
    wire = ('\t(wire\n\t\t(pts\n\t\t\t(xy 227.32999999999998 195.58) '
            '(xy 229.87 195.58)\n\t\t)')
    i = t.index(wire)
    s, e = block(t, i)
    t = t[:s] + t[e + 1:]
    m = re.search(r'\t\(label "GND"\n\t\t\(at 229\.87 195\.58 [\d.]+\)\n(?:.*?\n)*?\t\)\n', t)
    t = t[:m.start()] + t[m.end():]

    # ---- 5. labels for Q3's extra package pins -----------------------------
    tail = t.rindex("\t(sheet") if "\t(sheet" in t else len(t) - 1
    add = (label("P12V", 184.15, 165.1, 90)
           + label("HIGATE", 184.15, 175.26, 270)
           + label("HIGATE", 179.07, 175.26, 270)
           + label("HIGATE", 176.53, 175.26, 270))
    t = t[:tail] + add + t[tail:]

    SCH.write_text(t)
    print("symbols now on the sheet:")
    for m in re.finditer(r'\t\t\(symbol "(mosfet-fan-switch:[^"]+)"', t):
        print("   ", m.group(1))
    print("instances:")
    for ref in ("Q1", "Q2", "Q3", "Q4"):
        i = t.index('(property "Reference" "%s"' % ref)
        blk = t[t.rfind("\t(symbol", 0, i):i + 3000]
        print("   ", ref, re.search(r'\(lib_id "([^"]+)"', blk).group(1),
              re.search(r'\(at [\d.-]+ [\d.-]+ ([\d.-]+)\)', blk).group(1), "deg",
              re.findall(r'\(property "Sim\.[A-Za-z]+" "([^"]*)"', blk)[:2])


if __name__ == "__main__":
    main()
