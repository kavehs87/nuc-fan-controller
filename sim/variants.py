#!/usr/bin/env python3
"""Run the same 12 V fan against every drive option the parts bin allows.

The schematic on the sheet is the *booster* version.  This script builds small
netlists from the same exported device lines - same fan, same flyback diode,
same resistors - and swaps only the gate drive, so the numbers are comparable:

    booster-3v3      3.3 V pin -> 2N7002 -> IRF7416 -> IRFZ44N gate at +10.9 V
    booster-3v3-wc   same, but the IRFZ44N is a worst-case unit, Vgs(th) = 4.0 V
    direct-3v3       3.3 V pin -> 1k -> IRFZ44N gate            (one transistor)
    direct-3v3-wc    same, worst-case unit
    direct-5v        5 V pin -> 1k -> IRFZ44N gate (if the Pro Mini is the 5 V one)
    2n7002-only      3.3 V pin -> 1k -> 2N7002 as the pass element

Writes sim/out/variants.csv (for the plot) and prints the table.
"""
from __future__ import annotations

import csv
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "sim" / "out"
SRC = OUT / "mosfet-fan-switch.spice"

MODELS = ["2n7002.lib", "irf7416.lib", "irfz44n.lib", "irfz44n_wc.lib", "schottky.lib",
          "bc547.lib"]

BOOSTER_ONLY = {"R2", "R3", "MQ2", "MQ3", "R4", "C2"}


def device_lines() -> dict[str, str]:
    """Device lines of the exported netlist, keyed by designator."""
    out = {}
    for line in SRC.read_text().splitlines():
        s = line.strip()
        if not s or s.startswith("."):
            continue
        out[s.split()[0]] = s.replace("NC-Q2-0", "GND")
    return out


def pulse(v_drive: float) -> str:
    return f"V2 /PWM GND PULSE( 0 {v_drive} 0 20n 20n 500u 1m )"


def drive_of(dev: str) -> float:
    """High level of a 'V2 /PWM GND PULSE( 0 <high> ...' line."""
    return float(dev.split()[5])


def build(name: str, devs: dict[str, str], vectors: list[str]) -> Path:
    deck = OUT / f"variant_{name}.cir"
    data = OUT / f"variant_{name}.txt"
    head = [f'.include "{ROOT / "sim" / "models" / m}"' for m in MODELS]
    control = (
        "\n.control\n"
        f"dc V2 0 {drive_of(devs['V2'])} 0.01\n"
        f"wrdata sim/out/variant_{name}.txt {' '.join(vectors)}\n"
        ".endcontrol\n"
    )
    deck.write_text("\n".join(head) + "\n" + "\n".join(devs.values()) + "\n" + control + ".end\n")
    subprocess.run(["ngspice", "-b", str(deck)], check=True,
                   stdout=open(OUT / "variants.log", "a"), stderr=subprocess.STDOUT)
    return data


def last_row(path: Path) -> list[float]:
    rows = [ln.split() for ln in path.read_text().splitlines() if ln.strip()]
    return [float(v) for v in rows[-1]]


def main() -> None:
    base = device_lines()
    booster_vecs = ["v(/LGATE)", "v(/BOOT)", "v(/GATE)", "v(/DRAIN)", "i(v1)"]
    direct_vecs = ["v(/GATE)", "v(/DRAIN)", "i(v1)"]

    def direct(v_drive: float, model: str = "irfz44n") -> dict[str, str]:
        d = {k: v for k, v in base.items() if k not in BOOSTER_ONLY}
        d["V2"] = pulse(v_drive)
        d["R1"] = "R1 /PWM /GATE 1k"
        d["MQ1"] = f"MQ1 /DRAIN /GATE GND GND {model}"
        return d

    booster = dict(base)                      # exactly what the sheet shows
    booster_wc = dict(base)
    booster_wc["MQ1"] = "MQ1 /DRAIN /GATE GND GND irfz44n_wc"

    runs = [
        ("booster-3v3", booster, booster_vecs),
        ("booster-3v3-wc", booster_wc, booster_vecs),
        ("direct-3v3", direct(3.3), direct_vecs),
        ("direct-3v3-wc", direct(3.3, "irfz44n_wc"), direct_vecs),
        ("direct-5v", direct(5.0), direct_vecs),
        ("2n7002-only", {**direct(3.3, "2n7002"), "C1": "C1 /GATE GND 45p"}, direct_vecs),
    ]

    rows = []
    for name, devs, vecs in runs:
        # wrdata repeats the x column before every vector: x, v1, x, v2, ...
        vals = last_row(build(name, devs, vecs))
        vgate = abs(vals[1 + 2 * (len(vecs) - 3)])
        vdrain = abs(vals[1 + 2 * (len(vecs) - 2)])
        i_fan = abs(vals[1 + 2 * (len(vecs) - 1)])
        if i_fan < 1e-6:
            state = "off"
        elif vdrain < 0.2 * vgate:
            state = "ohmic"
        else:
            state = "saturated"
        rows.append({
            "variant": name,
            "pin_drive_V": drive_of(devs["V2"]),
            "gate_V": round(vgate, 3),
            "fan_mA": round(i_fan * 1e3, 1),
            "drain_mV": round(vdrain * 1e3, 1),
            "state": state,
            "rds_mOhm": round(vdrain / i_fan * 1e3, 1) if state == "ohmic" else None,
            "mW": round(vdrain * i_fan * 1e3, 2),
        })

    with open(OUT / "variants.csv", "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)

    print()
    print("  how the same fan behaves with the parts in your bin")
    print("  " + "-" * 82)
    print(f"  {'variant':15} {'pin':>5} {'gate':>6} {'fan':>7} {'V(drain)':>9} {'state':>10} {'Rds(on)':>9} {'in the FET':>11}")
    print(f"  {'':15} {'[V]':>5} {'[V]':>6} {'[mA]':>7} {'[mV]':>9} {'':>10} {'[mOhm]':>9} {'[mW]':>11}")
    for r in rows:
        rds = f"{r['rds_mOhm']:.1f}" if r["rds_mOhm"] is not None else "-"
        print(f"  {r['variant']:15} {r['pin_drive_V']:5.1f} {r['gate_V']:6.2f} "
              f"{r['fan_mA']:7.1f} {r['drain_mV']:9.1f} {r['state']:>10} {rds:>9} {r['mW']:11.2f}")
    print()


if __name__ == "__main__":
    main()
