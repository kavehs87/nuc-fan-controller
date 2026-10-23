#!/usr/bin/env python3
"""Turn the KiCad SPICE export into a runnable ngspice deck.

KiCad writes the schematic's analysis cards *before* the device lines and only
prints tables.  For plotting we want the raw vectors, so the cards KiCad
exported are dropped and an equivalent .control block is appended at the end of
the circuit - that is the ordering ngspice likes.

The transistors arrive as sub-circuit calls (`XQ1 /GATE /DRAIN GND mos_irfz44n`)
in symbol pin order, which is the real package leg order; each wrapper in
`sim/models/*.lib` re-orders the terminals for ngspice.  Nothing to repair here.
"""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "sim" / "out" / "mosfet-fan-switch.spice"
DST = ROOT / "sim" / "out" / "run_deck.cir"

# lines KiCad exported for the built-in simulator; replaced by the block below
SKIP_PREFIXES = (".op", ".dc", ".tran", ".print", ".control", ".endcontrol")

CONTROL = """
.control
* 1. DC operating point with the Arduino pin low (fan off)
op
print v(/LGATE) v(/BOOT) v(/HIGATE) v(/GATE) v(/DRAIN) i(v1)

* 2. DC transfer curve: sweep the Arduino drive 0 -> 3.3 V
dc V2 0 3.3 0.005
wrdata sim/out/dc_sweep.txt v(/LGATE) v(/BOOT) v(/GATE) v(/DRAIN) i(v1) i(v2)

* 3. Transient: 1 kHz PWM (50 % duty) for 5 ms
tran 100n 5m
wrdata sim/out/tran_data.txt v(/PWM) v(/LGATE) v(/BOOT) v(/GATE) v(/DRAIN) i(l1) i(v1) i(v2)
.endcontrol
"""


def main() -> None:
    lines = SRC.read_text().splitlines()
    keep = [l for l in lines if not l.strip().startswith(SKIP_PREFIXES)]
    if keep and keep[-1].strip() == ".end":
        keep.pop()
    DST.write_text("\n".join(keep) + "\n" + CONTROL + "\n.end\n")
    print(f"    wrote {DST.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
