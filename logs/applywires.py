"""Splice logs/wires.inc into the schematic, replacing every top-level wire and
junction block.

genwires.py emits the whole wire set from layout.py; this puts it back into the
.sch so the schematic on disk is exactly what the generator produces.  Symbols,
labels, power symbols and text are left where they are.
"""
import re
import sys

SCH = "/Users/kaveh/Documents/Projects/nuc-tach-sim/nuc-fan-controller.kicad_sch"
INC = "wires.inc"


def _skip_string(text, i):
    """i points at a quote; return the index just past the closing quote."""
    i += 1
    while i < len(text):
        if text[i] == "\\":
            i += 2
            continue
        if text[i] == '"':
            return i + 1
        i += 1
    return i


def top_level_forms(text, names):
    """(start, end, name) for every balanced form at depth 1 whose head is in names."""
    out = []
    depth = 0
    i = 0
    n = len(text)
    while i < n:
        c = text[i]
        if c == '"':
            i = _skip_string(text, i)
            continue
        if c == "(":
            if depth == 1:
                m = re.match(r"\((%s)\b" % "|".join(names), text[i:i + 12])
                if m:
                    j, d = i, 0
                    while j < n:
                        ch = text[j]
                        if ch == '"':
                            j = _skip_string(text, j)
                            continue
                        if ch == "(":
                            d += 1
                        elif ch == ")":
                            d -= 1
                            if d == 0:
                                break
                        j += 1
                    out.append((i, j + 1, m.group(1)))
                    i = j + 1
                    continue
            depth += 1
        elif c == ")":
            depth -= 1
        i += 1
    return out


def main():
    src = open(SCH).read()
    forms = top_level_forms(src, ("wire", "junction"))
    wires = sum(1 for f in forms if f[2] == "wire")
    print("schematic had %d wire and %d junction blocks" % (wires, len(forms) - wires))

    # drop the whole line a block starts on, unless something else shares that line
    spans = []
    for s, e, _ in forms:
        line = src.rfind("\n", 0, s) + 1
        spans.append((line if src[line:s].strip() == "" else s, e))

    inc = open(INC).read().rstrip("\n")
    out = src[:spans[0][0]] + inc + "\n"
    prev = spans[0][1]
    for s, e in spans[1:]:
        out += src[prev:s]
        prev = e
    out += src[prev:]

    depth = 0
    i = 0
    n = len(out)
    while i < n:
        c = out[i]
        if c == '"':
            i = _skip_string(out, i)
            continue
        if c == "(":
            depth += 1
        elif c == ")":
            depth -= 1
        i += 1
    if depth != 0:
        sys.exit("refusing to write: paren balance is %d" % depth)

    open(SCH, "w").write(out)
    kept = top_level_forms(out, ("wire", "junction"))
    print("wrote %s: %d wire and %d junction blocks"
          % (SCH, sum(1 for f in kept if f[2] == "wire"), len(kept) - sum(1 for f in kept if f[2] == "wire")))


if __name__ == "__main__":
    main()
