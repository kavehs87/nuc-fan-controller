#!/bin/sh
# Regenerate everything a reader or a fab house needs, from the .kicad_sch/.kicad_pcb
# in the repository root.  Run from the repository root:  sh logs/export.sh
#
# This board has one copper layer, and it is the component side: F.Cu carries the parts,
# the pour and every trace.  There is no bottom plot and no drill-to-order package - the
# board is cut, etched and drilled at home, so the exports that matter are the Gerbers,
# the drill file, and a 1:1 copper print for toner transfer.
set -e
cd "$(dirname "$0")/.."
P=nuc-fan-controller

# The board must be refilled and re-checked before anything is plotted: the pour is the
# ground, and a plot of an unfilled pour is not the board.
kicad-cli pcb drc "$P.kicad_pcb" --refill-zones --save-board >/dev/null
kicad-cli sch export netlist "$P.kicad_sch" --format kicadxml --output logs/netlist.net

kicad-cli sch export pdf "$P.kicad_sch" -o "exports/${P}_schematic.pdf"
# sch export svg always names the file after the project, so it is renamed here
mkdir -p exports/tmp
kicad-cli sch export svg "$P.kicad_sch" -o exports/tmp/
mv -f "exports/tmp/$P.svg" "exports/${P}_schematic.svg"
rmdir exports/tmp
kicad-cli sch export bom "$P.kicad_sch" -o "exports/${P}_bom.csv"

kicad-cli pcb export pdf "$P.kicad_pcb" --check-zones --mode-single \
    --layers "F.Cu,F.Silkscreen,F.Mask,Edge.Cuts" -o "exports/${P}_board.pdf"
kicad-cli pcb export svg "$P.kicad_pcb" --check-zones --mode-single --fit-page-to-board \
    --layers "F.Cu,F.Silkscreen,F.Mask,Edge.Cuts" -o "exports/${P}_board.svg"

# 1:1 copper only, black on white: print with scaling off, iron the toner onto copper-clad,
# etch, drill.  Edge.Cuts is on the sheet so the outline can be sawn to.
kicad-cli pcb export pdf "$P.kicad_pcb" --check-zones --mode-single --scale 1 \
    --black-and-white --layers "F.Cu,Edge.Cuts" -o "exports/${P}_etch_copper.pdf"
kicad-cli pcb export pdf "$P.kicad_pcb" --check-zones --mode-single --scale 1 \
    --black-and-white --negative --layers "F.Cu,Edge.Cuts" -o "exports/${P}_etch_negative.pdf"
kicad-cli pcb export svg "$P.kicad_pcb" --check-zones --mode-single --fit-page-to-board \
    --black-and-white --layers "F.Cu,Edge.Cuts" -o "exports/${P}_etch_copper.svg"

rm -rf exports/fab
kicad-cli pcb export gerbers "$P.kicad_pcb" --check-zones -o exports/fab/ \
    --layers "F.Cu,F.Silkscreen,F.Mask,Edge.Cuts"
kicad-cli pcb export drill "$P.kicad_pcb" -o exports/fab/

echo "exports/ rebuilt"
