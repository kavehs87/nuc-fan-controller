#!/usr/bin/env python3
"""Measure the NUC fan-header block: the PWM-request divider and the tach output.

The board reads the ITE's 5 V / 23 kHz PWM request through R7+R8 (two 10 k, so a
0.500 tap = 2.50 V at 100 % duty, 0.8 V of headroom on a 3.3 V Pro Mini), filters
it with C5 1u + C6 100 n so the ADC reads the *mean* of the PWM, and answers the
ITE's tach pin with Q4 (BC547) as an open collector - the pull-up that makes the
high side lives inside the NUC, modelled here by V4 5 V and R10 1 k.

Three things get measured, each in its own deck built from the exported netlist
(same parts, only the stimulus swapped):

  demand-<duty>   ITE PWM at 23 kHz with duty 0..100 %  -> settled tap voltage,
                ripple on the tap, what the ADC counts, what duty that means,
                and how much current the divider asks of the ITE.
  step          a single 0 -> 5 V edge on the PWM line -> the time constant the
                filter actually has, measured rather than quoted.
  tach          the tach carrier (V5, 100 Hz) driving R9 -> Q4 -> how far the
                tach line swings and how hard Q4 saturates.

Writes sim/out/nuc_link.csv and sim/out/nuc_link.png and prints the tables.
"""
from __future__ import annotations

import csv
import subprocess
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "sim" / "out"
SRC = OUT / "mosfet-fan-switch.spice"

# the ITE (Intel IT8607E on this NUC) as measured in ../nuc-tach-sim
ITE_PWM_HZ = 23_000          # its PWM output frequency
ITE_PWM_TOP = 5.0            # V, top of the PWM swing on the wire
ITE_TACH_RAIL = 5.0          # V, the rail it pulls the tach line to (assumed 5 V)
ITE_PULSES_PER_REV = 2       # RPM the BIOS shows = 30 x tach frequency
RPM_FLOOR, RPM_CEIL = 700, 10_500

VREF = 3.3                   # the Pro Mini's ADC reference is its own 3.3 V rail
DIVIDER_RATIO = 10_000 / (10_000 + 10_000)
ADC_AT_100PCT = round(ITE_PWM_TOP * DIVIDER_RATIO / VREF * 1023)   # 775 counts


def devices() -> list[str]:
    """Device lines of the exported netlist, minus the two sources this script drives."""
    out = []
    for line in SRC.read_text().splitlines():
        s = line.strip()
        if not s or s.startswith(".") or s[0] not in "RQCVXLM":
            continue
        if s.split()[0] in {"V3", "V5"}:
            continue
        out.append(s.replace("NC-Q2-0", "GND"))
    return out


def run(name: str, sources: list[str], vectors: list[str], tran: str) -> Path:
    deck, data = OUT / f"nuc_{name}.cir", OUT / f"nuc_{name}.txt"
    head = [ln for ln in SRC.read_text().splitlines() if ln.startswith(".include")]
    control = ("\n.control\ntran " + tran + "\nwrdata sim/out/" + data.name + " "
               + " ".join(vectors) + "\n.endcontrol\n")
    deck.write_text("\n".join(head) + "\n" + "\n".join(devices()) + "\n"
                    + "\n".join(sources) + control + ".end\n")
    subprocess.run(["ngspice", "-b", str(deck)], check=True,
                   stdout=open(OUT / "nuc_link.log", "a"), stderr=subprocess.STDOUT)
    return data


def columns(path: Path) -> list[np.ndarray]:
    d = np.loadtxt(path)
    return [d[:, 0]] + [d[:, i] for i in range(1, d.shape[1], 2)]


def pulse(node: str, high: float, duty_pct: float, period_s: float) -> str:
    tw = period_s * duty_pct / 100.0
    return (f"V3 {node} GND PULSE( 0 {high} 0 20n 20n {tw:g} {period_s:g} )")


# ---------------------------------------------------------------- demand divider
def measure_demand() -> list[dict]:
    per = 1.0 / ITE_PWM_HZ
    rows = []
    for duty in range(0, 101, 10):
        data = run(f"demand{duty}",
                   [pulse("/NUC_PWM", ITE_PWM_TOP, duty, per),
                    "V5 /TACH_PWM GND PULSE( 0 0 0 20n 20n 5m 10m )"],   # tach branch quiet
                   ["v(/NUC_PWM)", "v(/DEMAND)", "i(v3)"],
                   "200n 60m")
        t, vpin, vtap, i_src = columns(data)
        tail = vtap[t >= 0.05]                     # settled: the last 10 ms of the run
        mean, ripple_pp = tail.mean(), tail.max() - tail.min()
        counts = mean / VREF * 1023
        rows.append({
            "duty_pct": duty,
            "tap_V": round(mean, 4),
            "ripple_mV": round(ripple_pp * 1e3, 2),
            "adc_counts": round(counts, 1),
            "duty_read_pct": round(counts / ADC_AT_100PCT * 100.0, 1),
            "ite_load_uA": round(-np.mean(i_src[t >= 0.05]) * 1e6, 1),
        })
    return rows


