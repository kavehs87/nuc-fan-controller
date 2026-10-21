# 12 V fan switched by 3.3 V logic — a gate booster built from my own parts

A KiCad schematic plus a real ngspice simulation of the thing every 3D printer needs:
**an Arduino pin turning a 12 V fan on and off with a MOSFET.**

Every real component on this sheet is a part that actually sits in my parts cabinets
(`L1` and `R1`). Nothing here is a catalogue placeholder.

```
Arduino D9 (3.3 V PWM)
      |
     R1 1k ---- Q2  2N7002   level shifter: 3.3 V logic pulls /BOOT down to ~0 V
      |                |
     R2 10k          /BOOT ---- Q3  IRF7416 (P-ch)  gate booster: switches +12 V onto the gate
      |                |               |
     GND            R3 10k          R4 1k
                                     |
                                   /GATE ---- Q1  IRFZ44N  the switch that carries the fan
                                     |             |
                                    R5 10k       /DRAIN --- 12 V fan --- +12 V
                                    GND             |
                                                 D1 1N5819 (flyback, cathode to +12 V)
```

Run everything with one command:

```bash
./sim/run.sh
```

It exports the netlist from the schematic, runs ngspice, writes four plots and a
variant-comparison table, and prints the numbers that matter. Plots and raw data land
in `sim/out/` (git-ignored).

---

## The three stages

| net | what it is | who drives it |
|---|---|---|
| `/PWM` | the Arduino pin (D9 = OC1A, timer 1 channel A) | Arduino Pro Mini 3V3 |
| `/LGATE` | 2N7002 gate, held at 3.0 V by the R1/R2 divider | `/PWM` through R1 1k |
| `/BOOT` | booster node: +12 V when the pin is low, ~0 V when it is high | R3 10k up, Q2 down |
| `/HIGATE` | +12 V handed to the power FET by Q3 | Q3 IRF7416 |
| `/GATE` | IRFZ44N gate, settles at **10.91 V** | R4 1k from `/HIGATE`, pulled down by R5 10k |
| `/DRAIN` | the switching node under the fan | Q1 IRFZ44N, clamped by D1 |
| `/FAN_W` | between the fan's winding and its drag resistance | fan model L1 + R6 |

**Why `/GATE` is 10.9 V and not 12 V.** A MOSFET gate draws no steady current, so R4 and
R5 are simply a divider: 12 V × 10 k / (1 k + 10 k) = 10.91 V. That is still deep inside
the region where the IRFZ44N's 17.5 mΩ is specified. R5 exists to keep the gate firmly at
0 V when the pin is low, so the fan cannot drift on.

**Why the logic is not inverted.** Two inversions (Q2 inverts, Q3's P-channel orientation
inverts again) cancel. Pin high → fan on. At power-up the pin is floating, R2 keeps Q2 off,
so Q3 is off, so Q1 is off. The fan stays off.

**Why Q3's source must be the +12 V terminal.** A P-channel device's body diode conducts
drain → source. Wire Q3 the other way round and that diode feeds +12 V straight into
Q1's gate through R4 — the fan would be permanently on and no amount of code would fix it.
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
- **L1 = 10 mH + R6 = 80 Ω** — the fan. My bins hold no 12 V fan, so the fan is a model:
  an inductor for the winding and a resistor for the mechanical load.
- The KiCad symbol for U1 is `MCU_Module:Arduino_Nano_v2.x` because the library has no Pro
  Mini symbol; it is the same ATmega328P pinout, and D9 is pin 12 = OC1A. U1 is excluded
  from the simulation and `V2` (a VPULSE source) stands in for the pin.

---

## Why one transistor is not enough

This is the actual lesson. `sim/variants.py` runs the *same fan, same diode, same
resistors* against every drive option the bin allows, and the numbers are brutal:

