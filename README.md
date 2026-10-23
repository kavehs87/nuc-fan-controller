# NUC fan control — one project, two halves

This repo is what `nuc-fan-controller` and the perfboard fan‑switch build became when they were merged in
October 2026. The fan‑switch history came across with it — 22 commits and the `checkpoint-fan-driver-v1`
and `checkpoint-pro-mini-v2` tags — parked under one directory, so nothing collided.

| half | what it holds | state |
|---|---|---|
| **`fan-switch-booster/`** | the gate booster that lets a 3.3 V logic pin switch a 12 V fan: its schematic, an ngspice model with hand‑written FET models, five sketches, the bench scripts | **built on perfboard, scoped, and listened to.** It is the electrical reference |
| **root** | the record of the NUC's own fan control: 4 577 paired 1 Hz samples in `bench/data/`, the analysers and graphs that read them, `BUILD.md`, and the sketches that carry the measured ITE constants | **measured.** The enclosure board that was designed around those numbers is retired to git at the tag `nuc-fan-controller-full-2026-10-23` |

**The perfboard is the reference.** Every claim about how a 12 V two‑pin fan behaves under a chopped
supply — carrier frequency, delivered duty, the fan's start threshold, what the noise actually was — comes
from that board and is recorded in `fan-switch-booster/README.md`. Every claim about how the NUC's ITE
behaves — its PWM frequency and amplitude, where its demand bottoms out, what it follows — comes from the
breadboard runs recorded below and in `BUILD.md`. The two were measured on the same machine, and they
complement each other; they do not agree on everything, and where they differ is written down rather than
smoothed over.

In October 2026 the repo was reduced to that: one KiCad project, the one that was simulated and
perfboard‑tested. The enclosure board's drawings, its exports, its board generator, the archived
tach‑simulator board and the two abandoned routings were removed, along with every KiCad cache and scratch
copy. They are complete at the tag named above, and no measurement went with them — the ITE runs were done
on a breadboard with an Uno.

## The tree

```
README.md                  this file — the merged record, and the measured facts both halves rest on
AGENTS.md                  what is settled, so it is not re-litigated
BUILD.md                   the NUC-side bench procedures: meter the header, the divider, the BC547 check,
                           the log pairs and offsets, calibration order  (its board sections are a
                           retired record; the commands in them no longer run)

bench/                     the ITE measurements
  data/                      12 raw 1 Hz logs — every number in this file comes from these
  analyze-*.py               the five analysers
  plot-curve.py plot-hold.py draw the two graphs in docs/bench/
  prepare-photos.py          the tool that cropped docs/bench/ from the phone originals; its input
                             directory was purged, so it no longer runs

docs/
  bench/                     five bench photographs, two graphs
  parts-collection.*         the cabinet walk for the retired board's BOM

firmware/                  the sketches that made those measurements
  nuc-tach-modeB/            the ITE constants live here
  nuc-tach-modeA/            the archived tach simulator's sketch
  probe-*/                   the five breadboard probes

fan-switch-booster/        the built reference — its own README.md and AGENTS.md
  mosfet-fan-switch.kicad_sch   the schematic the perfboard was built from
  sim/                       ngspice model, hand-written FET models, ./sim/run.sh
  firmware/                  the sketch on the chip, three earlier variants, an Arduino-as-ISP programmer,
                             and the bench scripts (set.sh, seq.sh, flash-bootloader.sh, verify-flash.sh)
  pcb/  docs/pcb-*           the retired PCB record
  archive/                   the 5 V low-side first attempt
```

Three tags mark the states this repo has been through: `checkpoint-fan-driver-v1` and
`checkpoint-pro-mini-v2` from the fan‑switch work, and `nuc-fan-controller-full-2026-10-23`, which holds
everything the October 2026 cleanup removed.

## The facts both halves rest on

