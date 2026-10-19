#!/usr/bin/env python3
"""
Analyse the tach-vs-demand test.

Uno side (loop.log): one line per second, "claim=NNN adc=NNN ...". No timestamps, so time is the
sample index. The ladder is 800 / 2000 / 4500 / 2000 at 40 s per rung, so a full cycle is 160 s.

The question: does the ITE's requested duty (adc) follow the claimed RPM, or its own sensors?
If it follows the claim, every occurrence of 800 reads about the same and 4500 reads clearly lower.
If it follows temperature, all three claims read the same band and the swing has its own period.
"""
import re
import sys

def read_uno(path):
    rows = []
    for line in open(path):
        m = re.search(r"claim=(\d+).*adc=(\d+)", line)
        if m:
            rows.append((int(m.group(1)), int(m.group(2))))
    return rows

def read_nuc(path):
    rows = []
    for line in open(path):
        m = re.match(r"(\d+)\s+pkg=(\d+)\s+pch=(\d+)", line)
        if m:
            rows.append((int(m.group(1)), int(m.group(2)) / 1000.0))
    return rows

def mean(v):
    return sum(v) / len(v) if v else 0.0

def occurrences(rows):
    """Group consecutive samples that share the same claim - one group per dwell."""
    out = []
    cur = None
    for claim, adc in rows:
        if cur is None or claim != cur[0]:
            cur = (claim, [])
            out.append(cur)
        cur[1].append(adc)
    return out

def main(uno_path, nuc_path=None):
    rows = read_uno(uno_path)
    if not rows:
        print("no Uno samples")
        return
    adcs = [a for _, a in rows]
    print(f"Uno samples: {len(rows)} at ~1/s  ({len(rows)/60:.1f} minutes)")

    occ = occurrences(rows)
    print(f"dwell groups found: {len(occ)}  (a 40 s ladder gives ~8 for 5.5 minutes)")
    print("\nevery dwell, in time order")
    for claim, vals in occ:
        print(f"  claim {claim:5d}  n={len(vals):3d}  mean={mean(vals):6.1f}  "
              f"min={min(vals):4d}  max={max(vals):4d}")

    print("\nper claim, averaged over all its dwells")
    claims = sorted({c for c, _ in rows})
    for claim in claims:
        vals = [a for c, a in rows if c == claim]
        dwell_means = [mean(v) for c, v in occ if c == claim]
        print(f"  claim {claim:5d}  n={len(vals):3d}  mean={mean(vals):6.1f}  "
              f"min={min(vals):4d} max={max(vals):4d}  dwell-means: "
              + " ".join(f"{m:.0f}" for m in dwell_means))

    if len(claims) >= 2:
        means = {c: mean([a for a, cc in ((a, cc) for cc, a in rows) if cc == c]) for c in claims}
        lo, hi = min(claims), max(claims)
        d = means[hi] - means[lo]
        print(f"\nresponse to the claim: {lo} -> {hi} RPM ({hi/lo:.1f}x) moves the duty by "
              f"{d:+.1f} counts out of {mean(adcs):.0f}  ({d/mean(adcs)*100:+.1f}%)")
        spread = max(adcs) - min(adcs)
        print(f"swing that happens anyway, same claim: up to {spread} counts")

    # Dominant period of the duty swing, by autocorrelation - if it is the ITE's own loop or a
    # thermal cycle, it shows up as a peak away from the ladder's 160 s.
    m = mean(adcs)
    n = len(adcs)
    best = []
    for lag in range(2, min(200, n // 2)):
        num = sum((adcs[i] - m) * (adcs[i + lag] - m) for i in range(n - lag))
        den = sum((x - m) ** 2 for x in adcs)
        best.append((lag, num / den if den else 0))
    peaks = [(lag, r) for lag, r in best if r > 0.25]
    print("\nautocorrelation of the duty series (lag s, r):")
    print("  " + "  ".join(f"{lag}s:{r:+.2f}" for lag, r in peaks[:14]))
    print(f"  ladder cycle is 160 s; a peak near 6-10 s is the ITE's own rhythm, not the test")

    if nuc_path:
        nuc = read_nuc(nuc_path)
        if nuc:
            temps = [t for _, t in nuc]
            print(f"\nNUC package temp: {len(temps)} samples  start={temps[0]:.1f}C end={temps[-1]:.1f}C "
                  f"min={min(temps):.1f} max={max(temps):.1f}  drift {temps[-1]-temps[0]:+.1f} C")
            best_pair = None
            for off in range(-200, 201):
                pairs = [(adcs[i], temps[i + off]) for i in range(len(adcs)) if 0 <= i + off < len(temps)]
                if len(pairs) < 80:
                    continue
                xs, ys = [p[0] for p in pairs], [p[1] for p in pairs]
                mx, my = mean(xs), mean(ys)
                num = sum((x - mx) * (y - my) for x, y in pairs)
                den = (sum((x - mx) ** 2 for x in xs) * sum((y - my) ** 2 for y in ys)) ** 0.5
                if den and (best_pair is None or abs(num / den) > abs(best_pair[1])):
                    best_pair = (off, num / den, len(pairs))
            if best_pair:
                print(f"  best adc-vs-temperature correlation: offset {best_pair[0]:+4d} s  r={best_pair[1]:+.3f}  n={best_pair[2]}")

if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else None)
