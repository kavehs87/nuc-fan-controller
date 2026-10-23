# AGENTS.md — nuc-fan-controller

One repo, two halves. The **perfboard fan‑switch build** lives under `fan-switch-booster/`; the
**`nuc-fan-controller` enclosure board** lives at the root. `README.md` is the record. This file is the
short list of what is already settled, so it is not re‑litigated.

## Read in this order

1. `README.md` — the merged record, the measured facts both halves share, and the four ways they disagree;
2. `fan-switch-booster/AGENTS.md` — the settled list for the booster half, including how to flash and
   command the remote bench;
3. `BUILD.md` — the bench sequence for the enclosure board: header identification with a meter, setting
   the module to 12.0 V, calibration, order of work.

## Which half wins an argument

- **How a chopped 12 V two‑pin fan behaves** — the perfboard decides. Carrier frequency, delivered duty,
  the fan's start threshold, what the noise was: all measured on that board.
- **How the NUC's ITE behaves** — the breadboard runs at the root decide. Frequency, amplitude, floor,
  ladder, what the demand follows: all measured on that machine.

Neither half's numbers may be moved into the other half's circuit without saying which circuit they were
measured on. A number that crossed without that sentence is how a 170 µs turn‑off gets mistaken for a
design that tolerates 31 kHz.

## Settled — the NUC side (4 577 paired 1 Hz samples, 6th‑gen i3)

- The ITE's request is **23 kHz** and tops out near **4.90 V**. The header's own fan supply is **5 V** on
  this machine and is a **deliberate no‑connect** (`J2` pin 4). Never connect it, and never power 12 V fans
  from it.
- The demand has a **46–48 % floor** — 1 946 samples of it, no sample below 100 counts of 717. Under ITE
  control the fan never stops, so `FAN_DUTY_MIN` is a clamp against a broken sense wire, not an operating
  point the ITE reaches.
- The demand is **stepped**: dwell rungs 198 / 257 / 320 / 380 counts, an 11.9‑point quantum, and the ITE
  dwells on rungs and passes through everything else.
- It follows the **board / PCH temperature, not the cores** — cores at 73 °C moved the demand by nothing.
  It climbs in ~75 s and releases in ~30 s, and it is **not an integrator**: 16 flat minutes at 68.5 °C held
  378 counts.
- Reported speed is **not in the loop**: a 5.6× tach claim moved the duty 1.1 %. The tach exists to keep the
  BIOS happy. `ITE_READ_GAIN` = 0.990, `RPM = 30 × f_tach` (IT8607E counts 2 pulses per turn).
- Because the ITE does not ramp on a timer, `DEMAND_TAU_S` does not have to outwait one. Do not "fix" it.

## Settled — the booster side

The full list, with the measurements behind each line, is `fan-switch-booster/AGENTS.md`. The headlines:

- **0 % is not `OCR1A = 0`** — clear `COM1A1:0` and hold D9 low as GPIO.
- **The carrier is 100 Hz, and it is a measurement.** The booster's turn‑off costs a fixed ~170 µs; at
  1 kHz that inflated 50 % into 65–68 % delivered and hummed at every chopped duty. Do not raise it.
- **Above ~5 kHz this board is stuck on as built.** The `Q5` helper plus `R3 = 1k` is modelled, not fitted.
- **No capacitor across the fan terminals** — it forms an LC tank with the fan's own 10 mH.
- **`R5` stays 10 kΩ**; `R4 = 1k` / `R5 = 10k` is what sets 10.9 V of gate drive.
- **`/BOOT` carries ~8 nF on the perfboard**, not the netlist's 1.7 nF. Predictions built on 1.7 nF are
  optimistic by ~3×.
- **The PCB inside `fan-switch-booster/` is retired** — `mosfet-fan-switch.kicad_pcb`, `pcb/`,
  `docs/pcb-*`. Never built, never routed. Do not route, fab, extend or "clean up" it. If a task looks
  like *finish that layout*, stop and ask.

## Four traps when the two halves are mixed

| trap | the perfboard | the enclosure board |
|---|---|---|
| **pin map** | drive **D9**, tach D10 (unused on the bench) | drive **D11**, tach **D9** |
| **polarity** | non‑inverting: pin high → fan on | `Q2` inverts, and `nuc-tach-modeB` asks for the complement to undo it |
| **carrier** | 100 Hz | 31.25 kHz, exactly 8 MHz / 256 |
| **ADC scale** | 3.3 V reference: the 2.50 V tap is **775 counts** | the logs are on an **Uno's 5 V** reference, where the same tap is 512 counts |