| fact | value | evidence |
|---|---|---|
| the machine | 6th‑generation i3 NUC, whose stock blower is a **5 V** fan | measured |
| the ITE's PWM request | **23 kHz** square, inside Intel's 25 kHz ±10 % | measured, scope |
| top of that swing | **≈ 4.90 V** on the wire, ≈ 2.45 V at a 10 k / 10 k tap | measured, extrapolated from the dwell ladder |
| the header's own fan supply | **5 V**, and a deliberate no‑connect on both boards | measured |
| the ITE's duty **floor** | **46–48 %** — 1 946 samples, none below 100 counts of 717. Under ITE control the fan never stops | measured |
| the duty is stepped | dwell rungs 198 / 257 / 320 / 380 counts, an 11.9‑point quantum | measured |
| what the demand follows | the **board / PCH temperature**, not the cores | measured, 4 577 paired samples |
| what a tach claim does to the demand | **1.1 %** for a 5.6× claim — reported speed is not in the loop | measured |
| tach read gain | 1 186 RPM against a 1 200 RPM claim, factor **0.990** | measured |
| tach ↔ RPM | `RPM = 30 × f_tach` (ITE IT8607E counts 2 pulses per turn) | measured |
| a 12 V two‑wire fan's start threshold | **4–7 V at its terminals**; 10 % and 20 % at 100 Hz deliver 1.2 V and 2.4 V and will not start it | measured on the perfboard |
| ATmega328P absolute maximum, any pin | **VCC + 0.5 V** = 3.8 V on a 3.3 V part | datasheet |
| Intel's published pinout for these headers | **there is none** — meter the four wires before splicing | `BUILD.md` |

The floor and the start threshold fit together, which is worth saying out loud: the ITE never asks for
less than ~47 %, and 47 % at 100 Hz is about 6.4 V at the fan terminals — above the voltage the fan needs
to start. So a fan driven by the ITE's demand is never asked to start from a dead stop, and the "start
kick" left open in `fan-switch-booster/README.md` only matters for manual control below about 30 %.

## Four ways the two designs disagree, and how to not mix them

The second column is retired hardware, but its sketch `firmware/nuc-tach-modeB` is still in this repo and
still carries the measured ITE constants — so these differences are live whenever a sketch crosses over.

| | the perfboard, `fan-switch-booster/` | the retired enclosure board |
|---|---|---|
| fan drive pin | **D9** (`OC1A`), Timer 1 | **D11** (`OC2A`), Timer 2 |
| tach pin | **D10**, and unused on the bench — that board has no tach path | **D9** (`OC1A`), sinking `Q1`'s open collector |
| polarity | non‑inverting: pin high → fan on | `Q2` inverts once — pin high → gate low → fan off — and `nuc-tach-modeB` asks for the complement to undo it |
| carrier | **100 Hz**, measured quiet | **31.25 kHz**, exactly 8 MHz / 256 |
| gate stage | `Q2` 2N7002 + `Q3` IRF7416 booster. Turn‑off costs a fixed **~170 µs**, because `/BOOT` charges back through `R3` 10 kΩ into a node that measures **~8 nF** | `Q2` BC547 with **`R8` 1 kΩ pulling the gate node to +12 V**, `R9` 120 Ω in series with `Q3`'s gate, `R10` 10 kΩ across gate‑to‑source. Turn‑off dumps through 120 Ω: τ ≈ 0.2 µs |
| ADC scale at the divider tap | **775 counts** — a 3.3 V reference | the logs are on an **Uno's 5 V** reference, where the same 2.50 V is **512 counts** |

**Both carriers are correct, for their own gate stage.** 31.25 kHz is safe on the BC547 board because its
gate dumps through 120 Ω in well under a microsecond; it is *unusable* on the perfboard, where the off
half‑period (16 µs) is far shorter than the 170 µs the booster needs to turn off, so the output is simply
stuck on. That is not a contradiction, it is two different circuits. Neither has to copy the other's carrier:
the ITE's 23 kHz is only *read* — the divider turns it into a DC level — and the fan drive frequency is a
free choice. Do not feed the ITE's clock into either output stage.

**And one thing that CAD never caught up with.** The bench settled on a **10 kΩ / 10 kΩ** divider — 2.50 V on
the tap, 0.8 V of headroom on a 3.3 V part — while the retired schematic still carried `R3` 4.7 k → `R4`
2.2 k in series from `NUC_PWM`, over `R5` 10 kΩ to ground: a **2.96 V** tap with 0.34 V of headroom. If that
board is ever rebuilt from the tag, it starts at two 10 kΩ, not at what the drawing says.

## Where the fan‑switch half lives

