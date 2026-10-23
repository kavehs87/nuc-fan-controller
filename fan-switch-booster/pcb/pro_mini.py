#!/usr/bin/env python3
"""The Arduino Pro Mini's hole map, and the socket footprint built from it.

KiCad ships no Pro Mini footprint, and the two families of Pro Mini boards do
not share a header geometry, so every number that describes the module lives
here.  Measure your board before you solder anything into it.

clone  (Geeetech / Baite / HiLetgo "compatible board" - what the parts bins
       hold):  two rows of 12 holes with 15.24 mm between the rows, one 6-hole
       programming row one pitch past the end of those rows, GND/A6/A7 as three
       holes at the other end, and A4/A5 as two inner pads.  35 holes total on
       a 33.02 x 17.78 mm board.

genuine SparkFun:  two rows of 13 holes with 12.70 mm between the rows, and the
       six programming holes in the end column of those rows instead of a
       separate row.

If your board turns out to be the SparkFun layout, set ROW_SPACING = 12.70,
add the extra name to each of ROW_A and ROW_B and drop the three SPARE holes
that the SparkFun board does not have; then re-run

    python3 pcb/build_board.py && python3 tools/skeleton_board.py

Frame used below: KiCad footprint coordinates, X right, Y down, origin at the
corner where D9 and D10 sit (the end *away* from the programming row).  Pad 1
is at the opposite end, next to the programming row, and it is square so the
orientation of the whole module is unambiguous.

Silkscreen labels are written at local angle 270 (or 0 for the programming
row) because pcb/build_board.py places U1 at 90 degrees: that is what makes
them read horizontally on the finished board.
"""
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LIB_DIR = ROOT / "pcb" / "footprints" / "mosfet-fan-switch.pretty"
LIB_NAME = "mosfet-fan-switch"          # the project's own footprint/symbol library
FOOTPRINT = "Arduino_Pro_Mini_328_Socket"
SYMBOL_LIB = ROOT / "mosfet-fan-switch.kicad_sym"

PITCH = 2.54
ROW_SPACING = 15.24          # centre to centre between the two long rows
PADS_PER_ROW = 12

# Silkscreen names, read from the programming-row end outwards.
ROW_A = ["TX0", "RX1", "RST", "GND", "D2", "D3", "D4", "D5", "D6", "D7", "D8", "D9"]
ROW_B = ["RAW", "GND", "RST", "VCC", "A3", "A2", "A1", "A0", "D13", "D12", "D11", "D10"]
PROG = ["DTR", "TX0", "RX1", "VCC", "GND", "BLK"]

# Holes that are not in a row: GND/A6/A7 share the D9-D10 line, A4/A5 are inner
# pads.  (x, y) in the frame described above.
SPARE = [("GND", 7.62, 0.0), ("A6", 10.16, 0.0), ("A7", 12.70, 0.0),
         ("A4", 12.70, 16.51), ("A5", 12.70, 19.05)]

BODY = (-1.27, -1.27, 16.51, 31.75)     # the module's own outline, 33.02 x 17.78
COURT = (-1.77, -1.77, 17.01, 32.25)    # body + 0.5 mm, nothing may stand in here


def pads():
    """[(pad number, silkscreen name, x, y)] in the footprint's local frame."""
    out = []
    row_len = PADS_PER_ROW - 1
    for i, name in enumerate(ROW_A):
        out.append((i + 1, name, 0.0, (row_len - i) * PITCH))
    for i, name in enumerate(ROW_B):
        out.append((PADS_PER_ROW + i + 1, name, ROW_SPACING, (row_len - i) * PITCH))
    for i, name in enumerate(PROG):
        out.append((2 * PADS_PER_ROW + i + 1, name, 1.27 + i * PITCH,
                    row_len * PITCH + PITCH))
    for i, (name, x, y) in enumerate(SPARE):
        out.append((2 * PADS_PER_ROW + len(PROG) + i + 1, name, x, y))
    return out


