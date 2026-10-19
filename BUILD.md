# nuc-fan-controller — Mode B (19 V → 12 V fan supply, follows the NUC's PWM, simulates the tach)

A 124 × 85 mm two-layer board that sits between a 6th-gen NUC's processor-fan header and a
12 V fan in a custom enclosure. It does four things:

1. bucks **19 V → 12 V** for the fan (LM2596T-ADJ, 3 A);
2. makes **5 V then 3.3 V** from that 12 V for a 3.3 V / 8 MHz Arduino Pro Mini;
3. reads the **PWM duty the ITE is asking for** and drives the fan at that duty through a
   12 V low-side switch;
4. reports a **tach rate** that matches what that duty would really produce, so the ITE's
   closed loop closes instead of hunting.

The fan is an ordinary **two-pin 12 V fan**: no PWM input, no tach wire. All the speed
control happens on this board, and all the tach the NUC sees is generated here.

The old Mode A board (fixed-RPM tach simulator only) is archived in
`archive/modeA-2026-10-19/` — nothing on it changed.

---

## Files

| File | What it is |
|---|---|
| `nuc-fan-controller.kicad_pro` / `.kicad_sch` / `.kicad_pcb` | the project |
| `exports/nuc-fan-controller_schematic.pdf` / `.svg` | schematic, openable without KiCad |
| `exports/nuc-fan-controller_board.pdf` | top plot: F.Cu, silk, mask, outline |
| `exports/nuc-fan-controller_board_bottom.pdf` | bottom plot: B.Cu, silk, mask, outline |
| `exports/nuc-fan-controller_board.svg` | top view fitted to the board outline |
| `exports/nuc-fan-controller_bom.csv` | 38 rows — the four mounting holes are board-only, so they are correctly not in it |
| `exports/fab/` | 8 Gerbers + `nuc-fan-controller.drl` + `_pos.csv` + `job.gbrjob`, ready to zip |
| `firmware/nuc-tach-modeB/nuc-tach-modeB.ino` | the sketch |
| `firmware/nuc-tach-modeA/` | the previous fixed-RPM sketch, kept for reference |
| `logs/erc.json`, `logs/drc.json`, `logs/netlist.net` | last ERC / DRC / netlist runs |

**ERC: 0 violations.** **DRC: 0 violations, 0 unconnected items** after
`kicad-cli pcb drc --schematic-parity --refill-zones` (2026-10-19).

Parity reports **one warning**, and it is the intended one: `Pad missing net given by
schematic (unconnected-(J2-Pin_4-Pad4))`. J2 pin 4 is the NUC header's fan-supply wire,
which this board deliberately does not connect; `kicad-cli` names a no-connect pin as a
net and then complains that the pad has no net. It is a wording artefact, not a wiring
error — every other pad on the board matches the schematic exactly.

The schematic is drawn with **wires, not net labels**: every pin reaches its neighbour
through a drawn wire, and the rails are `power:+12V / +5V / +3V3 / GND` symbols sitting on
the pins. Every signal net carries a name tag (`19V`, `SW`, `FB`, `5V`, `FAN_SW`, `BASE`,
`FAN_GATE`, `GATE`, `TACH_BASE`, `NUC_TACH`, `NUC_PWM`, `PWM_IN`, `TACH_OUT`, `FAN_PWM`) so
the print, the netlist, the board and the Gerber netlist all use the same readable names.
Delete a tag and KiCad renames that net to `Net-(…)` everywhere downstream.

---

## The circuit, in five blocks