| in `fan-switch-booster/` | what it is |
|---|---|
| `README.md` | the whole record of that half: the stages, every part from the cabinets, the simulation, the perfboard findings, why the carrier is 100 Hz, the firmware and the flashing route |
| `AGENTS.md` | the settled list for that half — read it before touching that subtree |
| `mosfet-fan-switch.kicad_sch` | the schematic the perfboard was built from. **Live** |
| `mosfet-fan-switch.kicad_pcb`, `pcb/`, `docs/pcb-*` | **retired** board design — never built, never routed. Kept as the reason the layout looks like it does |
| `sim/` | the ngspice model. `./sim/run.sh` regenerates netlist, deck, plots and the variant tables |
| `firmware/fan-switch-freq/` | the sketch on the chip right now: boots itself at `duty 0 % OCR1A 0/10000 carrier 100 Hz` |
| `firmware/bench/` | `set.sh`, `seq.sh`, `flash-bootloader.sh`, `verify-flash.sh`, and how to run them on the remote bench |
| `archive/` | the 5 V low‑side first attempt — its schematic, its placeholder models and its plots |

---

# What the NUC does on its own — measured

Everything below this line is the record of the **ITE side**: how the NUC asks for fan speed, what its
demand follows, where it bottoms out, and how it reads a tach signal. It was measured on a breadboard with an
Uno standing in for the Pro Mini, and none of it depends on any board in this repo.

## The enclosure board that used to be here

`nuc-fan-controller` was a board meant to sit inside the NUC enclosure — last drawn as 88.90 × 76.20 mm on a
single copper layer, small enough to etch at home, after an earlier life as 124 × 85 mm on two. It did four
things: brought 19 V down to 12 V with an XL4016E1 module for three 12 V two‑pin fans; made 3.3 V for a Pro
Mini with an AMS1117‑3.3, with no 5 V rail anywhere on it; read the ITE's PWM request on A0 and re‑made it at
31.25 kHz on D11 through a BC547 stage into an IRFZ44N; and answered the tach with a Timer 1 square wave on
D9 sinking `Q1`'s open collector, the pull‑up living in the NUC. ERC clean, DRC clean, 0 unconnected items,
one deliberate no‑connect on its fan‑header connector's supply pin — the header's own fan supply, which it
never touched.

**It is retired, and it was never built.** The perfboard in `fan-switch-booster/` is the reference, so that
board's KiCad project, its `exports/` (schematic, board, the 1:1 copper etch prints, BOM, Gerbers), its board
generator in `logs/`, the archived tach‑simulator board and the two abandoned routings of the booster were
removed from the working tree in October 2026. All of it is intact in git at the tag
**`nuc-fan-controller-full-2026-10-23`** — every drawing, every export, and `10bc262`, the version that built
its 19 V → 12 V converter out of discrete parts instead of the module.

What stayed is measurement rather than board: `bench/data/` and the analysers that read it, the photographs
and graphs in `docs/bench/`, `BUILD.md`, `docs/parts-collection.md`, and the sketches that produced the
numbers.

## What is here for the NUC side

| File | What it is |
|---|---|
| `fan-switch-booster/` | **the built reference** — the perfboard booster, its schematic, its simulation, its sketches, its bench scripts. Table near the top of this file |
| `firmware/nuc-tach-modeB/nuc-tach-modeB.ino` | the sketch written for the retired board, and where the measured ITE constants live: `ITE_READ_GAIN`, the demand follower, the duty clamp |
| `firmware/probe-uno/probe-uno.ino` | breadboard probe sketch for an Uno (5 V / 16 MHz): tach wave on D9 with the measured `ITE_READ_GAIN` applied, 31.25 kHz fan drive on D11 — for scope-checking the BC547 stages before the board exists |
| `firmware/probe-gain/probe-gain.ino` | sweep sketch: an exact ladder of tach claims (900–3000 RPM, 20 s each) with the fan following the ITE's demand, printing the divider's own count — measures the ITE's read gain and logs its fan curve |
| `firmware/probe-loop/probe-loop.ino` | test sketch: fan drive pinned, tach claims stepped 800 / 2000 / 4500 RPM — measures whether the ITE's demand answers the tach at all |
| `firmware/probe-temp/probe-temp.ino` | test sketch: claim frozen at 1500 RPM — measures whether the demand answers temperature, and what the ITE's floor demand is when the machine is cold |
| `firmware/probe-divider/probe-divider.ino` | test sketch: measures the divider's own ratio with nothing but the Uno, by feeding the chain from the Uno's 5 V pin so the rail voltage cancels |
| `bench/analyze-ladder.py`, `bench/analyze-temp.py`, `bench/analyze-cold.py`, `bench/analyze-heat.py` | the analysers that produced the numbers below, run against `bench/data/` — `analyze-heat.py` is the one that separates the cores from the board |
| `bench/analyze-hold.py` | the analyser for the "does it integrate time?" test: flat-window trend, same-temperature early against late, and a two-variable fit |
| `bench/plot-curve.py`, `bench/plot-hold.py` | draw `docs/bench/06-ite-fan-response.svg` and `docs/bench/07-ite-hold-test.svg`, the two graphs below, from the same logs |
| `bench/data/` | the raw logs: 1 Hz traces of the divider reading, and of the NUC's temperatures |
| `firmware/nuc-tach-modeA/nuc-tach-modeA.ino` | the archived tach simulator's sketch — the fixed‑RPM answer this project replaced |
| `bench/prepare-photos.py` | the tool that cropped `docs/bench/` out of the phone originals. Its input directory was purged in the cleanup, so it no longer runs; the recipe is in the file |
| `docs/parts-collection.md`, `.html` | the cabinet walk for the **retired board's** BOM — every line with the drawer it came from, and the measurements each part has to give up before its footprint can be drawn |
| `BUILD.md` | the bench sheet: identifying the four header wires with a meter, setting a buck module to 12.0 V, the divider / top‑of‑swing procedure, the BC547 pin‑order check, calibration order. Its assembly steps name parts of the retired board |
| `docs/parts-collection.html` | the collection sheet: every BOM line with the exact cabinet drawer it comes from, in drawer‑walk order, plus the eight measurements that decide the footprints (also `docs/parts-collection.md`) |
| `fan-switch-booster/archive/` | the booster's first version — a single logic‑level IRLZ44N driven directly at 5 V, with its plots. Kept because the reason it worked is the reason 3.3 V needs a booster |

