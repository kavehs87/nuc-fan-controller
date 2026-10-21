#!/usr/bin/env bash
# ------------------------------------------------------------------
# Run the MOSFET fan-switch simulation.
#
#   1. export the KiCad schematic to a SPICE netlist   (kicad-cli)
#   2. build an ngspice run deck (analyses appended at the end)
#   3. simulate with ngspice
#   4. plot the results and print the numbers that matter
#
#   ./sim/run.sh
# ------------------------------------------------------------------
set -euo pipefail
cd "$(dirname "$0")/.."

SCHEMATIC=mosfet-fan-switch.kicad_sch
OUT=sim/out
mkdir -p "$OUT"

if command -v kicad-cli >/dev/null 2>&1; then
    echo "==> exporting netlist from $SCHEMATIC"
    kicad-cli sch export netlist --format spice -o "$OUT/mosfet-fan-switch.spice" "$SCHEMATIC"
elif [[ ! -f "$OUT/mosfet-fan-switch.spice" ]]; then
    echo "kicad-cli not found and no cached netlist in $OUT" >&2
    exit 1
else
    echo "==> kicad-cli not found: re-using $OUT/mosfet-fan-switch.spice"
fi

echo "==> building ngspice deck"
python3 sim/prepare_deck.py

echo "==> simulating"
ngspice -b "$OUT/run_deck.cir" > "$OUT/ngspice.log" 2>&1 || { tail -30 "$OUT/ngspice.log"; exit 1; }

echo "==> plotting"
python3 sim/plot.py

echo "==> comparing the drive options your bin allows"
python3 sim/variants.py

echo "==> how many fans one output can carry"
python3 sim/fan_count.py

echo
echo "done. plots and data are in $OUT/"
