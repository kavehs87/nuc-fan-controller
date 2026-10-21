# 12 V fan switched by 3.3 V logic — a gate booster built from my own parts

A KiCad schematic, a real ngspice simulation, and a single-copper-layer PCB you can
etch at home — of the thing every 3D printer needs: **an Arduino pin turning 12 V fans
on and off with a MOSFET.**

Every real component on this sheet is a part that actually sits in my parts cabinets
(`L1` and `R1`). Nothing here is a catalogue placeholder. The fan model is sized to the
fans I actually use: **100 mA each at 12 V.**

```
Arduino D9 (3.3 V PWM)
      |
     R1 1k ---- Q2  2N7002   level shifter: 3.3 V logic pulls /BOOT down to ~0 V
      |                |
     R2 10k          /BOOT ---- Q3  IRF7416 (P-ch)  gate booster: switches +12 V onto the gate
      |                |               |
     GND            R3 10k          R4 1k
                                     |
                                   /GATE ---- Q1  IRFZ44N  the switch that carries the fans
                                     |             |
                                    R5 10k       /DRAIN --- 12 V fan(s) --- +12 V
                                    GND             |
                                                 D1 1N5819 (flyback, cathode to +12 V)
```

Run everything with one command:

```bash
./sim/run.sh
```

It exports the netlist from the schematic, runs ngspice, writes five plots and two
comparison tables, and prints the numbers that matter. Output lands in `sim/out/`
(git-ignored).

---

## The three stages

| net | what it is | who drives it |
|---|---|---|
| `/PWM` | the Arduino pin (D9 = OC1A, timer 1 channel A) | Arduino Pro Mini 3V3 |
| `/LGATE` | 2N7002 gate, held at 3.0 V by the R1/R2 divider | `/PWM` through R1 1k |
| `/BOOT` | booster node: +12 V when the pin is low, ~0 V when it is high | R3 10k up, Q2 down |
| `/HIGATE` | +12 V handed to the power FET by Q3 | Q3 IRF7416 |
| `/GATE` | IRFZ44N gate, settles at **10.91 V** | R4 1k from `/HIGATE`, pulled down by R5 10k |
| `/DRAIN` | the switching node under the fan(s) | Q1 IRFZ44N, clamped by D1 |
| `/FAN_W` | between a fan's winding and its drag resistance | fan model L1 + R6 |

**Why `/GATE` is 10.9 V and not 12 V.** A MOSFET gate draws no steady current, so R4 and
R5 are simply a divider: 12 V × 10 k / (1 k + 10 k) = 10.91 V. That is still deep inside the
region where the IRFZ44N's 17.5 mΩ is specified. R5 exists to keep the gate firmly at 0 V
when the pin is low, so the fan cannot drift on.

**Why the logic is not inverted.** Two inversions (Q2 inverts, Q3's P-channel orientation
inverts again) cancel. Pin high → fan on. At power-up the pin is floating, R2 keeps Q2 off,
so Q3 is off, so Q1 is off. The fans stay off.

**Why Q3's source must be the +12 V terminal.** A P-channel device's body diode conducts
drain → source. Wire Q3 the other way round and that diode feeds +12 V straight into
Q1's gate through R4 — the fans would be permanently on and no amount of code would fix it.
This is the single easiest way to get this circuit wrong, so the sheet draws Q3 rotated
180° with its source on the rail.

---

## Parts — all from my cabinets

| ref | part | package | cabinet · drawer | qty in bin |
|---|---|---|---|---|
| U1 | Arduino Pro Mini (3.3 V / 8 MHz, ATmega328P) | — | L1 · C5 | 1 |
| Q1 | IRFZ44N N-channel power MOSFET | TO-220 | R1 · B4 | 12 |
| Q2 | 2N7002 N-channel MOSFET | SOT-23 | R1 · A4 | 11 |
| Q3 | IRF7416 P-channel MOSFET | SO-8 | R1 · A4 | 6 (+1 already on a breakout board) |
| D1 | 1N5819 Schottky, 40 V / 1 A | DO-41 | L1 · E1 | 30 |
| R1, R4 | 1 kΩ through-hole | axial | R1 · A2 | 20 |
| R2, R3, R5 | 10 kΩ through-hole | axial | R1 · B2 | 20 |
| V1 | Switching Power Supply Module, 12 V 450 mA | module | L1 · B7 | 2 |