## On the bench

These measurements stand on their own. They were taken on a breadboard, with an Uno standing in for the Pro
Mini and the ITE's own behaviour logged at 1 Hz — no board in this repo was needed for any of them. Full
numbers and the raw logs are in `BUILD.md` and `bench/data/`; these are the readings that changed the design.

**The whole result in one picture** — 4 577 paired samples from five runs. Top: the ITE's requested duty
against the temperature of the *board* (`pch_thermal`), every sample as a dot, the heavy line being the
median in 3 °C bins, the dotted lines the dwell levels the ITE actually holds. The open circles are the
247 samples where the cores sat at 65 °C or hotter while the board stayed under 55 °C — they land on the
floor, not on the ramp, which is what makes the board the axis and the cores not. Bottom left: the fourth
run in time, board warmed by hand with the bench fans off and the NUC's own blower at minimum, then a
four‑core load, then left alone. Bottom right: the fifth run in time, held at 68.5–69 °C for sixteen flat
minutes — the duty sits on 378 counts for all of it. `bench/plot-curve.py` draws it from `bench/data/`.

![the ITE's fan demand against the board, and one run in time](docs/bench/06-ite-fan-response.svg)

![the bench: NUC mainboard, two 12 V fans, the Uno and the breadboard](docs/bench/01-bench-overview.jpg)

**The harness into the NUC's fan header.** Four wires, no published pinout — `BUILD.md` identifies
them with a meter before anything is spliced. The tach and PWM wires go to the breadboard; the
header's own fan supply is left unconnected, which is the same pin the retired board marked as a deliberate
no‑connect.

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

**The demand answers the board's temperature, not the cores, and not the reported speed.** Five tests,
all logged at 1 Hz, 4 577 paired samples. Stepping the claimed RPM 800 → 2000 → 4500 — a 5.6× swing —
moved the ITE's requested duty by 1.1 %, while the same claim swung 195–260 counts on its own: the
reported speed is not in the loop. Freezing the claim at 1500 RPM and driving the package 55 → 83 → 53 °C
moved the reading 231 → 327 → 230 counts, correlated at **r = +0.822 with a 4 s lag** — but that run had
the bench fans switched by hand, so the board rose with the cores (PCH 52 → 63.5 °C) and the two could not
be told apart.

The third run tells them apart. Same sketch, same frozen claim, bench fans at maximum: `stress-ng --cpu 4`
for 300 s took the package 34 → 73 °C and it cooled back to 38 °C, the PCH only reached 55.5 °C, and
**the demand did not move at all** — 195–260 counts for eleven minutes, r = +0.049 against the cores. The
fourth run goes the other way and pushes the top end out: bench fans off, the NUC's own blower at minimum,
the board warmed by hand and then loaded, taking the board to 68.5 °C while the cores sat pinned at
88 °C. The demand climbed to **380 counts, 74 %**, with 434 counts (85 %) seen. Binned by the board, all
four runs together:

| board (`pch_thermal`) | n | median demand | as duty, 512 counts = 100 % | PWM wire average |
|---|---|---|---|---|
| 33–51 °C | 2 131 | 239 counts | 46.7 % | 2.33 V |
| 51–54 °C | 306 | 247 counts | 48.2 % | 2.41 V |
| 54–57 °C | 251 | 254 counts | 49.6 % | 2.48 V |
| 57–60 °C | 169 | 259 counts | 50.6 % | 2.53 V |
| 60–66 °C | 365 | 319 counts | 62.3 % | 3.12 V |
| 66–72 °C | 1 352 | 377 counts | 73.6 % | 3.68 V |

The decisive 247 samples have the cores at 68.7 °C and the board at 51.0 °C, and the ITE asks for exactly
what it asks for when everything is cold: 243 counts, 47 %, no sample above 261. `bench/analyze-heat.py`
reproduces these tables from the logs.

Two corrections to what this README said before the fourth run. The 297 counts it listed at 57–60 °C was
not a step the ITE holds — 285–314 counts account for 55 samples out of 4 577, while the four rungs
195–206, 253–264, 315–326 and 373–384 account for 667, 1 120, 321 and 826: the ITE dwells on rungs and
passes through everything else on its way between them.
And the demand does not chase the board at the same speed in both directions. In the fourth run the board
crossed 55 °C and the demand took **about 75 s** to reach its plateau, while on the way back it went
381 → 242 counts **within 30 s** of the board falling back through the same knee. The follower's 15 s tau
sits well inside both, so it filters the ITE's cycling without fighting its response.

**It is not an integrator: 20 minutes with the board held hot does not make the duty climb.** The theory
worth killing was that the ITE raises its duty for as long as the temperature refuses to fall — that it
integrates dwell time, and maybe accelerates past some threshold. The earlier runs could not touch it,
because in all of them the temperature was moving while the demand was being measured. The fifth run is
built for the question: a 300 s four‑core ramp to push the board past the knee, then **1200 s at a lighter
two‑core load** so the board sits still, then 300 s left alone. The board settled at 68.5–69 °C and stayed
there for sixteen flat minutes with the cores at 84–86 °C, and the demand sat at **378 counts** — the same
6/8 rung the fourth run found at the same board temperature, repeatable to 2 counts.

![held hot and flat for 20 minutes, and the same temperature reached quickly against reached and held](docs/bench/07-ite-hold-test.svg)

Three independent reads, all saying the same thing (`bench/analyze-hold.py`):

- Across the 16 windows where the board held within 0.8 °C of its plateau, the demand trended
  **+0.6 counts per minute** — and the board's own +0.07 °C/min drift already explains +1.5 counts per
  minute at the ladder's 20 counts per °C. Nothing is left over for time to explain.
- The same board temperature reached quickly against reached and held: at 63–66 °C, 342 counts on the ramp
  against **319** in the hold; at 66–69 °C, 378 against **368**. Later is *lower*, not higher.
- Fitting the 1 513 samples above the knee on board temperature **and** seconds since the knee was crossed:
  temperature alone gives R² 0.669, adding time gives 0.670 with a coefficient of **−0.00 counts per
  minute**. Time does not earn its place in the model.

What the run found instead is the opposite of a ratchet: held steady, **the ITE stops hunting**. Early in
the hold the reading swung 318–380 counts, dipping to the rung below; by the end the dips had shrunk to
346–381 and the mode was 379 throughout. And the ramp's overshoot — 342 counts at 63–66 °C on the way up
against 319 counts at the same temperature in the hold — says the ITE answers how *fast* the board is
moving as well as where it is, which is the same asymmetry the fourth run measured as 75 s to climb and
30 s to release. For the build this is a simplification: `DEMAND_TAU_S` does not have to outwait a
controller that ramps on a timer, because this one does not.

**The demand has a floor, and it is not near zero.** With the fans at maximum the package sat at 32–36 °C
for twelve minutes — 21 °C below the plateau the first temperature run had been stuck at — and the duty
did not follow it down: 196–260 counts, median 239, and not one sample of 717 below 100 counts. The floor
is 46–48 % duty, 2.33 V on the PWM wire, and it holds from the coldest measured board to a PCH of about
54 °C — 1 946 samples of it. So the fan this board drives never stops: `FAN_DUTY_MIN` is a clamp against a
broken sense wire rather than something the ITE ever reaches, and a fan that is always turning is a fan
whose tach claim is always plausible.

The fan also sits **inside** the ITE's loop — the fan cools the board, the ITE reads the board, the ITE
changes the demand — which is an enclosure requirement rather than a firmware one: air has to move across
the board and the ITE's own ambient sensor (the BIOS screen's "motherboard ambient", 40 °C against a CPU
at 58 °C), not only over the heatsink. The ITE will sit at its floor quite happily while the cores are at
73 °C.