```
A. 19 V in and the buck                     B. 12 V → 5 V → 3.3 V
   J1 19V IN ─ C1 220 µ/35V ─ U1 LM2596T       +12V ─ U2 AMS1117-5.0 ─ 5V ─ U3 AMS1117-3.3 ─ +3V3
   C2 100n    (VIN 1, GND 3, ON/OFF 5)          C5 10µ + C6 100n on 5V   C7 10µ + C8 100n on 3V3
   SW (U1.2) ─ D1 1N5822 ─ GND
   SW ─ L1 100 µH 6 A toroid ─ +12V             C9 100p sits on NUC_TACH, TP1 is its test point
   +12V ─ C3 470 µ/25V ─ C4 100n ─ GND
   FB (U1.4) ─ RV1 10 k trim ─ R1 1k ─ GND
   FB ─ back to U1.4

C. NUC interface (signals only)             D. 12 V fan speed drive
   J2  NUC fan header                        FAN_PWM (from D11) ─ R6 1k ─ BASE ─ R7 10k ─ GND
     1 GND                                          BASE ─ Q2 BC547B base;  Q2 emitter → GND
     2 NUC_TACH  ─ C9 100p ─ GND                    Q2 collector ─ FAN_GATE ─ R8 1k ─ +12V
     3 NUC_PWM   ─ R3 4.7k                          FAN_GATE ─ R9 120 Ω ─ GATE ─ Q3 gate
                                                   GATE ─ R10 10k ─ GND
     4  (no connect: the header's fan supply)       Q3 IRFZ44N:  gate GATE, drain FAN_SW, source GND
   NUC_TACH ─ Q1 BC547B collector                   FAN_SW ─ D2 1N5819 ─ +12V   (freewheel)
   Q1 base ─ TACH_BASE ─ R2 1k ─ D9 (OC1A)          FAN_SW ─ J3 pin 2 ─ J4 pin 2 ─ C12 100n ─ GND
   Q1 emitter ─ GND                                  +12V ─ J3 pin 1 ─ J4 pin 1
   NUC_PWM ─ R3 4.7k ─ R4 2.2k ─ PWM_IN ─ C10 1µ
                        PWM_IN ─ R5 10k ─ GND       J3 / J4 are the two 2-pin 12 V fan connectors
                        PWM_IN ─ C11 100n ─ GND
                        PWM_IN ─ A0
E. Pro Mini header J5: 1 GND, 2 TACH_OUT (D9), 3 FAN_PWM (D11), 4 PWM_IN (A0), 5 +3V3
```

**Q1 is open-collector.** It only ever pulls `NUC_TACH` low; the pull-up that makes the
high side is inside the NUC. That is the whole point — a push-pull drive from a 3.3 V pin
would hold the tach line ~1.7 V under whatever rail the ITE pulls it to, and would push
that current into the AVR. Q1 cannot do either, and its Vceo (45 V) is indifferent to
which rail the ITE chose.

**Q2 exists because IRFZ44N is not a logic-level FET.** Its Vgs(th) is 2–4 V, so 3.3 V from
a pin is not enough to turn it on. Q2 is driven by the AVR, and R8 1 kΩ pulls Q3's gate to
+12 V whenever Q2 is off. Q2 inverts once; the sketch inverts once more, so the fan ends up
with the duty the ITE asked for. R7 (10 kΩ base pull-down) and R10 (10 kΩ gate pull-down)
hold the two transistors off during the ~1.2 s the Pro Mini's bootloader leaves its pins
floating, which otherwise leaves Q3's gate at the mercy of a 12 V pull-up through 1 kΩ.

**D2 is not optional.** A fan is a motor winding. Every time Q3 turns off, that winding
kicks `FAN_SW` above the 12 V rail; D2 (1N5819, 40 V, 3 A) clamps it back into the rail it
came from. Without it the edge rings into the 12 V rail and the buck is nowhere near fast
enough (150 kHz) to clean it up.

**C9 is 100 pF, not 100 nF.** At 40 Hz with a 1–10 kΩ pull-up, 100 nF gives a 0.1–1 ms time
constant against a 12.5 ms half-period — harmless — but 100 nF on a tach line invites
ringing and crosstalk from a 31.25 kHz fan drive sitting 30 mm away. 100 pF kills RF and
leaves the edges alone.

---

## BOM, and where the parts came from

All through-hole except the two SOT-223 regulators, all already in the cabinet.