Four items on the sheet are **not** bin parts and are marked as such on the drawing:

- **C1 = 1.5 nF** — the IRFZ44N's own input capacitance (Ciss ≈ 1489 pF), drawn explicitly.
- **C2 = 1.7 nF** — the IRF7416's Ciss (≈ 1700 pF), drawn explicitly.
- **L1 = 10 mH + R6 = 120 Ω** — the fan. My bins hold no 12 V fan, so the fan is a model: an
  inductor for the winding and a resistor for the mechanical load. 12 V / 120 Ω = **100 mA**,
  which is what my real fans draw. Change R6 if yours are different: 80 Ω models a 150 mA fan.
- The KiCad symbol for U1 is `MCU_Module:Arduino_Nano_v2.x` because the library has no Pro
  Mini symbol; it is the same ATmega328P pinout, and D9 is pin 12 = OC1A. U1 is excluded
  from the simulation and `V2` (a VPULSE source) stands in for the pin.

---

## Why one transistor is not enough

This is the actual lesson. `sim/variants.py` runs the *same fan, same diode, same resistors*
against every drive option the bin allows:

| variant | pin | gate | fan | V(drain) | state | Rds(on) | in the FET |
|---|---|---|---|---|---|---|---|
| **booster-3v3** (this sheet) | 3.3 V | 10.91 V | 102.3 mA | 1.6 mV | ohmic | 15.7 mΩ | **0.16 mW** |
| booster-3v3-wc (Vgs(th) = 4.0 V unit) | 3.3 V | 10.91 V | 102.3 mA | 1.6 mV | ohmic | 15.5 mΩ | 0.16 mW |
| direct-3v3 (one transistor) | 3.3 V | 3.00 V | 99.6 mA | 51.9 mV | ohmic | 521 mΩ | 5.17 mW |
| **direct-3v3-wc** (worst-case unit) | 3.3 V | 3.00 V | **0 mA** | 12.0 V | **off** | — | 0 |
| direct-5v (if you use the 5 V Pro Mini) | 5.0 V | 4.54 V | 100.0 mA | 5.7 mV | ohmic | 56.6 mΩ | 0.57 mW |
| 2n7002-only (2N7002 as the pass element) | 3.3 V | 3.00 V | 52.0 mA | 5.76 V | saturated | — | **300 mW** |

Read the two bold rows:

- **The IRFZ44N is not a logic-level part.** Its Rds(on) is specified at Vgs = 10 V, and its
  threshold is guaranteed anywhere between 2.0 V and 4.0 V. Wired straight to a 3.3 V pin the
  gate only reaches 3.0 V (R1 1k and R5 10k form a divider). A *typical* unit still runs the
  fan — which is exactly why "it worked on my bench" is not a design — but it wastes 32× more
  power, and a *worst-case* unit from the same drawer never turns on at all. The booster makes
  both units behave identically.
- **The 2N7002 cannot be the switch.** At Vgs = 3.0 V it saturates at 52 mA, starves a 100 mA
  fan, drops 5.76 V across itself and burns 300 mW against a 200 mW rating. It is a level
  shifter here, nothing else.

---

## Measured by the simulation

