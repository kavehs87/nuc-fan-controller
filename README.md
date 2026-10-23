# 12 V fan switched by 3.3 V logic — a gate booster built from my own parts

A KiCad schematic, a real ngspice simulation, and a single-copper-layer PCB you can
etch at home — of the thing every 3D printer needs: **an Arduino pin turning 12 V fans
on and off with a MOSFET.**  And since the board grew a NUC fan-header socket, the same
Arduino now reads the NUC's own fan request and answers on its tachometer line.

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

NUC fan header J4
  PWM request 5 V --R7 10k--.  R8 10k to GND  -> /DEMAND 2.50 V at full request -> A0
  tach answer  <--Q4 BC547--  base via R9 1k from /TACH_PWM (D10, 100 Hz carrier)
  +12 V pin    not connected            the fans are powered by this board's own brick
```

Run everything with one command:

```bash
./sim/run.sh
```

It exports the netlist from the schematic, runs ngspice, writes five plots and two
comparison tables, and prints the numbers that matter. Output lands in `sim/out/`
(git-ignored).

---

## The stages, and the nets they live on

| net | what it is | who drives it |
|---|---|---|
| `/PWM` | the Arduino pin (D9 = OC1A, timer 1 channel A) | Arduino Pro Mini 3V3 |
| `/LGATE` | 2N7002 gate, held at 3.0 V by the R1/R2 divider | `/PWM` through R1 1k |
| `/BOOT` | booster node: +12 V when the pin is low, ~0 V when it is high | R3 10k up, Q2 down |
| `/HIGATE` | +12 V handed to the power FET by Q3 | Q3 IRF7416 |
| `/GATE` | IRFZ44N gate, settles at **10.91 V** | R4 1k from `/HIGATE`, pulled down by R5 10k |
| `/DRAIN` | the switching node under the fan(s) | Q1 IRFZ44N, clamped by D1 |
| `/FAN_W` | between a fan's winding and its drag resistance | fan model L1 + R6 |
| `/NUC_PWM` | the NUC's own fan request, 5 V at J4 pin 1 | the NUC (V3 in simulation) |
| `/DEMAND` | that request halved and smoothed for a 3.3 V ADC input | R7/R8 divider, C5 + C6 |
| `/TACH_PWM` | the Pro Mini's answer, D10 = OC1B, a 100 Hz carrier | Arduino Pro Mini 3V3 |
| `/TBASE` | `/TACH_PWM` after R9 1k, into Q4's base | R9 1k |
| `/NUC_TACH` | the tach line the NUC reads, pulled up inside the NUC | Q4 as an open collector |

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

## The NUC fan-header link

The same board also talks to a PC. A NUC's 4-pin fan header wants to drive a fan itself:
it puts out a PWM **request**, expects a tachometer **answer** on the second pin, and
supplies the fan on the third. This board refuses both jobs and does them anyway:

```
NUC fan header J4                Pro Mini (on the board, U1)
  1  PWM request, 5 V ──R7 10k──┐
  2  tach answer   <──Q4 BC547──┼── D10 (OC1B)  /TACH_PWM  100 Hz carrier out
  3  +12 V         not connected│
  4  GND ───────────────────────┴── GND (shared with the 12 V brick)
                                 A0  /DEMAND   2.50 V at full request, read as 775 counts
                                 D9  /PWM      the fan drive, unchanged
        R8 10k from /DEMAND to GND, with C5 1µ + C6 100n across it
