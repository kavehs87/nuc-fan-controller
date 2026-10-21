#!/usr/bin/env python3
"""How many 12 V fans can this driver switch at the same time?

Each extra fan is just another copy of the fan branch drawn on the sheet - 10 mH
winding plus the drag resistor that makes it draw the current your real fans draw
- hanging off /DRAIN.  The script clones that branch 1..4 times and re-runs the
same two analyses:

    DC   - pin held high, read the fully-on state
    tran - 1 kHz PWM at 50 % duty for 5 ms (3 ms of it is steady state)

and then checks the parts that actually carry the load:

    Q1  IRFZ44N        drain current, Rds(on), dissipation   (49 A, 94 W part)
    D1  1N5819         peak and average current at turn-off  (1 A part)
    V1  12 V module    current drawn from the supply         (450 mA part)

Writes sim/out/fan_count.csv, sim/out/fan_count.png and prints the table.
"""
from __future__ import annotations

import csv
import subprocess
from pathlib import Path

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from variants import MODELS, OUT, device_lines, drive_of

ROOT = Path(__file__).resolve().parents[1]
FAN_COUNTS = [1, 2, 3, 4]

# what the parts in the bin are actually rated for
LIMITS = {"irfz44n_A": 49, "1n5819_A": 1.0, "supply_mA": 450}


def deck(n: int) -> tuple[Path, Path, list[str]]:
    """Netlist with n copies of the sheet's fan branch, plus its two wrdata dumps.

    The fan branch is whatever L1 and R6 say on the schematic, so the sheet stays
    the single source of truth for the fan model.
    """
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
    control = (
        "\n.control\n"
        f"dc V2 0 {drive_of(base['V2'])} 0.01\n"
        f"wrdata sim/out/fans{n}_dc.txt {' '.join(vectors)}\n"
        "tran 100n 5m\n"
        f"wrdata sim/out/fans{n}_tran.txt {' '.join(vectors)}\n"
        ".endcontrol\n"
    )
    cir.write_text("\n".join(head) + "\n" + "\n".join(base.values()) + "\n" + control + ".end\n")
    subprocess.run(["ngspice", "-b", str(cir)], check=True,
                   stdout=open(OUT / "fan_count.log", "a"), stderr=subprocess.STDOUT)
    return dc_txt, tran_txt, vectors


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
    row = {
        "fans": n,
        "fan_current_each_mA": round(i_fans_dc / n * 1e3, 1),
        "total_fan_mA": round(i_fans_dc * 1e3, 1),
        "drain_mV": round(vdrain_dc * 1e3, 2),
        "rds_mOhm": round(vdrain_dc / i_fans_dc * 1e3, 2),
        "Q1_mW": round(vdrain_dc * i_fans_dc * 1e3, 2),
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
    """Left: total fan current for 1/2/3 fans. Right: what the 1N5819 carries with 3."""
    fig, (axl, axr) = plt.subplots(1, 2, figsize=(11.6, 4.8))

    for n, colour in zip([1, 2, 3], ["#1f77b4", "#2ca02c", "#d35400"]):
        _, tran_txt, _ = deck(n)
        cols = wrdata(tran_txt)
        t = cols[0]
        total = np.sum(cols[4:], axis=0)
        axl.plot(t * 1e3, total * 1e3, lw=1.2, color=colour,
                 label=f"{n} fan{'s' if n > 1 else ''}: peak {total.max()*1e3:.0f} mA")
    axl.set_xlim(1.0, 3.0)
    axl.set_xlabel("time [ms]")
    axl.set_ylabel("current into all fans [mA]")
    axl.set_title("3 fans: three times the current, same shape - the fan's own L/R sets it")
    axl.grid(True, alpha=0.3)
    axl.legend(fontsize=8, loc="upper right")

    _, tran_txt, _ = deck(3)
    cols = wrdata(tran_txt)
    t, vdrain = cols[0], cols[1]
    i_fans = np.sum(cols[4:], axis=0)
    i_diode = i_fans + cols[2]
    window = (t > 1e-3) & (t < 2.5e-3)
    axr.plot(t[window] * 1e3, i_fans[window] * 1e3,
             lw=1.4, color="#1f77b4", label="current into the 3 fans")
    axr.plot(t[window] * 1e3, i_diode[window] * 1e3,
             lw=1.6, color="#c0392b", label="current through D1 (1N5819)")
    axr.annotate("all 295 mA of fan current switches into the diode\n"
                 "at turn-off - the 1N5819 is rated 1 A average",
                 (1.05, 330), fontsize=8, color="#c0392b")
    axr.set_xlim(1.0, 2.5)
    axr.set_ylim(-30, 420)
    axr.set_xlabel("time [ms]")
    axr.set_ylabel("current [mA]")
    axr.set_title("the flyback diode is the part that feels 3 fans most")
    axr.grid(True, alpha=0.3)
    axr.legend(fontsize=8, loc="center right")

    fig.tight_layout()
    fig.savefig(OUT / "fan_count.png", dpi=140)
    plt.close(fig)


def main() -> None:
    rows = [measure(n) for n in FAN_COUNTS]
    plot(rows)

    with open(OUT / "fan_count.csv", "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)

    print()
    print("  the same driver with 1, 2, 3 and 4 fans on one output")
    print("  " + "-" * 96)
    print(f"  {'fans':>4} {'each':>7} {'total':>8} {'V(drain)':>9} {'Rds':>8} {'Q1 loss':>8} "
          f"{'spike':>7} {'D1 peak':>8} {'D1 avg':>7} {'D1 loss':>7} {'supply avg':>11}")
    print(f"  {'':>4} {'[mA]':>7} {'[mA]':>8} {'[mV]':>9} {'[mOhm]':>8} {'[mW]':>8} "
          f"{'[V]':>7} {'[mA]':>8} {'[mA]':>7} {'[mW]':>7} {'[mA]':>11}")
    for r in rows:
        print(f"  {r['fans']:4} {r['fan_current_each_mA']:7.1f} {r['total_fan_mA']:8.1f} "
              f"{r['drain_mV']:9.2f} {r['rds_mOhm']:8.2f} {r['Q1_mW']:8.2f} {r['spike_V']:7.2f} "
              f"{r['diode_peak_mA']:8.1f} {r['diode_avg_mA']:7.1f} {r['diode_mW']:7.1f} "
              f"{r['supply_avg_mA']:11.1f}")

    print()
    print("  against the ratings of the parts in the bins")
    print("  " + "-" * 96)
    for r in rows:
        notes = []
        if r["diode_peak_mA"] > LIMITS["1n5819_A"] * 1e3:
            notes.append("D1 1N5819 over its 1 A rating")
        if r["total_fan_mA"] > LIMITS["supply_mA"]:
            notes.append(f"over the 450 mA supply module's rating at full speed")
        if r["total_fan_mA"] > LIMITS["irfz44n_A"] * 1e3:
            notes.append("Q1 over its 49 A rating")
        verdict = "fits" if not notes else "; ".join(notes)
        print(f"  {r['fans']} fans: {r['total_fan_mA']:6.1f} mA total, "
              f"{r['Q1_mW']:5.2f} mW in Q1, {r['diode_peak_mA']:6.1f} mA peak through D1 -> {verdict}")
    print()


if __name__ == "__main__":
    main()
