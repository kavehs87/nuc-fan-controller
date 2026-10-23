#!/usr/bin/env python3
"""How many 12 V fans can this driver switch at the same time?

Each extra fan is just another copy of the fan branch drawn on the sheet - 10 mH
winding plus the drag resistor that makes it draw the current your real fans draw
- hanging off /DRAIN.  The script clones that branch as many times as you ask and
re-runs the same two analyses:

    DC   - pin held high, read the fully-on state
    tran - 1 kHz PWM at 50 % duty for 5 ms (3 ms of it is steady state)

and then checks the parts that actually carry the load:

    Q1  IRFZ44N        drain current, Rds(on), dissipation, junction temperature
                       rise in free air (49 A, 94 W, TO-220 part)
    D1  1N5819         peak and average current at turn-off (1 A part; the bin
                       also holds a 1N5822, which is the 3 A version)
    V1  the 12 V supply you say you are using  (--supply-ma, default the 450 mA
                       module in L1 - B7)

Examples:
    python3 sim/fan_count.py                        # 1..4 fans, the 450 mA bin module
    python3 sim/fan_count.py --fans 1 2 4 8 16 32 64 --supply-ma 8000

Writes sim/out/fan_count.csv, sim/out/fan_count.png and prints the tables.
"""
from __future__ import annotations

import argparse
import csv
import subprocess
from pathlib import Path

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from variants import MODELS, OUT, device_lines, drive_of

ROOT = Path(__file__).resolve().parents[1]

# default: the parts in the bins, exactly as the README quotes them
DEFAULT_FANS = [1, 2, 3, 4]
LIMITS = {
    "irfz44n_A": 49,          # continuous drain current, TO-220, case held at 25 C
    "irfz44n_rtheta_C_per_W": 62,   # junction-to-ambient, TO-220 in free air, no heatsink
    "irfz44n_rise_C": 100,    # beyond this it wants a heatsink
    "1n5819_A": 1.0,          # average rectified current
    "1n5822_A": 3.0,          # the bigger Schottky in the same drawer
}

_DECKS: dict[int, tuple[Path, Path, list[str]]] = {}


def deck(n: int) -> tuple[Path, Path, list[str]]:
    """Netlist with n copies of the sheet's fan branch, plus its two wrdata dumps.

    The fan branch is whatever L1 and R6 say on the schematic, so the sheet stays
    the single source of truth for the fan model.  Runs are cached: the plot needs
    the same runs the table does.
    """
    if n in _DECKS:
        return _DECKS[n]

    base = device_lines()
    winding, drag = base["L1"].split()[3], base["R6"].split()[3]
    base = {k: v for k, v in base.items() if k not in {"L1", "R6"}}
    for i in range(1, n + 1):
        base[f"Lf{i}"] = f"Lf{i} /P12V /FW{i} {winding}"
        base[f"Rf{i}"] = f"Rf{i} /FW{i} /DRAIN {drag}"

    fan_currents = [f"i(Lf{i})" for i in range(1, n + 1)]
    vectors = ["v(/DRAIN)", "i(v1)", "i(v2)"] + fan_currents

    cir = OUT / f"fans{n}.cir"
    dc_txt = OUT / f"fans{n}_dc.txt"
    tran_txt = OUT / f"fans{n}_tran.txt"
    head = [f'.include "{ROOT / "sim" / "models" / m}"' for m in MODELS]
    # fine steps while the node voltages are what matter, coarser once the load is
    # big and the numbers to read are the fan and diode currents
    step = "100n" if n <= 8 else "2u"
    control = (
        "\n.control\n"
        f"dc V2 0 {drive_of(base['V2'])} 0.01\n"
        f"wrdata sim/out/fans{n}_dc.txt {' '.join(vectors)}\n"
        f"tran {step} 5m\n"
        f"wrdata sim/out/fans{n}_tran.txt {' '.join(vectors)}\n"
        ".endcontrol\n"
    )
    cir.write_text("\n".join(head) + "\n" + "\n".join(base.values()) + "\n" + control + ".end\n")
    subprocess.run(["ngspice", "-b", str(cir)], check=True,
                   stdout=open(OUT / "fan_count.log", "a"), stderr=subprocess.STDOUT)
    _DECKS[n] = (dc_txt, tran_txt, vectors)
    return _DECKS[n]


