# Parts collection sheet — what is built, and where every part came from

> **Two halves, and they are not equally live.** §1 is the **perfboard build** in `fan-switch-booster/` —
> the circuit that exists, was scoped, and produced every fan-side number in this repo. §2 and §3 are the
> cabinet walk for the **retired** `nuc-fan-controller` enclosure board: kept because those parts are still
> in the drawers and this sheet is the record of where they came from, but the board they describe is at the
> tag `nuc-fan-controller-full-2026-10-23` and is not being built.

Every part below came from the parts cabinets. Nothing here needs buying except possibly M3 hardware.

---

## 1. The perfboard build, as it actually is

| Ref | Part | Package | Cabinet · drawer | On the bench |
|---|---|---|---|---|
| U1 | Arduino Pro Mini, 3.3 V / 8 MHz, ATmega328P | 35‑hole module | **L1 C5** | **fitted**, in female sockets. Flashed through its own bootloader, 57600 |
| Q1 | IRFZ44N N‑channel power MOSFET | TO‑220 | **R1 B4** | **fitted.** `/GATE` is Q1 pin 1, `/DRAIN` is its tab and J3 pin 2 — the two probe points |
| Q2 | 2N7002 N‑channel MOSFET | SOT‑23 | **R1 A4** | **fitted.** Sinks `/BOOT` when the Arduino pin goes high |
| Q3 | IRF7416 P‑channel MOSFET | SO‑8 | **R1 A4** | **fitted.** The booster: it is what puts 10.9 V on `/GATE` from a 3.3 V pin. One of the six in the bin is already mounted on a breakout board |
| D1 | 1N5819 Schottky, 40 V / 1 A | DO‑41 | **L1 E1** | **fitted**, from `/DRAIN` to +12 V. The freewheel current it carries, collapsing through the fan's own ~10 mH, is what pulls `/DRAIN` to **−1.2 V** at turn‑on — briefly forward‑biasing Q1's body diode. Measured in the 1 kHz trace |
| R1 | 1 kΩ | axial | **R1 A2** | **fitted.** Arduino pin → Q2 base |
| R2 | 10 kΩ | axial | **R1 B2** | **fitted.** Q2 base pull‑down |
| R3 | 10 kΩ | axial | **R1 B2** | **fitted, and it is the part that decides the carrier.** `/BOOT` charges back through it into a node that measures **~8 nF**, which is the fixed ~170 µs turn‑off |
| R4 | 1 kΩ | axial | **R1 A2** | **fitted.** `/HIGATE` → `/GATE` series; also the edge‑rate limiter |
| R5 | 10 kΩ | axial | **R1 B2** | **fitted, and it stays 10 k.** With R4 it sets 10.9 V of gate drive; drop it to 1 k and `/GATE` collapses to 6.0 V |
| — | 12 V supply on the bench | an **8 A 12 V brick**, not the 450 mA module in `L1 B7` | — | the brick is what moves the fan‑count limit from the supply to the flyback diode |
| — | the fans | real 12 V **two‑pin** fans, no PWM pin, no tach | — | 100 mA each at full speed |

**On the schematic but not on this bench.** The schematic carries the NUC interface and the spare parts;
the perfboard does not:

- **Q4** (BC547, `R1 D3`) and the tach pull‑up — the bench has **no tach path**;
- **R7 / R8** and **C5 / C6** — the `/DEMAND` divider on A0. **A0 is unused on this bench**;
- **D2** (1N5822, DO‑27) and **D3** (MBR10100CT, TO‑220) — `dnp yes`, laid down as parallel footprints so
  growing to a dozen fans is a soldering job. `fan-switch-booster/sim/fan_count.py` says when to fit one;
- **C1 = 1.5 n** and **C2 = 1.7 n** — not parts at all. They are the IRFZ44N's and the IRF7416's own
  `Ciss`, drawn explicitly so the RC timing is auditable. On the perfboard `/BOOT` carries about
  **8 nF**, three times the netlist's 1.7 nF, and the extra ~6 nF is the wiring;
- **V1**, the 12 V 450 mA supply module in `L1 B7` — the bench runs from the brick instead.

