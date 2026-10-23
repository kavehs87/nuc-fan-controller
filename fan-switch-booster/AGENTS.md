# AGENTS.md — mosfet-fan-switch

12 V brushless fan **speed control** from 3.3 V logic: an ATmega328P Pro Mini drives a small
charge-pump-ish gate booster (Q2 2N7002 + Q3 IRF7416 P‑FET) that switches an IRFZ44N carrying the
fan. `README.md` is the full record with the evidence behind every number. This file is the short
list of things that have already been settled, so they are not re-litigated.

## The circuit is the perfboard build — the PCB is retired

| | status |
|---|---|
| the **perfboard build** | **the circuit itself.** Built, running, quiet across the duty range. Every scope and multimeter number in the README came from it. Pro Mini in sockets, `R1`–`R5` at schematic values (1 k / 10 k), no fitted `C1` or `C2` |
| `mosfet-fan-switch.kicad_pcb`, `pcb/`, `docs/pcb-*` | **retired design record.** Never built, never routed. Keep it as the reason the layout looks like it does; do not route, fab, extend or "clean up" it |

If a task looks like *finish the board layout*, stop and ask — that work is closed on purpose. The
schematic, the simulation and the firmware are still live; only the board is retired.

`C1` and `C2` in the netlist are **not fitted parts** — they model `Ciss` of the IRFZ44N and the
IRF7416. On the perfboard the `/BOOT` node also carries its wiring, and it measures about **8 nF**,
not the netlist's 1.7 nF. Any perfboard prediction that uses 1.7 nF is optimistic by ~3×.

## Settled — do not re-derive, and do not "fix" without new evidence

- **0 % is not `OCR1A = 0`.** In fast PWM that is a 125 ns spike every carrier cycle, which the
  booster turns into ~10.9 V on Q1's gate for tens of microseconds — that was the hum at 0 %. 0 % is
  `COM1A1:0 = 00` plus `digitalWrite(D9, LOW)`. Confirmed silent on the bench.
- **The carrier is 100 Hz, and that is a measured value, not a preference.** The booster's turn-off
  costs a fixed ~170 µs. At 1 kHz that inflated 50 % commanded into ~65–68 % delivered and hummed at
  *every* chopped duty; at 100 Hz the delivered duty is 48.1 % for 50 % commanded and the fan is
  quiet across the range. Do not "improve" this by raising the carrier.
- **Carriers above ~5 kHz are unusable on this board as built** — the off half-period is shorter than
  the turn-off, so the output is stuck on. 25 kHz needs the `Q5` helper fitted (below).
- **Do not put a capacitor across the fan terminals.** It forms an LC tank with the fan's own 10 mH
  and made it measurably worse. The only capacitor wanted there is 100 nF film at J3, for EMI.
- **`R5` stays 10 kΩ.** Dropping it to 1 kΩ collapses `/GATE` from 10.9 V to 6.0 V. `R4 = 1k` /
  `R5 = 10k` is what sets the gate drive level.
- **The fans are 2-wire fans.** No PWM control pin, no tach. Speed control is chopping the supply,
  and a 12 V fan will not start below roughly 4–7 V at its terminals — so 10 % and 20 % duty
  correctly deliver nothing. That is the fan, not a fault.
- **`/DRAIN` undershoots to about −1.2 V at turn-on** (Q1's body diode conducts as D1's freewheel
  current collapses). Known, not the noise source, not worth chasing.

## The NUC side — measured in `../nuc-tach-sim`, do not re-derive it here

`nuc-fan-controller` in the sibling repo has 4 577 paired 1 Hz samples from a **6th-generation i3 NUC**.
Those numbers govern: the ITE's request is **23 kHz** and tops out near **4.90 V**; the header's own fan
supply is **5 V on that machine** and is a deliberate no-connect here; the ITE's duty has a **46–48 %
floor** (under ITE control the fan never stops) and moves in ~12-point rungs; the demand follows the
**board / PCH temperature**, not the cores; and a 5.6× tach claim changes the demand by 1.1 %, so the
tach answer exists only to keep the BIOS happy. The tach is read 1 % low (`ITE_READ_GAIN` 0.990).

- **Counts are not portable between boards.** Those logs are on an Uno's 5 V ADC reference, where 512
  counts is full duty. On this project's 3.3 V Pro Mini the same 2.50 V tap is 775 counts. Carry the
  calibration as volts, or multiply counts by 5 / 3.3.
- **Never feed the ITE's 23 kHz into this board's booster.** The `/BOOT` turn-off is ~170 µs, so above
  ~5 kHz the output is stuck on. Read the request and re-make it at this board's own 100 Hz. The sibling
  project drives at 31.25 kHz because its gate stage is *different* — a BC547 with a 1 kΩ pull-up to
  12 V and a 120 Ω dump, which turns off in well under a microsecond — not the Q2/Q3 booster used here.
- **Pin assignments differ between the two projects.** `nuc-fan-controller` uses D9 for the tach and D11
  for the fan drive; this project's sketches use D9 for the drive and D10 for the tach. Do not mix
  sketches across the two boards.

## Firmware

- Drive pin is **D9 = OC1A, and only D9**. Timer 1 is the module's only 16-bit timer, so the sketches
  write `TCCR1A/B`, `ICR1`, `OCR1A` directly — `analogWrite()` would silently move the drive to Timer 2
  at 980 Hz. On the perfboard bench **D10 (tach) and A0 (`/DEMAND`) are unused**: that board has no
  tach path and no `/DEMAND` tap.