| variant | pin | gate | fan | V(drain) | state | Rds(on) | in the FET |
|---|---|---|---|---|---|---|---|
| **booster-3v3** (this sheet) | 3.3 V | 10.91 V | 152.3 mA | 2.4 mV | ohmic | 15.9 mΩ | **0.37 mW** |
| booster-3v3-wc (Vgs(th) = 4.0 V unit) | 3.3 V | 10.91 V | 152.3 mA | 2.4 mV | ohmic | 15.6 mΩ | 0.36 mW |
| direct-3v3 (one transistor) | 3.3 V | 3.00 V | 148.9 mA | 85.9 mV | ohmic | 577 mΩ | 12.8 mW |
| **direct-3v3-wc** (worst-case unit) | 3.3 V | 3.00 V | **0 mA** | 12.0 V | **off** | — | 0 |
| direct-5v (if you use the 5 V Pro Mini) | 5.0 V | 4.54 V | 149.9 mA | 8.5 mV | ohmic | 56.7 mΩ | 1.27 mW |
| 2n7002-only (2N7002 as the pass element) | 3.3 V | 3.00 V | 52.0 mA | 7.84 V | saturated | — | **408 mW** |

Read the two bold rows:

- **The IRFZ44N is not a logic-level part.** Its Rds(on) is specified at Vgs = 10 V, and
  its threshold is guaranteed anywhere between 2.0 V and 4.0 V. Wired straight to a 3.3 V
  pin the gate only reaches 3.0 V (R1 1k and R5 10k form a divider). A *typical* unit still runs the fan —
  which is exactly why "it worked on my bench" is not a design — but it wastes 34× more
  power, and a *worst-case* unit from the same drawer never turns on at all. The booster
  makes both units behave identically.
- **The 2N7002 cannot be the switch.** At Vgs = 3.0 V it saturates at 52 mA, starves the
  fan, drops 7.84 V across itself and burns 408 mW against a 200 mW rating. Its Id max in
  my own spec record is 115 mA; the fan wants 150 mA. It is a level shifter here, nothing else.

---

## Measured by the simulation

```
pin voltage where the fan starts                :  2.27 V
/BOOT when the pin is high (2N7002 sinks 1.2 mA):  11.6 mV
/GATE steady state (12 V x R5/(R4+R5))          :  10.91 V
fan current with the power FET on               :  152.3 mA
V(drain) with the power FET on                  :   2.4 mV
Rds(on) at that point                           :  15.9 mΩ
power FET dissipation while on                  :  0.37 mW
V(drain) spike at turn-off (clamped by D1)      : 12.37 V
Arduino pin current (max)                       :  0.30 mA
/GATE rise 5 tau (R4=1k, C1=1.5n)               :   7.5 µs
/BOOT rise 5 tau (R3=10k, C2=1.7n)              :  85.0 µs
/BOOT back at 12 V after the pin goes low       : 120.6 µs
fan L/R time constant                           : 125.0 µs
peak fan current during a PWM on-time           : 147.9 mA
average fan current at 1 kHz / 50 % duty        :  80.6 mA
```

A few of those deserve a comment:

- **The pin only ever sources 0.30 mA** — that is 3.3 V / (R1 + R2). Charging the power
  MOSFET's 1.5 nF gate, which would be a 12 mA hammering if you connected the pin to it
  directly, is the booster's job. This is the whole point of the two extra transistors.
- **12.37 V at turn-off.** When Q1 opens, the fan's winding has 147 mA flowing through it
  and that current has to go somewhere. The 1N5819 takes over and holds the node at
  12 V + 0.37 V. Without D1 the node would fly to whatever voltage is needed to force that
  current through the parasitic capacitances — hundreds of volts. Delete D1 in KiCad and
  look at the transient; it is the most instructive ten seconds of this project.
- **The fan current is chopped, not dimmed.** With 10 mH and 80 Ω the fan's time constant
  is 125 µs, so at 1 kHz it never reaches steady state: it ramps to ~148 mA and decays to
  zero every cycle. The *average* is 80.6 mA. The fan always sees either a full 12 V or
  0 V — that is how PWM speed control works. At Klipper's default 100 Hz the effect is the
  same but with 5 ms pulses.