| Ref | Value | Footprint | Cabinet |
|---|---|---|---|
| U1 | LM2596T-ADJ | `Package_TO_SOT_THT:TO-220-5_P3.4x3.7mm_StaggerOdd_Lead3.8mm_Vertical` | R1 B4 (1) |
| L1 | 100 µH 6 A, 15 mm toroid | `Inductor_THT:L_Toroid_Horizontal_D16.8mm_P14.70mm_Vishay_TJ3` | L1 D2 (2) |
| D1 | 1N5822 (40 V 3 A, catch diode) | `Diode_THT:D_DO-201AD_P15.24mm_Horizontal` | R1 C3 (9) |
| C1 | 220 µF 35 V | `Capacitor_THT:CP_Radial_D10.0mm_P5.00mm` | L1 A1 |
| C2 | 100 nF | `Capacitor_THT:C_Disc_D3.8mm_W2.6mm_P2.50mm` | L1 C9 |
| C3 | 470 µF 25 V | `Capacitor_THT:CP_Radial_D10.0mm_P5.00mm` | L1 A1 |
| C4 | 100 nF | `Capacitor_THT:C_Disc_D3.8mm_W2.6mm_P2.50mm` | L1 C9 |
| R1 | 1 kΩ | `Resistor_THT:R_Axial_DIN0204_L3.6mm_D1.6mm_P5.08mm_Horizontal` | R1 A2 |
| RV1 | 10 kΩ multi-turn trim (3296W) | `Potentiometer_THT:Potentiometer_Bourns_3296W_Vertical` | R1 D1 |
| U2 | AMS1117-5.0 | `Package_TO_SOT_SMD:SOT-223-3_TabPin2` | L1 B1 (8) |
| U3 | AMS1117-3.3 | `Package_TO_SOT_SMD:SOT-223-3_TabPin2` | L1 B1 (19) |
| C5, C7 | 10 µF | `Capacitor_THT:CP_Radial_D6.3mm_P2.50mm` | L1 A1 |
| C6, C8, C11, C12 | 100 nF | `Capacitor_THT:C_Disc_D3.8mm_W2.6mm_P2.50mm` | L1 C9 |
| C9 | 100 pF | `Capacitor_THT:C_Disc_D3.0mm_W2.0mm_P2.50mm` | L1 C9 (8) |
| C10 | 1 µF | `Capacitor_THT:CP_Radial_D8.0mm_P3.50mm` | L1 A1 |
| R3 | 4.7 kΩ | `Resistor_THT:R_Axial_DIN0204_L3.6mm_D1.6mm_P5.08mm_Horizontal` | R1 A2 |
| R4 | 2.2 kΩ | same | R1 A2 |
| R5, R7, R10 | 10 kΩ | same | R1 B2 |
| R2, R6, R8 | 1 kΩ | same | R1 A2 |
| R9 | 120 Ω | same | R1 A2 |
| Q1, Q2 | BC547B | `Package_TO_SOT_THT:TO-92_Inline_Wide` | R1 D3 (20) |
| Q3 | IRFZ44N | `Package_TO_SOT_THT:TO-220-3_Vertical` | R1 A4 (12) |
| D2 | 1N5819 | `Diode_THT:D_DO-41_SOD81_P10.16mm_Horizontal` | R1 C3 (30) |
| J1 | 19 V IN | `Connector_PinHeader_2.54mm:PinHeader_1x02_P2.54mm_Vertical` | — |
| J2 | NUC fan header | `Connector:FanPinHeader_1x04_P2.54mm_Vertical` | — |
| J3, J4 | FAN 1 / FAN 2 | `Connector_PinHeader_2.54mm:PinHeader_1x02_P2.54mm_Vertical` | — |
| J5 | Pro Mini | `Connector_PinHeader_2.54mm:PinHeader_1x05_P2.54mm_Vertical` | — |
| TP1 | TACH test point | `TestPoint:TestPoint_Pad_D1.5mm` | — |
| MH1–4 | M3 mounting holes | `MountingHole:MountingHole_3.2mm_M3` | — |
| — | Arduino Pro Mini **3.3 V / 8 MHz** | 5-pin header into J5 | L1 C5 (1) |