def labels():
    """[(text, x, y, angle)] - pad names just outside the rows they belong to."""
    out = []
    for num, name, x, y in pads():
        if num <= PADS_PER_ROW:                      # row A: outboard of the row
            out.append((name, -2.4, y, 270))
        elif num <= 2 * PADS_PER_ROW:                # row B
            out.append((name, ROW_SPACING + 2.4, y, 270))
        elif num <= 2 * PADS_PER_ROW + len(PROG):    # programming row
            out.append((name, x, 32.6, 0))
        elif y == 0.0:                               # GND / A6 / A7 line
            out.append((name, x, -2.2, 270))
        # A4 and A5 sit under the module: labelled in docs/pcb-notes.md instead
    return out


def _line(x1, y1, x2, y2, layer, width=0.12):
    return (f'\t(fp_line (start {x1} {y1}) (end {x2} {y2})'
            f' (stroke (width {width}) (type solid)) (layer "{layer}")\n\t)')


def _rect(box, layer, width=0.12):
    x1, y1, x2, y2 = box
    return (_line(x1, y1, x2, y1, layer, width) + '\n'
            + _line(x2, y1, x2, y2, layer, width) + '\n'
            + _line(x2, y2, x1, y2, layer, width) + '\n'
            + _line(x1, y2, x1, y1, layer, width))


def _text(s, x, y, angle, size=0.6):
    return (f'\t(fp_text user "{s}" (at {x} {y} {angle}) (layer "F.SilkS")\n'
            f'\t\t(effects (font (size {size} {size}) (thickness 0.12)))\n\t)')


def footprint_text() -> str:
    lines = [f'(footprint "{FOOTPRINT}"',
             '\t(version 20260206)',
             '\t(generator "pcb/pro_mini.py")',
             '\t(layer "F.Cu")',
             f'\t(descr "Arduino Pro Mini 328 on 2x{PADS_PER_ROW} + 1x{len(PROG)} female '
             f'headers, {ROW_SPACING:.2f} mm between the rows, clone hole map")',
             '\t(tags "arduino pro mini module socket")',
             '\t(property "Reference" "REF**" (at 7.62 -3.4 270) (layer "F.SilkS")'
             '\t\t(effects (font (size 1 1) (thickness 0.15))))',
             '\t(property "Value" "Arduino_Pro_Mini_328" (at 7.62 33.4 270)'
             ' (layer "F.Fab") (hide yes)'
             '\t\t(effects (font (size 1 1) (thickness 0.15))))',
             '\t(attr through_hole)',
             _rect(COURT, "F.CrtYd", 0.05),
             _rect(BODY, "F.Fab"),
             _rect(BODY, "F.SilkS"),
             # pad 1 is square; the "1" beside it names the programming-row corner
             _text("1", -2.4, 30.48, 270, 0.8),
             ]
    for s, x, y, a in labels():
        lines.append(_text(s, x, y, a))
    for num, name, x, y in pads():
        shape = 'rect' if num == 1 else 'circle'
        lines.append(f'\t(pad "{num}" thru_hole {shape} (at {x} {y}) (size 1.7 1.7)'
                     ' (drill 1.0) (layers "*.Cu" "*.Mask")\n\t\t(remove_unused_layers no)\n\t)')
    lines.append(')')
    return '\n'.join(lines) + '\n'


def write_footprint() -> Path:
    LIB_DIR.mkdir(parents=True, exist_ok=True)
    path = LIB_DIR / f"{FOOTPRINT}.kicad_mod"
    path.write_text(footprint_text())
    return path


# --------------------------------------------------------------- schematic --
SYMBOL = "Arduino_Pro_Mini_328"
SYM_BOX = (-15.24, -22.86, 15.24, 22.86)      # symbol body, library Y up
PIN_LEN = 2.54


def symbol_pins():
    """[(pin number, name, x, y, angle)] in symbol coordinates (Y up).

    The symbol is the module's hole map, not an IC's pin model: every hole is a
    passive pin, and a pin number is a pad number in the socket footprint, which
    is what lets the schematic, the footprint and the board's silkscreen use one
    numbering.  Row A and the spare holes go down the left side, row B and the
    programming row down the right.
    """
    ps = pads()
    left = ([p for p in ps if p[0] <= PADS_PER_ROW]
            + [p for p in ps if p[0] > 2 * PADS_PER_ROW + len(PROG)])
    right = [p for p in ps if PADS_PER_ROW < p[0] <= 2 * PADS_PER_ROW + len(PROG)]
    out = []
    for group, x, ang in ((left, -17.78, 0), (right, 17.78, 180)):
        y = (len(group) - 1) * PITCH / 2
        for num, name, _, _ in group:
            out.append((num, name, x, y, ang))
            y -= PITCH
    return sorted(out)