Carry calibration as **volts**, not counts. A sketch written for one board drives the wrong pin, at the
wrong polarity, on the other.

And one thing the CAD has not caught up with: the bench settled on a **10 kΩ / 10 kΩ** divider (2.50 V tap,
0.8 V headroom), while `nuc-fan-controller.kicad_sch` still carries `R3` 4.7 k → `R4` 2.2 k over `R5` 10 k,
which taps 2.96 V and leaves 0.34 V. Fix it in the schematic before building.

## Three things that break hardware

1. a 12 V fan's tach or PWM wire spliced into the NUC header — that fan pulls those lines to its own 12 V;
2. a 5 V FTDI on a 3.3 V Pro Mini — ATmega328P absolute maximum on any pin is **VCC + 0.5 V**;
3. a BC547 fitted in the onsemi **C‑B‑E** order when this board is drawn and routed for the NXP/Philips
   **E‑B‑C** order — meter the two of them before they go in, `BUILD.md` says how.

Flash with Board → *Arduino Pro or Pro Mini*, Processor → **ATmega328 (3.3V, 8MHz)**.

## Commands

Enclosure board, from the repo root:

```sh
sh logs/export.sh                       # rebuilds exports/: PDF, SVG, BOM, Gerbers, drill
kicad-cli sch erc nuc-fan-controller.kicad_sch --output logs/erc.json --format json --severity-all
python3 logs/build1l.py                 # the board is generated: parts, drawn bars, holes, router
kicad-cli pcb drc nuc-fan-controller.kicad_pcb --output logs/drc.json --format json \
    --severity-all --refill-zones --save-board
python3 logs/verify.py
```

`layout.py`, `genwires.py` and `applywires.py` are **parked** — their tables still describe the schematic
as it was before it was edited by hand, and running them now would undo work. The schematic and the board
are the source of truth.

Booster half, from `fan-switch-booster/`:

```sh
./sim/run.sh                            # KiCad netlist -> ngspice deck -> simulate -> variants -> plots
V=/Users/kaveh/Documents/Projects/schemdraw-mcp-server/.venv/bin/python3
$V sim/variants.py && $V sim/plot.py    # if the default python3 has no matplotlib
```

`sim/run.sh` resolves every path from its own directory, so it works unchanged from inside the subtree.
It needs `kicad-cli`, `ngspice`, and a Python 3 with numpy and matplotlib; on this machine neither system
python has matplotlib, which is why the second line exists. `sim/plot.py` reads `sim/out/variants.csv`, so
variants must run before plotting. `sim/out/` is gitignored and regenerated (~14 MB). Read *About the
models* in `fan-switch-booster/README.md` before quoting a simulation number as a fact about the board, and
keep `plot.py`'s measured perfboard numbers printed beside the model's optimistic ones rather than
"correcting" the model to match.

## The remote bench

`ssh root@10.0.5.1`, then `pct exec 130 -- sh -c "..."`. Push with `scp` to the host's `/tmp` then
`pct push 130 /tmp/<f> /root/<f>`. `/dev/ttyUSB0` is inside container 130.
`AVR=$(find ~/.arduino15 -name avrdude -type f | head -1)`. Scripts and their notes:
`fan-switch-booster/firmware/bench/` — `set.sh`, `seq.sh`, `flash-bootloader.sh`, `verify-flash.sh`. No
long‑lived console daemon: an earlier one expired silently.

## Conventions

- **`README.md` is the record.** Every claim carries its evidence, and the type of evidence matters:
  measured on the bench, simulated, or inferred. Say which one. Tables with units, not prose numbers.
- Commit subjects: a lowercase area, a colon, then what changed — `pcb:`, `sch:`, `firmware:`, `docs:`,
  `bench:`.
- Gitignored on purpose: KiCad runtime cruft (`*.lck`, `~*`, `*.bak`, `*.kicad_prl`, `*-backups/`),
  `sim/out/`, `__pycache__/`, `.DS_Store`, and `images/` — the phone originals; `docs/bench/` carries the
  cropped, captioned versions.
- **Do not push to the GitHub remote without being asked.**

## Repo shape after the merge

Merged in October 2026 with `--allow-unrelated-histories` from a local remote, so the booster's 22 commits
and its two checkpoint tags are part of this repo's history rather than a copied snapshot. The subtree
keeps its own `.gitignore`, KiCad project, symbol and footprint tables, sim pipeline, firmware and docs, so
nothing at the root collides — and the two KiCad projects live in different directories on purpose:
`nuc-fan-controller` at the root, `mosfet-fan-switch` inside `fan-switch-booster/`.