# ------------------------------------------------------------------- time constant
def measure_step() -> dict:
    # one clean 0 -> 5 V edge at t = 10 ms, held high until 50 ms
    src = "V3 /NUC_PWM GND PULSE( 0 5 10m 1u 1u 40m 80m )"
    data = run("step", [src, "V5 /TACH_PWM GND PULSE( 0 0 0 20n 20n 5m 10m )"],
               ["v(/NUC_PWM)", "v(/DEMAND)"], "20u 60m")
    t, vpin, vtap = columns(data)
    plateau = (t > 0.045) & (t <= 0.050)           # end of the high half of the pulse
    final = vtap[plateau].mean()                   # the settled tap, not the wire's 5 V
    edge = t[(vpin > vpin.max() / 2) & (t > 0.009)][0]
    target = final * (1 - 1 / np.e)
    after = (t > edge) & (t < 0.05)
    tau_ms = (t[after & (vtap >= target)][0] - edge) * 1e3
    return {"final_V": round(vpin.max(), 3), "tap_at_100pct_V": round(final, 3),
            "tau_ms": round(tau_ms, 3)}


# --------------------------------------------------------------------- tach output
def measure_tach() -> dict:
    per = 1.0 / ITE_PWM_HZ
    data = run("tach",
               [pulse("/NUC_PWM", ITE_PWM_TOP, 50, per),
                "V5 /TACH_PWM GND PULSE( 0 3.3 0 20n 20n 5m 10m )"],   # 100 Hz carrier
               ["v(/TACH_PWM)", "v(/NUC_TACH)", "v(/TBASE)", "i(v5)", "i(v4)"],
               "200n 40m")
    t, vcar, vtach, vbase, i_base, i_coll = columns(data)
    on = vcar >= 1.65          # carrier high -> Q4 on -> tach line low
    off = ~on
    high = float(np.median(vtach[off]))            # median: the switching kick is brief
    return {
        "carrier_hz": 100.0,                 # V5: per = 10 ms
        "tach_low_V": round(vtach[on].min(), 4),
        "tach_high_V": round(high, 4),
        "kick_V": round(vtach[off].max() - high, 4),
        "vce_sat_mV": round(vtach[on].min() * 1e3, 1),
        "collector_mA": round(-i_coll[on].mean() * 1e3, 2),
        "base_mA": round(-i_base[on].mean() * 1e3, 2),
        "forced_beta": round(abs(i_coll[on].mean()) / abs(i_base[on].mean()), 1),
    }


