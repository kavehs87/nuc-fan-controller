# Bench photographs and graphs

What each file is. The numbers, the log pairs they came from, and the commands that reproduce them are in
**`../../README.md`**, *On the bench* and *Reproducing the measurements*.

| file | what it shows |
|---|---|
| `01-bench-overview.jpg` | the bench: NUC mainboard, two 12 V fans, the Uno and the breadboard |
| `02-fan-header.jpg` | the NUC's fan header with the measurement harness in it |
| `03-divider-on-breadboard.jpg` | the PWM divider on the breadboard — the two resistors that tap the ITE's request down to something an ADC can read |
| `04-tach-at-40hz.jpg` | the fabricated tach square wave on the scope, at the low end of the carrier window |
| `05-bios-reads-1186.jpg` | the BIOS reporting **CPU FAN 1186 RPM** against a 1 200 RPM claim — the measured tach read gain of 0.990 |
| `06-ite-fan-response.svg` | the ITE's fan demand plotted against board temperature, with the duty floor and the dwell rungs visible |
| `07-ite-hold-test.svg` | the hold test: flat and hot for 20 minutes, and the same temperature reached quickly against reached and held |

Provenance: `01`–`05` were cropped from the phone originals by `../bench/prepare-photos.py`, whose input
directory was purged in the October 2026 cleanup — the crops are the surviving half, the recipe is in the
script. `06` and `07` are drawn from `../bench/data/` by `../bench/plot-curve.py` and
`../bench/plot-hold.py`; re-running them redraws the SVGs cosmetically, so check the diff before committing
one.
