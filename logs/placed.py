"""Read the placed instances out of the .kicad_sch and report their pin map.

Used to confirm that nothing the MCP placed drifted off the coordinates
layout.py drew the wires for.
"""
import re
import sys
sys.path.insert(0, ".")
from pins import place

SCH = "/Users/kaveh/Documents/Projects/nuc-tach-sim/nuc-fan-controller.kicad_sch"

def placed(path=SCH):
    """Every top-level symbol instance: ref, lib, x, y, angle, mirrorY, unit.

    Handles both the compact and the multi-line instance formats KiCad writes.
    """
    text = open(path, errors="ignore").read()
    out = []
    for m in re.finditer(r'\n\t\(symbol[ \n]', text):
        i = m.start()
        depth = 0
        end = i
        for j in range(i + text[i:].index("(symbol"), len(text)):
            if text[j] == "(":
                depth += 1
            elif text[j] == ")":
                depth -= 1
                if depth == 0:
                    end = j
                    break
        blk = text[i:end + 1]
        lib = re.search(r'\(lib_id "([^"]+)"', blk)
        at = re.search(r'\(at ([\d.\-]+) ([\d.\-]+) ([\d.\-]+)\)', blk)
        if not lib or not at:
            continue
        mirror = bool(re.search(r'\(mirror [yY]\)', blk))
        unit = re.search(r'\(unit (\d+)\)', blk)
        ref = re.search(r'\(property "Reference" "([^"]+)"', blk)
        out.append((ref.group(1) if ref else "?", lib.group(1), float(at.group(1)),
                    float(at.group(2)), float(at.group(3)), mirror,
                    int(unit.group(1)) if unit else 1))
    return out


def pinmap(path=SCH):
    P = {}
    for ref, lib, X, Y, A, mir, unit in placed(path):
        for num, nm, x, y in place(lib, X, Y, A, mirrorY=mir):
            P[(ref, num)] = (round(x, 4), round(y, 4))
    return P


if __name__ == "__main__":
    for ref, lib, X, Y, A, mir, unit in placed():
        print(f"{ref:8s} {lib:34s} ({X},{Y}) rot {A}{' mirrorY' if mir else ''}")
        for num, nm, x, y in place(lib, X, Y, A, mirrorY=mir):
            print(f"         pin {num} {nm:10s} ({round(x,4)},{round(y,4)})")