```
pin voltage where the fan starts                :  2.27 V
/BOOT when the pin is high (2N7002 sinks 1.2 mA):  11.6 mV
/GATE steady state (12 V x R5/(R4+R5))          :  10.91 V
fan current with the power FET on               :  102.3 mA
V(drain) with the power FET on                  :   1.6 mV
Rds(on) at that point                           :  15.7 mΩ
power FET dissipation while on                  :  0.16 mW
V(drain) spike at turn-off (clamped by D1)      : 12.36 V
Arduino pin current (max)                       :  0.30 mA
/GATE rise 5 tau (R4=1k, C1=1.5n)               :   7.5 µs
/BOOT rise 5 tau (R3=10k, C2=1.7n)              :  85.0 µs
/BOOT back at 12 V after the pin goes low       : 120.6 µs
fan L/R time constant                           :  83.3 µs
peak fan current during a PWM on-time           :  99.8 mA
average fan current at 1 kHz / 50 % duty        :  54.2 mA
```

A few of those deserve a comment:

- **The pin only ever sources 0.30 mA** — that is 3.3 V / (R1 + R2). Charging the power
  MOSFET's 1.5 nF gate, which would be a 3 mA hammering if you connected the pin to it
  directly, is the booster's job. This is the whole point of the two extra transistors.
- **12.36 V at turn-off.** When Q1 opens, the fan's winding has ~100 mA flowing through it and
  that current has to go somewhere. The 1N5819 takes over and holds the node at
  12 V + 0.36 V. Without D1 the node would fly to whatever voltage is needed to force that
  current through the parasitic capacitances — hundreds of volts. Delete D1 in KiCad and look
  at the transient; it is the most instructive ten seconds of this project.
- **The fan current is chopped, not dimmed.** With 10 mH and 120 Ω the fan's time constant is
  83 µs, so at 1 kHz it never reaches steady state: it ramps to ~100 mA and decays to zero
  every cycle. The *average* is 54 mA. The fan always sees either a full 12 V or 0 V — that is
  how PWM speed control works. At Klipper's default 100 Hz the effect is the same but with
  5 ms pulses.
- **Turn-off is slower than turn-on.** `/BOOT` has to charge the IRF7416's 1.7 nF back up to
  12 V through R3 10 kΩ: τ = 17 µs, and the fan stays on for ~55 µs after the pin goes low. At
  100 Hz that is irrelevant. If you drive the fan at several kHz, drop R3 to 1 kΩ (τ = 1.7 µs);
  the 2N7002 then sinks 12 mA, which is well inside its 115 mA rating.

---

## How many fans one output can carry

`sim/fan_count.py` clones the sheet's fan branch as many times as you ask and re-runs both
analyses. The gate drive does not change at all — the fans are on the *drain* side — so the
only things to check are the parts that carry load current: Q1, D1 and the 12 V supply.

```bash
python3 sim/fan_count.py                                   # 1..4 fans, the 450 mA bin module
python3 sim/fan_count.py --fans 1 2 4 8 16 32 64 --supply-ma 8000
```

| fans | each | total | V(drain) | Q1 loss | spike | D1 peak | D1 avg | D1 loss | supply avg | supply peak |
|---|---|---|---|---|---|---|---|---|---|---|
| 1 | 102.3 mA | 102.3 mA | 1.6 mV | 0.16 mW | 12.36 V | 99 mA | 8 mA | 2.5 mW | 48 mA | 102 mA |
| 2 | 101.1 mA | 202.2 mA | 3.2 mV | 0.65 mW | 12.38 V | 197 mA | 15 mA | 5.3 mW | 94 mA | 202 mA |
| **3** | **100.7 mA** | **302.2 mA** | **4.8 mV** | **1.46 mW** | **12.40 V** | **295 mA** | **22 mA** | **8.2 mW** | **141 mA** | **301 mA** |
| 4 | 100.5 mA | 402.1 mA | 6.4 mV | 2.59 mW | 12.41 V | 392 mA | 30 mA | 11.2 mW | 187 mA | 401 mA |

**Three fans fit, with room to spare.** What the numbers say:

