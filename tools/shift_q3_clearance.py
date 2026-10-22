#!/usr/bin/env python3
"""Move Q3 east by 5.08 mm so the SO-8 box clears the /BOOT branch.

The old 4-pin SPICE glyph was about 6 mm wide, so the /BOOT wire running down at
x = 177.80 passed to its left.  The package view is 9.53 mm wide and reaches to
x = 175.90, which puts that wire *through* the symbol body.  Shifting the symbol
two grid steps east fixes it and keeps every existing tap:

    source legs land on 184.15 / 186.69 / 189.23  -> the /P12V drop moves to 184.15
    drain legs land on  181.61 / 184.15 / 186.69 / 189.23
                                                   -> the drop to R4 stays at 181.61
    gate leg lands on   193.04                     -> the /BOOT wire is extended

Run after tools/tidy_q3_labels.py, then tools/fix_schematic_junctions.py --rebuild,
then the ERC.
"""
import pathlib
import re
import uuid

ROOT = pathlib.Path(__file__).resolve().parents[1]
SCH = ROOT / "mosfet-fan-switch.kicad_sch"
D = 5.08                                    # two grid steps east

Y_SRC, Y_DRAIN = "165.1", "175.26000000000002"


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


def move_wire(text, x1, y1, x2, y2, new):
    """Rewrite one wire segment in place."""
    pat = (r'\t\(wire\n\t\t\(pts\n\t\t\t\(xy %s %s\) \(xy %s %s\)\n'
           % (re.escape(str(x1)), re.escape(str(y1)), re.escape(str(x2)), re.escape(str(y2))))
    m = re.search(pat, text)
    if not m:
        raise SystemExit(f"wire ({x1},{y1}) -> ({x2},{y2}) not found")
    s, e = block(text, m.start())
    wire = ('\t(wire\n\t\t(pts\n\t\t\t(xy %s %s) (xy %s %s)\n\t\t)\n'
            '\t\t(stroke\n\t\t\t(width 0)\n\t\t\t(type default)\n\t\t)\n\t\t(uuid "%s")\n\t)'
            % (new[0], new[1], new[2], new[3], uuid.uuid4()))
    return text[:s] + wire + text[e + 1:]        # e is the old ')': skip it


def add_wire(text, x1, y1, x2, y2):
    wire = ('\n\t(wire\n\t\t(pts\n\t\t\t(xy %s %s) (xy %s %s)\n\t\t)\n'
            '\t\t(stroke\n\t\t\t(width 0)\n\t\t\t(type default)\n\t\t)\n'
            '\t\t(uuid "%s")\n\t)\n' % (x1, y1, x2, y2, uuid.uuid4()))
    i = text.rfind("\n)")
    return text[:i] + wire + text[i:]


def drop_wire(text, x1, y1, x2, y2):
    m = re.search(r'\t\(wire\n\t\t\(pts\n\t\t\t\(xy %s %s\) \(xy %s %s\)\n'
                  % (re.escape(str(x1)), re.escape(str(y1)),
                     re.escape(str(x2)), re.escape(str(y2))), text)
    if not m:
        print(f"  wire ({x1},{y1}) -> ({x2},{y2}) is already gone")
        return text
    s, e = block(text, m.start())
    return text[:s] + text[e + 1:]


def move_label(text, net, x, y, new_xy, new_rot=None):
    m = re.search(r'\t\(label "%s"\n\t\t\(at %s %s ([\d.]+)\)' % (net, re.escape(str(x)), re.escape(str(y))),
                  text)
    if not m:
        raise SystemExit(f"label {net} at ({x}, {y}) not found")
    rot = new_rot if new_rot is not None else m.group(1)
    head = '\t(label "%s"\n\t\t(at %s %s %s)' % (net, new_xy[0], new_xy[1], rot)
    return text[:m.start()] + head + text[m.end():]


def drop_label(text, net, x, y):
    m = re.search(r'\t\(label "%s"\n\t\t\(at %s %s [\d.]+\)\n(?:.*?\n)*?\t\)\n'
                  % (net, re.escape(str(x)), re.escape(str(y))), text)
    if not m:
        print(f"  label {net} at ({x}, {y}) is already gone")
        return text
    return text[:m.start()] + text[m.end():]


def main():
    t = SCH.read_text()

    # 1. the symbol itself, and its Reference / Value
    i = t.index('(property "Reference" "Q3"')
    s, e = block(t, t.rfind("\t(symbol", 0, i))
    inst = t[s:e + 1]
    inst = inst.replace("(at 184.15 170.18 0)", "(at 189.23 170.18 0)")
    inst = inst.replace('(property "Reference" "Q3"\n\t\t\t(at 168.91 168.91 0)',
                        '(property "Reference" "Q3"\n\t\t\t(at 181.61 163.5 0)')
    inst = re.sub(r'\(property "Value" "irf7416"\n\t\t\t\(at [\d. ]+\)',
                  '(property "Value" "irf7416"\n\t\t\t(at 186.69 177.8 0)', inst)
    t = t[:s] + inst + t[e + 1:]

    # 2. source row: drop the old taps, lay the new ones, move the /P12V drop
    t = drop_wire(t, 179.07, Y_SRC, 181.61, Y_SRC)
    t = drop_wire(t, 181.61, Y_SRC, 184.15, Y_SRC)
    t = move_wire(t, 181.61, Y_SRC, 181.61, 111.76, (184.15, Y_SRC, 184.15, 111.76))
    t = add_wire(t, 184.15, Y_SRC, 186.69, Y_SRC)
    t = add_wire(t, 186.69, Y_SRC, 189.23, Y_SRC)

    # 3. drain row: clear the three old segments, then lay the new ones
    #    (dropping first avoids matching a segment that has just been rewritten)
    for a, b in [(176.53, 179.07), (179.07, 181.61), (181.61, 184.15)]:
        t = drop_wire(t, a, Y_DRAIN, b, Y_DRAIN)
    for a, b in [(181.61, 184.15), (184.15, 186.69), (186.69, 189.23)]:
        t = add_wire(t, a, Y_DRAIN, b, Y_DRAIN)

    # 4. gate: extend the /BOOT wire to the new leg
    t = move_wire(t, 195.58, 170.18, 187.96, 170.18, (195.58, 170.18, 193.04, 170.18))

    # 5. labels follow their pins.  The /P12V label rides a little higher up the
    #    drop wire so its glyphs do not crowd the pin-name/pin-number row.
    t = move_label(t, "P12V", 181.61, Y_SRC, (184.15, 162.56))
    t = drop_label(t, "P12V", 179.07, Y_SRC)
    t = move_label(t, "BOOT", 187.96, 170.18, (193.04, 170.18))

    # 6. a broken splice in this kind of surgery shows up as unbalanced parens
    if t.count("(") != t.count(")"):
        raise SystemExit("paren balance broken - refusing to write (restore the backup)")

    SCH.write_text(t)
    print("Q3 moved to (189.23, 170.18); source/drain legs tied, /BOOT and /P12V re-tapped")


if __name__ == "__main__":
    main()
