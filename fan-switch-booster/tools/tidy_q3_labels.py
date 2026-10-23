#!/usr/bin/env python3
"""Tidy the Q3 area after the SO-8 package symbol was dropped in.

The 8-pin package view has four drain legs and three source legs.  Labeling every
leg buries the symbol in text (KiCad draws a rotated net label *from* its anchor,
so four vertical /HIGATE labels ran straight through the box).  The legs are one
node inside the package anyway, so this joins them with wires and labels each
node once:

    source legs 1,2,3  -> wire along y=165.10,  labelled /P12V twice (as before)
    drain legs  5..8   -> wire along y=175.26,  labelled /HIGATE once

It also drops the "P-MOS" text from the symbol body (the value "irf7416" already
says what it is) and moves Q3's Reference and Value to the left of the box, where
nothing else is.

Run after tools/make_package_symbols.py, then tools/fix_schematic_junctions.py
--rebuild, then the ERC.
"""
import pathlib
import re
import uuid

ROOT = pathlib.Path(__file__).resolve().parents[1]
SCH = ROOT / "mosfet-fan-switch.kicad_sch"
LIB = ROOT / "mosfet-fan-switch.kicad_sym"


def block(text, start):
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


def drop_text_element(text, needle):
    """Delete every (text "...") graphic element named `needle`.

    KiCad writes a symbol twice in a library (unit variants `_0_1` and `_1_1`), so
    the body text appears more than once and every copy has to go.
    """
    while needle in text:
        s = text.index(needle)                 # the needle is the element itself
        assert text.startswith("(text ", s)
        s, e = block(text, s)
        text = text[:s].rstrip() + "\n" + text[e + 1:].lstrip()
    return text


def drop_label(text, net, x, y):
    m = re.search(r'\t\(label "%s"\n\t\t\(at %s %s [\d.]+\)\n(?:.*?\n)*?\t\)\n'
                  % (net, re.escape(str(x)), re.escape(str(y))), text)
    if not m:
        print(f"  label {net} at ({x}, {y}) is already gone")
        return text
    return text[:m.start()] + text[m.end():]


def add_wire(text, x1, y1, x2, y2):
    """Insert a wire just before the closing paren of the schematic."""
    wire = ('\n\t(wire\n\t\t(pts\n\t\t\t(xy %s %s) (xy %s %s)\n\t\t)\n'
            '\t\t(stroke\n\t\t\t(width 0)\n\t\t\t(type default)\n\t\t)\n'
            '\t\t(uuid "%s")\n\t)\n' % (x1, y1, x2, y2, uuid.uuid4()))
    i = text.rfind("\n)")
    if i < 0:
        raise SystemExit("schematic does not end with a closing paren")
    return text[:i] + wire + text[i:]


def main():
    # 1. the library symbol: no in-body text
    lib = LIB.read_text()
    if '(text "P-MOS"' in lib:
        LIB.write_text(drop_text_element(lib, '(text "P-MOS"'))
        print("library: dropped the P-MOS body text")

    t = SCH.read_text()

    # 2. the embedded copy of that symbol
    if '(text "P-MOS"' in t:
        t = drop_text_element(t, '(text "P-MOS"')

    # 3. labels that the leg-joining wires make redundant
    for net, x, y in [("P12V", 184.15, 165.1),
                      ("HIGATE", 184.15, 175.26),
                      ("HIGATE", 179.07, 175.26),
                      ("HIGATE", 176.53, 175.26)]:
        t = drop_label(t, net, x, y)

    # 4. join the legs: source row already runs 179.07 -> 181.61, extend it;
    #    drain row is new and passes through all four drain legs.
    t = t.rstrip("\n")
    t = add_wire(t, 181.61, 165.1, 184.15, 165.1)
    t = add_wire(t, 176.53, 175.26, 184.15, 175.26)

    # 5. Reference and Value to the left of the box
    i = t.index('(property "Reference" "Q3"')
    s, e = block(t, t.rfind("\t(symbol", 0, i))
    inst = t[s:e + 1]
    inst = inst.replace('(property "Reference" "Q3"\n\t\t\t(at 176.53 163.5 0)',
                        '(property "Reference" "Q3"\n\t\t\t(at 168.91 168.91 0)')
    m = re.search(r'\(property "Value" "irf7416"\n\t\t\t\(at [\d. ]+\)', inst)
    inst = inst[:m.start()] + '(property "Value" "irf7416"\n\t\t\t(at 168.91 171.45 0)' + inst[m.end():]
    t = t[:s] + inst + t[e + 1:]

    SCH.write_text(t)
    print("schematic: leg wires added, redundant labels dropped, Q3 text moved")


if __name__ == "__main__":
    main()