- **Q1 is not remotely stressed.** Three fans put 302 mA through it and it drops 4.8 mV:
  1.5 mW. The IRFZ44N is a 49 A / 94 W TO-220 part; it could switch twenty of these fans.
  Its gate drive is unchanged, because gate current is set by R4 and the gate capacitance,
  not by the load.
- **D1 is the part that actually feels the extra fans.** At turn-off all 295 mA of fan current
  commutates into the 1N5819. Its rating is 1 A average; it averages 22 mA here and peaks at
  295 mA, dissipating 8 mW. Four fans (392 mA peak) are still fine. The diode only ever has to
  carry the *total* fan current, so add diode current, not diode count.
- **The 12 V supply is the real limit.** Three fans at full speed draw 301 mA from the
  Switching Power Supply Module in L1 · B7, which is rated 450 mA — that works. Four fans draw
  401 mA, which technically fits but leaves almost nothing for the electronics. If your fans
  are the 150 mA kind instead, three of them need 452 mA and **that module is too small**;
  use the 5 V module's bigger sibling, a USB-C PD source triggered by the IP2721 module in
  L1 · A5, or a proper 12 V brick.
- **Everything shares equally** because the branches are identical, and each fan keeps its own
  83 µs L/R — the current waveforms just scale by three, they do not change shape.

Wiring three fans on one output also means one flyback diode serves all three, and one
blown fan stalls the others only mechanically, not electrically.

### With a bigger 12 V supply, the flyback diode becomes the limit

The 450 mA module in L1 · B7 is what makes "three fans" the answer above. Fed from a real
12 V brick (8 A, which is what this build actually uses), the same sheet and the same three
transistors scale a long way:

| fans | total | V(drain) | Q1 loss | Q1 rise | spike | **D1 peak** | D1 avg | D1 loss | supply peak |
|---|---|---|---|---|---|---|---|---|---|
| 1 | 102 mA | 1.6 mV | 0.16 mW | +0.0 °C | 12.36 V | 99 mA | 8 mA | 2.5 mW | 102 mA |
| 4 | 402 mA | 6.4 mV | 2.6 mW | +0.2 °C | 12.41 V | 392 mA | 30 mA | 11 mW | 402 mA |
| 8 | 801 mA | 12.9 mV | 10.3 mW | +0.6 °C | 12.45 V | 779 mA | 58 mA | 24 mW | 800 mA |
| 16 | 1.60 A | 25.7 mV | 41 mW | +2.5 °C | 12.51 V | 1.53 A | 104 mA | 47 mW | 1.60 A |
| 32 | 3.19 A | 51.4 mV | 164 mW | +10 °C | 12.60 V | 2.99 A | 201 mA | 102 mW | 3.18 A |
| 64 | 6.35 A | 102 mV | 650 mW | +40 °C | 12.77 V | 5.93 A | 399 mA | 242 mW | 6.34 A |

`Q1 rise` is the junction temperature rise in free air, using the TO-220's
62 °C/W junction-to-ambient rating with no heatsink.

Read the two right-hand columns carefully, because a diode has three different ratings and
only two of them apply here:

- **Q1 is never the problem.** Sixty-four fans put 6.35 A through it and it dissipates 0.65 W,
  which is a 40 °C rise — the part is rated to 150 °C junction and 49 A continuous. The MOSFET
  is good for roughly eighty of these fans with no heatsink at all.
- **D1's average current and dissipation stay comfortable** even at 64 fans: 399 mA average and
  0.24 W in a DO-41 Schottky. That is not what limits it.
- **What limits D1 is the repetitive peak.** At turn-off the *entire* fan current commutates
  through the diode every single cycle. Eight fans already push 779 mA through a 1 A part;
  sixteen push 1.53 A. The datasheet's 45 A surge figure is for a *single* pulse, not for
  1000 pulses a second, so treat the peak as the working limit.

So the practical ladder, using only parts already in **L1 · E1**:

