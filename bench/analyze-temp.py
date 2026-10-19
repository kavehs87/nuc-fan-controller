#!/usr/bin/env python3
"""
Analyse the temperature test.

Uno log (temp.log): "claim=NNNN adc=NNN duty=.. duty_alt=..", one line per second, no timestamps.
NUC log (stress.log): "epoch pkg=NNNNN pch=NNNNN load=X.XX" with "PHASE idle|load|cool|end" markers.

The question is whether the ITE's requested duty tracks the NUC's temperature. Time alignment is
found by searching for the offset that best lines the two series up, so the two captures do not
have to have been started together.

The strongest single check is hysteresis-free or not: take a temperature bin and compare the duty
seen at that temperature on the way up with the duty seen at the same temperature on the way down.
If the duty is a function of temperature, those agree. If the duty is unrelated, the bins say
nothing about temperature and the spread inside each bin is the same noise seen everywhere.
"""
import re
import sys

def read_uno(path):
    out = []
    for line in open(path):
        m = re.search(r"adc=(\d+)", line)
        if m:
            out.append(int(m.group(1)))
    return out

def read_nuc(path):
    stamps, temps, phases = [], [], {}
    cur_t = None
    for line in open(path):
        line = line.strip()
        if line.startswith("PHASE"):
            cur_t = len(stamps)
            phases.setdefault(line.split()[1], cur_t)
            continue
        m = re.match(r"(\d+)\s+pkg=(\d+)", line)
        if m:
            stamps.append(int(m.group(1)))
            temps.append(int(m.group(2)) / 1000.0)
    return stamps, temps, phases

def mean(v):
    return sum(v) / len(v) if v else 0.0

def main(uno_path, nuc_path):
    adcs = read_uno(uno_path)
    stamps, temps, phases = read_nuc(nuc_path)
    print(f"Uno samples: {len(adcs)}   NUC samples: {len(temps)}")
    if not adcs or not temps:
        return
    print(f"NUC phases at sample: " + ", ".join(f"{k}={v}" for k, v in sorted(phases.items(), key=lambda kv: kv[1])))
    print(f"package temp: start={temps[0]:.1f} max={max(temps):.1f} end={temps[-1]:.1f} C")

    # Where the temperature is rising vs falling, so the same bin can be compared up against down.
    rising = [i for i in range(1, len(temps)) if temps[i] > temps[i - 1] + 0.4]
    falling = [i for i in range(1, len(temps)) if temps[i] < temps[i - 1] - 0.4]

    best = None
    for off in range(-260, 261):
        pairs = [(adcs[i], temps[i + off]) for i in range(len(adcs)) if 0 <= i + off < len(temps)]
        if len(pairs) < 100:
            continue
        xs, ys = [p[0] for p in pairs], [p[1] for p in pairs]
        mx, my = mean(xs), mean(ys)
        num = sum((x - mx) * (y - my) for x, y in pairs)
        den = (sum((x - mx) ** 2 for x in xs) * sum((y - my) ** 2 for y in ys)) ** 0.5
        if den and (best is None or abs(num / den) > abs(best[1])):
            best = (off, num / den, len(pairs))
    if best:
        print(f"best adc-vs-temperature correlation: offset {best[0]:+4d} s  r={best[1]:+.3f}  n={best[2]}")
    off = best[0] if best else 0

    print("\nsame temperature, ramp up vs ramp down (adc means)")
    bins = {}
    for i, a in enumerate(adcs):
        j = i + off
        if not (0 <= j < len(temps)):
            continue
        b = int(temps[j] // 5) * 5
        direction = "up" if j in rising else ("down" if j in falling else "flat")
        bins.setdefault(b, {"up": [], "down": [], "flat": []})[direction].append(a)
    for b in sorted(bins):
        d = bins[b]
        line = f"  {b:3d}-{b+5:<3d}C"
        for k in ("up", "down", "flat"):
            v = d[k]
            line += f"  {k}={mean(v):6.1f}(n={len(v):3d})" if v else f"  {k:>6s}      -     "
        print(line)

    print("\nduty series, 10 s means")
    for i in range(0, len(adcs) - 9, 10):
        seg = adcs[i:i + 10]
        j = i + off
        tseg = [temps[k] for k in range(j, j + 10) if 0 <= k < len(temps)]
        print(f"  t+{i:3d}s  adc={mean(seg):6.1f}  min={min(seg):4d} max={max(seg):4d}"
              + (f"   pkg={mean(tseg):5.1f}C" if tseg else ""))

    m = mean(adcs)
    peaks = []
    for lag in range(2, min(120, len(adcs) // 2)):
        num = sum((adcs[i] - m) * (adcs[i + lag] - m) for i in range(len(adcs) - lag))
        den = sum((x - m) ** 2 for x in adcs)
        if den and num / den > 0.25:
            peaks.append((lag, num / den))
    print("\nautocorrelation peaks (lag s, r): " + "  ".join(f"{l}s:{r:+.2f}" for l, r in peaks[:12]))

if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