- **Timer 1 has one period.** `/PWM` (OC1A) and `/TACH_PWM` (OC1B) share `ICR1`, so they share the
  frequency and can only differ in duty. 100 Hz happens to be correct for both — the fan drive and the
  tach carrier. Change the fan carrier and the tach carrier moves with it, which the NUC's tachometer
  input rejects; then the tach belongs on Timer 2 (D11 = OC2B) or in software.
- The sketch on the chip is `firmware/fan-switch-freq`. It boots by itself at
  `duty 0 %  OCR1A 0/10000  carrier 100 Hz`. Console at 9600: `0..100` duty, `f <16..25000>` carrier in
  hertz, `?` report, `h` help.
- `firmware/fan-switch-ladder` is the no-serial version (100 % → 50 %, one rung per minute) and now
  shares the 100 Hz default. `fan-switch-serial` and `fan-switch-debug` are left at 1 kHz as the record
  of what the bench ran before the carrier was measured — do not "modernise" them.
- `fan-switch-debug` has a **known, deliberately unfixed bug**: `PORTB ^= _BV(PB6)` where Arduino D10
  is `PB2`. Fix it before reusing that sketch.

## Flashing and commanding the bench

Route is the Pro Mini's **own bootloader** — no ISP, no programmer:

```sh
arduino-cli compile --fqbn arduino:avr:pro:cpu=8MHzatmega328 <sketch>
avrdude -C <avrdude.conf> -c arduino -P /dev/ttyUSB0 -b 57600 -p m328p -U flash:w:<sketch>.ino.hex:i
```

- Bootloader is **57600**, the sketch is **9600** — two baud rates on one wire, which is why a failed
  upload looks like a dead link.
- **DTR must reach RST** (FTDI DTR → J5‑1). Without it `avrdude` just times out.
- **J5 data lines are crossed**: J5‑2 is `TX0` (the module's output) so it goes to the adapter's **RX**;
  J5‑3 is `RX1` goes to the adapter's **TX**. Label-to-label is the wrong way round.
- Opening the port pulses DTR and resets the module, then `ATmegaBOOT` eats any command sent for about
  a second. `set.sh` waits 3 s and sends the command list twice for exactly that reason.
- **No long-lived console daemon.** An earlier one expired silently and left commands unread with nothing
  reporting it. Use the self-contained `set.sh` / `seq.sh`.

The bench lives on a remote host: `ssh root@10.0.5.1`, then `pct exec 130 -- sh -c "..."`; push files with
`scp` to the host `/tmp` then `pct push 130 /tmp/<f> /root/<f>`. `/dev/ttyUSB0` is inside container 130.
`AVR=$(find ~/.arduino15 -name avrdude -type f | head -1)`. Scripts and their notes: `firmware/bench/`.

Probe points: `/GATE` at Q1 pin 1, `/DRAIN` at Q1's tab and at J3 pin 2. Scope on the bench is a Hantek
DSO2D10; its ground clip goes on the board's input ground, which is shared with the Pro Mini.

## Simulation

```bash
./sim/run.sh     # KiCad export -> ngspice -> plots -> variant and fan-count tables
```

Needs KiCad 9 or 10 (`kicad-cli`), `ngspice`, Python 3 with numpy and matplotlib. `sim/out/` is
gitignored and regenerated. Device models are the hand-written `sim/models/*.lib` — read
"About the models" in the README before quoting a simulation number as a fact about the board.
`sim/plot.py` prints the measured perfboard numbers beside the model's optimistic ones; keep them
side by side rather than "correcting" the model to match.

## Parts

Everything already on the bench came from the user's own parts cabinets (the `parts-inventory` MCP:
`list_cabinets`, `get_cabinet`, `get_drawer`, `search_components`). Do not propose buying a part that
might be in a drawer. If the `Q5` gate helper is ever fitted, its parts are already held: a BC547 and
a 4.7 kΩ base resistor. `R3` would then become 1 kΩ and must dissipate ~145 mW, so it has to be chosen
as a power-rated part, not a random 1 kΩ from a drawer.

## Conventions

- **`README.md` is the record.** Every claim carries its evidence, and the evidence type matters:
  measured on the bench, simulated, or inferred. Say which one. Tables with units, not prose numbers.
- Commit subjects follow the existing style: a lowercase area, a colon, then what changed —
  `pcb:`, `sch:`, `schematic + sim:`, `firmware:`, `docs:`.
- Gitignored on purpose: KiCad runtime cruft (`*.lck`, `~*`, `*.bak`, `*.kicad_prl`), `sim/out/`,
  `__pycache__/`, `.DS_Store`.
- `archive/` is history kept for reference. Do not route new work through it.

## Open items

- **Start kick not implemented.** A thermostat wants low duty to mean low speed, but a stopped fan will
  not start at 1.2 V. A brief 100 % before the commanded duty would fix it. Not written.
- **`Q5` helper + `R3 = 1k` is modelled, not fitted.** Emitter to ground, base to `/BOOT` through
  4.7 kΩ, collector to `/GATE`. It restores exact duty from 1 kHz to 25 kHz. Only worth building if a
  carrier above hearing is actually wanted; 100 Hz already solved the noise.
- **The fan's exact start threshold was never pinned down** — somewhere between 20 % and 30 % at 100 Hz.
