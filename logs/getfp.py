#!/usr/bin/env python3
"""Pull whole footprint blocks out of the KiCad footprint libraries into logs/fp-templates.inc.

build1l.py clones these and, where a part has to sit on the board's 2.54 mm grid at a
pitch the library does not offer, moves its pads.  Cloning KiCad's own artwork — F.Fab
outline, courtyard, 3D model — is what keeps a hand-placed board honest about what a
part actually covers.

The footprint keeps its `Library:Footprint` name, which is what BUILD.md and the BOM call
it, so a missing part on the board shows up as a missing part in the list.

  python3 logs/getfp.py
"""
import re

LIB = "/Applications/KiCad/KiCad.app/Contents/SharedSupport/footprints"

NAMES = [
    "Package_TO_SOT_SMD:TO-252-3_TabPin2",
    "Package_TO_SOT_THT:TO-220-3_Vertical",
    "Package_TO_SOT_THT:TO-92_Inline_Wide",
    "Connector_PinHeader_2.54mm:PinHeader_1x02_P2.54mm_Vertical",
    "Connector_PinHeader_2.54mm:PinHeader_1x04_P2.54mm_Vertical",
    "Connector_PinHeader_2.54mm:PinHeader_1x05_P2.54mm_Vertical",
    "Connector:FanPinHeader_1x04_P2.54mm_Vertical",
    "TestPoint:TestPoint_Pad_D1.5mm",
    "MountingHole:MountingHole_3.2mm_M3",
    "Capacitor_THT:CP_Radial_D8.0mm_P3.50mm",
    "Capacitor_THT:CP_Radial_D6.3mm_P2.50mm",
    "Capacitor_THT:C_Disc_D6.0mm_W2.5mm_P5.00mm",
    "Capacitor_THT:C_Disc_D3.8mm_W2.6mm_P2.50mm",
    "Diode_THT:D_DO-41_SOD81_P10.16mm_Horizontal",
    "Resistor_THT:R_Axial_DIN0204_L3.6mm_D1.6mm_P5.08mm_Horizontal",
]


def block_at(text, i):
    """the whole s-expression block that starts at text[i] == '('" """
    depth, j = 0, i
    while j < len(text):
        c = text[j]
        if c == '(':
            depth += 1
        elif c == ')':
            depth -= 1
            if depth == 0:
                return text[i:j + 1]
        j += 1
    raise ValueError("unbalanced s-expression")


out = []
for name in NAMES:
    lib, fp = name.split(":")
    path = "%s/%s.pretty/%s.kicad_mod" % (LIB, lib, fp)
    try:
        text = open(path).read()
    except OSError:
        print("MISSING", name)
        continue
    block = block_at(text, text.find("(footprint"))
    block = re.sub(r'\(footprint "[^"]+"', '(footprint "%s"' % name, block, count=1)
    block = re.sub(r'\(uuid "[^"]*"\)', '', block)
    # a .kicad_mod is written at top level; build1l.py splices it inside a board, where
    # every line of a footprint sits one tab deeper
    lines = block.split('\n')
    block = '\t' + lines[0] + ''.join('\n\t' + l for l in lines[1:])
    out.append(block)

open("logs/fp-templates.inc", "w").write("\n\n".join(out) + "\n")
print("wrote logs/fp-templates.inc:", len(out), "templates")
