#!/usr/bin/env python3
"""
Plot what the ITE's fan demand actually does, from the bench logs.

One SVG, three panels:

  Top - the pooled curve. Every paired sample from every run that has both captures, plotted against the
        temperature of the BOARD (pch_thermal) rather than the cores. The board is the right axis: the 247
        samples where the cores sat at 65 C or hotter while the board stayed under 55 C sit at the floor,
        not on the ramp, and they are drawn as open circles so they cannot be argued away. The faint
        dotted lines are the dwell levels the ITE actually holds - 198, 257, 320, 380 counts, spaced about
        61 counts apart, which is 1/8 of the swing.

  Bottom left - the warm run in time. Board dragged up by hand heat and then a four-core load, then left
        alone: the floor, the climb through the knee near 55 C of board, the plateau at 74-76 %, and the
        release about 30 s after the board fell back through the same knee.

  Bottom right - the hold run in time. A four-core ramp to get past the knee and then 1200 s at a lighter
        load, so the board sits at 68.5-69 C for sixteen flat minutes. The duty sits on 378 counts for all
        of it: the ITE does not integrate the time the board spends hot.

Counts are the Uno's raw ADC reading at the tap of two 10k resistors, so 512 counts is 100 % duty and the
wire's average volts are counts x 5.00 / 1024 / 0.5. The duty axis is therefore counts / 512, which is
exact whatever the top of the ITE's swing turns out to be; the volts axis is what a meter would read.

Run:  python3 bench/plot-curve.py            (add --png for a raster copy to look at)
Writes: docs/bench/06-ite-fan-response.svg
"""
import os
import re
import statistics as st
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.gridspec import GridSpec

DATA = "bench/data"
OUT = "docs/bench/06-ite-fan-response.svg"

# Uno logs carry no timestamps, so each run's alignment is recorded here. The offsets are the scripted
# ones - the NUC capture sleeps a known number of seconds after the Uno capture opens the port (which
# resets the board), and the Uno prints one line per second. Maximizing the correlation instead gives a
# peak about 8 s further along for the warm run, which is the ITE's response lag being absorbed into the
# alignment rather than a better alignment; analyze-heat.py reports the lag separately.
RUNS = [
    ("heat, fans by hand", "temp.log", "stress.log", -4),
    ("cold, fans at max", "cold.log", "coldtemp.log", 0),
    ("stress, fans max", "stress2.log", "stress2-temps.log", -15),
    ("board warmed by hand", "warm.log", "warm-temps.log", -20),
    ("board held hot 20 min", "hold.log", "hold-temps.log", -20),
]

# the two runs drawn as time traces, and what to say beside each trace
TRACES = [
    ("board warmed by hand",
     "The warm run: floor, knee, plateau, release",
     ("warm", "load", "cool"),
     (830, 58.0, "the release\n381 -> 242 counts\nwithin 30 s")),
    ("board held hot 20 min",
     "The hold run: 16 flat minutes at 68.5-69 C, no climb",
     ("ramp", "hold", "cool"),
     (420, 38.0, "16 flat windows, board 68.5-69 C\n378 counts throughout\n"
                 "trend +0.6 counts per minute")),
]

RUN_COLORS = {
    "heat, fans by hand": "#4c72b0",
    "cold, fans at max": "#3aa6a0",
    "stress, fans max": "#8172b3",
    "board warmed by hand": "#c44e52",
    "board held hot 20 min": "#b8860b",
}

DWELLS = (198, 257, 320, 380)     # levels the ITE holds for many seconds, from the pooled histogram
COUNTS_FULL = 512.0               # two 10k resistors, the Uno's 5 V rail as the ADC reference
VCC = 5.00
RATIO = 0.5


def read_uno(path):
    return [int(m.group(1)) for line in open(path) if (m := re.search(r"adc=(\d+)", line))]


def read_nuc(path):
    rows, marks = [], []
    for line in open(path):
        line = line.strip()
        if line.startswith("PHASE"):
            marks.append((line.split()[1], len(rows)))
            continue
        m = re.match(r"^(\d+)\s+pkg=(\d+)\s+pch=(\d+)", line)
        if m:
            rows.append((int(m.group(2)) / 1000.0, int(m.group(3)) / 1000.0))
    return rows, marks


def pair(run):
    """Paired index k corresponds to NUC data row k, because the Uno capture is the longer one."""
    name, unof, nucf, off = run
    a = read_uno(os.path.join(DATA, unof))
    R, marks = read_nuc(os.path.join(DATA, nucf))
    samples = [(a[j], R[j + off][0], R[j + off][1]) for j in range(len(a)) if 0 <= j + off < len(R)]
    return name, samples, marks


def duty(counts):
    return 100.0 * counts / COUNTS_FULL


def duty_to_volts(d):
    """duty % -> average volts on the PWM wire, through the confirmed 0.500 divider"""
    return d * 0.01 * COUNTS_FULL * VCC / 1024.0 / RATIO


def volts_to_duty(v):
    return v * 100.0 / (COUNTS_FULL * VCC / 1024.0 / RATIO)


