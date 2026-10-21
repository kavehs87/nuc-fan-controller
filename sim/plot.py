#!/usr/bin/env python3
"""Plot the ngspice results and print the numbers worth remembering."""
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "sim" / "out"


def wrdata(name: str) -> list[np.ndarray]:
    """ngspice 'wrdata' ASCII dump: x, value, x, value, ..."""
    data = np.loadtxt(OUT / name)
    return [data[:, 0]] + [data[:, i] for i in range(1, data.shape[1], 2)]


def main() -> None:
    # ------------------------------------------------------------------ DC sweep
    vpin, vlgate, vboot, vgate, vdrain, i_sup, i_pin = wrdata("dc_sweep.txt")
    fan_ma = -i_sup * 1e3                      # current the 12 V supply delivers

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(11.6, 4.9))

    ax1.plot(vpin, vboot, lw=2.0, color="#d35400", label="/BOOT  (IRF7416 gate)")
    ax1.plot(vpin, vgate, lw=2.0, color="#2ca02c", label="/GATE  (IRFZ44N gate)")
    ax1.plot(vpin, vlgate, lw=1.2, color="#7d3c98", label="/LGATE (2N7002 gate)")
    ax1.set_xlabel("Arduino pin  V(PWM)  [V]")
    ax1.set_ylabel("voltage  [V]")
    ax1.set_ylim(-1, 13)
    ax1.grid(True, alpha=0.3)
    ax1.legend(fontsize=8, loc="center right")
    ax1.set_title("the booster: 3.3 V in, a 10.9 V gate out")
    ax1.annotate("pin low: 2N7002 off,\n/BOOT sits at 12 V through R3,\nIRF7416 off, /GATE at 0 V",
                 (0.15, 11.4), fontsize=8, color="0.35")
    ax1.annotate("pin high: 2N7002 on,\n/BOOT ~ 0 V, IRF7416 on,\n/GATE = 12 V x R5/(R4+R5) = 10.9 V",
                 (1.6, 8.6), fontsize=8, color="0.35")

    ax2.plot(vpin, vdrain, lw=2.0, color="#c0392b", label="V(drain)")
    ax2.set_xlabel("Arduino pin  V(PWM)  [V]")
    ax2.set_ylabel("V(drain)  [V]", color="#c0392b")
    ax2.set_ylim(-0.5, 13)
    ax2.grid(True, alpha=0.3)
    ax2b = ax2.twinx()
    ax2b.plot(vpin, fan_ma, lw=2.0, color="#1f77b4", label="fan current")
    ax2b.set_ylabel("fan current  [mA]", color="#1f77b4")
    ax2b.set_ylim(-5, 125)

    vth = vpin[np.argmax(fan_ma > 20)]
    ax2.axvline(vth, ls="--", color="0.4")
    ax2.annotate(f"fan starts at ~{vth:.2f} V on the pin", (vth + 0.08, 6.4), fontsize=8, color="0.3")
    ax2.annotate("OFF: the fan sees the full 12 V\nacross the MOSFET, no current", (0.15, 11.3), fontsize=8, color="#c0392b")
    ax2.annotate("ON: V(drain) = I x Rds(on) ~ 1.6 mV\nthe fan gets ~12 V and runs", (0.15, 1.3), fontsize=8, color="#1f77b4")
    ax2.set_title("DC transfer curve - a MOSFET is a voltage-controlled resistor")
    fig.tight_layout()
    fig.savefig(OUT / "dc_transfer.png", dpi=140)
    plt.close(fig)

    # -------------------------------------------------------------- transient
    t, vpwm, vlgate_t, vboot_t, vgate_t, vdrain_t, i_l1, i_sup_t, i_pin_t = wrdata("tran_data.txt")
    t_ms = t * 1e3

    fig, axes = plt.subplots(4, 1, figsize=(10, 10.6), sharex=True)
    axes[0].plot(t_ms, vpwm, lw=1.0, color="0.55", label="Arduino D9 (PWM)")
    axes[0].plot(t_ms, vboot_t, lw=1.6, color="#d35400", label="/BOOT (P-FET gate)")
    axes[0].plot(t_ms, vgate_t, lw=1.8, color="#2ca02c", label="/GATE (power FET gate)")
    axes[0].set_ylabel("voltage [V]")
    axes[0].set_title("3.3 V PWM -> 2N7002 -> IRF7416 -> IRFZ44N -> 12 V fan   (1 kHz, 50 %)")
    axes[0].legend(loc="upper right", fontsize=8)

    axes[1].plot(t_ms, vdrain_t, lw=1.2, color="#c0392b")
    axes[1].set_ylabel("V(drain) [V]")
    axes[1].set_ylim(-0.5, 14)
    axes[1].grid(True, alpha=0.3)
    axes[1].annotate("12.36 V: the fan's inductance flies the node up,\nthe 1N5819 clamps it at 12 V + Vf",
                     (1.05, 10.4), fontsize=8, color="0.3")

    axes[2].plot(t_ms, i_l1 * 1e3, lw=1.4, color="#1f77b4")
    axes[2].set_ylabel("fan current [mA]")
    axes[2].grid(True, alpha=0.3)
    axes[2].annotate("the fan model's L/R = 10 mH / 120 ohm = 83 us: at 1 kHz the fan never\n"
                     "reaches steady state, it is chopped between 0 and 100 mA",
                     (2.1, 45), fontsize=8, color="0.3")

    axes[3].plot(t_ms, -i_pin_t * 1e3, lw=1.4, color="#7d3c98")
    axes[3].set_ylabel("current the pin sources [mA]")
    axes[3].set_xlabel("time [ms]")
    axes[3].set_ylim(-0.1, 0.6)
    axes[3].grid(True, alpha=0.3)
    axes[3].annotate("0.3 mA = 3.3 V / (R1 + R2).  The pin never has to charge\n"
                     "the power MOSFET's 1.5 nF gate - that is the booster's job",
                     (1.05, 0.35), fontsize=8, color="0.3")
    for a in axes:
        a.set_xlim(0, 5)
    fig.tight_layout()
    fig.savefig(OUT / "transient.png", dpi=140)
    plt.close(fig)

    # ------------------------------------------------- one turn-on / turn-off edge
    m_on = t <= 12e-6                                    # first turn-on edge
    m_off = (t >= 498e-6) & (t <= 700e-6)               # first turn-off edge

    fig, axes = plt.subplots(1, 2, figsize=(11.6, 4.8))
    axes[0].plot(t[m_on] * 1e6, vpwm[m_on], lw=1.2, color="0.55", label="Arduino pin")
    axes[0].plot(t[m_on] * 1e6, vboot_t[m_on], lw=1.8, color="#d35400", label="/BOOT")
    axes[0].plot(t[m_on] * 1e6, vgate_t[m_on], lw=2.0, color="#2ca02c", label="/GATE")
    axes[0].set_xlabel("time after the pin goes high  [µs]")
    axes[0].set_ylabel("voltage [V]")
    axes[0].set_ylim(-1, 13)
    axes[0].set_title("turn-on: /BOOT collapses, /GATE charges through R4")
    axes[0].grid(True, alpha=0.3)
    axes[0].annotate("/BOOT falls through the 2N7002\n(10 ohm x 1.7 nF, ~17 ns)", (1.2, 8.5), fontsize=8, color="#d35400")
    axes[0].annotate("/GATE rises with tau = R4 x C1\n= 1 kohm x 1.5 nF = 1.5 us\nsettles in 5 tau = 7.5 us",
                     (4.0, 3.0), fontsize=8, color="#2ca02c")
    axes[0].legend(fontsize=8, loc="center right")

    axes[1].plot(t[m_off] * 1e6, vdrain_t[m_off], lw=2.0, color="#c0392b", label="V(drain)")
    axes[1].axhline(12.37, ls="--", lw=1.0, color="0.4")
    axes[1].annotate("clamped at 12 V + 0.36 V by the 1N5819", (555, 11.0), fontsize=8, color="0.3")
    axes[1].annotate("/BOOT must charge back to 12 V through R3:\ntau = 10 kohm x 1.7 nF = 17 us\n-> /GATE takes tens of us to fall",
                     (545, 3.5), fontsize=8, color="#d35400")
    axes[1].set_xlabel("time around the pin going low  [µs]")
    axes[1].set_ylabel("V(drain) [V]", color="#c0392b")
    axes[1].set_ylim(-1, 14)
    axes[1].set_title("turn-off: the fan's inductance flies the node up")
    axes[1].grid(True, alpha=0.3)
    axes[1].legend(fontsize=8, loc="center left")

    ax1b = axes[1].twinx()
    ax1b.plot(t[m_off] * 1e6, i_l1[m_off] * 1e3, lw=1.6, color="#1f77b4", label="fan current")
    ax1b.set_ylabel("fan current [mA]", color="#1f77b4")
    ax1b.set_ylim(0, 115)
    ax1b.annotate("the fan keeps spinning: its current\nfreewheels through D1 and decays",
                  (560, 60), fontsize=8, color="#1f77b4")
    fig.tight_layout()
    fig.savefig(OUT / "switching_edge.png", dpi=140)
    plt.close(fig)

    # ------------------------------------------------------------- variant table
    import csv
    rows = list(csv.DictReader(open(OUT / "variants.csv")))
    labels = [r["variant"] for r in rows]
    fan = [float(r["fan_mA"]) for r in rows]
    pw = [float(r["mW"]) for r in rows]

    fig, (axl, axr) = plt.subplots(1, 2, figsize=(11.6, 4.8))
    idx = np.arange(len(rows))
    axl.barh(idx, fan, color=["#2ca02c", "#2ca02c", "#1f77b4", "#c0392b", "#1f77b4", "#d35400"])
    axl.set_yticks(idx, labels, fontsize=8)
    axl.set_xlabel("fan current while the pin is high  [mA]")
    axl.set_xlim(0, 115)
    axl.grid(True, alpha=0.3, axis="x")
    axl.invert_yaxis()
    for i, v in zip(idx, fan):
        axl.text(v + 3, i, f"{v:.0f} mA", va="center", fontsize=8)
    axl.set_title("does the fan actually get its 12 V?")

    axr.barh(idx, pw, color=["#2ca02c", "#2ca02c", "#1f77b4", "#c0392b", "#1f77b4", "#d35400"])
    axr.set_yticks(idx, labels, fontsize=8)
    axr.set_xscale("log")
    axr.set_xlim(0.1, 1200)
    axr.set_xlabel("dissipated in the switching device  [mW]  (log)")
    axr.grid(True, alpha=0.3, axis="x")
    axr.invert_yaxis()
    for i, r in zip(idx, rows):
        if float(r["mW"]) > 0.1:
            axr.text(float(r["mW"]) * 1.25, i, f"{float(r['mW']):.2f} mW", va="center", fontsize=8)
        else:
            axr.text(0.15, i, "the fan never turns on", va="center", fontsize=8, color="#c0392b")
    axr.set_title("and what it costs the transistor")
    fig.tight_layout()
    fig.savefig(OUT / "drive_compare.png", dpi=140)
    plt.close(fig)

    # ------------------------------------------------------------------ summary
    spike = vdrain_t.max()
    on_mask = vgate_t > 8.0            # fully enhanced: gate well above the threshold
    fan_on = i_l1[on_mask].max()
    i_pin_pk = np.max(np.abs(i_pin_t))
    fan_avg = np.trapezoid(i_l1, t) / t[-1]
    boot_off = t[np.argmax((t > 500e-6) & (vboot_t > 11.99))] - 500e-6

    # the DC sweep is the cleanest place to read the "fully on" numbers
    vgate_on = vgate[-1]
    i_fan_dc = abs(i_sup[-1])
    vds_on = abs(vdrain[-1])
    rds = vds_on / i_fan_dc
    p_mos = vds_on * i_fan_dc

    # the fan model lives on the sheet, so read its L and R from the exported netlist
    netlist = (OUT / "mosfet-fan-switch.spice").read_text().splitlines()
    eng = {"m": 1e-3, "u": 1e-6, "n": 1e-9, "p": 1e-12, "f": 1e-15,
           "k": 1e3, "K": 1e3, "M": 1e6, "G": 1e9, "T": 1e12}.get

    def value(line: str) -> float:
        token = next(ln for ln in netlist if ln.startswith(line)).split()[3]
        return float(token[:-1]) * eng(token[-1], 1.0) if token[-1].isalpha() else float(token)

    l_fan, r_fan = value("L1"), value("R6")

    print()
    print("  measured from the simulation")
    print("  " + "-" * 68)
    print(f"  pin voltage where the fan starts                : {vth:5.2f} V")
    print(f"  /BOOT when the pin is high (2N7002 sinks 1.2 mA): {vboot_t[on_mask].min()*1e3:5.1f} mV")
    print(f"  /GATE steady state (12 V x R5/(R4+R5))          : {vgate_on:5.2f} V")
    print(f"  fan current with the power FET on               : {i_fan_dc*1e3:5.1f} mA")
    print(f"  V(drain) with the power FET on                  : {vds_on*1e3:5.1f} mV")
    print(f"  Rds(on) at that point                           : {rds*1e3:5.1f} mΩ")
    print(f"  power FET dissipation while on                  : {p_mos*1e3:5.2f} mW")
    print(f"  V(drain) spike at turn-off (clamped by D1)      : {spike:5.2f} V")
    print(f"  Arduino pin current (max)                       : {i_pin_pk*1e3:5.2f} mA")
    print(f"  /GATE rise 5 tau (R4=1k, C1=1.5n)               : {5*1e3*1.5e-9*1e6:5.1f} µs")
    print(f"  /BOOT rise 5 tau (R3=10k, C2=1.7n)              : {5*10e3*1.7e-9*1e6:5.1f} µs")
    print(f"  /BOOT back at 12 V after the pin goes low       : {boot_off*1e6:5.1f} µs")
    print(f"  fan L/R time constant                           : {l_fan / r_fan * 1e6:5.1f} µs")
    print(f"  peak fan current during a PWM on-time           : {fan_on*1e3:5.1f} mA")
    print(f"  average fan current at 1 kHz / 50 % duty        : {fan_avg*1e3:5.1f} mA")
    print()


if __name__ == "__main__":
    main()