def wrdata(path: Path) -> list[np.ndarray]:
    """ngspice wrdata dump: x, value, x, value, ..."""
    data = np.loadtxt(path)
    return [data[:, 0]] + [data[:, i] for i in range(1, data.shape[1], 2)]


def measure(n: int) -> dict:
    dc_txt, tran_txt, vectors = deck(n)

    # ---- DC, pin held high: the fully-on state
    dc = wrdata(dc_txt)
    vdrain_dc = abs(dc[1][-1])
    i_fans_dc = abs(dc[2][-1])                  # current the supply delivers = all fans
    i_pin_dc = abs(dc[3][-1])

    # ---- transient, steady part of the 1 kHz PWM
    t, vdrain, i_sup, i_pin = wrdata(tran_txt)[:4]
    i_fans = np.sum(wrdata(tran_txt)[4:], axis=0)

    # KCL at /P12V: the diode carries whatever the fans draw that the supply does not.
    # i(v1) is negative while the supply delivers, ~0 while the fans freewheel.
    i_diode = i_fans + i_sup
    i_q1 = i_fans - np.clip(i_diode, 0, None)
    v_diode = np.clip(vdrain - 12.0, 0, None)

    steady = t >= 2e-3                          # 3 ms of settled PWM
    q1_mw = vdrain_dc * i_fans_dc * 1e3
    row = {
        "fans": n,
        "fan_current_each_mA": round(i_fans_dc / n * 1e3, 1),
        "total_fan_mA": round(i_fans_dc * 1e3, 1),
        "drain_mV": round(vdrain_dc * 1e3, 2),
        "rds_mOhm": round(vdrain_dc / i_fans_dc * 1e3, 2),
        "Q1_mW": round(q1_mw, 2),
        "Q1_rise_C": round(q1_mw / 1e3 * LIMITS["irfz44n_rtheta_C_per_W"], 1),
        "spike_V": round(vdrain.max(), 2),
        "diode_peak_mA": round(np.max(i_diode) * 1e3, 1),
        "diode_avg_mA": round(np.mean(np.clip(i_diode[steady], 0, None)) * 1e3, 1),
        "diode_mW": round(np.mean(v_diode[steady] * np.clip(i_diode[steady], 0, None)) * 1e3, 1),
        "supply_avg_mA": round(-np.mean(i_sup[steady]) * 1e3, 1),
        "supply_peak_mA": round(-np.min(i_sup) * 1e3, 1),
        "pin_mA": round(max(abs(i_pin_dc), np.max(np.abs(i_pin))) * 1e3, 2),
        "avg_fan_total_mA": round(np.mean(i_fans[steady]) * 1e3, 1),
    }
    return row


def plot(rows: list[dict]) -> None:
    """Left: total fan current for a spread of counts.  Right: what D1 carries at the biggest."""
    counts = [r["fans"] for r in rows]
    picks = [counts[0]] + [c for c in counts[1:-1] if c in (2, 4, 8, 16)] + [counts[-1]]
    picks = list(dict.fromkeys(picks))
    biggest = counts[-1]

    fig, (axl, axr) = plt.subplots(1, 2, figsize=(11.6, 4.8))
    palette = ["#1f77b4", "#2ca02c", "#d35400", "#7d3c98", "#c0392b"]

    for colour, n in zip(palette, picks):
        _, tran_txt, _ = deck(n)
        cols = wrdata(tran_txt)
        t = cols[0]
        total = np.sum(cols[4:], axis=0)
        axl.plot(t * 1e3, total * 1e3, lw=1.2, color=colour,
                 label=f"{n} fans: peak {total.max()*1e3/1000:.2f} A")
    axl.set_xlim(1.0, 3.0)
    axl.set_xlabel("time [ms]")
    axl.set_ylabel("current into all fans [mA]")
    axl.set_title(f"same driver, {picks[0]} to {biggest} fans - the shape never changes, only the scale")
    axl.grid(True, alpha=0.3)
    axl.legend(fontsize=8, loc="upper left")

    _, tran_txt, _ = deck(biggest)
    cols = wrdata(tran_txt)
    t, vdrain = cols[0], cols[1]
    i_fans = np.sum(cols[4:], axis=0)
    i_diode = i_fans + cols[2]
    window = (t > 1e-3) & (t < 2.5e-3)
    axr.plot(t[window] * 1e3, i_fans[window] * 1e3,
             lw=1.4, color="#1f77b4", label=f"current into the {biggest} fans")
    axr.plot(t[window] * 1e3, i_diode[window] * 1e3,
             lw=1.6, color="#c0392b", label="current through D1 (1N5819)")
    peak = i_diode.max() * 1e3
    axr.annotate(f"all {peak:.0f} mA of fan current switches into the diode at\n"
                 f"turn-off - the 1N5819 is a 1 A part, the 1N5822 in the same\n"
                 f"drawer is a 3 A part",
                 (1.05, peak * 1.12), fontsize=8, color="#c0392b")
    axr.set_xlim(1.0, 2.5)
    axr.set_ylim(-30, peak * 1.35)
    axr.set_xlabel("time [ms]")
    axr.set_ylabel("current [mA]")
    axr.set_title("the flyback diode is the part that feels extra fans first")
    axr.grid(True, alpha=0.3)
    axr.legend(fontsize=8, loc="center right")

    fig.tight_layout()
    fig.savefig(OUT / "fan_count.png", dpi=140)
    plt.close(fig)