def trace(ax, samples, marks, title, phases_to_show, note, color):
    """One run in time: the ITE's duty, with the board and the cores on the right axis."""
    t = range(len(samples))
    d = [duty(s[0]) for s in samples]
    ax.plot(t, d, color=color, linewidth=1.3, zorder=4, label="ITE duty, counts / 512")
    ax.fill_between(t, d, 30, color=color, alpha=0.13)
    ax.axhspan(duty(196), duty(262), color="#3aa6a0", alpha=0.13)

    for phase, m in marks:
        if phase not in phases_to_show:
            continue
        ax.axvline(m, color="#999999", linestyle=":", linewidth=1.0)
        ax.text(m + 6, 90.0, phase, fontsize=8.5, color="#555555")

    axb = ax.twinx()
    axb.plot(t, [s[1] for s in samples], color="#2b2b2b", linewidth=0.9, label="package C")
    axb.plot(t, [s[2] for s in samples], color="#4c72b0", linewidth=1.3, label="board C")
    axb.set_ylabel("temperature, C", fontsize=9)
    axb.set_ylim(30, 95)

    if note:
        ax.annotate(note[2], xy=(note[0], note[1]), fontsize=8.2, color="#333333")

    ax.set_xlabel("seconds from the start of the run", fontsize=9)
    ax.set_ylabel("ITE requested duty, %", fontsize=9)
    ax.set_xlim(0, len(samples))
    ax.set_ylim(30, 92)
    ax.grid(True, color="#dddddd", linewidth=0.7)
    ax.set_axisbelow(True)
    ax.set_title(title, fontsize=10.2, loc="left")

    h1, l1 = ax.get_legend_handles_labels()
    h2, l2 = axb.get_legend_handles_labels()
    ax.legend(h1 + h2, l1 + l2, loc="lower center", fontsize=7.4, ncol=3, framealpha=0.92)


def main():
    runs = [pair(r) for r in RUNS]
    by_name = {name: (samples, marks) for name, samples, marks in runs}
    pooled = [(name, samples) for name, samples, _ in runs]

    fig = plt.figure(figsize=(11.0, 9.8))
    fig.patch.set_facecolor("white")
    gs = GridSpec(2, 2, figure=fig, height_ratios=[1.32, 1.0], hspace=0.22, wspace=0.16)
    ax1 = fig.add_subplot(gs[0, :])
    ax2 = fig.add_subplot(gs[1, 0])
    ax3 = fig.add_subplot(gs[1, 1])

    # -------------------------------------------------------------- top panel: the pooled curve
    for w in DWELLS:
        ax1.axhline(duty(w), color="#bbbbbb", linestyle=":", linewidth=1.0, zorder=1)
        ax1.text(71.6, duty(w) + 0.7, f"{w} counts", fontsize=8, color="#777777", ha="right")

    for name, samples in pooled:
        c = RUN_COLORS.get(name, "#888888")
        ax1.scatter([s[2] for s in samples], [duty(s[0]) for s in samples],
                    s=6, c=c, alpha=0.30, linewidths=0, label=f"{name} ({len(samples)} samples)")

    # the samples that separate the two candidates: cores hot, board cool
    disagree = [s for _, ss in pooled for s in ss if s[1] >= 65.0 and s[2] < 55.0]
    ax1.scatter([s[2] for s in disagree], [duty(s[0]) for s in disagree],
                s=48, facecolors="none", edgecolors="#111111", linewidths=1.1,
                label=f"cores >= 65 C, board < 55 C ({len(disagree)} samples)")

    # binned medians against the board
    bins = {}
    for _, samples in pooled:
        for counts, pkg, pch in samples:
            bins.setdefault(int(pch // 3) * 3, []).append(counts)
    xs = sorted(bins)
    for k in xs:
        ax1.plot([k, k + 3], [duty(st.median(bins[k]))] * 2, color="#111111", linewidth=2.4,
                 solid_capstyle="butt", zorder=5)
    ax1.plot([], [], color="#111111", linewidth=2.4, label="median in 3 C bins of board temperature")

    ax1.axvline(55, color="#c44e52", linestyle="--", linewidth=1.2)
    ax1.text(54.4, 36.5, "knee: the board at about 55 C", color="#c44e52", fontsize=9.5, ha="right")
    ax1.text(30.6, 59.5, "floor 46-48 % - 240 counts, 2.33 V on the wire,\n"
                         "flat from 32 C to 54 C of board (2131 samples)",
             fontsize=9.5, color="#333333")
    ax1.text(61.5, 31.2, "board held at 68-69 C:\n377 counts, 73.6 %, 3.68 V\nmax seen 434 counts (85 %)",
             fontsize=9.5, color="#333333")

    ax1.set_xlabel("board temperature - pch_thermal, C")
    ax1.set_ylabel("ITE requested duty, counts / 512")
    ax1.set_xlim(29, 72)
    ax1.set_ylim(30, 92)
    ax1.grid(True, color="#dddddd", linewidth=0.7)
    ax1.set_axisbelow(True)
    ax1.legend(loc="upper left", fontsize=8.2, framealpha=0.92)
    ax1.set_title(f"The ITE's fan demand against the board - "
                  f"{sum(len(s) for _, s in pooled)} paired samples from {len(pooled)} runs",
                  fontsize=11.5, loc="left")

    sec = ax1.secondary_yaxis("right", functions=(duty_to_volts, volts_to_duty))
    sec.set_ylabel("average volts on the PWM wire")

    # ------------------------------------------------- bottom panels: the two runs, in time
    for name, title, phases, note in TRACES:
        ax = ax2 if name == TRACES[0][0] else ax3
        samples, marks = by_name[name]
        trace(ax, samples, marks, title, phases, note, RUN_COLORS[name])

    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    fig.savefig(OUT, format="svg")
    if "--png" in sys.argv[1:]:
        # an inspection copy for reading the plot in a terminal-side viewer; not shipped
        fig.savefig(OUT.replace(".svg", "-check.png"), format="png", dpi=110)
    print(f"wrote {OUT}")
    for name, samples, _ in runs:
        print(f"  {name:24s} {len(samples):4d} paired samples")


if __name__ == "__main__":
    main()
