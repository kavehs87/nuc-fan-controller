#!/usr/bin/env python3
"""Board side of the BC547 pin-order fix, plus the two things the schematic had
already grown (J7 = FAN 1, C12 on FAN_SW) that this session's Update-from-
schematic dropped on the board.

1. Q1/Q2 pad nets swapped by the symbol change (pad 1 = emitter = GND, pad 3 =
   collector), so the copper that used to hang off those pads goes away and the
   collector nets are re-routed to the new pads.
2. The MCP's update renamed two labelled nets on the board (FAN_SW ->
   Net-(C12-Pad1), PWM_DIV -> Net-(R3-Pad2)); they come back to their labels.
3. J7 moves from (0,0) to the fan column at (130,76) and gets routed; its pad 2
   gets the FAN_SW net the schematic says it has.
4. Footprint fields brought back in line with the schematic (J3/J4 values, the
   Q1/Q2 datasheet and description, J7's description).

Run once against nuc-fan-controller.kicad_pcb.
"""
import re, uuid

PCB = 'nuc-fan-controller.kicad_pcb'
DS  = 'https://doc.platan.ru/pdf/datasheets/philips/BC547.pdf'
DESC = ('0.1A Ic, 45V Vce, NPN small-signal transistor, TO-92 - '
        '1=emitter 2=base 3=collector (NXP/Philips order)')
J7DESC = 'Generic connector, single row, 01x02, script generated (kicad-library-utils/schlib/autogen/connector/)'

src = open(PCB).read()

# ---- 1. net names back to the schematic's labels
n1 = src.count('Net-(C12-Pad1)'); n2 = src.count('Net-(R3-Pad2)')
src = src.replace('"Net-(C12-Pad1)"', '"FAN_SW"').replace('"Net-(R3-Pad2)"', '"PWM_DIV"')
assert n1 == 20 and n2 == 3, (n1, n2)

# ---- 2. copper that the pad swap orphaned
DROP_SEG = ['59095c24', '61966441',                    # NUC_TACH into Q1 pad 1
            '16f5e1cf', 'b0423822', 'a3b4456d',        # FAN_GATE out of Q2 pad 1
            'a393db2b',                                # GND off Q1 pad 3
            '4fdde34e', '9efd2008']                    # GND off Q2 pad 3
DROP_VIA = ['117.45 22.45', '127.45 77.45']            # stitching in the two new corridors

# Walk the top-level items line by line: a segment/via block starts at column 1 with a
# tab and ends at a lone tab + ")".  Dropping by uuid keeps the neighbours intact.
lines = src.split('\n')
keep, cur, kind, dropped = [], None, None, []
for l in lines:
    if cur is None:
        if l in ('\t(segment', '\t(via'):
            cur = [l]; kind = l[2:]
        else:
            keep.append(l)
        continue
    cur.append(l)
    if l == '\t)':
        body = '\n'.join(cur)
        u = re.search(r'\(uuid "([^"]{8})', body)
        at = re.search(r'\n\t\t\(at ([-\d.]+ [-\d.]+)\)', body)
        gone = (kind == 'segment' and u and u.group(1) in DROP_SEG) or \
               (kind == 'via' and at and at.group(1) in DROP_VIA)
        if gone:
            dropped.append(body.split('\n')[1].strip() + ' ' + (u.group(1) if u else at.group(1)))
        else:
            keep.extend(cur)
        cur, kind = None, None
assert len(dropped) == len(DROP_SEG) + len(DROP_VIA), dropped
src = '\n'.join(keep)

# ---- 3. J7 into the fan column, pad 2 on FAN_SW
i = src.index('"Reference" "J7"')
start = src.rindex('\n\t(footprint "', 0, i) + 1
j = src.index('\n\t)\n', i)
blk = src[start:j]
assert '\n\t\t(at 0 0)\n' in blk and '(net "+12V")' in blk
blk = blk.replace('\n\t\t(at 0 0)\n', '\n\t\t(at 130 76)\n', 1)
blk = blk.replace('(property "Description" ""', '(property "Description" "%s"' % J7DESC, 1)
blk = re.sub(r'(\(pad "2" thru_hole circle\n[\s\S]*?)(\t\t\t\(uuid "251c1bbe)',
             r'\1\t\t\t(net "FAN_SW")\n\2', blk, count=1)
assert '(net "FAN_SW")' in blk
src = src[:i] + blk + src[j:]

# ---- 4. footprint fields back in step with the schematic
def field(ref, name, old, new):
    global src
    i = src.index('"Reference" "%s"' % ref); j = src.index('\n\t)\n', i)
    blk = src[i:j]
    assert '"%s" "%s"' % (name, old) in blk, (ref, name)
    blk = blk.replace('"%s" "%s"' % (name, old), '"%s" "%s"' % (name, new), 1)
    src = src[:i] + blk + src[j:]

field('J3', 'Value', 'FAN 1', 'FAN 2')
field('J4', 'Value', 'FAN 2', 'FAN 3')
for q in ('Q1', 'Q2'):
    field(q, 'Datasheet', 'https://www.onsemi.com/pub/Collateral/BC550-D.pdf', DS)
    field(q, 'Description', '0.1A Ic, 45V Vce, Small Signal NPN Transistor, TO-92', DESC)

# ---- 5. the new routing
def seg(x1, y1, x2, y2, width, layer, net):
    return ('\n\t(segment\n\t\t(start %s %s)\n\t\t(end %s %s)\n\t\t(width %s)\n'
            '\t\t(layer "%s")\n\t\t(net "%s")\n\t\t(uuid "%s")\n\t\t)\n'
            % (x1, y1, x2, y2, width, layer, net, uuid.uuid4()))

ADD = []
# NUC_TACH: Q1 pad 3 -> around Q1's body -> onto the tach line at (109.73,18.782)
ADD += seg(117.08, 20, 117.08, 24, 0.2, 'F.Cu', 'NUC_TACH')
ADD += seg(117.08, 24, 109.73, 24, 0.2, 'F.Cu', 'NUC_TACH')
ADD += seg(109.73, 24, 109.73, 18.782, 0.2, 'F.Cu', 'NUC_TACH')
# FAN_GATE: Q2 pad 3 -> east of Q2 -> back onto the existing run at (102.969,77.1109)
ADD += seg(97.08, 76, 99.5, 76, 0.2, 'F.Cu', 'FAN_GATE')
ADD += seg(99.5, 76, 99.5, 77.1109, 0.2, 'F.Cu', 'FAN_GATE')
ADD += seg(99.5, 77.1109, 102.969, 77.1109, 0.2, 'F.Cu', 'FAN_GATE')
# +12V to J7 pin 1: east bypass around J4's pin 2, same style as the J3 leg
ADD += seg(130, 68, 134, 68, 1.5, 'B.Cu', '+12V')
ADD += seg(134, 68, 134, 76, 1.5, 'B.Cu', '+12V')
ADD += seg(134, 76, 130, 76, 1.5, 'B.Cu', '+12V')
# FAN_SW to J7 pin 2: extend the column that already serves J3 and J4
ADD += seg(128.09, 69.2419, 128.09, 78.54, 1.5, 'B.Cu', 'FAN_SW')
ADD += seg(128.09, 78.54, 130, 78.54, 1.5, 'B.Cu', 'FAN_SW')

tail = '\n\t(embedded_fonts no)\n)\n'
assert src.endswith(tail), src[-40:]
src = src[:-len(tail)] + ''.join(ADD) + tail

open(PCB, 'w').write(src)
print('board: nets renamed, fields realigned, J7 placed and routed.')
print('dropped %d items:' % len(dropped))
for d in dropped: print('   ', d)