| fans | what to change |
|---|---|
| up to ~8 | nothing — the sheet is exactly right as drawn |
| ~9 to ~30 | replace D1 with the **1N5822** (3 A, same DO-41 package, same drawer) |
| ~30 to ~60 | a proper TO-220 Schottky (MBR1045 class), or two 1N5822 in parallel |
| beyond | Q1 starts wanting a heatsink around 8 A, and the wiring matters more than the semiconductors |

The turn-off spike creeps up with load — 12.36 V at one fan, 12.77 V at sixty-four — simply
because the Schottky's forward drop grows with current. Still nowhere near the IRFZ44N's 55 V
or the IRF7416's 30 V.

And the honest caveat, again: this fan model always limits itself to 100 mA. Real fans draw a
surge when they start, and a stalled fan draws amps. Sixteen fans all starting on the same PWM
edge can momentarily ask for 3–5 A, which an 8 A supply absorbs and a 450 mA module does not.

---

## The plots

`sim/run.sh` writes these to `sim/out/`:

| file | what it shows |
|---|---|
| `dc_transfer.png` | sweeping the pin 0 → 3.3 V: `/BOOT` falls from 12 V to 12 mV while `/GATE` jumps from 0 to 10.9 V, and the fan starts at 2.27 V |
| `transient.png` | 1 kHz / 50 % PWM: all four node voltages, the fan current, and the 0.3 mA the pin actually supplies |
| `switching_edge.png` | one turn-on edge (gate charging through R4) and one turn-off edge (the 12.36 V clamp and the freewheeling decay) |
| `drive_compare.png` | the variant table above as a chart: fan current and dissipation for each drive option |
| `fan_count.png` | fan counts side by side, and the current the flyback diode carries at the largest count |

---

## Running it

```bash
./sim/run.sh              # export -> ngspice -> plots -> variant and fan-count tables
```

Requirements: KiCad 9 or 10 (`kicad-cli`), `ngspice`, Python 3 with `numpy` and `matplotlib`.

Files:

```
mosfet-fan-switch.kicad_sch     the sheet (A3, ERC clean: 0 errors / 0 warnings)
mosfet-fan-switch.kicad_pcb     the board (generated; 56 x 44 mm, one copper layer, DRC clean)
pcb/build_board.py              the board generator: part table, track list, design rules
pcb/drc.txt                     the current DRC report
pcb/gerber/  pcb/drill/         Gerbers and Excellon drill file + map
docs/mosfet-fan-switch.pdf      the sheet as a PDF
docs/pcb-notes.md               board rules, pad-to-net table, etch and assembly notes
docs/pcb-etch-bottom.svg/.pdf   the print for toner transfer (1:1, mirrored)
docs/pcb-assembly-top.pdf       component-side assembly view
sim/run.sh                      the whole pipeline
sim/prepare_deck.py             KiCad export -> runnable ngspice deck
sim/variants.py                 the six-drive comparison
sim/fan_count.py                how many fans one output carries, checked against part ratings
sim/plot.py                     plots + printed summary
sim/models/irfz44n.lib          level-1 fit of the IRFZ44N in my bin
sim/models/irfz44n_wc.lib       the same part at the datasheet's worst-case threshold
sim/models/2n7002.lib           level-1 fit of the 2N7002
sim/models/irf7416.lib          level-1 fit of the IRF7416
sim/models/schottky.lib         1N5819 as a sub-circuit (explicit K/A terminals)
archive/                        the first version of this project (single 5 V-driven IRLZ44N)
```

You can also run the simulation inside KiCad: **Simulator → Run Simulator**. The sheet carries
`.op`, `.dc V2 0 3.3 0.01` and `.tran 1u 5m` cards as text, and Q1/Q2/Q3/D1 point at the
`.lib` files through their `Sim.Library` / `Sim.Name` fields, so KiCad's built-in ngspice picks
the real models up.

### Things to try in KiCad