def symbol_text() -> str:
    x1, y1, x2, y2 = SYM_BOX
    lines = [f'\t(symbol "{SYMBOL}"',
             '\t\t(exclude_from_sim yes)',
             '\t\t(in_bom yes)',
             '\t\t(on_board yes)',
             '\t\t(in_pos_files yes)',
             '\t\t(duplicate_pin_numbers_are_jumpers no)',
             '\t\t(property "Reference" "U" (at 0 24.13 0) (show_name no)'
             '\t\t\t(effects (font (size 1.27 1.27)) (justify left)))',
             f'\t\t(property "Value" "{SYMBOL}" (at 0 -24.13 0) (show_name no)'
             '\t\t\t(effects (font (size 1.27 1.27)) (justify left)))',
             '\t\t(property "Footprint" "' + LIB_NAME + f':{FOOTPRINT}" (at 0 0 0)'
             '\t\t\t(hide yes) (show_name no) (effects (font (size 1.27 1.27))))',
             '\t\t(property "Datasheet" "https://www.arduino.cc/en/uploads/Main/'
             'ArduinoProMiniSchematic.pdf" (at 0 0 0) (hide yes) (show_name no)'
             '\t\t\t(effects (font (size 1.27 1.27))))',
             '\t\t(property "Description" "Arduino Pro Mini ATmega328P (3.3 V, 8 MHz), '
             'clone hole map: every module hole as a passive pin" (at 0 0 0)'
             '\t\t\t(hide yes) (show_name no) (effects (font (size 1.27 1.27))))',
             '\t\t(property "ki_keywords" "arduino pro mini atmega328p module socket"'
             ' (at 0 0 0) (hide yes) (show_name no) (effects (font (size 1.27 1.27))))',
             f'\t\t(property "ki_fp_filters" "{FOOTPRINT}*" (at 0 0 0) (hide yes)'
             '\t\t\t(show_name no) (effects (font (size 1.27 1.27))))',
             f'\t\t(symbol "{SYMBOL}_0_1"',
             f'\t\t\t(rectangle (start {x1} {y1}) (end {x2} {y2})',
             '\t\t\t\t(stroke (width 0.254) (type default)) (fill (type none)))',
             '\t\t\t(polyline (pts (xy -15.24 -22.86) (xy -12.70 -22.86))',
             '\t\t\t\t(stroke (width 0.254) (type default)) (fill (type none)))',
             '\t\t)',
             f'\t\t(symbol "{SYMBOL}_1_1"']
    for num, name, x, y, ang in symbol_pins():
        lines.append(f'\t\t\t(pin passive line (at {x} {y:.2f} {ang}) (length {PIN_LEN})')
        lines.append(f'\t\t\t\t(name "{name}" (effects (font (size 1.0 1.0))))')
        lines.append(f'\t\t\t\t(number "{num}" (effects (font (size 1.0 1.0))))')
        lines.append('\t\t\t)')
    lines += ['\t\t)', '\t)']
    return '\n'.join(lines) + '\n'


def write_symbol(lib_path: Path) -> Path:
    """Put (or refresh) this symbol inside the project's symbol library."""
    txt = lib_path.read_text()
    head = f'\t(symbol "{SYMBOL}"\n'
    i = txt.find(head)
    if i >= 0:                                    # drop the previous copy
        depth, j = 0, i
        while j < len(txt):
            depth += txt.count('(', j, j + 1) - txt.count(')', j, j + 1)
            j += 1
            if depth <= 0:
                break
        txt = txt[:i] + txt[j:]
    end = txt.rstrip().rfind(')')                 # the library's own closing paren
    lib_path.write_text(txt[:end] + symbol_text() + txt[end:])
    return lib_path


if __name__ == '__main__':
    p = write_footprint()
    print(f"wrote {p}")
    print(f"wrote symbol {SYMBOL} into {write_symbol(SYMBOL_LIB).name}")
    print(f"{len(pads())} pads, courtyard {COURT[0]}..{COURT[2]} x {COURT[1]}..{COURT[3]}")
    for num, name, x, y in pads():
        print(f"  pad {num:>2}  {name:<4} local ({x:6.2f}, {y:6.2f})")
