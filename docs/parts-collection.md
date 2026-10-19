# Parts collection sheet — every BOM line, and where it lives in the cabinet

Read this top to bottom once, then walk the cabinet in the **drawer order** at the bottom.
Quantities include spares. Nothing here needs buying except possibly M3 hardware.

Status of the design it describes: the 19 V→12 V stage is the **XL4016E1 step-down module**
(cabinet `L1 A10`), so the board carries no power inductor, no Schottky rectifier for that stage,
and no buck IC — see *A reversal worth stating* in `README.md`.

---

## 1. By reference (what the board needs)

| Ref | Value | Qty | Cabinet drawer | Inventory entry | Stock | Take | What to measure / check |
|---|---|---|---|---|---|---|---|
| Q3 | IRFZ44N | 1 | **R1 B4** | IRFZ44N N-Channel Power MOSFET (TO-220) — id 208 | 12 | 2 | TO-220 body, tab, lead pitch. Specs on file: 55 V, 49 A, 17.5 mΩ |
| Q1, Q2 | BC547B | 2 | **R1 D3** | BC547 NPN Transistor (TO-92) — id 248 | 20 | 4 | Body **flat or staggered** leads; confirm the B bin. Pin order is E‑B‑C facing the flat face (1=E, 2=B, 3=C) |
| D2 | 1N5819 | 1 | **L1 E1** | 1N5819 — id 48 | 30 | 3 | Body length and diameter, natural lead spacing (see §3.4) |
| U2 | AMS1117-5.0 | 1 | **L1 B1** | AMS1117-5.0 — id 28 | 8 | 2 | Confirm the package is SOT‑223 / TO‑252, not TO‑220 |
| U3 | AMS1117-3.3 | 1 | **L1 B1** | AMS1117-3.3 (TO‑252) — id 27 | 19 | 2 | Same |
| C3 | 470 µF 25 V | 1 | **L1 C1** | 470uF 25v 8x20mm Radial — id 111 | 6 | 2 | Can Ø and **lead pitch**. The footprint in the current design says Ø10 / P5.00; an 8×20 can is almost certainly P3.50, so `C3`'s footprint changes |
| C5, C7 | 10 µF | 2 | **L1 D3** | 10uF 16v Radial 4x7.5mm — id 147 | 4 | 3 | Lead pitch (design assumes P2.50). Spare pool: `L1 C1` id 33, 10uF 16V, 19 pcs, size unknown |
| C10 | 1 µF | 1 | **L1 E7** | 1uF 50V Radial Electrolytic Cap 8x4mm — id 256 | 8 | 2 | Can Ø and pitch (design assumes Ø8 / P3.50 — the 8 mm label agrees) |
| C4, C6, C8, C11, C12 | 100 n | 5 | **L1 C9** | Ceramic Cap 100nF (104) — id 294 | 30 | 7 | Body Ø and thickness, lead spread (design assumes Ø3.8 / P2.50; a 104 disc is usually Ø5–6) |
| C9 | 100 p | 1 | **L1 C9** | Ceramic Cap 100pF (101) — id 293 | 8 | 2 | Body Ø (design assumes Ø3.0 / P2.50) |
| R2, R6, R8 | 1 k | 3 | **R1 A2** | 1k Ohm Through-Hole Resistor — id 221 | 20 | 5 | Body length/Ø and seated lead spacing — see §3.1, this is the biggest lever on board area |
| R3 | 4.7 k | 1 | **R1 B2** | 4.7k Ohm Through-Hole Resistor — id 223 | 20 | 2 | as above |
| R4 | 2.2 k | 1 | **R1 A2** | 2.2k Ohm Through-Hole Resistor — id 222 | 20 | 2 | as above |
| R5, R7, R10 | 10 k | 3 | **R1 B2** | 10k Ohm Through-Hole Resistor — id 224 | 20 | 5 | as above |
| R9 | 120 Ω | 1 | **R1 B1** | 120 Ohm Through-Hole Resistor — id 213 | 20 | 2 | as above |
| J1, J3, J4, J7 | 1×02 header | 4 | **L1 E9** | 2-Pin Male Header 2.54mm — id 310 | 7 | 5 | Pin length; whether the strip is breakaway |
| J2 | 1×04, NUC fan header | 1 | **L1 E9** | 5-Pin Male Header 2.54mm — id 309 | 7 | 3 strips | Snap two 5‑pin strips down to 4 (see §3.3) |
| J5 | 1×05, Pro Mini | 1 | **L1 E9** | 5-Pin Male Header 2.54mm — id 309 | 7 | (same 3 strips) | one strip stays whole |
| J6 | 1×04, buck module | 1 | **L1 E9** | 5-Pin Male Header 2.54mm — id 309 | 7 | (same 3 strips) | snap to 4 |
| TP1 | TACH test point | 0 | — | no part: it is a bare 1.5 mm pad on the board | — | — | — |
| — | XL4016E1 step-down module | 1 | **L1 A10** | XL4016E1 Step-Down Module — id 319 | 1 | 1 | Module L×W, how the wires attach, pot positions, mounting holes — see §3.5 |
| — | Arduino Pro Mini (3.3 V / 8 MHz) | 1 | **L1 C5** | Arduino Pro Mini — id 125 | 1 | 1 | Confirm it is the **3.3 V/8 MHz** variant, not 5 V/16 MHz |
| — | TO‑220 isolation pad + hardware | 1 | **L1 E7** | TO-220 Heatsink Isolation Pads — id 202 | 10 | 1 | Only if Q3's tab gets bolted to anything metal |