**On the shelf, modelled and not fitted.** The pair that buys the high carriers back: **Q5** BC547
(`R1 D3`), emitter to ground, base to `/BOOT` through **4.7 kΩ** (`R1 B2`), collector to `/GATE` — with
**R3 dropped to 1 kΩ** (`R1 A2`). Modelled exact from 1 kHz to 25 kHz. Two things to know before fitting
it: `R3` then carries about 12 mA and has to dissipate **~145 mW**, so it is a power‑rated part chosen
knowingly, not a random 1 k from the drawer; and it is only worth doing if a carrier above hearing is
actually wanted, because 100 Hz already solved the noise.

---

## 2. The retired board's BOM, by reference

*Kept as the record of that design and of where its parts came from. `docs/pcb-notes.md` in
`fan-switch-booster/` is the equivalent sheet for the booster's own retired PCB.*

| Ref | Value | Qty | Cabinet drawer | Inventory entry | Stock | Take | What to measure / check |
|---|---|---|---|---|---|---|---|
| Q3 | IRFZ44N | 1 | **R1 B4** | IRFZ44N N-Channel Power MOSFET (TO-220) — id 208 | 12 | 2 | TO-220 body, tab, lead pitch. Specs on file: 55 V, 49 A, 17.5 mΩ |
| Q1, Q2 | BC547B | 2 | **R1 D3** | BC547 NPN Transistor (TO-92) — id 248 | 20 | 4 | Body **flat or staggered** leads; confirm the B bin. Pin order is E‑B‑C facing the flat face (1=E, 2=B, 3=C) |
| D2 | 1N5819 | 1 | **L1 E1** | 1N5819 — id 48 | 30 | 3 | Body length and diameter, natural lead spacing (see §4.4) |
| U3 | AMS1117-3.3 | 1 | **L1 B1** | AMS1117-3.3 (TO‑252) — id 27 | 19 | 2 | Confirm the package is TO‑252 / SOT‑223, not TO‑220. **The board's pads are TO‑252; the SOT‑223 in the same drawer will not fit them** |
| C3 | 470 µF 25 V | 1 | **L1 C1** | 470uF 25v 8x20mm Radial — id 111 | 6 | 2 | Can Ø and **lead pitch**. The board's footprint is Ø8 / P3.50 with its pads spread to 5.08; an 8×20 can is almost certainly P3.50, which is why this one is drawn that way |
| C7 | 10 µF | 1 | **L1 D3** | 10uF 16v Radial 4x7.5mm — id 147 | 4 | 3 | Lead pitch (board assumes P2.50). Spare pool: `L1 C1` id 33, 10uF 16V, 19 pcs, size unknown |
| C10 | 1 µF | 1 | **L1 E7** | 1uF 50V Radial Electrolytic Cap 8x4mm — id 256 | 8 | 2 | Can Ø and pitch — **the board draws it as Ø6.3 / P2.50**, so an 8×4 can has to be stood on its leads and bent |
| C4, C8, C11, C12 | 100 n | 4 | **L1 C9** | Ceramic Cap 100nF (104) — id 294 | 30 | 6 | Body Ø and thickness, lead spread (the board draws Ø6.0 / W2.5 / P5.00, pads spread to 5.08; a 104 disc is usually Ø5–6, which is why) |
| C9 | 100 p | 1 | **L1 C9** | Ceramic Cap 100pF (101) — id 293 | 8 | 2 | Body Ø (the board draws Ø3.8 / W2.6 / P2.50) |
| R2, R6, R8 | 1 k | 3 | **R1 A2** | 1k Ohm Through-Hole Resistor — id 221 | 20 | 5 | Body length/Ø and seated lead spacing — see §4.1, this is the biggest lever on board area |
| R3 | 4.7 k | 1 | **R1 B2** | 4.7k Ohm Through-Hole Resistor — id 223 | 20 | 2 | as above |
| R4 | 2.2 k | 1 | **R1 A2** | 2.2k Ohm Through-Hole Resistor — id 222 | 20 | 2 | as above |
| R5, R7, R10 | 10 k | 3 | **R1 B2** | 10k Ohm Through-Hole Resistor — id 224 | 20 | 5 | as above |
| R9 | 120 Ω | 1 | **R1 B1** | 120 Ohm Through-Hole Resistor — id 213 | 20 | 2 | as above |
| **R11** | **0 Ω — board only, not in the schematic** | 1 | any drawer, or scrap | the bridge that carries `FAN_PWM` over the divider row | — | 1 | Same DIN0204 pad spacing as every other resistor. A 0 Ω, a lead scraped off a scrapped part, or a staple of bare wire |
| J1, J3, J4, J7 | 1×02 **male** header | 4 | **L1 E9** | 2-Pin Male Header 2.54mm — id 310 | 7 | 4 | Pin length; whether the strip is breakaway |
| J2 | 1×04 **male**, NUC fan header | 1 | **L1 E9** | 5-Pin Male Header 2.54mm — id 309 | 7 | 1 strip | Snap a 5‑pin strip down to 4 (see §4.3). A shrouded fan header is nicer — the footprint is the shrouded Intel/AMD kind |
| J5 | 1×05 **male**, Pro Mini | 1 | **L1 E9** | 5-Pin Male Header 2.54mm — id 309 | 7 | 1 strip (whole) | Measure the Pro Mini's own header rows first: see §4.8, this line may become two headers |
| J6 | 1×04 **male**, buck module | 1 | **L1 E9** | 5-Pin Male Header 2.54mm — id 309 | 7 | 1 strip | Snap to 4. What it actually mates with depends on the module's terminals — §4.5 |
| TP1 | TACH test point | 0 | — | no part: it is a bare 1.5 mm pad on the board | — | — | — |
| — | XL4016E1 step-down module | 1 | **L1 A10** | XL4016E1 Step-Down Module — id 319 | 1 | 1 | Module L×W, how the wires attach, pot positions, mounting holes — see §4.5 |
| — | Arduino Pro Mini (3.3 V / 8 MHz) | 1 | **L1 C5** | Arduino Pro Mini — id 125 | 1 | 1 | Confirm it is the **3.3 V/8 MHz** variant, not 5 V/16 MHz |
| — | TO‑220 isolation pad + hardware | 1 | **L1 E7** | TO-220 Heatsink Isolation Pads — id 202 | 10 | 1 | Only if Q3's tab gets bolted to anything metal |