```

- **The request has to be knocked from 5 V to 3.3 V** before it touches an Arduino pin.
  R7 (10 k, in series at the header) and R8 (10 k, to ground) halve it; C5 + C6 turn the
  23 kHz square wave into a DC level (τ = 5.49 ms, ≤ 5 mV ripple). Full request =
  **2.50 V = 775 counts**, 0.80 V of headroom. The NUC's PWM output only has to source
  **250 µA**.
- **The answer is an open collector**, because the pull-up lives in the NUC: R9 (1 k) into
  a BC547's base, collector on the tach line. 2.58 mA of base drive sinks 4.96 mA of
  pull-up current; the line lands at **0.037 V** low, 5.00 V high.
- **The tach carrier is a separate signal.** An ITE counts two pulses per revolution, so
  `RPM = 30 × f_tach`, and the legal window (700–10 500 RPM) is **23–350 Hz** on that
  wire. Copying the 1 kHz fan drive onto it would read 30 000 RPM and be rejected, so D10
  generates its own 100 Hz carrier (which reads 3 000 RPM). "Same PWM being sent to the
  fans" is the right *idea* — the frequency is what has to differ.
- J4 pin 3 (the NUC's own fan supply) is **not connected**: the fans are powered by this
  board's 12 V brick.

`sim/nuc_link.py` (run by `./sim/run.sh`) is the check: duty-by-duty tap voltage, ripple,
ADC counts, the divider's load, the tach levels and the carrier window. Numbers and
caveats: `docs/pcb-notes.md`, *The NUC link*.

---

## Parts — all from my cabinets

| ref | part | package | cabinet · drawer | qty in bin |
|---|---|---|---|---|
| U1 | Arduino Pro Mini (3.3 V / 8 MHz, ATmega328P) | 35-hole module, on female sockets | L1 · C5 | 1 |
| Q1 | IRFZ44N N-channel power MOSFET | TO-220 | R1 · B4 | 12 |
| Q2 | 2N7002 N-channel MOSFET | SOT-23 | R1 · A4 | 11 |
| Q3 | IRF7416 P-channel MOSFET | SO-8 | R1 · A4 | 6 (+1 already on a breakout board) |
| Q4 | BC547 NPN small-signal transistor | TO-92 | R1 · D3 | 20 |
| D1 | 1N5819 Schottky, 40 V / 1 A | DO-41 | L1 · E1 | 30 |
| D2 | 1N5822 Schottky, 40 V / 3 A — **spare footprint, not soldered** | DO-27 | L1 · E1 | 9 |
| D3 | MBR10100CT Schottky, 100 V / 10 A dual — **spare footprint, not soldered** | TO-220 | L1 · E1 | 3 |
| R1, R4, R9 | 1 kΩ through-hole | axial | R1 · A2 | 20 |
| R2, R3, R5, R7, R8 | 10 kΩ through-hole | axial | R1 · B2 | 20 |
| C3, C6 | 100 n (104) ceramic disc | radial | L1 · C9 | 30 |
| C4 | 10 µ 16 V electrolytic | radial, 6.3 mm | L1 · C1 | 20 |
| C5 | 1 µ 50 V electrolytic | radial, 8 mm | L1 · E7 | 8 |
| V1 | Switching Power Supply Module, 12 V 450 mA | module | L1 · B7 | 2 |

These items on the sheet are **not** bin parts. They carry `dnp yes` (do not populate)
and have no footprint on the board:

- **C1 = 1.5 nF** — the IRFZ44N's own input capacitance (Ciss ≈ 1489 pF), drawn explicitly.
- **C2 = 1.7 nF** — the IRF7416's Ciss (≈ 1700 pF), drawn explicitly.
- **L1 = 10 mH + R6 = 120 Ω** — the fan. My bins hold no 12 V fan, so the fan is a model: an
  inductor for the winding and a resistor for the mechanical load. 12 V / 120 Ω = **100 mA**,
  which is what my real fans draw. Change R6 if yours are different: 80 Ω models a 150 mA fan.
- **V2, V3, V5** (VPULSE sources) stand in for the three pins: D9's fan drive, the NUC's
  5 V / 23 kHz request at J4 pin 1, and D10's 100 Hz tach carrier. **V4 + R10** stand in for
  the 5 V and 1 kΩ pull-up the NUC carries on its own tach line.
- The KiCad symbol for U1 is `mosfet-fan-switch:Arduino_Pro_Mini_328`, generated by
  `pcb/pro_mini.py` from the same hole map as the board's socket footprint: 35 passive
  pins, one per module hole, so a symbol pin number, a footprint pad number and the
  silkscreen name beside a hole are one number. U1 is excluded from the simulation
  (`exclude_from_sim yes`) because ngspice has no model for a microcontroller, and `V2`
  and `V5` (VPULSE sources) stand in for the two pins it drives.
- **D2 and D3 are on the board but not populated.** They are the stronger flyback
  diodes the bins already hold, laid down as footprints in parallel with D1 so that
  growing this board to a dozen fans is a soldering job, not a new board.
  `sim/fan_count.py` says when to fit one (see *How many fans one output can carry*).

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
- **Turn-off is slower than turn-on, and the model understates it.** `/BOOT` has to charge back up
  to 12 V through R3 10 kΩ. With the netlist's `C2 = 1.7n` — only the IRF7416's own `Ciss` — that
  is τ = 17 µs and the fan stays on ~55 µs after the pin goes low. The perfboard measured
  **~170 µs**, because that node also carries its wiring: about 8 nF rather than 1.7 nF, see
  "Why the carrier is 100 Hz". At 100 Hz the difference is 3 % of the off half-period, which is
  why the board runs there. If you want several kHz, drop `R3` to 1 kΩ *and* fit the `Q5` gate
  helper described under that heading; `R3 = 1k` then sinks 12 mA, well inside the 2N7002's
  115 mA rating, but has to dissipate about 145 mW.

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
| ~9 to ~30 | fit **D2**: the 1N5822 (3 A, **DO-27** — a fatter body than D1's DO-41, and it already has a footprint on the board) |
| ~30 to ~60 | fit **D3**: the **MBR10100CT** (100 V, 10 A dual, TO-220 — two anodes on `/DRAIN`, common cathode on `+12 V`), or two 1N5822 |
| beyond | Q1 starts wanting a heatsink around 8 A, and the wiring matters more than the semiconductors |

Both spares are already drawn and already have copper on the board, in parallel with D1;
`dnp yes` means nobody solders them until this table says to. See *Spare flyback diodes* in
`docs/pcb-notes.md` for their pad → net table.

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
| `nuc_link.csv` | not a plot: the NUC-link duty table (tap voltage, ripple, ADC counts) that `sim/nuc_link.py` prints |

---

## Running it

```bash
./sim/run.sh              # export -> ngspice -> plots -> variant and fan-count tables
```

Requirements: KiCad 9 or 10 (`kicad-cli`), `ngspice`, Python 3 with `numpy` and `matplotlib`.

Files:

```
mosfet-fan-switch.kicad_sch     the sheet (A3, ERC clean: 0 errors / 0 warnings)
mosfet-fan-switch.kicad_sym     five local symbols: four package-accurate transistors, and
                                the Pro Mini itself - 35 pins, one per module hole
sym-lib-table                   registers that library for this project
mosfet-fan-switch.kicad_pcb     the board (56 x 92 mm, one copper layer, placed but unrouted:
                                a routing skeleton - see "The board")
