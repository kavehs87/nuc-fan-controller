#!/usr/bin/env python3
"""Swap Q1/Q2 from Transistor_BJT:BC547 (1=C 2=B 3=E) to Transistor_BJT:Q_NPN_EBC
(1=E 2=B 3=C) in place, so the footprint pad numbers match the BC547s in the
cabinet, which are the NXP/Philips order.

The two symbols draw at identical pin coordinates (C at 2.54,5.08 / B at -5.08,0 /
E at 2.54,-5.08); only the pin *numbers* differ.  So no wire, junction, name tag or
power symbol moves.  What changes is the netlist: pad 1 becomes the emitter (GND)
and pad 3 the collector (NUC_TACH on Q1, FAN_GATE on Q2).

Run once.  It rewrites nuc-fan-controller.kicad_sch in place.
"""
import re, sys

SCH = 'nuc-fan-controller.kicad_sch'
LIB = '/Applications/KiCad/KiCad.app/Contents/SharedSupport/symbols/Transistor_BJT.kicad_sym'
DS  = 'https://doc.platan.ru/pdf/datasheets/philips/BC547.pdf'
DESC = ('0.1A Ic, 45V Vce, NPN small-signal transistor, TO-92 - '
        '1=emitter 2=base 3=collector (NXP/Philips order)')

sch = open(SCH).read()
lib = open(LIB).read()

# --- 1. the library's canonical Q_NPN_EBC definition, re-indented for lib_symbols
i = lib.index('\t(symbol "Q_NPN_EBC"\n')
j = lib.index('\n\t(symbol "Q_NPN_ECB"', i)
block = lib[i + 1 : j + 1]                      # keep the closing "\t)" line
assert block.rstrip().endswith('\t)') or block.rstrip().endswith(')'), block[-40:]
block = '\n'.join('\t' + ln if ln.strip() else ln for ln in block.rstrip('\n').split('\n'))
block = block.replace('(symbol "Q_NPN_EBC"\n', '(symbol "Transistor_BJT:Q_NPN_EBC"\n', 1)
assert block.count('(symbol "Q_NPN_EBC_') == 2 and 'Transistor_BJT:Q_NPN_EBC' in block

# --- 2. replace the cached Transistor_BJT:BC547 definition with it
i = sch.index('\t\t(symbol "Transistor_BJT:BC547"\n')
j = sch.index('\n\t\t(symbol "', i + 10)        # start of the next lib_symbols entry
old = sch[i : j + 1]
assert old.count('(number "1"') == 1 and old.count('(number "3"') == 1
assert '(symbol "BC547_1_1"' in old and '(embedded_fonts no)' in old
sch = sch[:i] + block + sch[j:]

# --- 3. the two placed instances
n = 0
def fix(m):
    global n
    head = m.group(0)
    ref = re.search(r'\(property "Reference" "(Q[12])"', head)
    if not ref:
        return head
    n += 1
    head = head.replace('(lib_id "Transistor_BJT:BC547")', '(lib_id "Transistor_BJT:Q_NPN_EBC")')
    head = re.sub(r'\(property "Datasheet" "[^"]*"', '(property "Datasheet" "%s"' % DS, head, count=1)
    head = re.sub(r'\(property "Description" "[^"]*"', '(property "Description" "%s"' % DESC, head, count=1)
    return head

pat = re.compile(r'\t\(symbol\n\t\t\(lib_id "Transistor_BJT:BC547"\)[\s\S]*?\n\t\)\n')
sch = pat.sub(fix, sch)
assert n == 2, n
assert 'Transistor_BJT:BC547' not in sch

open(SCH, 'w').write(sch)
print('Q1 and Q2 are Q_NPN_EBC now; lib_symbols updated; datasheet and description rewritten.')