Board functions, so nothing gets collected twice: `C3/C4` bulk and bypass the module's 12 V where it
lands on the rail; `C7/C8` are the 3.3 V regulator's caps; `C9` filters the fabricated tach;
`C10/C11` slow the ITE's PWM into the ADC; `C12` bypasses the switched fan rail; `D2` is the fans'
freewheel; `R2` is the tach pull‑up; `R3/R4/R5` are the PWM divider; `R6/R7` drive and hold down
`Q2`; `R8` feeds the fan drive; `R9/R10` are `Q3`'s gate series and pull‑down; **`R11` is a copper
concession, not a circuit part** — it is the single crossing this board cannot route around, so a
0 Ω carries `FAN_PWM` over the divider row.

---

## 3. The same list as a drawer walk

| Order | Drawer | Take |
|---|---|---|
| 1 | **L1 B1** | AMS1117‑3.3 (TO‑252) ×2 |
| 2 | **L1 C1** | 470 µF 25 V 8×20 radial ×2 |
| 3 | **L1 C9** | 100 n (104) ×6, 100 p (101) ×2 |
| 4 | **L1 D3** | 10 µF 16 V 4×7.5 ×3 |
| 5 | **L1 E1** | 1N5819 ×3 |
| 6 | **L1 E7** | 1 µF 50 V 8×4 ×2, TO‑220 isolation pad ×1 |
| 7 | **L1 E9** | 2‑pin male headers ×4, 5‑pin male headers ×3 |
| 8 | **L1 A10** | XL4016E1 step‑down module ×1 |
| 9 | **L1 C5** | Arduino Pro Mini ×1 |
| 10 | **R1 A2** | 1 k ×5, 2.2 k ×2 |
| 11 | **R1 B1** | 120 Ω ×2 |
| 12 | **R1 B2** | 4.7 k ×2, 10 k ×5 |
| 13 | **R1 B4** | IRFZ44N ×2 |
| 14 | **R1 D3** | BC547 ×4 |
| 15 | any | one 0 Ω, or a lead scraped off a scrapped part, for `R11` |

Optional, only if the 3.5″ HDD tap (`J7`‑style 12 V tap beside `C3`) gets built: **L1 A8** glass
fuse 3–4 A ×1 and **L1 B6** glass fuse socket ×1 for the tapped 19 V lead.

