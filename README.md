# nuc-fan-controller

A board that lets a 12 V two‑pin fan be used in place of a NUC's stock 5 V fan, and that
answers the NUC's tach input so the BIOS believes the fan it is asking for.

It does four things:

1. **bucks 19 V → 12 V** for the fans — LM2596T‑ADJ, 100 µH / 6 A toroid, 1N5822 catch diode,
   trimmed with a 10 kΩ multi‑turn pot to 12.0 V;
2. **12 V → 5 V → 3.3 V** for a 3.3 V / 8 MHz Arduino Pro Mini (AMS1117‑5.0 then AMS1117‑3.3,
   into the Pro Mini's **VCC**; RAW unused);
3. **follows the duty the NUC's ITE asks for** — the ITE's PWM wire is divided to 2.96 V, read
   on A0, and re‑made as 31.25 kHz on D11 driving Q2 → IRFZ44N → the fans;
4. **simulates the tach signal** — Timer1 hardware square wave on D9 sinks Q1's open collector;
   the pull‑up lives in the NUC. `RPM = 30 × f_tach` (the ITE IT8607E counts 2 pulses per turn).

Board: 124 × 85 mm, 2 layers, GND poured both sides with 326 stitching vias, `Power` net class
1.5 mm on 19V / SW / +12V / FAN_SW / +3V3 / GND. **ERC 0 violations. DRC 0 violations,
0 unconnected items**, one schematic‑parity warning: `J2` pin 4 carries a deliberate no‑connect
(it is the NUC header's own fan supply, which this board never touches).

## Open it without KiCad

[`exports/index.html`](exports/index.html) — schematic, both board views, BOM, links.

| File | What it is |
|---|---|
| `nuc-fan-controller.kicad_sch` / `.kicad_pcb` / `.kicad_pro` | KiCad 10 design |
| `exports/nuc-fan-controller_schematic.pdf` / `.svg` | schematic, wires not net labels, name tags on every signal net |
| `exports/nuc-fan-controller_board.pdf`, `…_board_bottom.pdf`, `…_board.svg` | board plots |
| `exports/nuc-fan-controller_bom.csv` | 38 fitted parts |
| `exports/fab/` | 8 Gerbers + `.drl` + `_pos.csv` + `job.gbrjob` — ready to zip and order |
| `firmware/nuc-tach-modeB/nuc-tach-modeB.ino` | the sketch; calibration constants at the top |
| `firmware/probe-uno/probe-uno.ino` | breadboard probe sketch for an Uno (5 V / 16 MHz): tach wave on D9 with the measured `ITE_READ_GAIN` applied, 31.25 kHz fan drive on D11 — for scope-checking the BC547 stages before the board exists |
| `firmware/probe-gain/probe-gain.ino` | sweep sketch: emits an exact ladder of tach claims (900–3000 RPM, 8 s each) so the ITE's read gain can be measured from the BIOS/hwmon number instead of guessed |
| `BUILD.md` | the build sheet: header identification with a meter, buck trim, calibration, bench order |
| `archive/modeA-2026-10-19/` | the fixed‑RPM tach simulator this board replaced |

## Build order, short version

1. Identify the four NUC fan‑header wires with a meter — Intel publishes no pinout.
2. Fit the buck only, trim to 12.0 V, then confirm 5 V and 3.3 V.
3. Find the fan's stall duty and measure its RPM at two duties; those four numbers are the
   constants at the top of the sketch.
4. Read TP1 with a frequency counter — it must equal `rpm / 30` Hz exactly, it is a hardware timer.
5. Tach side first (J2.1 + J2.2), then the PWM wire (J2.3), then the fans on J3/J4.

**Two things that break hardware:** a 12 V fan's tach or PWM wire spliced into the NUC header
(that fan pulls those lines to its own 12 V internally), and a 5 V FTDI on a 3.3 V Pro Mini
(ATmega328P absolute maximum on any pin is VCC + 0.5 V). Flash with Board → *Arduino Pro or Pro
Mini*, Processor → **ATmega328 (3.3V, 8MHz)**.

## Reproducing the design work

```
python3 logs/genwires.py                 # regenerates the schematic's wires/junctions from logs/layout.py
kicad-cli sch erc nuc-fan-controller.kicad_sch --output logs/erc.json --format json --severity-all
kicad-cli pcb drc nuc-fan-controller.kicad_pcb --output logs/drc.json --format json \
    --severity-all --schematic-parity --refill-zones --save-board
docker run --rm -v "$PWD/logs/routing:/work" eclipse-temurin:25-jre \
    java -Djava.awt.headless=true -jar /work/freerouting.jar \
    -de /work/nuc-fan-controller.dsn -do /work/nuc-fan-controller.ses -mp 150
```

The layout in `logs/layout.py` is the source of the schematic's geometry; `logs/genwires.py`
checks cross‑net crossings, wires through symbol bodies, pins on two nets and shorted parts
before it emits anything.

## Status

Design verified on paper and in the CAD, not yet built. `BUILD.md` is the bench sequence, and the
four calibration constants in the sketch are placeholders until a fan is measured.

No license is granted — all rights reserved. It is published so the drawings and the reasoning
behind them are readable.
