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
| `firmware/probe-gain/probe-gain.ino` | sweep sketch: an exact ladder of tach claims (900–3000 RPM, 20 s each) with the fan following the ITE's demand, printing the divider's own count — measures the ITE's read gain and logs its fan curve |
| `firmware/probe-loop/probe-loop.ino` | test sketch: fan drive pinned, tach claims stepped 800 / 2000 / 4500 RPM — measures whether the ITE's demand answers the tach at all |
| `firmware/probe-temp/probe-temp.ino` | test sketch: claim frozen at 1500 RPM — measures whether the demand answers temperature |
| `bench/analyze-ladder.py`, `bench/analyze-temp.py` | the analysers that produced the numbers below, run against `bench/data/` |
| `bench/data/` | the raw logs: 1 Hz traces of the divider reading, and of the NUC's temperatures |
| `BUILD.md` | the build sheet: header identification with a meter, buck trim, calibration, bench order |
| `archive/modeA-2026-10-19/` | the fixed‑RPM tach simulator this board replaced |

## On the bench

The board itself is not built yet. Its two control signals have been measured on a breadboard, with
an Uno standing in for the Pro Mini and the ITE's own behaviour logged at 1 Hz. Full numbers and the
raw logs are in `BUILD.md` and `bench/`; these are the measurements that changed the design.

![the bench: NUC mainboard, two 12 V fans, the Uno and the breadboard](docs/bench/01-bench-overview.jpg)

**The harness into the NUC's fan header.** Four wires, no published pinout — `BUILD.md` identifies
them with a meter before anything is spliced. The tach and PWM wires go to the breadboard; the
header's own fan supply is left unconnected, which is the deliberate no‑connect on `J2` pin 4.

![the fan header with the harness in it](docs/bench/02-fan-header.jpg)

**The duty‑read chain.** The ITE's PWM wire through the series resistors to the tap, the tap to A0,
the bottom resistor and the caps to ground. A0 sits at the tap — put it at the far end of the chain
and nothing divides, because the AVR draws no current.

![the divider on the breadboard](docs/bench/03-divider-on-breadboard.jpg)

**The ITE's PWM is 23 kHz, not an assumption.** A scope on the PWM wire reads a 23 kHz square at
45 % duty mid‑sweep — inside Intel's 25 kHz ±10 % for a 4‑wire fan. At that frequency the divider and
C10/C11 are comfortably over‑specified: τ = 4.49 ms against a 43.5 µs period leaves 7 mV of ripple at
the ADC, 0.24 % of the duty span.

**The tach is read, and it is read 1 % low.** The scope on the tach line:

![the fabricated tach square wave on the scope](docs/bench/04-tach-at-40hz.jpg)

and the NUC's own hardware monitor, 40.000 Hz later:

![CPU FAN 1186 RPM against a 1200 RPM claim](docs/bench/05-bios-reads-1186.jpg)

1186 against a 1200 claim, 1188 at the same setting a minute later — the ITE's display steps by
2 RPM, and the gap is 0.990. That is `ITE_READ_GAIN`. Note what is on the same screen: CPU 58 °C,
memory 44 °C, motherboard ambient 40 °C. Those are the ITE's own sensors, and they turn out to be
what its fan policy runs on.

**The demand answers temperature, not the reported speed.** Two tests, both logged at 1 Hz. Stepping
the claimed RPM 800 → 2000 → 4500 — a 5.6× swing — moved the ITE's requested duty by 1.1 %, while the
same claim swung 195–260 counts on its own. Freezing the claim at 1500 RPM and driving the package
55 → 83 → 53 °C moved the same reading 231 → 327 → 230 counts, correlated at **r = +0.822 with a 4 s
lag**. So the tach's job is to keep the ITE satisfied — no fan error, a plausible number on the
screen — and following the demand is following the NUC's own thermal policy.

![both ends probed at once](docs/bench/06-probing-both-ends.jpg)

![the scope on the bench, and the buck module trimmed first](docs/bench/08-scope-and-buck.jpg)

![the parts drawer the BOM was written against](docs/bench/07-parts-drawer.jpg)

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

Design verified on paper and in the CAD; **the board is not built yet.** The control side has been
measured on a breadboard — the ITE's PWM frequency and amplitude, how it reads the tach, and what
actually drives its demand — see *On the bench*. `BUILD.md` is the bench sequence. The fan-side
constants (`FAN_RPM_MIN`, `FAN_RPM_FULL`, `ADC_AT_100PCT`) are still placeholders until a real fan is
fitted and measured; `ITE_READ_GAIN` has a measured value for the Uno driving this NUC and needs the
same measurement on the finished board.

No license is granted — all rights reserved. It is published so the drawings and the reasoning
behind them are readable.
