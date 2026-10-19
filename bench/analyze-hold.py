#!/usr/bin/env python3
"""
Does the ITE's fan demand depend on how LONG the board has been hot, or only on how hot it is?

The theory being tested: the ITE raises its requested duty while the board refuses to cool, so a board
held at a constant temperature above the knee should see the duty climb with elapsed time - possibly
accelerating past some threshold. The alternative: the duty is a function of board temperature alone, and
everything that looked like a climb in the shorter runs was the temperature moving underneath it.

The four runs already in bench/data/ cannot answer this, because in all of them the temperature was
changing while the demand was being measured. The hold run is built for the question: a 300 s four-core
ramp to push the board past the knee, then 1200 s at a lighter two-core load so the board sits near a
plateau, then 300 s left alone. The test is what the demand does during those 1200 seconds while the
board's own temperature is flat.

Three separate reads, because one can be fooled and three are hard to fool:

  1. WINDOW TREND. 60 s windows in which the board's median temperature stays within FLAT_C of the
     plateau. Regress the window's median demand on window time. If time-at-temperature drives the duty,
     the slope is positive and larger than the drift in the board's own temperature can explain.

  2. EARLY AGAINST LATE AT THE SAME TEMPERATURE. Take the samples in a temperature band, split them by
     whether they came the first time the run passed through that band or during the long hold, and
     compare. A pure temperature function gives equal medians.

  3. TWO-VARIABLE FIT. Least squares of demand on (board temperature, seconds since the knee was
     crossed). Reports how much of the variance each variable carries alone and together - the honest
     way to say whether time earns its place in the model.

Run:  python3 bench/analyze-hold.py bench/data/hold.log bench/data/hold-temps.log -20
"""
import os
import re
import statistics as st
import sys

FLAT_C = 0.8          # a window counts as "the board held flat" if its median is this close to the plateau
WINDOW_S = 60
COUNTS_FULL = 512.0
VCC = 5.00
RATIO = 0.5


def read_uno(path):
    return [int(m.group(1)) for line in open(path) if (m := re.search(r"adc=(\d+)", line))]


def read_nuc(path):
    rows, marks = [], []
    for line in open(path):
        line = line.strip()
        if line.startswith(("PHASE", "NOTE", "GUARD")):
            marks.append((line, len(rows)))
            continue
        m = re.match(r"^(\d+)\s+pkg=(\d+)\s+pch=(\d+)", line)
        if m:
            rows.append((int(m.group(2)) / 1000.0, int(m.group(3)) / 1000.0))
    return rows, marks


def pair(uno_path, nuc_path, off):
    a = read_uno(uno_path)
    R, marks = read_nuc(nuc_path)
    samples = [(a[j], R[j + off][0], R[j + off][1]) for j in range(len(a)) if 0 <= j + off < len(R)]
    # paired index k corresponds to NUC data row k
    phase_at = {}
    for text, i in marks:
        if text.startswith("PHASE"):
            phase_at[i] = text.split()[1]
    phases, cur = [], None
    for k in range(len(samples)):
        cur = phase_at.get(k, cur)
        phases.append(cur)
    return samples, phases


def volts(counts):
    return counts * VCC / 1024.0 / RATIO


def lsq(x, y):
    """slope, intercept for y = a*x + b"""
    mx, my = st.mean(x), st.mean(y)
    den = sum((a - mx) ** 2 for a in x)
    if den == 0:
        return 0.0, my
    a = sum((p - mx) * (q - my) for p, q in zip(x, y)) / den
    return a, my - a * mx


def r2(x, y, a, b):
    my = st.mean(y)
    ss = sum((q - my) ** 2 for q in y)
    res = sum((q - (a * p + b)) ** 2 for p, q in zip(x, y))
    return 1.0 - res / ss if ss else 0.0


def fit2(x1, x2, y):
    """least squares y = b0 + b1*x1 + b2*x2 by normal equations (2 variables, no numpy needed)"""
    n = len(y)
    S = [[n, sum(x1), sum(x2)],
         [sum(x1), sum(a * a for a in x1), sum(a * b for a, b in zip(x1, x2))],
         [sum(x2), sum(a * b for a, b in zip(x1, x2)), sum(a * a for a in x2)]]
    T = [sum(y), sum(a * b for a, b in zip(x1, y)), sum(a * b for a, b in zip(x2, y))]
    # Gaussian elimination
    for i in range(3):
        piv = S[i][i]
        if abs(piv) < 1e-9:
            return None
        for j in range(i + 1, 3):
            f = S[j][i] / piv
            S[j] = [s - f * t for s, t in zip(S[j], S[i])]
            T[j] = T[j] - f * T[i]
    b = [0.0] * 3
    for i in range(2, -1, -1):
        b[i] = (T[i] - sum(S[i][j] * b[j] for j in range(i + 1, 3))) / S[i][i]
    pred = [b[0] + b[1] * p + b[2] * q for p, q in zip(x1, x2)]
    my = st.mean(y)
    ss = sum((q - my) ** 2 for q in y)
    res = sum((q - p) ** 2 for p, q in zip(pred, y))
    return b, (1.0 - res / ss if ss else 0.0)