- Run the DC sweep and watch `/BOOT` fall while `/GATE` rises. That step *is* the booster.
- Delete Q2, Q3, R3, R4 and C2, wire R1 straight to `/GATE`, re-run: the fan still runs
  (100 mA) but Q1 now burns 5.2 mW. Then change Q1's `Sim.Name` to `irfz44n_wc`: dead fan.
  Same drawer, same part number, different transistor.
- Copy the `L1 / R6` fan branch twice, tie all three drains to `/DRAIN`, and re-run the
  transient: that is the three-fan case above, drawn.
- Shorten R3 to 1 kΩ and watch the turn-off delay shrink.
- Remove D1 and look at the `/DRAIN` spike.
- Change V2's `tw` from `500u` to `250u` (25 % duty): the average fan current falls, but the
  pulses the fans see are still a full 12 V.

---

## About the models — read this before quoting the numbers

The five `.lib` files are **level-1 fits to the spec records in my own parts cabinet**, not
vendor models. Each one is calibrated on the two numbers I actually recorded for the part:

| part | cabinet record | fit |
|---|---|---|
| IRFZ44N | Vgs(th) 2.0–4.0 V, Rds(on) ≤ 0.0175 Ω at Vgs = 10 V, 55 V / 49 A / 94 W | `vto=2.8 kp=11.11 rd=5m` → 17 mΩ at 10 V |
| IRFZ44N (worst case) | same bin, threshold at the datasheet maximum | `vto=4.0 kp=13.33 rd=5m` → 17.5 mΩ at 10 V |
| 2N7002 | Vgs(th) ≤ 2.5 V, Rds(on) ≤ 1.2 Ω at Vgs = 10 V, Id max 115 mA, 0.2 W | `vto=2.0 kp=0.104` → 1.2 Ω at 10 V |
| IRF7416 | Vgs(th) −2 V, Rds(on) ≤ 0.025 Ω at Vgs = −10 V, 30 V / 10 A, 2.5 W | `vto=-2.0 kp=5.0` → 25 mΩ at −10 V |
| 1N5819 | 40 V / 1 A Schottky | `is=1e-7 rs=0.05` → 0.36 V at 100 mA |

What a level-1 model gets right, and what this circuit depends on: the threshold voltage, the
on-resistance at a properly driven gate, and the fact that at Vgs = 3 V the 2N7002 is
comfortably on while the IRFZ44N is barely on at all.

What it gets wrong, honestly:

- **No subthreshold region.** `direct-3v3-wc` reports exactly 0 mA. A real worst-case unit
  would trickle some milliamps. The point of the row is "not usable", not "literally zero".
- **Level-1's transconductance is too linear at low Vgs**, so its Rds(on) at Vgs = 3 V is a
  rough guess. The datasheet curves are steeper.
- **The gate capacitances are drawn on the sheet as C1 and C2** rather than being inside the
  models, so the RC timing is visible and auditable. The models themselves carry no
  capacitance, otherwise Ciss would be counted twice.
- **The fan is a model, not a measurement.** A real 12 V fan has back-EMF that dominates its
  behaviour; `10 mH + 120 Ω` reproduces the electrical lesson (the winding current that makes
  the flyback diode necessary) and the right steady current, but not the aerodynamics. It also
  cannot show a stalled fan: a real stalled 12 V fan draws amps through its few-ohm winding,
  whereas this model always limits itself to 100 mA. The IRFZ44N and the 1N5819 are both rated
  far above any stall current a small fan can pull, so the design is safe even where the model
  is blind.

---

## KiCad → SPICE gotchas that cost time

Kept here so the next schematic is faster:

- A `Sim.Library` file that does not exist makes KiCad export a **broken device card**
  (`Q1 Q1.irfz44n` with no nodes at all) instead of `MQ1 /DRAIN /GATE GND GND irfz44n`.
  Write the `.lib` files before exporting.
