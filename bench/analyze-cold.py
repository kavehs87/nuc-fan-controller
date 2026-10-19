#!/usr/bin/env python3
"""
Analyse the cold-floor test: what is the lowest duty the ITE ever asks for?

Uno log (cold.log): "claim=NNNN adc=NNN duty=.. duty_alt=..", one line per second, no timestamps.
NUC log (coldtemp.log): "epoch pkg=NNNNN pch=NNNNN acpi1=NNNNN acpi2=NNNNN load=X.XX" with
"PHASE cold-fans-max" / "PHASE end" markers.

The question this run was built to answer is whether the ITE's fan curve has a floor at all. With
the bench fans at maximum the package sat at 33 C for twelve minutes, 21 C below the plateau the
previous temperature run had been stuck at, so if the ITE was going to ask for a small duty this is
where it would have said so.

It does not. The demand sits in a band around 235 counts and never approaches zero, and inside that
band it dwells at two levels and switches between them in one to three seconds. Both of those facts
change the firmware: a follower that chases a 0.3 Hz two-level dance pumps the fan for nothing, and
a fan that never stops is a fan whose tach claim is always plausible.

The dwell levels also say something about which divider is actually built. Levels land on a lattice
about 60 counts wide. On the 10k/10k reading (512 counts = 100 %) that is 11.7 duty points, close to
1/8 steps, and the levels are 3/8, 4/8, 5/8. On the 4.7k+2.2k over 10k reading (605 counts) the same
spacing is 9.9 points, which matches no binary quantum. A meter on the two resistors settles it; the
lattice only points at it.
"""
import re
import statistics as st
import sys
from collections import Counter


def read_uno(path):
    out = []
    for line in open(path):
        m = re.search(r"adc=(\d+)", line)
        if m:
            out.append(int(m.group(1)))
    return out


def read_nuc(path):
    rows = []
    for line in open(path):
        m = re.match(r"(\d+)\s+pkg=(\d+)\s+pch=(\d+)\s+acpi1=(\d+)\s+acpi2=(\d+)\s+load=([\d.]+)", line)
        if m:
            rows.append({
                "pkg": int(m.group(2)) / 1000.0,
                "pch": int(m.group(3)) / 1000.0,
                "acpi1": int(m.group(4)) / 1000.0,
                "acpi2": int(m.group(5)) / 1000.0,
                "load": float(m.group(6)),
            })
    return rows


def quantile(v, p):
    v = sorted(v)
    return v[min(len(v) - 1, int(p * len(v)))]


def main(uno_path, nuc_path):
    adcs = read_uno(uno_path)
    rows = read_nuc(nuc_path)
    print(f"Uno samples: {len(adcs)}   NUC samples: {len(rows)}")
    if not adcs or not rows:
        return

    print("\nwhat the machine was doing")
    for k in ("pkg", "pch", "acpi1", "acpi2"):
        v = [r[k] for r in rows]
        print(f"  {k:6s} min={min(v):5.1f} median={st.median(v):5.1f} max={max(v):5.1f} C")
    print(f"  load   max={max(r['load'] for r in rows):.2f}  (idle: the fans are doing the cooling)")

    print("\nwhat the ITE asked for")
    print(f"  counts: min={min(adcs)} p5={quantile(adcs, .05)} median={st.median(adcs)} "
          f"p95={quantile(adcs, .95)} max={max(adcs)}")
    for full, label in ((512, "10k/10k, 5.0 V top"), (605, "4.7k+2.2k/10k, 5.0 V top"),
                        (563, "10k/10k, 5.5 V top"), (666, "4.7k+2.2k/10k, 5.5 V top")):
        print(f"  {label:24s} floor {100 * min(adcs) / full:5.1f}%   median {100 * st.median(adcs) / full:5.1f}%   "
              f"top {100 * max(adcs) / full:5.1f}%")
    zeros = len([a for a in adcs if a < 100])
    print(f"  samples below 100 counts (a 10 % duty request): {zeros}")

    print("\n30 s windows")
    for i in range(0, len(adcs) - 29, 30):
        seg = adcs[i:i + 30]
        j = min(i + 15, len(rows) - 1)
        print(f"  t+{i:4d}s  median={st.median(seg):6.1f}  min={min(seg):4d}  max={max(seg):4d}"
              f"   pkg={rows[j]['pkg']:5.1f}C")

    print("\nlevels the demand dwells at (values seen more than 25 times)")
    c = Counter(adcs)
    levels = sorted(v for v, n in c.items() if n > 25)
    for v in levels:
        print(f"  {v:4d} x {c[v]:4d}")
    groups = []
    for v in levels:
        if groups and v - groups[-1][-1] <= 3:
            groups[-1].append(v)
        else:
            groups.append([v])
    centres = [st.mean(g) for g in groups]
    print("  as levels: " + "  ".join(f"{x:.0f}" for x in centres))
    if len(centres) > 1:
        gaps = [centres[i + 1] - centres[i] for i in range(len(centres) - 1)]
        print(f"  spacing:   " + "  ".join(f"{g:.0f}" for g in gaps)
              + f"   (mean {st.mean(gaps):.0f} counts)")
        for full, label in ((512, "512 = 100%"), (605, "605 = 100%")):
            print(f"  against {label}: step = {100 * st.mean(gaps) / full:.1f} duty points; "
                  f"levels " + "  ".join(f"{100 * x / full:.1f}%" for x in centres))
        # how far the levels sit from a 1/8 lattice, which is what a stepped fan controller looks like
        for full in (512, 605):
            q = full / 8.0
            err = [abs(x / q - round(x / q)) * q for x in centres]
            print(f"  off a 1/8 lattice at {full} counts: mean error {st.mean(err):.1f} counts "
                  f"({100 * st.mean(err) / full:.1f} duty points)")

    print("\nhow fast it moves")
    deltas = [abs(adcs[i + 1] - adcs[i]) for i in range(len(adcs) - 1)]
    moved = len([d for d in deltas if d > 3])
    print(f"  median sample-to-sample step {st.median(deltas):.0f} counts, "
          f"{moved} of {len(deltas)} seconds moved by more than 3 counts")
    print("  the ITE ramps between its levels over a couple of seconds, so a smoothing pole shorter")
    print("  than about 10 s passes the whole dance to the fan.")


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