**The demand is stepped, and the ladder holds across five runs.** The dwell levels are 198, 257, 320 and
380 counts, spaced 59–63, held for 667, 1 120, 321 and 826 samples of 4 577, and the hottest samples reach
434 — close to the fifth rung the spacing predicts, 441. A straight line through the four is counts = 15 + 61·k for k = 3, 4, 5, 6, so the step
is 11.9 duty points and 0.595 V on the wire: a binary duty quantum of 1/8, with the ITE sitting on 3/8 when
the board is cold and reaching 6/8 or 7/8 when it is hot. Read as 605 counts the step is 10.1 points and
matches nothing, which is one more reason the 10 kΩ / 10 kΩ divider is the right one. The cycling is fast —
535 of 716 seconds moved by more than 3 counts, one dwell switching to the other in 1–3 s — so the follower
filters it (tau 15 s, 1.5 duty point deadband) instead of pumping the fan at 0.3 Hz while the machine's own
thermal time constant is minutes. The cycle is the ITE closing its loop through the fan: it asks for more
duty, the board cools, it asks for less.

**The divider is settled: two 10 kΩ.** The tap is half the PWM line, so on the Uno 512 counts is 100 %
duty and every count in `bench/data/` reads on that scale. In volts, which is what a meter should agree
with: the ITE's four dwell levels — 198, 257, 320 and 380 counts — are **0.97 V, 1.26 V, 1.56 V and 1.86 V
at A0**, i.e. **1.94 V, 2.51 V, 3.13 V and 3.71 V average on the PWM wire**. That also argues for changing
the board's divider from 4.7 kΩ + 2.2 kΩ over 10 kΩ to 10 kΩ / 10 kΩ: 2.50 V on the tap instead of 2.96 V,
0.8 V of headroom on a 3.3 V part instead of 0.34 V, one fewer resistor, and bench and board reading the
same scale.