def main() -> None:
    OUT.mkdir(exist_ok=True)
    (OUT / "nuc_link.log").write_text("")

    demand = measure_demand()
    step = measure_step()
    tach = measure_tach()

    with open(OUT / "nuc_link.csv", "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(demand[0]))
        w.writeheader()
        w.writerows(demand)

    print(f"  ITE PWM: {ITE_PWM_HZ:,} Hz, {ITE_PWM_TOP} V top   divider 10k/10k = {DIVIDER_RATIO:.3f}")
    print(f"  100 % duty lands at {ITE_PWM_TOP * DIVIDER_RATIO:.2f} V on the tap "
          f"= {ADC_AT_100PCT} counts of a {VREF} V reference "
          f"({VREF - ITE_PWM_TOP * DIVIDER_RATIO:.2f} V of headroom)\n")
    print(f"   ITE duty   tap V   ripple mV   ADC counts   duty the Arduino reads")
    for r in demand:
        print(f"   {r['duty_pct']:>8} %  {r['tap_V']:>6.3f}   {r['ripple_mV']:>9.2f}"
              f"   {r['adc_counts']:>10.1f}   {r['duty_read_pct']:>10.1f} %")
    print(f"\n   divider load on the ITE's PWM line: {demand[-1]['ite_load_uA']:.0f} uA at 100 % "
          f"(5 V across 20 k)")
    print(f"   filter time constant measured: {step['tau_ms']:.2f} ms "
          f"(expected {5000 * 1.1e-6 * 1e3:.2f} ms from 5 k x 1.1 uF)")
    print(f"   that is {step['tau_ms'] * 1e-3 / (1 / ITE_PWM_HZ):.0f} ITE PWM periods, "
          f"so the ADC sees the mean, not the square wave\n")
    print(f"   tach line: {tach['tach_high_V']:.2f} V high (the ITE's own pull-up), "
          f"{tach['tach_low_V']:.3f} V low - Vce(sat) {tach['vce_sat_mV']:.0f} mV; the "
          f"switching kick adds {tach['kick_V'] * 1e3:.0f} mV")
    print(f"   Q4: {tach['base_mA']:.2f} mA of base drive sinks {tach['collector_mA']:.2f} mA "
          f"of pull-up current - beta only has to reach {tach['forced_beta']:.1f}, "
          f"and a BC547 gives 200+")
    print(f"   a {100:.0f} Hz carrier reads {30 * 100:,} RPM to the ITE "
          f"(RPM = 30 x f; the ITE counts {RPM_FLOOR:,}-{RPM_CEIL:,} RPM, "
          f"i.e. {RPM_FLOOR / 30:.0f}-{RPM_CEIL / 30:.0f} Hz on this wire)")
    print(f"   the fan drive itself (1 kHz here) would read {30 * 1000:,} RPM - out of range, "
          f"which is why the tach branch has its own carrier\n")

    # ------------------------------------------------------------------ the plot
    d = columns(OUT / "nuc_tach.txt")
    t, vcar, vtach, vbase, i_base, i_coll = d
    dm = columns(OUT / "nuc_demand50.txt")
    td, vpin, vtap, i_src = dm

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(11.6, 4.9))

    win = td <= 1.2e-3
    ax1.plot(td[win], vpin[win], lw=1.0, color="0.6",
             label="ITE PWM on the wire (5 V, 23 kHz)")
    ax1.plot(td[win], vtap[win], lw=1.6, color="#d35400", label="/DEMAND at the ADC pin")
    ax1.axhline(1.25, ls=":", lw=1.2, color="#d35400")
    ax1.axhline(2.50, ls="--", lw=1.2, color="#2ca02c")
    ax1.text(0.66, 0.60, "this run: 50 % duty\n1.25 V mean = 388 counts",
             transform=ax1.transAxes, fontsize=8, color="#d35400")
    ax1.text(0.66, 0.86, "100 % duty would sit\nhere: 2.50 V = 775 counts",
             transform=ax1.transAxes, fontsize=8, color="#2ca02c")
    ax1.text(0.53, 0.06, "C5+C6: tau 5.5 ms = 126 ITE periods,\n"
             "so the ADC reads the mean, not the square wave",
             transform=ax1.transAxes, fontsize=8, color="0.35")
    ax1.set_xlabel("time  [s]")
    ax1.set_ylabel("voltage  [V]")
    ax1.set_xlim(0, 2.3e-3)
    ax1.set_ylim(-0.4, 5.6)
    ax1.set_title("reading the ITE's PWM request (50 % duty)")
    ax1.grid(True, alpha=0.3)
    ax1.legend(fontsize=8, loc="upper left")

    on = vcar >= 1.65
    ax2.plot(t, vtach, lw=1.8, color="#c0392b", label="/NUC_TACH (to the ITE)")
    ax2.plot(t, vcar, lw=1.0, color="0.55", label="/TACH_PWM (Pro Mini D10, 100 Hz)")
    ax2.set_xlim(0, 30e-3)
    ax2.set_ylim(-0.5, 6.0)
    ax2.annotate(f"high: the ITE's own pull-up, {tach['tach_high_V']:.2f} V",
                 (9e-3, 5.35), fontsize=8, color="0.3")
    ax2.annotate(f"low: Q4 saturated, {tach['tach_low_V'] * 1e3:.0f} mV",
                 (11e-3, 0.45), fontsize=8, color="0.3")
    ax2.set_xlabel("time  [s]")
    ax2.set_ylabel("voltage  [V]")
    ax2.set_title("answering the tach pin: open collector, the NUC makes the high side")
    ax2.grid(True, alpha=0.3)
    ax2.legend(fontsize=8, loc="upper right")

    fig.tight_layout()
    fig.savefig(OUT / "nuc_link.png", dpi=130)
    print(f"    wrote {OUT / 'nuc_link.png'} and {OUT / 'nuc_link.csv'}")


if __name__ == "__main__":
    main()
