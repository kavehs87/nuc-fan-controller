"""Schematic surgery for the 1-layer board revision: the 5 V stage is redundant.

U2 (AMS1117-5.0, and the cabinet's copy of it is SOT-89, not the SOT-223 the footprint
claimed), C5 and C6 only ever made 5 V in order to feed U3's input.  U3 takes +12 V
directly, so those three parts, their GND symbols, the +12 V symbol that fed U2, the 5 V
label, four wire segments and one junction all come out of the sheet.

Run from the repository root:  python3 logs/schsurgery.py            (prints the plan)
                               python3 logs/schsurgery.py --write    (rewrites the sheet)
"""
import re, sys, uuid

SCH = 'nuc-fan-controller.kicad_sch'

DROP_REFS = {'U2', 'C5', 'C6', '#PWR10', '#PWR11', '#PWR12'}
DROP_WIRES = [
    ((161.29, 44.45), (162.56, 44.45)),   # +12 V symbol into U2's input
    ((177.80, 44.45), (185.42, 44.45)),   # U2 out to C5
    ((185.42, 44.45), (193.04, 44.45)),   # C5 to C6
    ((193.04, 44.45), (201.93, 44.45)),   # C6 to U3 in  (replaced by one long wire)
    ((193.04, 44.45), (193.04, 41.91)),   # up to the 5 V label
]
ADD_WIRES = [((161.29, 44.45), (201.93, 44.45))]   # +12 V straight into U3's input
DROP_LABELS = [('5V', (193.04, 41.91))]
DROP_JUNCTIONS = [(193.04, 44.45)]


def blocks(src, head):
    """Yield (start, end) spans of every top-level block that starts with `head`."""
    for m in re.finditer(re.escape(head), src):
        i = src.index('(', m.start())      # the '(' that opens the block
        depth = 0
        while i < len(src):
            c = src[i]
            if c == '(':
                depth += 1
            elif c == ')':
                depth -= 1
                if depth == 0:
                    yield (m.start(), i + 1)
                    break
            i += 1


def prop(block, name):
    m = re.search(r'\(property "%s" "([^"]*)"' % name, block)
    return m.group(1) if m else ''


def at(block):
    m = re.search(r'\(at (-?[\d.]+) (-?[\d.]+)(?: (-?[\d.]+))?\)', block)
    return tuple(float(x) for x in m.groups()[:2]) if m else None


def main(write):
    src = open(SCH).read()
    spans = []

    for s, e in blocks(src, '\t(symbol\n'):
        b = src[s:e]
        if not re.search(r'\n\t\t\(lib_id ', b):
            continue                      # a library definition, not a placed instance
        ref = prop(b, 'Reference')
        if ref in DROP_REFS:
            spans.append((s, e, 'symbol ' + ref + ' (' + (re.search(r'\(lib_id "([^"]*)"', b) or re.match('','')).group(1) + ')'))

    for s, e in blocks(src, '\t(wire'):
        b = src[s:e]
        pts = [tuple(float(v) for v in m.groups())
               for m in re.finditer(r'\(xy (-?[\d.]+) (-?[\d.]+)\)', b)]
        for a, c in zip(pts, pts[1:]):
            if (a, c) in DROP_WIRES or (c, a) in DROP_WIRES:
                spans.append((s, e, 'wire %s -> %s' % (a, c)))
                break

    for s, e in blocks(src, '\t(global_label "'):
        b = src[s:e]
        text = re.match(r'\t\(global_label "([^"]*)"', b).group(1)
        pos = at(b)
        if (text, pos) in DROP_LABELS:
            spans.append((s, e, 'label ' + text))

    for s, e in blocks(src, '\t(junction'):
        b = src[s:e]
        if at(b) in DROP_JUNCTIONS:
            spans.append((s, e, 'junction %s' % (at(b),)))

    # KiCad 10 writes each instance's own (instances (project (path (reference)))) tail
    # inside the instance block, so dropping the block drops the override with it.

    spans.sort()
    for s, e, what in spans:
        print('drop  %-28s chars %d..%d' % (what, s, e))

    if not write:
        print('\nnothing written; re-run with --write')
        return

    out, last = [], 0
    for s, e, what in spans:
        if out and s < last:
            raise SystemExit('spans overlap at %s - refusing to write' % what)
        out.append(src[last:s])
        last = e
    out.append(src[last:])
    src = ''.join(out)
    if src.count('(') != src.count(')'):
        raise SystemExit('paren count unbalanced (%d/%d) - refusing to write'
                         % (src.count('('), src.count(')')))

    # the one wire the +12 V now needs, in the same shape KiCad writes
    add = '\n'.join('\n'.join(
        ['\t(wire',
         '\t\t(pts',
         '\t\t\t(xy %.2f %.2f) (xy %.2f %.2f)' % (a[0], a[1], c[0], c[1]),
         '\t\t)',
         '\t\t(stroke',
         '\t\t\t(width 0)',
         '\t\t\t(type default)',
         '\t\t)',
         '\t\t(uuid "%s")' % uuid.uuid4(),
         '\t)']) for a, c in ADD_WIRES)
    at_wire = src.index('\t(wire')
    src = src[:at_wire] + add + '\n' + src[at_wire:]

    open(SCH, 'w').write(src)
    print('\n%s rewritten: %d blocks dropped, %d wire added'
          % (SCH, len(spans), len(ADD_WIRES)))


if __name__ == '__main__':
    main('--write' in sys.argv)