**Why LM2596T rather than the XL4016E1** (which is not on this board by request): the
LM2596 is 150 kHz, runs at 19 V in with comfortable margin to its 40 V limit, is a 3 A part
in TO-220 with a 6 A toroid and a 40 V/3 A catch diode behind it, and its feedback is a
simple 1.2 V divider you can trim with a screwdriver. The XL4016's internal diode and its
higher frequency buy nothing at 12 V / 1 A. LM2576HVT (R1 B4) is the spare if a lower
12 V current is ever wanted.

**Why 120 Ω for R9** rather than the usual 10–47 Ω gate resistor: there is no 100 Ω or 47 Ω
value in the cabinet in the size needed. It is not the resistor that limits turn-on, though —
with Q2 off the gate is fed through R8 1 kΩ + R9 120 Ω = 1.12 k, so turn-on current is
12 / 1.12k = **10.7 mA**, and R10 10 kΩ pulls the gate down to 12 × 10 / 11.12 = **10.7 V**,
above the 10 V at which IRFZ44N's Rds(on) is specified. R9's real job is the fast half: on
turn-off the gate dumps through 120 Ω alone into Q2's saturated collector (≈ 89 mA), so the
falling edge is under 1 µs. Turn-on is the slow half — 1.7 µs to charge Ciss 1.5 nF, then
≈ 7.5 µs of Miller plateau at 6.1 mA out of the 32 µs period, which costs about 0.3 W in the
FET at a 0.2 A fan and leaves the fan's true duty roughly 7 µs short of the commanded one.
Both are why the RPM mapping is calibrated at the bench rather than derived from arithmetic.
Dropping R8 to 470 Ω (two 1 kΩ in parallel) would cut the plateau to about 3 µs if the FET
ever runs warm; it raises Q2's collector current to 21 mA, which 2.6 mA of base drive still
saturates.

**Two SMD parts.** The SOT-223 regulators are the only ones. They are hand-solderable with
a fine tip and a little flux (drag the tip across the three pads with solder on it), and
their tab pad is the VOUT pad on this footprint, which is the one that wants the most heat.
If you would rather not solder SMD: an AMS1117 in TO-263 will not drop into this footprint,
so keep the SOT-223.

---

## Power budget, and what the board actually carries

| Rail | What hangs off it | Worst case |
|---|---|---|
| 19 V in | the buck only | 1.2 A at 12 V / 1 A out, 85 % efficiency |
| SW (switch node) | D1, L1 | 1 A average, ~1.5 A peak triangular |
| +12 V | C3/C4, RV1's tap, U2, R8, D2, J3, J4 | 1.0 A (two 0.5 A fans) |
| 5 V | U3's input, C5/C6 | ~30 mA |
| +3V3 | Pro Mini, C7/C8, the divider's load side | ~25 mA |
| FAN_SW | Q3's drain, J3/J4 pin 2, D2, C12 | 1.0 A pulsed |

The buck's 3 A and the toroid's 6 A are both far above the 1 A the two fan connectors can
draw, and the IRFZ44N at 1 A dissipates I²·Rds(on) = 1² × 0.045 ≈ **0.045 W** — no heatsink,
and its 55 V Vds is three times the rail. The `Power` net class — 19V, SW, +12V, FAN_SW, +3V3
and GND — is 1.5 mm wide, which at 1 A on 35 µm copper is about 15 °C above ambient; the GND
pours (both layers, 326 stitching vias) carry the return current as a plane rather than as a
trace. The class patterns had to be re-pointed at the renamed nets: they still held the
pre-rename `Net-(C1-Pad1)` strings, which left 19V, SW and FAN_SW routed at 0.2 mm.

The two LDOs drop 7 V and 1.7 V at ~25 mA: 0.18 W and 0.04 W, both trivial for SOT-223.
Do not hang anything bigger off 5 V — U2 is a 1 A part and its junction rises fast in a
closed enclosure.

---

## Before wiring anything: identify the four wires

Intel's *NUC6i5SYB / NUC6i3SYB Thermal Design Power Specification* (H92311-008) publishes no
signal table for the processor-fan header. It publishes only the current limit — **Table 23:
processor fan header, 0.25 A max** — and §2.2 advises against powering external devices from
internal headers at all. So the four wires get identified with a meter, not from a datasheet:

1. **GND** — continuity to the NUC's USB shell or bare chassis, NUC off. → `J2.1`
2. **TACH** — sits high and *moves*: a frequency counter or scope on it while the stock fan
   spins reads 20–350 Hz. It is the only one of the four that pulses. → `J2.2`
3. **PWM** — 21–28 kHz (25 kHz nominal), so a multimeter shows a steady 2–3 V average that
   changes when the fan audibly speeds up. → `J2.3`
4. **Whatever is left** — on this generation that is the header's fan **supply** wire (5 V on
   a stock BSB05505HP fan). → **leave it unconnected.** It goes on J2's fourth pin only so
   you can see it, and the schematic puts a no-connect flag on that pin.

Mark the wires before cutting anything. Cutting first and identifying later is how this gets
reversed, and reversing the supply wire into the tach input is how the ITE gets hurt.

**This board takes no power from the NUC.** Everything it burns comes from the 19 V tap. What
crosses to the NUC side is three signal wires and a shared ground.

---

## Four rules that keep the NUC alive

1. **The stock fan is 5 V, not 12 V.** A 6th-gen NUC ships a BSB05505HP (5 V, 0.4–0.5 A).
   Never splice a 12 V fan's tach or PWM wires into J2: a 12 V fan pulls its tach and PWM
   lines up to its own 12 V rail internally, and 12 V on the ITE's 3–5 V input is how the
   controller dies.
2. **The external 12 V negative must be tied to NUC ground**, through J2.1. Without a common
   reference none of the three signal wires mean anything, and the tach line floats.
3. **Nothing 5 V may touch a 3.3 V pin.** The ATmega328P's absolute maximum on any pin is
   VCC + 0.5 V. This board never puts 5 V on an AVR pin — the Pro Mini is fed 3.3 V on VCC
   (its **RAW** pin is unused), and the PWM line is divided down to 2.96 V before it reaches
   A0. Flash it with a **3.3 V** FTDI.
4. **Measure the PWM wire's amplitude before trusting the divider.** R3 4.7 k + R4 2.2 k in
   series against R5 10 k puts 10 / 16.9 = 0.59 of the line on A0, i.e. **2.96 V for a 5 V
   swing**. If your header's PWM actually swings to 12 V, that node would hit 7.1 V and
   exceed the chip: change **R5 from 10 kΩ to 2.2 kΩ** (both are in the cabinet), which
   brings the node to 2.9 V for a 12 V swing.

The tach line sinks 1–5 mA into the ITE's pull-up and the PWM divider draws 5 V / 16.9 kΩ
≈ 0.3 mA: about 5 mA total from a header rated at 250 mA, and none of it is power.

---

## Board

- 124.0 × 85.0 mm, 2 layers, four M3 mounting holes at the corners.
- **GND poured on both layers** (0.5 mm clearance, thermal relief) with 326 stitching vias,
  so every GND pad lands on a plane on the layer it sits on.
- Net classes: `Power` at **1.5 mm** track / 0.25 mm clearance / 0.7 mm via for `19V`, `SW`,
  `+12V`, `5V`, `FAN_SW`, `+3V3`, `GND`; everything else (the signals) at the 0.2 mm default.
- Routed by Freerouting (Specctra DSN out, SES back in): 112 track segments, 0 unrouted,
  0 violations at the router's own rules, then re-verified against KiCad's rules.
- Flow is left to right: input and buck at the left, the 12 V rail across the middle to the
  LDOs and the Pro Mini header, the NUC interface along the top, the fan drive and the two
  fan connectors at the bottom-right.
- `exports/fab/` plots as-is for a 2-layer prototype order.

One layout compromise worth knowing about: the SW node (U1 → D1 → L1) is a little longer than
a converter data sheet would like, because the toroid's 16.8 mm body needs the room it has.
At 150 kHz with the input caps at the connector and a GND plane directly under it, that costs
a few millivolts of ripple on the 12 V rail and nothing else. If it ever matters, the fix is
a smaller toroid, not a different layout.

---

## Trim the buck before anything else is connected