Board functions, so nothing gets collected twice: `C3/C4` bulk and bypass the module's 12 V;
`C5/C6` and `C7/C8` are the 5 V and 3.3 V regulator caps; `C9` filters the fabricated tach;
`C10/C11` slow the ITE's PWM into the ADC; `C12` bypasses the switched fan rail; `D2` is the fans'
freewheel; `R2` is the tach pull‑up; `R3/R4/R5` are the PWM divider; `R6/R7` drive and hold down
`Q2`; `R8` pulls the fan rail; `R9/R10` are `Q3`'s gate series and pull‑down.

---

## 2. By drawer (walk the cabinet in this order)

| Order | Drawer | Take |
|---|---|---|
| 1 | **L1 B1** | AMS1117‑5.0 ×2, AMS1117‑3.3 ×2 |
| 2 | **L1 C1** | 470 µF 25 V 8×20 radial ×2 |
| 3 | **L1 C9** | 100 n (104) ×7, 100 p (101) ×2 |
| 4 | **L1 D3** | 10 µF 16 V 4×7.5 ×3 |
| 5 | **L1 E1** | 1N5819 ×3 |
| 6 | **L1 E7** | 1 µF 50 V 8×4 ×2, TO‑220 isolation pad ×1 |
| 7 | **L1 E9** | 2‑pin headers ×5, 5‑pin headers ×3 |
| 8 | **L1 A10** | XL4016E1 step‑down module ×1 |
| 9 | **L1 C5** | Arduino Pro Mini ×1 |
| 10 | **R1 A2** | 1 k ×5, 2.2 k ×2 |
| 11 | **R1 B1** | 120 Ω ×2 |
| 12 | **R1 B2** | 4.7 k ×2, 10 k ×5 |
| 13 | **R1 B4** | IRFZ44N ×2 |
| 14 | **R1 D3** | BC547 ×4 |

Optional, only if the 3.5″ HDD tap (`J7`‑style 12 V tap beside `C3`) gets built: **L1 A8** glass
fuse 3–4 A ×1 and **L1 B6** glass fuse socket ×1 for the tapped 19 V lead.

---

## 3. What the photos and measurements have to settle

These eight answers decide the footprints, and the footprints decide how small the etched board can
be. Measure with calipers if possible; a photo next to a ruler is enough for the rest.

**3.1 The nine resistors — the biggest lever on area.** The design assumes DIN0204: 3.6 mm body,
1.6 mm Ø, **5.08 mm** pad pitch. If the cabinet's are 0207 (≈5.5 × 2.5 mm body, leads spread to
≈10 mm) every resistor takes twice the room, and a 0207 can also be seated with its body off the
board to halve that. Report: body length, body Ø, and the spacing the leads land at when it sits flat.

**3.2 The disc caps.** `C4/C6/C8/C11/C12` are assumed Ø3.8 mm / P2.50 and `C9` Ø3.0 / P2.50. A 104
disc is usually Ø5–6 mm. Report each body's Ø and thickness, and how far apart the leads are where
they exit the body.

**3.3 Headers.** The cabinet has **no 4‑pin strip** and no keyed 4‑pin fan connector. Three ways to
do `J2` and `J6`: snap 5‑pin strips to 4 (leftover single pins come off clean); salvage the NUC's
own fan plug and solder its wires into a 4‑pin header; or solder the fan wires straight into the pads.
The `JST‑XH 4P` housings in `L1 E9` are 2.5 mm pitch and will **not** sit on 2.54 mm pins. Report
whether the strips are breakaway (moulded gaps between pins) or a continuous moulding.

**3.4 D2's span.** The footprint spreads its pads 10.16 mm apart. A DO‑41 body is ≈5.3 × 2.7 mm with
≈2.7 mm natural lead spacing, so the leads can be bent out to 5.08 mm and it sits flat. That matters
because `D2` is the part that decides how far apart the +12 V and switched‑fan rails can run. Report
body length and Ø.

**3.5 The buck module.** Its connector decides `J6`'s footprint: some XL4016 modules have screw
terminals (5.08 mm pitch, no header at all), some have plain pins. Report: module L × W, what the
input and output terminals are and their spacing, where the two trim pots sit, whether there are
mounting holes, and how tall the tallest part on it is.

**3.6 The regulators.** Confirm both AMS1117s are SOT‑223 (TO‑252). If the 5 V one turns out to be
TO‑220, note that `L1 B1` also holds `L7805CV` (TO‑220, 9 pcs) and `BA033ST` (TO‑220 3.3 V, 4 pcs) —
a deliberate all‑THT option, at the cost of two TO‑220 footprints on a board that is trying to be small.

**3.7 The transistors.** TO‑92 comes flat (all three leads in one row) or staggered (middle lead
offset). The design uses `TO-92_Inline_Wide`. Report which the BC547s are, and confirm the marking
reads BC547**B**.

**3.8 The Pro Mini.** Confirm the silkscreen or crystal: 3.3 V/8 MHz (crystal marked 8.000) is what
the board's 3.3 V rail and firmware expect.

---

## 4. Not in the cabinet

M3 mounting hardware for the four board corners (if they stay), 4 M3 nuts, and hookup wire. The
19 V lead, its fuse, and the NUC's 5 V tap are bench items, not board items.