- **Turn-off is slower than turn-on.** `/BOOT` has to charge the IRF7416's 1.7 nF back up
  to 12 V through R3 10 kΩ: τ = 17 µs, and the fan stays on for ~55 µs after the pin goes
  low. At 100 Hz that is irrelevant. If you drive the fan at several kHz, drop R3 to 1 kΩ
  (τ = 1.7 µs); the 2N7002 then sinks 12 mA, which is well inside its 115 mA rating.

---

## The plots

`sim/run.sh` writes these to `sim/out/`:

| file | what it shows |
|---|---|
| `dc_transfer.png` | sweeping the pin 0 → 3.3 V: `/BOOT` falls from 12 V to 12 mV while `/GATE` jumps from 0 to 10.9 V, and the fan starts at 2.27 V |
| `transient.png` | 1 kHz / 50 % PWM: all four node voltages, the fan current, and the 0.3 mA the pin actually supplies |
| `switching_edge.png` | one turn-on edge (gate charging through R4) and one turn-off edge (the 12.37 V clamp and the freewheeling decay) |
| `drive_compare.png` | the variant table above as a chart: fan current and dissipation for each drive option |

---

## Running it

```bash
./sim/run.sh              # export -> ngspice -> plots -> variant table
```

Requirements: KiCad 9 or 10 (`kicad-cli`), `ngspice`, Python 3 with `numpy` and `matplotlib`.

Files:

```
mosfet-fan-switch.kicad_sch     the sheet (A3, ERC clean: 0 errors / 0 warnings)
docs/mosfet-fan-switch.pdf      the sheet as a PDF
sim/run.sh                      the whole pipeline
sim/prepare_deck.py             KiCad export -> runnable ngspice deck
sim/variants.py                 the six-drive comparison
sim/plot.py                     plots + printed summary
sim/models/irfz44n.lib          level-1 fit of the IRFZ44N in my bin
sim/models/irfz44n_wc.lib       the same part at the datasheet's worst-case threshold
sim/models/2n7002.lib           level-1 fit of the 2N7002
sim/models/irf7416.lib          level-1 fit of the IRF7416
sim/models/schottky.lib         1N5819 as a sub-circuit (explicit K/A terminals)
archive/                        the first version of this project (single 5 V-driven IRLZ44N)
```

You can also run the simulation inside KiCad: **Simulator → Run Simulator**. The sheet
carries `.op`, `.dc V2 0 3.3 0.01` and `.tran 1u 5m` cards as text, and Q1/Q2/Q3/D1 point
at the `.lib` files through their `Sim.Library` / `Sim.Name` fields, so KiCad's built-in
ngspice picks the real models up.

### Things to try in KiCad

- Run the DC sweep and watch `/BOOT` fall while `/GATE` rises. That step *is* the booster.
- Delete Q2, Q3, R3, R4 and C2, wire R1 straight to `/GATE`, re-run: the fan still runs
  (149 mA) but Q1 now burns 12.8 mW. Then change Q1's `Sim.Name` to `irfz44n_wc`: dead fan.
  Same drawer, same part number, different transistor.
- Shorten R3 to 1 kΩ and watch the turn-off delay shrink.
- Remove D1 and look at the `/DRAIN` spike.
- Change V2's `tw` from `500u` to `250u` (25 % duty): the average fan current falls, but
  the pulses the fan sees are still a full 12 V.

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
| 1N5819 | 40 V / 1 A Schottky | `is=1e-7 rs=0.05` → 0.38 V at 150 mA |

What a level-1 model gets right, and what this circuit depends on: the threshold voltage,
the on-resistance at a properly driven gate, and the fact that at Vgs = 3 V the 2N7002 is
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
  behaviour; `10 mH + 80 Ω` reproduces the electrical lesson (the winding current that makes
  the flyback diode necessary) but not the aerodynamics.