pcb/build_board.py              the board generator: part table, track list, design rules
pcb/pro_mini.py                 the module's hole map -> socket footprint AND schematic symbol
tools/embed_pro_mini_schematic.py  the one-shot migration that replaced the Nano with U1
tools/skeleton_board.py         strip a generated board down to placement + pad nets
tools/make_package_symbols.py   put the four package symbols on the sheet
tools/tidy_q3_labels.py         tie Q3's SO-8 legs together, label each node once
tools/shift_q3_clearance.py     move Q3 clear of the /BOOT branch it was crossing
tools/fix_schematic_junctions.py  put KiCad's junction dots back after any scripted edit
pcb/drc.txt                     the current DRC report
pcb/gerber/  pcb/drill/         Gerbers and Excellon drill file + map
docs/mosfet-fan-switch.pdf      the sheet as a PDF
docs/pcb-notes.md               board rules, pad-to-net table, the NUC link, etch and assembly notes
docs/pcb-etch-bottom.svg/.pdf   the print for toner transfer (1:1, mirrored)
docs/pcb-assembly-bottom.pdf    assembly drawing of the copper side, pads numbered
docs/pcb-assembly-top.pdf       component-side view (through-hole labels only)
docs/pcb-render-*.png           3D renders of both sides, plus a copper-side close-up
sim/run.sh                      the whole pipeline
sim/prepare_deck.py             KiCad export -> runnable ngspice deck
sim/variants.py                 the six-drive comparison
sim/fan_count.py                how many fans one output carries, checked against part ratings
sim/nuc_link.py                 the NUC fan-header link: divider, tach levels, carrier window
sim/plot.py                     plots + printed summary
sim/models/irfz44n.lib          level-1 fit of the IRFZ44N in my bin
sim/models/irfz44n_wc.lib       the same part at the datasheet's worst-case threshold
sim/models/2n7002.lib           level-1 fit of the 2N7002
sim/models/irf7416.lib          level-1 fit of the IRF7416
sim/models/bc547.lib            the BC547 on the tach output (one long .model line)
sim/models/schottky.lib         1N5819 as a sub-circuit (explicit K/A terminals)
tools/fix_schematic_junctions.py  restores junction dots that scripted schematic edits delete
archive/                        the first version of this project (single 5 V-driven IRLZ44N)
```

You can also run the simulation inside KiCad: **Simulator → Run Simulator**. The sheet carries
`.op`, `.dc V2 0 3.3 0.01` and `.tran 1u 5m` cards as text, and Q1/Q2/Q3/D1 point at the
`.lib` files through their `Sim.Library` / `Sim.Name` fields, so KiCad's built-in ngspice picks
the real models up.

### Things to try in KiCad

- Run the DC sweep and watch `/BOOT` fall while `/GATE` rises. That step *is* the booster.
- Delete Q2, Q3, R3, R4 and C2, wire R1 straight to `/GATE`, re-run: the fan still runs
  (100 mA) but Q1 now burns 5.2 mW. Then change Q1's `Sim.Name` to `mos_irfz44n_wc`: dead fan.
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
- **KiCad 10 ignores `Sim.Pins` for `.model` cards** and writes every device line in
  **symbol pin order**. So the symbol's pin numbers decide the SPICE terminal order, and
  the only reliable way to get ngspice's order is a symbol whose pins are the real package
  legs plus a `.subckt` wrapper that re-orders them (`sim/models/*.lib`). The old
  `Simulation_SPICE:NMOS` three-pin symbol left KiCad handing ngspice a dangling bulk node
  (`NC-Q2-0`) — with the package symbols and wrappers there is nothing left to repair, and
  `sim/prepare_deck.py` no longer tries.
- **ngspice wants four nodes on a MOSFET card**: `M d g s model` is refused with
  `not enough nodes`; `M d g s s model` (bulk spelled out, tied to the source) runs.
- **A pin whose endpoint lands in the middle of a wire is not connected** — KiCad calls it
  `Pin not connected` and the netlist names the terminal `unconnected-_Q3-D-Pad7_`. When a
  wire ties several package legs together, segment it so every pin lands on a segment end.
- **`kicad-cli` resolves a symbol from the sheet's own `lib_symbols` cache, not from the
  library.** Insert an instance whose `lib_id` has no cached definition and the file still
  loads, but ERC sees a symbol with no pins: `Pin not connected` **at the instance's
  anchor**, `Label not connected` on every net label attached to it, and the pin printed as
  `Pin 1 [???, ?]`. Carry the cached copy in yourself — the library's `(symbol "Name" …)`
  block, renamed to `(symbol "Library:Name" …)` — which is what
  `tools/embed_pro_mini_schematic.py` does.
- **A `.kicad_sch` wire is exactly two points.** Three points in one `(wire (pts …))` and
  `kicad-cli` refuses the whole file with `Failed to load schematic` and no other clue.
  Draw an L as two wires.
- **ERC's connection grid is 1.27 mm.** `endpoint_off_grid` fires on any pin or wire end
  that is not a multiple of it; symbol pin offsets are multiples of 1.27, so putting the
  anchors on the grid clears the whole batch at once.
- **`kicad-cli` needs the project context next to the schematic.** Copy a `.kicad_sch` to a
  scratch directory and every command answers `Failed to load schematic`, because
  `sym-lib-table`, `fp-lib-table` and the `.kicad_pro` are not there. It looks exactly like a
  corrupt file. Copy those three along with it, or test in the project directory.
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

**56 × 92 mm, one copper layer (B.Cu), zero vias** — and the board in the tree is now a
**routing skeleton**: all 30 footprints placed, every pad carrying its net, no copper
tracks. `tools/skeleton_board.py` produced it from the generated layout, because that
layout was not actually clean — `kicad-cli pcb drc --severity-all` on the routed version
reports **8 violations and 2 unconnected pads** (an unwired JP1 sitting on the GND lane,
the top-right mounting hole sitting on the GND band, `/TBASE` too close to the band rail).
On the skeleton the same command reports **7 violations — all of them cosmetic
`lib_footprint_mismatch`** — plus the 68 unconnected pads an unrouted board must report.
`docs/pcb-notes.md` lists the routing defects with coordinates and turns each one into a
keep-out. The rules are the ones a home-etched board actually needs, not the fab defaults
KiCad ships with:

| | |
|---|---|
| clearance between nets | **0.50 mm** |
| tracks | 0.80 mm signal · 1.5 mm `/DRAIN` and the GND return lanes (the generated routing used 64 of them) |
| `/GND` bus along the top edge | 2.0 mm · `/P12V` bus along y = 41 3.0 mm |
| drills | 0.8 mm ×29, 1.0 mm ×59, 1.1 mm ×8, 1.2 mm ×2, 3.2 mm ×4 (M3 mounting holes) |

Everything lives on one side. Q2 (SOT-23) and Q3 (SO-8) are the only surface-mount parts
and they sit on the **copper side**, which is exactly what removes the need for a via
anywhere: 26 electrical footprints, 4 mounting holes, one layer. The generator checks
every net pair for crossings and prints `no net crossings - the board is planar, no
jumpers needed` — true of the tracks it draws, but it gets there by **not drawing one net
at all**: `/P12V` → U1 pad 13, the module's RAW input, has no generated track, because pad
13 sits below both full-width rails and the `/GND` descent down the right edge blocks the
gap beside them. JP1 is the demonstration of the fix — a 0 Ω link across the GND return
spine at x = 5.5, which is how `/PWM` crosses it — and `docs/pcb-notes.md` gives the
alternative that needs no second jumper: feed the module's GND from the band rail instead,
stop the right-edge descent at y = 58, and the whole right corridor is `/P12V`'s.

The board grew from 56 × 68 to 56 × 92 because the Arduino is on it now. The fan driver is
the top 56 × 44 exactly as in the first version (tag `checkpoint-fan-driver-v1`): +12 V and
the PWM line come in at the bottom left, the level shifter sits mid-left, the booster in the
middle, the power FET on the right, the three fans out through a 2×03 header, and the two
buses hug the top and bottom edges. The **NUC interface band** (y = 42…59) hangs below the
12 V bus: the 5 V → 3.3 V request divider R7/R8 with C5/C6, the open-collector tach answer
R9 + Q4, and J4 — the socket the NUC's own fan cable plugs into. Its own GND return drops
down the right edge *past the end of the 12 V bus*, which is why nothing in the band has to
cross that bus. Below it, the **module deck** (y = 60…92) is U1 on three female sockets,
J5 (the FTDI programming header, wired pin for pin to the module's own programming row) and
J6 (a 2×03 ICSP header whose pin 2 is deliberately a dead pad).

**The symbols on the sheet are the package pinout now.** The MOSFET and transistor symbols
used to be KiCad's SPICE symbols, which number their pins **D-G-S** because that is the
order ngspice wants — while SOT-23 is 1 gate / 2 source / 3 drain, the IRF7416 SO-8 is
1-3 source / 4 gate / 5-8 drain, and the IRFZ44N TO-220 is 1 gate / 2 drain / 3 source.
The sheet now carries four local symbols (`mosfet-fan-switch.kicad_sym`) whose pin numbers
*are* the leg numbers, so the numbers printed beside each transistor leg match the
footprint pad, and KiCad's *Update PCB from Schematic* agrees with the layout instead of
fighting it. The ngspice order moved into `.subckt` wrappers in `sim/models/`.
`docs/pcb-notes.md` has the pad-to-net table and the wrapper table.

| file | what it is for |
|---|---|
| `docs/pcb-etch-bottom.svg` | the toner-transfer print: page is exactly the board size, mirrored, 1:1, black = copper |
| `docs/pcb-etch-bottom.pdf` | the same artwork on A4 (print at 100 %, do not scale to fit) |
| `docs/pcb-assembly-bottom.pdf` | **the assembly drawing to build from**: the copper side as you look at it, every pad outlined and numbered |
| `docs/pcb-assembly-top.pdf` | the component side: labels, outlines and through-hole pads only |
| `docs/pcb-render-smd-copper.png` | close-up of Q2 and Q3 on the copper side, notch markers visible |
| `docs/pcb-render-top.png`, `docs/pcb-render-bottom.png` | 3D renders of both sides |
| `pcb/gerber/`, `pcb/drill/` | Gerbers (`B.Cu`, `B.Mask`, `B.SilkS`, `Edge.Cuts`) and the Excellon drill file + map |
| `docs/pcb-notes.md` | design rules, courtyard boxes, the pad→net table for all 30 footprints, the routing corridor plan, programming the module, drill list, etch and assembly instructions |

**Everything plotted is stale until you route the board.** `docs/pcb-etch-bottom.*`,
`docs/pcb-assembly-*.pdf`, `docs/pcb-render-*.png`, `pcb/gerber/` and `pcb/drill/` were
regenerated from the current **unrouted** placement: they carry the outline, the pads, the
silkscreen and the drill set, but no copper. Re-run the export commands in
`docs/pcb-notes.md` after your own routing, before printing anything for toner transfer.

The two surface-mount parts (Q2 SOT-23, Q3 IRF7416 SO-8) sit on the **copper** side,
which is what keeps this a one-layer board. Their outlines and labels are therefore
stored mirrored, and a top-side view of the board shows them reversed — `Q3` reads as
`ƧQ` and pads 1–4 run right-to-left, so that view cannot tell you which pad is pin 1.
Read the copper-side drawing, not the top render: on the copper side the notch sits
beside pad 1, and pads 1–3 are the three pads that run straight into the wide +12 V bus.
Rotate the datasheet's top-view picture 90° counter-clockwise and it is the board. In
KiCad, `View → Flip Board View` shows the same thing, and the footprints carry their
3D models so the 3D viewer shows both chips lying on the copper. `docs/pcb-notes.md` has
the picture and the proof.

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

  `!PH6` is a hardware PWM pin on the Mega-class board that runs Klipper in my printer. If the
  Pro Mini on this board *is* the Klipper MCU, the pin wired to `/PWM` is **D9 = OC1A**, which
  Klipper spells `!PB1`.

  `pwm_cycle_time: 0.010` is 100 Hz — well above the ~60 µs turn-off delay of this driver, so
  the delays are invisible. Do not use a plain `[fan]` section: a `[heater_fan]` only runs the
  fan while the heater is active, which is what you want on a printer. Klipper drives one fan
  per pin, so three fans on one output means wiring them together in parallel — which is exactly
  the case `sim/fan_count.py` just measured.

### Wiring the NUC side

- **U1 is the Pro Mini, and it is on the board** — three female socket strips, 35 holes,
  with the four signals this circuit needs already assigned: pad 12 `/PWM` (**D9 = OC1A**),
  pad 24 `/TACH_PWM` (**D10 = OC1B**), pad 20 `/DEMAND` (read it on **A0**), and `/GND` on
  pads 4, 29 and 31. Pad 13 **RAW** takes `/P12V`, which is how the module powers itself;
  pads 16 and 28 are the module's 3.3 V **output**, and that rail is what the `/DEMAND`
  divider is referenced to. The board carries no regulator of its own, and the module's
  ground must be the same ground as J1's 12 V brick and J4's pin 4.
- **J4 is where the NUC's fan cable plugs in** — but check your own header with a meter
  first. Pin 1 is the ground-side PWM request, pin 2 the tach input, pin 3 the NUC's own fan
  supply (left unconnected here), pin 4 ground. A mis-mapped header puts 12 V on a 3.3 V
  input, so meter it before you plug it in.
- **JP1 is a real part.** A 0 Ω axial with its leads spread to the 7.62 mm pitch, or a piece
  of tinned wire, between the two pads at (2.00, 14) and (9.62, 14). Without it the PWM line
  is open-circuited and the fans never switch.
- **The tach carrier is firmware's job.** Drive D10 between 23 and 350 Hz — 100 Hz reads
  3 000 RPM on an ITE that counts two pulses per revolution. At the fan drive's 1 kHz the NUC
  sees 30 000 RPM and reports a fan that is not there. Nothing on the board enforces this.
- Read `/DEMAND` on A0 and map it straight onto the fan duty: 2.50 V is a full request
  (775 counts), so `duty = min(1.0, counts / 775)` is the whole control law. The 5.5 ms
  time constant at the tap means the ADC reading is already the average, so a plain
  `analogRead` per 100 ms is enough — no oversampling needed.
- `/PWM` and `/TACH_PWM` are Timer 1's two channels (OC1A and OC1B), so one `TCCR1A` /
  `TCCR1B` setup drives the fans and answers the NUC at two different frequencies. The Uno
  stays usable as the programmer, and it would also run the same four signals at 5 V logic,
  in which case R7/R8 should become a 10 k / 20 k divider (or simply go, if you feed
  `/DEMAND` from a 3.3 V reference instead of the NUC's 5 V).

### Programming the module

- **J5 is the FTDI route**: 1 DTR, 2 TX0, 3 RX1, 4 VCC, 5 GND, 6 BLK — the module's own
  programming row, repeated pin for pin 4.02 mm to its right. Plug the adapter with its
  **black wire over the BLK end**; that is the DTR line the bootloader waits for.
- **Use a 3.3 V FTDI or CH340 breakout.** This is the 3.3 V / 8 MHz module. A 5 V adapter's
  TX into the module's RX is tolerated by the ATmega328P, but the module drives 3.3 V back
  out, and there is no reason to find out what your particular adapter makes of that.
- **J6 is the Uno-as-ISP route**, and it is **five wires, not six**: Uno 10 → J6-1 (MISO),
  11 → J6-3 (SCK), 12 → J6-4 (MOSI), 9 → J6-5 (RST), GND → J6-6 — and **nothing to J6-2**.
  Pin 2 of an ICSP header is the programmer's 5 V, and an Uno pushing 5 V into a 3.3 V
  target's VCC makes two boards fight over the supply. J6's pin 2 is a dead pad so that you
  cannot make this mistake by pulling a sixth wire. The module powers itself from `/P12V`
  while it is being programmed.
- **IDE settings:** board **Arduino Pro or Pro Mini**, processor **ATmega328P (3.3 V,
  8 MHz)**. The 5 V / 16 MHz entry writes the wrong bootloader at the wrong baud rate, and
  the IDE then reports "programmer is not responding" while every wire is correct.
- **Measure the module before soldering the sockets.** The 35-hole map in `pcb/pro_mini.py`
  is the **clone** layout — 12 pads per row, **15.24 mm** between the rows, six programming
  holes in their own row. A genuine SparkFun board is 13 pads per row at 12.70 mm with the
  programming holes in the end column. `ROW_SPACING`, `PADS_PER_ROW` and `SPARE` are at the
  top of that file for exactly this argument.
- The bins hold 16/18/28-pin **DIP** sockets, and they do not fit: a DIP socket's rows are
  7.62 mm apart. What the module wants is a 2.54 mm **female** strip snapped to 12 + 12 + 6,
  and the drawers do not have one.

---

## Firmware, and why 0 % was humming

```
firmware/fan-switch-debug/     drive + tach blink, the first one that ran on the bench
firmware/fan-switch-ladder/    100 % -> 50 %, one step per minute, no serial needed
firmware/fan-switch-serial/    duty commanded over the UART: 0..100, ?, h
firmware/fan-switch-freq/      duty AND carrier over the UART: 0..100, f <Hz>, ?, h
firmware/bench/                the scripts that drive the bench: flash, set, sequence, verify
```

All four drive `/PWM` on **D9 = OC1A**, fast PWM with `TOP` from `ICR1`. Timer 1 is the only
16-bit timer on the module and D9 is the only pin carrying OC1A, which is why the sketches touch
`TCCR1A/B`, `ICR1` and `OCR1A` directly instead of calling `analogWrite()` — that would have moved
the whole thing to Timer 2 at 980 Hz.

The two sketches the bench uses now — `ladder` and `freq` — default to **`ICR1 = 9999` with a
prescaler of 8: 100 Hz**, 5 000 µs high at 50 %. That is not the value they started on: both ran at
1 kHz until the carrier was measured, and `serial` and `debug` are left at 1 kHz as the record of
what the bench ran before that measurement. The reason for the change is the next section.

### The hum at 0 % was `OCR1A = 0`, and it is not 0 %

In fast PWM, `OCR1A = 0` does not switch the output off. The datasheet calls it *"a narrow
spike for each TOP+1 timer clock cycle"*: one timer clock, whatever the carrier is. At 8 MHz that
is a **125 ns pulse on D9, once every carrier period, forever** — every 1 ms at the 1 kHz these
sketches originally ran at, every 10 ms at the 100 Hz they run at now.

Through the Q2/Q3 booster that spike is not small. Measured in `sim/out/mosfet-fan-switch.spice`
with the fan branch attached:

| node | what the spike does |
|---|---|
| `/LGATE` | 3.00 V pulled low |
| `/BOOT` | 12 V → **8.055 V** |
| `/HIGATE` | held at 12 V |
| `/GATE` | **10.905 V for 36.66 µs** |
| `i(L1)` | **31.1 mA** peak, 2.57 mA mean, every cycle |

So the fan was being kicked with 10.9 V on its MOSFET gate a thousand times a second, at the 1 kHz
carrier this board originally ran, while the sketch believed the output was off. 36.66 µs of a 1 ms
period is 3.7 % — enough to make the winding and its own capacitance ring audibly. That is the hum.

**The fix is not a smaller number, it is a different mode:** clear `COM1A1:0` to `00` so OC1A
leaves the pin, then hold D9 low as ordinary GPIO. Timer 1 keeps running, but it is no longer
connected to anything.

```c
if (pct == 0) {
    TCCR1A &= (uint8_t)~(_BV(COM1A1) | _BV(COM1A0));   // OC1A off the pin
    digitalWrite(PWM_PIN, LOW);                          // held low as GPIO
    return;
}
TCCR1A = _BV(COM1A1) | _BV(WGM11);                       // back to fast PWM
OCR1A  = (uint16_t)((uint32_t)(PWM_TOP + 1) * pct / 100);
```

**Confirmed on the bench.** `fan-switch-serial` written through the module's own bootloader
(`-c arduino -b 57600`, `ATmegaBOOT_168_atmega328_pro_8MHz.hex`) over J5 with DTR connected:
at `duty 0 %   OCR1A 0/8000` the fan is **silent**, and `50` spins it up on command. Every sketch
since carries the same fix, so 0 % is silent whatever the carrier is set to.

### Why the carrier is 100 Hz

The sketches started at 1 kHz on the theory that the hum was the chopping, and that putting the
carrier above hearing — the 4-pin fan PWM standard uses 25 kHz for exactly that reason — would fix
it. On the bench the opposite happened: 25 kHz is *not quieter*, it is the fan running at full
speed no matter what duty is commanded. A Hantek DSO2D10 with both channels on the board, CH1 on
Q1 pin 1 (`/GATE`) and CH2 on Q1's tab (`/DRAIN`), ground clip on the board's input ground, says
why.

At **1 kHz, 50 % commanded**, `OCR1A 4000/8000`, so 500 µs high:

| measurement | value |
|---|---|
| `/GATE` high width | **652 µs** of a 1000 µs period |
| `/DRAIN` low width | **680 µs** |
| `/GATE` swing | −0.2 V → 11 V, rise 12 µs |
| `/DRAIN` swing | −1.2 V → 12 V |
| `/DRAIN` average | 2.99 V, so the fan's own average supply is 12 − 2.99 = **9.01 V** |

The two channels agree with each other, which is what makes the reading trustworthy: the gate is
high for exactly as long as the drain is low. **A commanded 500 µs of conduction became
650–680 µs.** Turn-on is fast, 12 µs. Turn-off takes roughly **170 µs**.

That single number explains everything the bench had already shown, including measurements taken
before the scope existed. A fixed *time* error adds a fixed *voltage* offset: 12 V × 170 µs ÷
1000 µs ≈ **2 V**, and a multimeter sweep across the fan at 1 kHz had produced a straight line —
9.6 V at 60 %, 8.6 V at 50 %, 0.1 V per percent — sitting about 2 V above the ideal line at every
duty. The scope derived the same 2 V from a time measurement, independently. It also explains why
the hum appeared at *every* chopped duty from 60 % down to 10 % and at neither extreme: at 100 %
there is no chopping, and at 0 % the pin is held low as GPIO.

And it explains 25 kHz. The excess is a constant ~170 µs, but at 25 kHz the off half-period is
20 µs. The gate is told to fall and never gets there, so the output is simply **stuck on** — which
is exactly what the fan was doing.

### Calibrating the model to the board, and the two ways out

The netlist models `/BOOT` with `C2 = 1.7n`, which is only the IRF7416's own `Ciss`. Re-running the
transient at 1 kHz / 50 % against the measured 652 µs:

| `C2` in the model | `/GATE` high, 500 µs commanded |
|---|---|
| 1.7 nF (what the netlist says) | 538 µs |
| 4.7 nF | 580 µs |
| 6.8 nF | 616 µs |
| 10 nF | 689 µs |
| **the board** | **652 µs** |

So the perfboard's `/BOOT` node carries roughly **8 nF**, not 1.7 nF — the extra ~6 nF is the
wiring. That is the difference between a model that reports 53 % duty and a board that delivers
68 %. It is worth remembering that a hand-built board is three times its own netlist at this node.

Two ways out, and they were both measured:

**Slow the carrier.** The error is a fixed time, so at a long period it stops mattering. At
**100 Hz, 50 %** the scope reads:

| measurement | value |
|---|---|
| period | 10.02 ms |
| `/GATE` high / low width | **4.82 ms / 5.20 ms** |
| delivered duty | **48.10 %** for 50 % commanded |
| `/GATE` average | 4.76 V |

170 µs out of a 5 ms off-half is 3 %, and the delivered duty is honest. The fan is quiet — the
noise the 1 kHz carrier produced is gone. This is the fix the board is running now, and it cost
nothing but a constant in the sketch.

**Or make the turn-off fast, which buys the high carriers back.** A BC547 (`Q5`) with its emitter
to ground, base to `/BOOT` through 4.7 kΩ, and collector to `/GATE` clamps the gate directly
instead of waiting for `/BOOT` to charge back up. On the calibrated board:

| variant | 1 kHz | 10 kHz | 25 kHz |
|---|---|---|---|
| as built, `R3 = 10k` | 580 µs (want 500) | **stuck on** | **stuck on** |
| `Q5`, `R3 = 10k`, `Rb = 4.7k` | 500 µs | 53 µs | 23 µs, fan 58 mA |
| **`Q5`, `R3 = 1k`, `Rb = 4.7k`** | **496 µs** | **49 µs** | **19 µs, fan 47.5 mA** |

Wanted values are 500, 50 and 20 µs. The helper with `R3` dropped to 1 kΩ is essentially exact at
every carrier from 1 kHz to 25 kHz. With `R3 = 1k` the off state also gets cheaper rather than
more expensive: `/BOOT` settles near 10 V, which is high enough that `Q3` genuinely turns off, so
`/HIGATE` and `R4` stop carrying anything and the off-state loss collapses to about 25 mW. The
cost moves to the on state — `R3 = 1k` then carries about 12 mA while the fan runs, so **`R3` has
to dissipate around 145 mW**, fine for a quarter-watt through-hole part but a part to choose
knowingly. That variant is modelled and not fitted: 100 Hz already solved the noise, so `Q5` is on
the shelf until a carrier above hearing is wanted.

One more thing visible in the 1 kHz trace: **`/DRAIN` undershoots to −1.2 V**, which means Q1's
body diode conducts briefly at turn-on. The freewheel current circulating through D1 and the fan's
own 10 mH has to collapse, and it does that by pulling the drain below ground. It is not the noise
source, but it is why the drain edges look ragged.

### The whole duty range at 100 Hz, listened to

With the carrier fixed at 100 Hz the board was run up the entire range, 10 seconds per rung, with
`OCR1A` read back from the sketch at every step:

| duty | `OCR1A` | `/GATE` high per 10 ms | fan supply | what the bench did |
|---|---|---|---|---|
| 0 % | 0 | 0 — pin held low as GPIO | 0 V | silent |
| 10 % | 1000 | ~1.0 ms | ~1.2 V | **would not spin the fan** |
| 20 % | 2000 | ~2.0 ms | ~2.4 V | **would not spin the fan** |
| 30 % … 90 % | 3000 … 9000 | ~3 … 9 ms | ~3.6 … 10.7 V | ran |
| 100 % | 10000 | always high | ~11.9 V | ran, smooth |

**No humming at any rung.** That is the result the 1 kHz carrier could not produce at any chopped
duty, and it is the reason 100 Hz is the default.

The dead bottom of the ladder is the fan, not the switch. A 12 V brushless fan needs something like
4–7 V at its terminals before its own controller will start the rotor, so 10 % and 20 % are being
delivered correctly and the fan is simply declining to start — expected behaviour on a 2-wire fan,
and worth knowing before anyone reads "nothing happens at 10 %" as a board fault. The exact rung
where it starts was not pinned down. The other half of the same fact: once spinning, a fan keeps
turning at a terminal voltage well below the one it needed to start, so the speed at a given duty
depends on whether the fan was already running.

### Open item: a start kick, not written yet

A thermostat wants *low duty means low speed*, but a fan that will not start at 1.2 V makes the
bottom of the range dead. The usual answer is a start kick — 100 % for a second or two to get the
rotor going, then drop to the commanded duty. That belongs in `fan-switch-freq` as a `k` command
and in the ladder as a kick before each rung settles. Not implemented; the bench is happy without
it.

### Do not put a capacitor across the fan terminals

That was the other theory, and the simulation killed it. A capacitor there does not absorb the
spike, it becomes the other half of an LC tank with the fan's own 10 mH winding:

| `Cfan` | mean fan current at 0 % | ring with `L1 = 10 mH` |
|---|---|---|
| none | 2.57 mA | — |
| 100 nF | 14.9 mA | harmless |
| 10 µF | **69.6 mA** | 503 Hz, Q 3.8, ~2.4 ms |
| 100 µF | **96.1 mA** | 159 Hz, Q 12, ~24 ms |

At 10 % duty it is worse still: 74.9 mA with 10 µF, 97.0 mA with 100 µF. A bulk capacitor across
the terminals makes the fan *hotter and louder*, not quieter. The only capacitor on that side of
the board worth having is **100 nF film at J3**, and that is for EMI, not for the hum.

### Programming it on the bench

Both routes in `docs` work; the FTDI route is the one that keeps the bench quiet:

```sh
arduino-cli compile --fqbn arduino:avr:pro:cpu=8MHzatmega328 <sketch>
avrdude -C <avrdude.conf> -c arduino -P /dev/ttyUSB0 -b 57600 -p m328p \
        -U flash:w:<sketch>.ino.hex:i
```

`firmware/bench/` wraps exactly this. `flash-bootloader.sh` compiles and writes, `set.sh` leaves the
sketch in a commanded state so the board can be probed with the port released, `seq.sh` runs a timed
sequence so a duty range can be listened to, and `verify-flash.sh` reads all 32 kB back over ISP and
compares it against the compiled hex.

- **DTR must reach the module's RST.** Without it the bootloader never gets its reset pulse and
  `avrdude` just times out. The FTDI breakout's DTR to J5-1 is the whole auto-reset circuit.
- **Cross the data lines.** J5-2 is `TX0`, the module's *output*, so it goes to the breakout's
  **RX**; J5-3 is `RX1`, the module's *input*, so it goes to the breakout's **TX**. Matching the
  silkscreen names label-to-label is the wrong way round. If a breakout's labels are ambiguous,
  jumper its own TX to its RX with nothing else attached and send bytes at it — 20 out, 20 back
  identifies the pair by function.
- **57600, not 9600.** The 3.3 V / 8 MHz bootloader runs at 57600; the sketch runs at 9600. They
  are different baud rates on the same wire, which is why a failed upload looks like a dead link.
- **Opening the port resets the module, and that is both the feature and the trap.** DTR to J5-1
  is what gives the bootloader its reset pulse, so flashing needs the port to be opened. But the
  same pulse resets the sketch, which puts the duty back to 0 %, and `ATmegaBOOT` then sits
  listening for a sync byte for about a second — any command sent in that window is eaten by the
  bootloader instead of reaching the sketch. That is how `f 100` once arrived as `unknown: j`. The
  bench uses a `set.sh` that opens the port, waits 3 s for the bootloader to give up, sends the
  command list, waits again, sends the list a second time, and then releases the port; the sketch
  holds whatever it was last commanded, so the bench stays in that state while it is probed with a
  scope or a meter.

### Known bug, left in place

`firmware/fan-switch-debug` blinks the tach LED with `PORTB ^= _BV(PB6)`, but Arduino **D10 is
PB2**. The disassembly confirms it (`in r24,0x05; ldi r25,0x40; out 0x05`): it toggles a bit that
is not the tach pin. It is left as written because that sketch is the record of the first bench
run. Fix it to `_BV(PB2)` before reusing it on the embedded-Pro-Mini board.

### Where the bench is left

- The chip is running `firmware/fan-switch-freq`, flashed through its own bootloader, and boots on
  its own at `duty 0 %   OCR1A 0/10000   carrier 100 Hz`. Nothing has to be sent for it to be in the
  quiet configuration.
- `Q5` and the 1 kΩ `R3` are **not fitted**. The board is the perfboard build with `R3 = 10k`, and
  100 Hz is what makes that work.
- Carriers above roughly 5 kHz stay unusable on this board until `Q5` is fitted: the ~170 µs
  turn-off is longer than the off half-period there, so the output is stuck on.
- The fan is quiet at every chopped duty from 30 % to 100 %, silent at 0 %, and does not start below
  about 20 % because a 12 V brushless fan will not start on 2 V. That is the fan, not the switch.

---

## Archive

`archive/` keeps the first version of this project: a single logic-level IRLZ44N driven
directly at 5 V, plus its placeholder models and its plots. It is kept because the reason it
worked (a logic-level part, a 5 V pin) is exactly the reason the 3.3 V version does not.