- `Simulation_SPICE:NMOS` has three pins, so KiCad hands ngspice a dangling bulk node
  (`NC-Q2-0`). `sim/prepare_deck.py` ties it to the source. `NMOS_Substrate` /
  `PMOS_Substrate` avoid the problem entirely.
- A VPULSE source needs instance-level `Sim.Device=V`, `Sim.Type=PULSE`, `Sim.Pins=1=+ 2=-` and
  a `Value` of `VPULSE`. Otherwise the export writes `V2 /PWM GND dc="3.3V PWM" y1=0 ...` which
  ngspice cannot parse.
- KiCad writes schematic text directives **before** the device lines, so a
  `.control … .endcontrol` card on the sheet breaks ngspice. The sheet carries classic
  `.op` / `.dc` / `.tran` / `.print` cards; `prepare_deck.py` replaces them with a `.control`
  block at the end so `wrdata` can dump plottable vectors.
- Multi-line `(text "...")` blocks in a `.kicad_sch` must contain escaped `\n`. Raw newlines
  parse for ERC but make `kicad-cli sch export pdf` fail with "Failed to load schematic".
- Scripted wires need an explicit `(junction …)` at every T-junction or ERC reports
  "Unconnected wire endpoint". Crossings without a junction stay unconnected — the `BOOT` rail
  crossing Q3's source wire is one of those on purpose.
- `wrdata` repeats the x column before every vector, so the value columns are 1, 3, 5, …
- ERC checks ignored by KiCad's default settings here: "SPICE model issue" and "Assigned
  footprint doesn't match footprint filters" (the 4-pin substrate symbols do not match 8-pin
  MOSFET footprint filters, which is fine for a learning sheet).

---

## The board

`pcb/build_board.py` writes the layout. It is a generator rather than a hand-drawn board:
the part table, the track list and the design rules are the source, and the `.kicad_pcb`
is the output — so a placement change is an edit to a table, not an afternoon of dragging.

```bash
python3 pcb/build_board.py
kicad-cli pcb drc --output pcb/drc.txt --severity-all mosfet-fan-switch.kicad_pcb
```

**56 × 44 mm, one copper layer (B.Cu), zero vias, DRC clean** — `Found 0 violations`,
`Found 0 unconnected items` — against the rules a home-etched board actually needs, not
the fab defaults KiCad ships with:

| | |
|---|---|
| clearance between nets | **0.50 mm** |
| signal tracks | **0.80 mm** (34 segments) |
| `/GND` bus along the top edge | 2.0 mm · `/P12V` bus along the bottom edge 3.0 mm |
| `/GND` return lane down the left edge | 1.5 mm · the `/DRAIN` runs to the fans 1.5 mm |
| drills | 0.8 mm ×14, 1.0 mm ×10, 1.1 mm ×5, 3.2 mm ×4 (M3 mounting holes) |

Everything lives on one side. Q2 (SOT-23) and Q3 (SO-8) are the only surface-mount parts
and they sit on the **copper side**, which is exactly what removes the need for a via
anywhere: 2 SMD parts, 1 TO-220, 1 SOT-23… 14 electrical parts, 4 mounting holes, one
layer. The board is planar — the generator checks every net pair for crossings and prints
`no net crossings - the board is planar, no jumpers needed`, so the 0 Ω jumper trick was
never needed.

The layout follows the signal: +12 V and the PWM line come in at the bottom left (J1, J2),
the level shifter sits mid-left, the booster in the middle, the power FET on the right, the
three fans out through a 2×03 header, and the two buses hug the top and bottom edges.

**Read this before building it:** the schematic's MOSFET symbols number their pins
**D-G-S**, because that is the order ngspice wants. The real packages are not that way
round — SOT-23 is 1 gate / 2 source / 3 drain, the IRF7416 SO-8 is 1-3 source / 4 gate /
5-8 drain, and the IRFZ44N TO-220 is 1 gate / 2 drain / 3 source. The board is wired to the
**packages**, and the sheet now carries that pinout as a note block so the drawing and the
copper agree. `docs/pcb-notes.md` has the full pad-to-net table.