**One thing the bench still has to settle: the top of the PWM swing.** The four dwell levels now pin it
down without a scope. Extrapolated, the ladder reaches 15 counts (0.14 V) at zero duty and **502 counts
(4.90 V) at 8/8** — so the ITE's top is nearer 4.9 V than the 5.5 V the fan header's own supply would
suggest, and 100 % lands within 2 % of 512 counts rather than at 1009. Two things are still unexplained and
a meter settles both in one sitting: why the ladder has a 15‑count offset at zero (the ITE's output, or the
reading), and whether the top is flat or droops under load at the top dwell. The procedure is in `BUILD.md`.

## Bench order that carries over to any build

1. Identify the four NUC fan‑header wires with a meter — Intel publishes no pinout.
2. Set a buck module to 12.0 V with a meter before it is wired in and confirm its current limit is
   released; confirm 3.3 V at the regulator before it ever reaches a Pro Mini.
3. Find the fan's stall duty and measure its RPM at two duties. On the perfboard the stall is already
   bracketed: 20 % delivers ~2.4 V and will not start the fan, 30 % does.
4. Read the tach output with a frequency counter — it must equal `rpm / 30` Hz exactly, it is a hardware
   timer.
5. Wire the tach side first, then the PWM wire, then the fans.

**Three things that break hardware:** a 12 V fan's tach or PWM wire spliced into the NUC header
(that fan pulls those lines to its own 12 V internally), a 5 V FTDI on a 3.3 V Pro Mini
(ATmega328P absolute maximum on any pin is VCC + 0.5 V), and a BC547 fitted in the onsemi
**C‑B‑E** order when the footprint you are using is drawn for the NXP/Philips **E‑B‑C** order — meter
the two of them before they go in, `BUILD.md` says how. Flash with Board → *Arduino Pro or Pro
Mini*, Processor → **ATmega328 (3.3V, 8MHz)**.