---

## KiCad → SPICE gotchas that cost time

Kept here so the next schematic is faster:

- A `Sim.Library` file that does not exist makes KiCad export a **broken device card**
  (`Q1 Q1.irfz44n` with no nodes at all) instead of `MQ1 /DRAIN /GATE GND GND irfz44n`.
  Write the `.lib` files before exporting.
- `Simulation_SPICE:NMOS` has three pins, so KiCad hands ngspice a dangling bulk node
  (`NC-Q2-0`). `sim/prepare_deck.py` ties it to the source. `NMOS_Substrate` /
  `PMOS_Substrate` avoid the problem entirely.
- A VPULSE source needs instance-level `Sim.Device=V`, `Sim.Type=PULSE`, `Sim.Pins=1=+ 2=-`
  and a `Value` of `VPULSE`. Otherwise the export writes `V2 /PWM GND dc="3.3V PWM" y1=0 ...`
  which ngspice cannot parse.
- KiCad writes schematic text directives **before** the device lines, so a
  `.control … .endcontrol` card on the sheet breaks ngspice. The sheet carries classic
  `.op` / `.dc` / `.tran` / `.print` cards; `prepare_deck.py` replaces them with a
  `.control` block at the end so `wrdata` can dump plottable vectors.
- Multi-line `(text "...")` blocks in a `.kicad_sch` must contain escaped `\n`. Raw newlines
  parse for ERC but make `kicad-cli sch export pdf` fail with "Failed to load schematic".
- Scripted wires need an explicit `(junction …)` at every T-junction or ERC reports
  "Unconnected wire endpoint". Crossings without a junction stay unconnected — the `BOOT`
  rail crossing Q3's source wire is one of those on purpose.
- `wrdata` repeats the x column before every vector, so the value columns are 1, 3, 5, …
- ERC checks ignored by KiCad's default settings here: "SPICE model issue" and
  "Assigned footprint doesn't match footprint filters" (the 4-pin substrate symbols do not
  match 8-pin MOSFET footprint filters, which is fine for a learning sheet).

---

## Building it for real

- Q1 on a heatsink or a copper pour: at 150 mA it dissipates 0.4 mW, so it will not get warm,
  but the fan stall current (12 V / a few ohm winding) is several amps and that is what the
  TO-220 and the 17.5 mΩ are for.
- The 12 V supply in the bin is rated 450 mA, which is comfortable next to a 150 mA fan.
- Q3's SO-8 package is the awkward one. There is one IRF7416 already mounted on a breakout
  board in R1 · A4 — use that for the first build.
- Keep R4 (1 k) in series with Q1's gate. It slows the edge just enough to keep the
  switching noise down and it limits the current Q3 has to source when charging 1.5 nF.
- Keep R5 (10 k) from gate to ground. Without it a floating gate can sit at any voltage and
  the fan can half-turn-on while the Arduino is resetting.
- If you drive this from Klipper, the pin needs to be a hardware PWM pin and Klipper wants
  an inverted PWM output for a low-side switch that turns on with a high pin:

  ```ini
  [heater_fan fan]
  pin: !PH6
  pwm_cycle_time: 0.010
  max_power: 1.0
  heater_temp: 45.0
  fan_speed: 0.6
  ```

  `pwm_cycle_time: 0.010` is 100 Hz — well above the ~60 µs turn-off delay of this driver,
  so the delays are invisible. Do not use a plain `[fan]` section: a `[heater_fan]` only
  runs the fan while the heater is active, which is what you want on a printer.

---

## Archive

`archive/` keeps the first version of this project: a single logic-level IRLZ44N driven
directly at 5 V, plus its placeholder model and its plots. It is kept because the reason it
worked (a logic-level part, a 5 V pin) is exactly the reason the 3.3 V version does not.