---

## 4. What the photos and measurements have to settle

Eight answers decide the footprints, and the footprints decide how small an etched board can be.
Measure with calipers if possible; a photo next to a ruler is enough for the rest.

**4.1 The resistors — the biggest lever on area.** *Still live: it applies to any rebuild, and to how the
perfboard's R1–R5 sit.* The design assumes DIN0204: 3.6 mm body, 1.6 mm Ø, **5.08 mm** pad pitch. If the
cabinet's are 0207 (≈5.5 × 2.5 mm body, leads spread to ≈10 mm) every resistor takes twice the room, and a
0207 can also be seated with its body off the board to halve that. Report: body length, body Ø, and the
spacing the leads land at when it sits flat.

**4.2 The disc caps.** *Footprint detail for the retired board.* `C4/C8/C11/C12` are drawn Ø6.0 mm / W2.5 /
P5.00 with the pads spread to 5.08, and `C9` Ø3.8 / W2.6 / P2.50. Report each body's Ø and thickness, and
how far apart the leads are where they exit the body. If the 104s are smaller than Ø6 they will simply sit
loose in the pads.

**4.3 Headers.** *Still live — the cabinet has no 4‑pin strip, and any build into the NUC needs one.* Three
ways to do `J2` and `J6`: snap 5‑pin strips to 4 (leftover single pins come off clean); salvage the NUC's
own fan plug and solder its wires into a 4‑pin header; or solder the fan wires straight into the pads. The
`JST‑XH 4P` housings in `L1 E9` are 2.5 mm pitch and will **not** sit on 2.54 mm pins. Report whether the
strips are breakaway (moulded gaps between pins) or a continuous moulding.

**4.4 The flyback diode's span.** *Footprint detail for the retired board.* The board keeps the library's
**10.16 mm** pitch so the silkscreen outline matches the part. A DO‑41 body is ≈5.3 × 2.7 mm with ≈2.7 mm
natural lead spacing, so its leads get bent out to 10.16 and it lies flat with its body between the two
rails it joins. Report body length and Ø.

**4.5 The buck module.** *Live if a 12 V rail is ever built as a module.* Its connector decides `J6`'s
footprint: some XL4016 modules have screw terminals (5.08 mm pitch, no header at all), some have plain
pins. Report: module L × W, what the input and output terminals are and their spacing, where the two trim
pots sit, whether there are mounting holes, and how tall the tallest part on it is.

**4.6 The regulator.** *Footprint detail for the retired board.* Confirm the AMS1117‑3.3 is TO‑252
(SOT‑223). The board's pads are TO‑252; a SOT‑223 is the same 6.5 mm body with a longer lead stub and will
not sit down on them. If it turns out to be TO‑220 only, note that `L1 B1` also holds `BA033ST` (TO‑220
3.3 V, 4 pcs) — a deliberate all‑THT option, at the cost of a TO‑220 footprint on a board that is trying to
be small.

**4.7 The transistors.** *Still live, and it is the one that breaks hardware silently.* TO‑92 comes flat
(all three leads in one row) or staggered (middle lead offset) — the design uses `TO-92_Inline_Wide`. Report
which the BC547s are, and confirm the marking reads BC547**B**. Then check the **pin order**: this design's
footprints assume the NXP/Philips **E‑B‑C** order facing the flat face, and an onsemi part in **C‑B‑E**
looks identical and works not at all. Meter the two of them before they go in.

**4.8 The Pro Mini.** *Still live.* Confirm the silkscreen or crystal: 3.3 V/8 MHz (crystal marked 8.000)
is what the 3.3 V rail and the firmware expect — a 5 V/16 MHz board back‑feeds 5 V into every pin. Then
**measure where its pins actually are**: the retired board plugged it into one 1×05 header (`J5`), which is
only right if the five wires it needed — GND, VCC, A0, D11, D9 — happen to be reachable on one row. If they
are split across two rows, `J5` becomes two headers (say 1×02 and 1×03) and that changes the bottom edge of
the layout. Photograph both rows with the pin names legible.

---

## 5. Not in the cabinet

M3 mounting hardware for four board corners (4 M3 nuts, and whatever stands off the board from the
enclosure), and hookup wire. The 19 V lead, its fuse, and the NUC's 5 V tap are bench items, not board
items.
