#!/usr/bin/env python3
"""Strip the generated routing out of the board, leaving a routing skeleton.

The footprints, their positions, the board outline, the mounting holes and every
pad's net stay exactly as they are; only the copper track segments are deleted.
What is left is a placement with a ratsnest - the thing you actually want when
you intend to route the board by hand.

The generated routing is not lost: it is in git (commit a669df3), and
pcb/build_board.py can regenerate it.

    python3 tools/skeleton_board.py            # rewrite mosfet-fan-switch.kicad_pcb
    python3 tools/skeleton_board.py --check    # report only, change nothing

Why the routing went: the generated board carries 8 DRC violations and 2
unconnected pads - the /PWM jumper JP1 was placed but never wired and sat on top
of the GND band, the top-right mounting hole sat on the GND band, and the /TBASE
track came too close to that band.  Those are listed with coordinates in
docs/pcb-notes.md.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BOARD = ROOT / "mosfet-fan-switch.kicad_pcb"


def block(text: str, start: int) -> tuple[int, int]:
    """Index range of the parenthesised element that starts at `start`."""
    depth = 0
    j = start
    while True:
        if text[j] == "(":
            depth += 1
        elif text[j] == ")":
            depth -= 1
            if depth == 0:
                return start, j
        j += 1


def main() -> None:
    text = BOARD.read_text()
    out: list[str] = []
    i = 0
    removed = 0
    kept = 0
    while True:
        m = re.compile(r"\t\(segment").search(text, i)
        if not m:
            out.append(text[i:])
            break
        s, e = block(text, m.start())
        seg = text[s:e + 1]
        if re.search(r'\(layer "(F|B)\.Cu"\)', seg):
            removed += 1
            out.append(text[i:m.start()])          # keep the lead-in, drop the segment
        else:
            kept += 1
            out.append(text[i:e + 1])              # Edge.Cuts and friends stay
        i = e + 1

    new = "".join(out)
    if new.count("(") != new.count(")"):
        raise SystemExit("paren balance broken - nothing written")

    print(f"track segments on copper removed: {removed}")
    print(f"segments on other layers kept:    {kept}")
    print(f"footprints still on the board:    {new.count('(footprint ')}")
    print(f"pad net assignments untouched:    {len(re.findall(r'\(net \d+ \"', new))}")
    if "--check" in sys.argv:
        print("--check: nothing written")
        return
    BOARD.write_text(new)
    print(f"wrote {BOARD.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