1. Fit U1, L1, D1, C1–C4, R1, RV1. Fit **nothing** on the 5 V / 3.3 V side yet.
2. Put a meter across C3 (12 V rail), power J1 from the 19 V tap, current-limited.
3. Turn RV1 until the rail reads **12.0 V**. The wiper ends up around **8.8–9.0 kΩ**: the
   divider is `Vout = Vref × (1 + Rtop/Rbottom)` with Rbottom = R1 = 1 kΩ, and the LM2596's
   Vref is specified 1.158–1.238 V (1.198 typical), so 12.0 V lands anywhere in that band.
4. RV1's wiper (pin 2) is strapped to its pin 1 (the FB end) so the pot acts as a two-terminal
   rheostat. If that strap ever breaks, the full 10 kΩ is left in the divider and the rail
   rises only to ≈13.2 V — a fan can live with that long enough to notice.
5. Then fit U2/U3 and check 5 V and 3.3 V. Then fit Q1/Q2/Q3.

Check the 19 V tap's polarity on the connector before plugging in: J1 pin 1 is +19 V, and the
input electrolytic is 35 V, which is not enough headroom to survive a reverse connection for
long.

---

## Firmware

`firmware/nuc-tach-modeB/nuc-tach-modeB.ino`. Board → *Arduino Pro or Pro Mini*,
Processor → **ATmega328 (3.3V, 8MHz)**, programmer → the FTDI on the Pro Mini's own 6-pin
header, board powered from the FTDI and **not** from the 19 V tap while flashing.

Three hardware timers do all the work:

| Pin | Timer | What it makes |
|---|---|---|
| D9 (OC1A) | Timer1, CTC on ICR1, prescaler /8 | the tach square wave, `ICR1 + 1 = 15 × (F_CPU/8) / RPM` → 15 000 000 / RPM at 8 MHz |
| D11 (OC2A) | Timer2, fast PWM, TOP = 255, prescaler /1 | 8 MHz / 256 = **31.25 kHz** fan drive |
| A0 | ADC, 16-sample mean | the ITE's duty, through the divider and C10/C11 |

The ITE counts 2 tach pulses per revolution, so `RPM = 30 × f_tach`: 40 Hz reads 1200 RPM.
Timer2's pin is high for OCR2A counts out of 256; Q2 inverts that once and the sketch inverts
it again (`OCR2A = (100 − duty) × 256 / 100`), so the fan gets the duty the ITE asked for.

The constants at the top of the file are the calibration surface:

| Constant | Default | What it is |
|---|---|---|
| `FAN_RPM_FULL` | 3000 | your fan's RPM at 100 % duty |
| `FAN_RPM_MIN` | 900 | its RPM at `FAN_DUTY_MIN` |
| `FAN_DUTY_MIN` | 20 % | duty below which this fan stalls |
| `TACH_RPM_FLOOR` | 700 | stay above the ITE's stall detect (~1–2 s without pulses = fan error) |
| `TACH_RPM_CEIL` | 10500 | the ITE stops counting above ~11 000 RPM |
| `ADC_AT_100PCT` | 918 | 2.96 V / 3.3 V × 1023 — the two-point calibration's top point |

The sketch smooths the demand over ~300 ms and slews the reported RPM by 400 RPM per 100 ms
update (4000 RPM/s). Both are deliberate: the ITE integrates the tach over about a second, and
a step in the reported rate reads to it as a fan that surged.

It prints one line per update at 9600 baud — `duty_in`, `duty_fan`, `rpm`, `hz`, `adc` — which
is what the calibration below reads.

Expect one boot behaviour: the Pro Mini's bootloader holds the pins quiet for ~1.2 s after
power-on, so the tach line is high and pulseless for the first second of every start, and Q3's
gate is held low by R10 during that window (the fan stays off, which is the safe thing). The
ITE's stall window is 1–2 s. If this NUC's BIOS complains about a fan on boot, suspect that
first, and the fix is a bootloader without the timeout, not a different circuit.

---

## Bench test, in order

Each step answers a question the next one depends on. Do them before the board goes into the
enclosure.