def main(args):
    uno, nuc, off = args[1], args[2], int(args[3])
    samples, phases = pair(uno, nuc, off)
    print(f"{len(samples)} paired samples at offset {off:+d} s")
    for ph in ("ramp", "hold", "cool"):
        idx = [i for i, p in enumerate(phases) if p == ph]
        if idx:
            pch = [samples[i][2] for i in idx]
            print(f"  {ph:6s} n={len(idx):4d}  board {min(pch):.1f}..{max(pch):.1f} C "
                  f"(median {st.median(pch):.1f})  demand median {st.median([samples[i][0] for i in idx])} counts")

    hold = [i for i, p in enumerate(phases) if p == "hold"]
    if not hold:
        print("\nno hold phase in this log")
        return
    plateau = st.median([samples[i][2] for i in hold])
    print(f"\nplateau (median board temperature through the hold): {plateau:.1f} C")

    # ---------------------------------------------------------------- 1. window trend
    print(f"\n1. {WINDOW_S} s windows during the hold")
    print(f"  {'t':>6}  {'board':>13}  {'cores':>6}  {'demand med':>11}  {'mode':>6}  {'range':>9}  flat")
    wins = []
    for start in range(hold[0], hold[-1] + 1, WINDOW_S):
        w = [i for i in hold if start <= i < start + WINDOW_S]
        if len(w) < WINDOW_S * 0.6:
            continue
        pch = [samples[i][2] for i in w]
        pkg = [samples[i][1] for i in w]
        d = [samples[i][0] for i in w]
        try:
            mode = st.mode(d)
        except st.StatisticsError:
            mode = round(st.median(d))
        flat = abs(st.median(pch) - plateau) <= FLAT_C
        wins.append((start, st.median(pch), st.median(pkg), st.median(d), mode, min(d), max(d), flat))
        print(f"  {start:5d}s  {min(pch):5.1f}-{max(pch):5.1f}  {st.median(pkg):5.1f}  {st.median(d):8.1f}   "
              f"{mode:6d}  {min(d):4d}-{max(d):4d}  {'yes' if flat else '-'}")

    flat_wins = [w for w in wins if w[7]]
    if len(flat_wins) >= 4:
        a, b = lsq([w[0] for w in flat_wins], [w[3] for w in flat_wins])
        rr = r2([w[0] for w in flat_wins], [w[3] for w in flat_wins], a, b)
        aT, bT = lsq([w[0] for w in flat_wins], [w[1] for w in flat_wins])
        print(f"\n  across the {len(flat_wins)} flat windows: demand trend {a * 60:+.1f} counts per minute "
              f"(R^2 {rr:.2f}); board temperature trend {aT * 60:+.2f} C per minute")
        # how much of the demand trend the board's own drift could account for, using the pooled ladder's
        # ~61 counts per 1/8 rung and about 3 C per rung
        temp_slope = 61.0 / 3.0
        print(f"  using the ladder's {temp_slope:.1f} counts per C, the temperature drift explains "
              f"{aT * 60 * temp_slope:+.1f} counts per minute of the {a * 60:+.1f} seen")
    else:
        print("\n  too few flat windows to trend")

    # ------------------------------------------------- 2. early against late at the same temperature
    print("\n2. the same board temperature, first time through against during the long hold")
    bands = {}
    for i, (d, pkg, pch) in enumerate(samples):
        bands.setdefault(int(pch // 3) * 3, []).append((i, d, pkg, pch))
    for k in sorted(bands):
        v = bands[k]
        early = [x[1] for x in v if phases[x[0]] != "hold"]
        late = [x[1] for x in v if phases[x[0]] == "hold"]
        if len(early) >= 10 and len(late) >= 10:
            print(f"  board {k:3d}-{k+3:<3d}C  early n={len(early):4d} med {st.median(early):6.1f}   "
                  f"hold n={len(late):4d} med {st.median(late):6.1f}   difference {st.median(late)-st.median(early):+6.1f} counts")

    # ---------------------------------------------------------------- 3. two-variable fit
    print("\n3. demand against board temperature alone, and against temperature plus time")
    knee = 55.0
    idx = [i for i in range(len(samples)) if samples[i][2] >= knee]
    if len(idx) > 60:
        crossed = min(idx)
        y = [samples[i][0] for i in idx]
        xT = [samples[i][2] for i in idx]
        xS = [float(i - crossed) for i in idx]
        a1, b1 = lsq(xT, y)
        print(f"  temperature only:  {len(idx)} samples above {knee:.0f} C  demand = {a1:+.1f} per C "
              f"{b1:+.1f}   R^2 {r2(xT, y, a1, b1):.3f}")
        f = fit2(xT, xS, y)
        if f:
            (b0, bT, bS), rr = f
            print(f"  plus time:         demand = {b0:+.1f} {bT:+.1f} per C {bS / 60:+.2f} per minute"
                  f"   R^2 {rr:.3f}")
            gain = rr - r2(xT, y, a1, b1)
            print(f"  time adds {gain:+.3f} of R^2 for {bS / 60:+.2f} counts per minute at constant temperature")
            if abs(bS) * 60 < 2.0 and gain < 0.02:
                print("  -> the theory is not supported by this run: at constant board temperature the duty "
                      "does not climb.")
            elif bS > 0:
                print("  -> the theory holds: the duty keeps climbing while the board sits still.")
    else:
        print(f"  only {len(idx)} samples above the knee")

    # ---------------------------------------------------------------- dwell levels
    print("\ndwell levels during the hold (counts held for 10 or more samples):")
    c = {}
    for i in hold:
        c[samples[i][0]] = c.get(samples[i][0], 0) + 1
    rungs = sorted(v for v, n in c.items() if n >= 10)
    grouped = []
    for v in rungs:
        if grouped and v - grouped[-1][-1] <= 4:
            grouped[-1].append(v)
        else:
            grouped.append([v])
    for g in grouped:
        mid = st.mean(g)
        print(f"  {mid:6.1f} counts  {100 * mid / COUNTS_FULL:5.1f} %  {volts(mid):5.3f} V on the wire  "
              f"({sum(c[v] for v in g)} samples)")


if __name__ == "__main__":
    main(sys.argv)
