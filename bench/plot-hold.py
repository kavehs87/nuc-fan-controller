#!/usr/bin/env python3
"""
Draw the hold test: does the ITE's duty keep climbing while the board refuses to cool?

Two panels, one SVG:

  Top - the run in time. Baseline, a 300 s four-core ramp, 1200 s at a lighter two-core load (the hold),
        then 300 s left alone. The ITE's requested duty against the board's temperature and the cores'.
        The question lives entirely inside the shaded hold band: if the duty walks up the ladder there
        while the board sits still, time-at-temperature is real.

  Bottom - the decisive picture. Every sample plotted against board temperature, coloured by which phase
        it came from, with the ramp's median and the hold's median drawn as bars in each 3 C band. If the
        duty is a function of board temperature alone those two bars coincide. If the ITE integrates the
        time the board has been hot, the hold bar sits above the ramp bar. It is the same comparison
        analyze-hold.py reports as "early against late".

Counts are the Uno's raw ADC reading at the tap of two 10k resistors: 512 counts is 100 % duty, and the
wire's average volts are counts x 5.00 / 1024 / 0.5.

Run:  python3 bench/plot-hold.py bench/data/hold.log bench/data/hold-temps.log -20
Writes: docs/bench/07-ite-hold-test.svg
"""
import os
import re
import statistics as st
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

OUT = "docs/bench/07-ite-hold-test.svg"
COUNTS_FULL = 512.0
VCC = 5.00
RATIO = 0.5

PHASE_COLORS = {"baseline": "#3aa6a0", "ramp": "#4c72b0", "hold": "#c44e52", "cool": "#8172b3"}


def read_uno(path):
    return [int(m.group(1)) for line in open(path) if (m := re.search(r"adc=(\d+)", line))]


def read_nuc(path):
    rows, marks = [], []
    for line in open(path):
        line = line.strip()
        if line.startswith(("PHASE", "NOTE", "GUARD")):
            if line.startswith("PHASE"):
                marks.append((line.split()[1], len(rows)))
            continue
        m = re.match(r"^(\d+)\s+pkg=(\d+)\s+pch=(\d+)", line)
        if m:
            rows.append((int(m.group(2)) / 1000.0, int(m.group(3)) / 1000.0))
    return rows, marks


def duty(c):
    return 100.0 * c / COUNTS_FULL


def main():
    uno_path, nuc_path, off = sys.argv[1], sys.argv[2], int(sys.argv[3])
    a = read_uno(uno_path)
    R, marks = read_nuc(nuc_path)
    samples = [(a[j], R[j + off][0], R[j + off][1]) for j in range(len(a)) if 0 <= j + off < len(R)]
    phase_at = {i: p for p, i in marks}
    phases, cur = [], None
    for k in range(len(samples)):
        cur = phase_at.get(k, cur)
        phases.append(cur)

    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(11.0, 8.6))
    fig.patch.set_facecolor("white")

    # ------------------------------------------------------------------ top: the run in time
    t = range(len(samples))
    d = [duty(s[0]) for s in samples]
    if "hold" in phases:
        h0 = phases.index("hold")
        h1 = len(phases) - 1 - phases[::-1].index("hold")
        ax1.axvspan(h0, h1, color="#c44e52", alpha=0.07)
        ax1.text(h0 + 8, 89.0, f"the hold: {h1 - h0} s at a lighter load", fontsize=9, color="#c44e52")
    ax1.plot(t, d, color="#c44e52", linewidth=1.5, zorder=4, label="ITE duty, counts / 512")
    ax1.fill_between(t, d, 30, color="#c44e52", alpha=0.12)

    for phase, m in marks:
        if phase in ("baseline", "end"):
            continue
        ax1.axvline(m, color="#999999", linestyle=":", linewidth=1.0)
        ax1.text(m + 6, 84.0, phase, fontsize=8.5, color="#555555")

    ax1b = ax1.twinx()
    ax1b.plot(t, [s[1] for s in samples], color="#2b2b2b", linewidth=1.0, label="package C (the cores)")
    ax1b.plot(t, [s[2] for s in samples], color="#4c72b0", linewidth=1.5, label="board C (pch)")
    ax1b.set_ylabel("temperature, C")
    ax1b.set_ylim(30, 95)
    ax1b.legend(loc="center right", fontsize=8.2, framealpha=0.92)

    ax1.set_xlabel("seconds from the start of the run")
    ax1.set_ylabel("ITE requested duty, %")
    ax1.set_xlim(0, len(samples))
    ax1.set_ylim(30, 92)
    ax1.grid(True, color="#dddddd", linewidth=0.7)
    ax1.set_axisbelow(True)
    ax1.legend(loc="center left", fontsize=8.2, framealpha=0.92)
    ax1.set_title("Held hot and flat: does the ITE keep raising its duty anyway?", fontsize=11.5, loc="left")

    # -------------------------------------------- bottom: same temperature, ramp against hold
    for phase in ("baseline", "ramp", "hold", "cool"):
        ss = [s for s, p in zip(samples, phases) if p == phase]
        if not ss:
            continue
        ax2.scatter([s[2] for s in ss], [duty(s[0]) for s in ss], s=7,
                    c=PHASE_COLORS[phase], alpha=0.35, linewidths=0,
                    label=f"{phase} ({len(ss)} samples)")

    bands = {}
    for s, p in zip(samples, phases):
        bands.setdefault(int(s[2] // 3) * 3, {}).setdefault(p, []).append(s[0])
    for k in sorted(bands):
        for phase, y in (("ramp", 0), ("hold", 1)):
            v = bands[k].get(phase, [])
            if len(v) < 8:
                continue
            ax2.plot([k, k + 3], [duty(st.median(v))] * 2, color=PHASE_COLORS[phase],
                     linewidth=3.0, solid_capstyle="butt", zorder=5)

    ax2.set_xlabel("board temperature - pch_thermal, C")
    ax2.set_ylabel("ITE requested duty, counts / 512")
    ax2.set_xlim(38, 74)
    ax2.set_ylim(35, 92)
    ax2.grid(True, color="#dddddd", linewidth=0.7)
    ax2.set_axisbelow(True)
    ax2.legend(loc="upper left", fontsize=8.2, framealpha=0.92)
    ax2.set_title("The same board temperature reached quickly, and then held - the bars are each phase's median",
                  fontsize=11.5, loc="left")

    fig.tight_layout()
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    fig.savefig(OUT, format="svg")
    if "--png" in sys.argv[4:]:
        fig.savefig(OUT.replace(".svg", "-check.png"), format="png", dpi=110)
    print(f"wrote {OUT}")

    print(f"\n{len(samples)} paired samples at offset {off:+d} s")
    for phase in ("baseline", "ramp", "hold", "cool"):
        idx = [i for i, p in enumerate(phases) if p == phase]
        if idx:
            pch = [samples[i][2] for i in idx]
            print(f"  {phase:9s} n={len(idx):4d}  board {min(pch):5.1f}..{max(pch):5.1f} C "
                  f"  demand median {st.median([samples[i][0] for i in idx]):6.1f} counts")
    print("\nband by band, ramp median against hold median")
    for k in sorted(bands):
        r, h = bands[k].get("ramp", []), bands[k].get("hold", [])
        if len(r) >= 8 and len(h) >= 8:
            print(f"  board {k:3d}-{k+3:<3d}C  ramp n={len(r):3d} med {st.median(r):6.1f}   "
                  f"hold n={len(h):3d} med {st.median(h):6.1f}   hold - ramp {st.median(h)-st.median(r):+6.1f} counts")


if __name__ == "__main__":
    main()