1. **Identify the four NUC wires with a meter** (section above). Write down which is which.
2. **Trim the buck to 12.0 V** with nothing else fitted. Then confirm 5 V and 3.3 V.
3. **Find the fan's stall duty.** Synthesize the ITE's demand instead of buying a PWM box: a
   10 kΩ multi-turn pot across +3V3 and GND, wiper to A0, is a 0–100 % duty knob the sketch
   reads through the same divider it will read in service. Watch `duty_fan` on the serial line
   and the fan itself at 25 %, then 20 %, then 15 %, and write down where it stops. That number
   becomes `FAN_DUTY_MIN`. The sketch never commands below it: the fan idles at its stall duty
   rather than stopping, because a stopped fan whose tach still claims 700 RPM is a lie the ITE
   would never catch and the CPU would pay for.
4. **Measure the fan at two duties.** Point a phone camera at the hub in 240 fps slow-motion
   (or an optical tachometer) at 40 % and at 100 % duty, count blade passes per second × 60 /
   blade count. Those two numbers become `FAN_RPM_MIN` (at `FAN_DUTY_MIN`) and `FAN_RPM_FULL`.
5. **Power the board from the bench supply** (12 V into the buck's output side is *not* the
   test — power J1 from the 19 V tap, current-limited) and confirm the LED blinks at 1 Hz and
   the serial line prints.
6. **Read TP1 with a frequency counter** with the sketch running: it should sit at
   `rpm / 30` Hz to the last digit. It is a hardware timer, so a mismatch means a wiring
   error, not drift.
7. **Then connect the tach side to the NUC only** (J2.1 and J2.2; leave J2.3 and J2.4 open)
   and read the RPM in BIOS or hwmon. If the number appears, Q1's open-collector drive and the
   ITE's pull-up agree with each other.
8. **Then add the PWM wire** (J2.3) and watch the serial line while you load the machine
   (`yes > /dev/null` on every core). `duty_in` should climb with the fan demand the BIOS is
   asking for. If it stays flat, the PWM wire is not where you thought it was.
9. **Only then** connect the fan to J3/J4, and only then cut and splice the stock fan cable.

Step 7 before step 8 before step 9 matters: if something is wrong on the tach line, you want
it wrong while the board is driving nothing but a signal.

Calibration is then two numbers. At idle and at full load, read the fan's real RPM and the
sketch's `rpm`; if the sketch reports too much or too little, move `FAN_RPM_MIN` /
`FAN_RPM_FULL`, not the tach floor or ceiling.

---

## Known limits

- **The tach is a claim, not a measurement.** The board derives the reported RPM from the duty
  it is applying, so it is only honest if the fan really spins at that RPM. If the fan is
  gummed up or the wrong fan is fitted, the board will report a speed that does not exist —
  which is exactly what the ITE cannot tell apart.
- **The ITE's PWM amplitude is assumed to be 5 V.** It is on a 5 V fan header, but the divider
  ratio is the one thing on this board that has to be re-checked if a different NUC generation
  puts 12 V on that line (rule 4 above).
- **Two-pin fans have no tach.** There is no way to confirm the fan is turning other than
  looking at it, or adding a separate tach wire and a 10 kΩ pull-up to +12 V and reading it
  off a spare ADC pin (A1 is free on J5 if you want it — there is no pin on the header today).
- **The ITE stops counting above ~11 000 RPM** and calls a fan stalled after 1–2 s without
  pulses; Timer1's own floor on an 8 MHz board is 229 RPM, so the ITE's limits are the binding
  ones in both directions.
- **The 3.3 V Pro Mini must be the 8 MHz one.** The ATmega328P's speed grade reaches 8 MHz at
  2.7–5.5 V (automotive table) or 10 MHz (industrial table); 16 MHz needs 4.5 V. A 3.3 V board
  carrying a 16 MHz crystal — a common clone — runs the chip outside its datasheet, and a
  crystal outside its spec is a crystal that can fail to start when the machine is cold. Check
  the marking before ordering.
- **Mode A still exists** (`firmware/nuc-tach-modeA/`, `archive/modeA-2026-10-19/`) if you ever
  want the fixed-RPM lie again. It does not run on this board: it has no fan drive and no duty
  read, and its Pro Mini header is 3 pins, not 5.