def verdict(r: dict, supply_ma: float) -> str:
    notes = []
    if r["supply_peak_mA"] > supply_ma:
        notes.append(f"over the {supply_ma:.0f} mA supply at full speed")
    if r["diode_peak_mA"] > LIMITS["1n5819_A"] * 1e3:
        if r["diode_peak_mA"] <= LIMITS["1n5822_A"] * 1e3:
            notes.append("D1: swap the 1N5819 for the 1N5822 (3 A, also in L1 - E1)")
        else:
            notes.append("D1 over even the 1N5822's 3 A rating")
    if r["total_fan_mA"] > LIMITS["irfz44n_A"] * 1e3:
        notes.append("Q1 over its 49 A rating")
    if r["Q1_rise_C"] > LIMITS["irfz44n_rise_C"]:
        notes.append(f"Q1 needs a heatsink (+{r['Q1_rise_C']:.0f} C in free air)")
    return "fits" if not notes else "; ".join(notes)


def main() -> None:
    ap = argparse.ArgumentParser(description="how many 12 V fans one output can carry")
    ap.add_argument("--fans", nargs="+", type=int, default=DEFAULT_FANS,
                    help="fan counts to try, e.g. --fans 1 2 4 8 16 32")
    ap.add_argument("--supply-ma", type=float, default=450,
                    help="current rating of the 12 V supply you are actually using")
    args = ap.parse_args()

    log = OUT / "fan_count.log"
    if log.exists():
        log.unlink()

    rows = [measure(n) for n in args.fans]
    plot(rows)

    with open(OUT / "fan_count.csv", "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)

    print()
    print(f"  the same driver with {args.fans[0]} to {args.fans[-1]} fans on one output")
    print("  " + "-" * 104)
    print(f"  {'fans':>4} {'each':>7} {'total':>8} {'V(drain)':>9} {'Rds':>8} {'Q1 loss':>8} "
          f"{'Q1 +C':>6} {'spike':>7} {'D1 peak':>8} {'D1 avg':>7} {'D1 loss':>7} {'supply peak':>11}")
    print(f"  {'':>4} {'[mA]':>7} {'[mA]':>8} {'[mV]':>9} {'[mOhm]':>8} {'[mW]':>8} "
          f"{'[C]':>6} {'[V]':>7} {'[mA]':>8} {'[mA]':>7} {'[mW]':>7} {'[mA]':>11}")
    for r in rows:
        print(f"  {r['fans']:4} {r['fan_current_each_mA']:7.1f} {r['total_fan_mA']:8.1f} "
              f"{r['drain_mV']:9.2f} {r['rds_mOhm']:8.2f} {r['Q1_mW']:8.2f} {r['Q1_rise_C']:6.1f} "
              f"{r['spike_V']:7.2f} {r['diode_peak_mA']:8.1f} {r['diode_avg_mA']:7.1f} "
              f"{r['diode_mW']:7.1f} {r['supply_peak_mA']:11.1f}")

    print()
    print(f"  against the ratings of the parts in the bins, with a {args.supply_ma:.0f} mA 12 V supply")
    print("  " + "-" * 104)
    for r in rows:
        print(f"  {r['fans']:3} fans: {r['total_fan_mA']:8.1f} mA total, {r['Q1_mW']:7.2f} mW in Q1 "
              f"(+{r['Q1_rise_C']:4.1f} C), {r['diode_peak_mA']:8.1f} mA peak through D1 -> "
              f"{verdict(r, args.supply_ma)}")
    print()


if __name__ == "__main__":
    main()