## Reproducing the measurements

From the repo root, against the raw 1 Hz logs in `bench/data/`. Each Uno log is paired with its temperature
capture by a fixed offset in seconds — the Uno log has no timestamps — and these are the offsets the recorded
numbers were produced with:

```sh
# which temperature the ITE's demand follows: the table in *On the bench*
python3 bench/analyze-heat.py \
    bench/data/temp.log    bench/data/stress.log         -4 \
    bench/data/cold.log    bench/data/coldtemp.log        0 \
    bench/data/stress2.log bench/data/stress2-temps.log -15 \
    bench/data/warm.log    bench/data/warm-temps.log    -20 \
    bench/data/hold.log    bench/data/hold-temps.log    -20

# does the ITE integrate the time the board spends hot?
python3 bench/analyze-hold.py bench/data/hold.log bench/data/hold-temps.log -20

# the dwell rungs and the duty quantum
python3 bench/analyze-ladder.py bench/data/loop.log

# the two graphs
python3 bench/plot-curve.py
python3 bench/plot-hold.py bench/data/hold.log bench/data/hold-temps.log -20
```

Re‑run 2026‑10‑23, so this is verified rather than remembered: the five runs pair to 260 + 717 + 660 + 1 140
+ 1 800 = **4 577 samples**, `analyze-heat.py` reproduces the 2 131 / 306 / 251 / 169 / 365 / 1 352 board bins
and both discriminating subsets — 247 samples with the cores at 68.7 °C and the board at 51.0 °C at 243
counts, and 134 samples the other way round at 243 counts — and `analyze-ladder.py` reproduces the −1.1 %
answer to a 5.6× tach claim.

The plotters need matplotlib. The two shipped SVGs were drawn with **3.11.2**, which is not installed on this
machine; the venv that has matplotlib here has 3.10.3. Re‑running a plotter rewrites the tracked SVG with that
version's layout, so revert the change unless redrawing is what you wanted.

The booster's simulation, from `fan-switch-booster/`:

```sh
./sim/run.sh                                    # netlist -> ngspice -> variants -> plots
V=/Users/kaveh/Documents/Projects/schemdraw-mcp-server/.venv/bin/python3
$V sim/variants.py && $V sim/plot.py            # if the default python3 has no matplotlib
```

The board machinery that used to live in `logs/` — `build1l.py`, `layout.py`, `genwires.py`,
`applywires.py`, `verify.py`, `pourcheck.py`, `export.sh` — went with the retired board, and it was already
partly parked: `layout.py` and the wire generators still described the schematic as it was before it was
edited by hand, so running them would have undone work. All of it is at the tag.

One rule `genwires.py` enforced the hard way is worth keeping, because it is true of any KiCad sheet: **a
symbol pin or a name tag only connects to a wire *end***. A net whose wire carries a flag or a tag mid‑span
has to be written as the chain of segments it really is. Written as one straight wire, the flag and the tag
are orphaned and ERC reports them.

## Status

**Built, scoped and listened to:** the perfboard fan‑switch booster in `fan-switch-booster/`. Running at a
100 Hz carrier, quiet across the duty range, with the whole ladder heard.

**Measured and recorded:** the NUC's own fan control — its PWM frequency and amplitude, how it reads the
tach, what drives its demand, where that demand bottoms out and where it tops out, and that it does not
integrate the time the board spends hot. See *On the bench*; `BUILD.md` is the bench sequence.

**Retired:** the `nuc-fan-controller` enclosure board, and the archived boards before it. See *The enclosure
board that used to be here*.

**Open items:**

1. a sketch that reads `/DEMAND` on A0 and re‑makes it at the perfboard's own 100 Hz — the two halves
   joined, but the wire between them is not written yet;
2. the fan's exact start threshold, still only bracketed between 20 % and 30 % at 100 Hz, and the start kick
   that would make the bottom of the range usable;
3. `FAN_RPM_MIN`, `FAN_RPM_FULL` and `ADC_AT_100PCT` in `firmware/nuc-tach-modeB` are placeholders, and
   `ITE_READ_GAIN` was measured with an Uno — all four need the same measurement on a 3.3 V Pro Mini;
4. if the enclosure board is ever rebuilt, its divider starts at 10 kΩ / 10 kΩ, not the 4.7 k + 2.2 k over
   10 k the retired schematic still carries.

No license is granted — all rights reserved. It is published so the drawings and the reasoning
behind them are readable.
