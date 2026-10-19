#!/usr/bin/env python3
"""
Which temperature is the ITE's fan demand actually following - the cores, or the board?

Uno logs: "claim=NNNN adc=NNN duty=.. duty_alt=..", one line per second, no timestamps.
NUC logs: "epoch pkg=NNNNN pch=NNNNN [acpi1=.. acpi2=..] load=X.XX" with PHASE markers.

The first temperature run looked like a clean answer: the demand tracked the package at r = +0.822
with a 4 s lag, +3.7 counts per C. That run had the bench fans switched by hand, so the board and the
cores rose together and the two candidates could not be told apart. The second run separated them: the
fans ran at maximum, the package went 34 -> 73 C, and the demand did not move at all - it stayed in
the same 195-260 count band it sits in at 34 C. Meanwhile the PCH only reached 55.5 C in that run and
63.5 C in the first one.

So pool the runs and bin by each candidate. The demand is flat while PCH is under about 55 C, whatever
the cores are doing - 34 C or 69 C - and climbs from 255 to 319 counts once PCH passes ~55 C. The cores
are not in the loop; the board is.

Pass a run as: uno.log nuc.log offset_seconds. The offset aligns the two captures (the Uno log has no
timestamps); run analyze-temp.py first if it is unknown. Repeat the pair to pool runs.
"""
import re
import statistics as st
import sys


def read_uno(path):
    out = []
    for line in open(path):
        m = re.search(r"adc=(\d+)", line)
        if m:
            out.append(int(m.group(1)))
    return out


def read_nuc(path):
    out = []
    for line in open(path):
        m = re.match(r"(\d+)\s+pkg=(\d+)\s+pch=(\d+)", line)
        if m:
            out.append((int(m.group(2)) / 1000.0, int(m.group(3)) / 1000.0))
    return out


def corr(x, y):
    mx, my = st.mean(x), st.mean(y)
    num = sum((a - mx) * (b - my) for a, b in zip(x, y))
    den = (sum((a - mx) ** 2 for a in x) * sum((b - my) ** 2 for b in y)) ** 0.5
    return num / den if den else 0.0


def volts(counts, ratio=0.5, vcc=5.0):
    """The tap of two equal resistors reads half the PWM line, and the Uno's rail is its reference."""
    return counts * vcc / 1024.0 / ratio


def main(args):
    pool = []
    i = 0
    while i + 2 < len(args):
        uno, nuc, off = args[i], args[i + 1], int(args[i + 2])
        a = read_uno(uno)
        R = read_nuc(nuc)
        pairs = [(a[j], R[j + off][0], R[j + off][1]) for j in range(len(a)) if 0 <= j + off < len(R)]
        print(f"{uno}: {len(pairs)} paired samples at offset {off:+d} s   "
              f"pkg {min(p[1] for p in pairs):.1f}..{max(p[1] for p in pairs):.1f} C   "
              f"pch {min(p[2] for p in pairs):.1f}..{max(p[2] for p in pairs):.1f} C")
        print(f"    r(adc,pkg) = {corr([p[0] for p in pairs], [p[1] for p in pairs]):+.3f}   "
              f"r(adc,pch) = {corr([p[0] for p in pairs], [p[2] for p in pairs]):+.3f}")
        pool += pairs
        i += 3

    print(f"\npooled: {len(pool)} samples")
    print(f"  r(adc, pkg) = {corr([p[0] for p in pool], [p[1] for p in pool]):+.3f}")
    print(f"  r(adc, pch) = {corr([p[0] for p in pool], [p[2] for p in pool]):+.3f}")

    for label, idx in (("package (the cores)", 1), ("PCH (the board)", 2)):
        print(f"\nbinned by {label} temperature")
        bins = {}
        for adc, pkg, pch in pool:
            key = int((pkg if idx == 1 else pch) // 3) * 3
            bins.setdefault(key, []).append((adc, pkg, pch))
        for k in sorted(bins):
            v = bins[k]
            adc = st.median([x[0] for x in v])
            print(f"  {k:3d}-{k+3:<3d}C  n={len(v):4d}  adc med={adc:6.1f}  {100*adc/512:5.1f}%  "
                  f"{volts(adc):5.3f} V on the PWM wire   "
                  f"pkg={st.median([x[1] for x in v]):5.1f}  pch={st.median([x[2] for x in v]):5.1f}")

    print("\nThe test to look at: samples where the two candidates disagree. Take the ones with the")
    print("cores hot and the board cool, and the ones the other way round.")
    hot_core_cool_board = [p for p in pool if p[1] >= 65 and p[2] < 55]
    cool_core_hot_board = [p for p in pool if p[1] < 55 and p[2] >= 52]
    for label, group in (("pkg >= 65 C with pch < 55 C", hot_core_cool_board),
                         ("pkg < 55 C with pch >= 52 C", cool_core_hot_board)):
        if group:
            adc = [p[0] for p in group]
            print(f"  {label:32s} n={len(group):4d}  adc med={st.median(adc):6.1f}  "
                  f"min={min(adc)} max={max(adc)}  pkg={st.mean([p[1] for p in group]):5.1f} "
                  f"pch={st.mean([p[2] for p in group]):5.1f}")


if __name__ == "__main__":
    main(sys.argv[1:])