| file | what it is for |
|---|---|
| `docs/pcb-etch-bottom.svg` | the toner-transfer print: page is exactly the board size, mirrored, 1:1, black = copper |
| `docs/pcb-etch-bottom.pdf` | the same artwork on A4 (print at 100 %, do not scale to fit) |
| `docs/pcb-assembly-top.pdf` | component-side view: labels, outlines, pads |
| `docs/pcb-render-top.png`, `docs/pcb-render-bottom.png` | 3D renders of both sides |
| `pcb/gerber/`, `pcb/drill/` | Gerbers (`B.Cu`, `B.Mask`, `B.SilkS`, `Edge.Cuts`) and the Excellon drill file + map |
| `docs/pcb-notes.md` | design rules, courtyard boxes, pad→net table, drill list, etch and assembly instructions |

The generator's comments and the end of `docs/pcb-notes.md` record the KiCad 10 behaviour
that had to be pinned down before the DRC would go clean: **a footprint's placement rotation
rotates pad *positions* only — a pad's copper rotates only by that pad's own angle**, so a
hand-written rotated SO-8 has overlapping pads until the angle is baked into each pad;
**track ends are round**, so a 2 mm bus bulges 1 mm past its endpoint and can short a pad
1.27 mm away; and **text angles in the file are board-absolute**, not relative to the
footprint.

---

## Building it for real

- Q1 does not need a heatsink: at 100 mA it dissipates 0.16 mW, at 300 mA (three fans) 1.5 mW.
  What the TO-220 and the 17.5 mΩ are for is a stalled fan or a shorted output, where several
  amps flow.
- The 12 V supply decides the fan count. The module in the bin (L1 · B7) is rated 450 mA:
  comfortable for three 100 mA fans, tight for four, not enough for three 150 mA fans. This
  build runs from an **8 A 12 V brick**, which moves the limit to the flyback diode — see the
  ladder in *With a bigger 12 V supply* above.
- Q3's SO-8 package is the awkward one. There is one IRF7416 already mounted on a breakout
  board in R1 · A4 — use that for the first build.
- Keep R4 (1 k) in series with Q1's gate. It slows the edge just enough to keep switching noise
  down and limits the current Q3 has to source when charging 1.5 nF.
- Keep R5 (10 k) from gate to ground. Without it a floating gate can sit at any voltage and the
  fans can half-turn-on while the Arduino is resetting.
- Wire multiple fans in parallel **on the drain side**, all meeting at `/DRAIN`, with the one
  1N5819 from `/DRAIN` to `+12 V`. Keep each fan's wiring short and equal so no single cable
  carries the sum of the switching edges.
- If you drive this from Klipper, the pin needs to be a hardware PWM pin and Klipper wants an
  inverted PWM output for a low-side switch that turns on with a high pin:

  ```ini
  [heater_fan fan]
  pin: !PH6
  pwm_cycle_time: 0.010
  max_power: 1.0
  heater_temp: 45.0
  fan_speed: 0.6
  ```

  `pwm_cycle_time: 0.010` is 100 Hz — well above the ~60 µs turn-off delay of this driver, so
  the delays are invisible. Do not use a plain `[fan]` section: a `[heater_fan]` only runs the
  fan while the heater is active, which is what you want on a printer. Klipper drives one fan
  per pin, so three fans on one output means wiring them together in parallel — which is exactly
  the case `sim/fan_count.py` just measured.

---

## Archive

`archive/` keeps the first version of this project: a single logic-level IRLZ44N driven
directly at 5 V, plus its placeholder models and its plots. It is kept because the reason it
worked (a logic-level part, a 5 V pin) is exactly the reason the 3.3 V version does not.
