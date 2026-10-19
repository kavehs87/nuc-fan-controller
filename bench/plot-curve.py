#!/usr/bin/env python3
"""
Plot what the ITE's fan demand actually does, from the bench logs.

Two panels, one SVG:

  Top - the pooled curve. Every paired sample from every run that has both captures, plotted against the
        temperature of the BOARD (pch_thermal) rather than the cores. The board is the right axis: the 196
        samples where the cores sat at 65 C or hotter while the board stayed under 55 C sit at the floor,
        not on the ramp, and they are drawn as open circles so they cannot be argued away. The faint dotted
        lines are the dwell levels the ITE actually holds - 198, 257, 320, 380 counts, spaced about 61
        counts apart, which is 1/8 of the swing.

  Bottom - one run in time. The warm run: the board dragged up by hand heat and then a four-core load, then
        left alone. It shows the floor, the climb through the knee near 55 C of board, the plateau at
        74-76 % while the board sat at 68 C, and the release about 30 s after the board fell back through
        the same knee.

Counts are the Uno's raw ADC reading at the tap of two 10k resistors, so 512 counts is 100 % duty and the
wire's average volts are counts x 5.00 / 1024 / 0.5. The duty axis is therefore counts / 512, which is
exact whatever the top of the ITE's swing turns out to be; the volts axis is what a meter would read.

Run:  python3 bench/plot-curve.py
Writes: docs/bench/06-ite-fan-response.svg
"""
import os
import re
import statistics as st
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

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


def main():
    runs = [pair(r) for r in RUNS]
    pooled = [(name, samples) for name, samples, _ in runs]

    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(11.0, 8.6))
    fig.patch.set_facecolor("white")

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

    # ------------------------------------------------------- bottom panel: the warm run, in time
    name, warm, marks = next(r for r in runs if r[0] == "board warmed by hand")
    t = range(len(warm))
    d = [duty(s[0]) for s in warm]
    ax2.plot(t, d, color="#c44e52", linewidth=1.6, zorder=4, label="ITE duty, counts / 512")
    ax2.fill_between(t, d, 30, color="#c44e52", alpha=0.13)
    ax2.axhspan(duty(196), duty(262), color="#3aa6a0", alpha=0.13)
    ax2.text(8, 54.5, "the floor band, 196-262 counts", fontsize=9, color="#1f6f6a")

    ax2b = ax2.twinx()
    ax2b.plot(t, [s[1] for s in warm], color="#2b2b2b", linewidth=1.1, label="package C (the cores)")
    ax2b.plot(t, [s[2] for s in warm], color="#4c72b0", linewidth=1.6, label="board C (pch)")
    ax2b.set_ylabel("temperature, C")
    ax2b.set_ylim(30, 95)
    ax2b.legend(loc="upper right", fontsize=8.2, framealpha=0.92)

    label = {"warm": "start warming the board", "load": "four-core load", "cool": "leave it alone",
             "end": ""}
    for phase, m in marks:
        if phase in ("baseline", "end") or not label.get(phase):
            continue
        ax2.axvline(m, color="#999999", linestyle=":", linewidth=1.0)
        ax2.text(m + 6, 88.5, label[phase], fontsize=8.5, color="#555555")

    ax2.annotate("the release: 381 -> 242 counts within 30 s\nof the board falling back through 55 C",
                 xy=(810, duty(300)), xytext=(830, 58), fontsize=8.5, color="#333333",
                 arrowprops=dict(arrowstyle="->", color="#777777", linewidth=0.9))

    ax2.set_xlabel("seconds from the start of the run")
    ax2.set_ylabel("ITE requested duty, %")
    ax2.set_xlim(0, len(warm))
    ax2.set_ylim(30, 92)
    ax2.grid(True, color="#dddddd", linewidth=0.7)
    ax2.set_axisbelow(True)
    ax2.legend(loc="center left", fontsize=8.2, framealpha=0.92)
    ax2.set_title("One run in time: the floor, the climb through the knee, the plateau, the release",
                  fontsize=11.5, loc="left")

    fig.tight_layout()
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
