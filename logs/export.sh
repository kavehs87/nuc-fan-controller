#!/bin/sh
# Regenerate everything a reader or a fab house needs, from the .kicad_sch/.kicad_pcb
# in the repository root.  Run from the repository root:  sh logs/export.sh
#
# The layer lists are the ones exports/fab/ was built with; --check-zones means the
# copper pours are re-filled before they are plotted.
set -e
cd "$(dirname "$0")/.."
P=nuc-fan-controller

kicad-cli sch export pdf "$P.kicad_sch" -o "exports/${P}_schematic.pdf"
# sch export svg always names the file after the project, so it is renamed here
kicad-cli sch export svg "$P.kicad_sch" -o exports/tmp/
mv -f "exports/tmp/$P.svg" "exports/${P}_schematic.svg"
rmdir exports/tmp
kicad-cli sch export bom "$P.kicad_sch" -o "exports/${P}_bom.csv"

kicad-cli pcb export pdf "$P.kicad_pcb" --check-zones --mode-single \
    --layers "F.Cu,F.Silkscreen,F.Mask,Edge.Cuts" -o "exports/${P}_board.pdf"
kicad-cli pcb export pdf "$P.kicad_pcb" --check-zones --mode-single --mirror \
    --layers "B.Cu,B.Silkscreen,B.Mask,Edge.Cuts" -o "exports/${P}_board_bottom.pdf"
kicad-cli pcb export svg "$P.kicad_pcb" --check-zones --mode-single \
    --layers "F.Cu,F.Silkscreen,F.Mask,Edge.Cuts" -o "exports/${P}_board.svg"

kicad-cli pcb export gerbers "$P.kicad_pcb" --check-zones -o exports/fab/ \
    --layers "F.Cu,B.Cu,F.Silkscreen,B.Silkscreen,F.Mask,B.Mask,Edge.Cuts,Margin"
kicad-cli pcb export drill "$P.kicad_pcb" -o exports/fab/
kicad-cli pcb export pos "$P.kicad_pcb" -o "exports/fab/${P}_pos.csv"

# logs/netlist.net is not in here: KiCad's own netlist plugin writes it, kicad-cli
# no longer writes that format, so it is regenerated from the KiCad python API.

echo "exports/ rebuilt"
