#!/usr/bin/env python3
"""Preliminary energy estimate per run (active state only): python3 lpn1/scripts/energy.py 'm5out/lpn1_*'"""
import glob, json, os, sys
sys.path.insert(0, os.path.dirname(__file__))
from summ import load, row

M = json.load(open(os.path.join(os.path.dirname(__file__), "energy_model.json")))

def energy(r):
    name, V, mhz, ms, cyc, ins, ipc, ia, im, da, dm, mem = r
    t = ms / 1e3
    e = {}
    e["core"] = (M["core_energy_per_inst_pJ_at_1V"] * ins + M["core_energy_per_cycle_pJ_at_1V"] * cyc) * V * V * 1e-12
    e["L1"] = M["l1_access_pJ_at_1V"] * (ia + da) * V * V * 1e-12
    e["memory"] = M["memory_access_pJ"] * mem * (M["memory_voltage_V"] ** 2) * 1e-12
    leak_w = (M["core_leakage_uA"] * V + 2 * M["l1_leakage_uW_each_at_1V"] * V) * 1e-6 + M["memory_banks"] * M["memory_leakage_uW_per_bank_active"] * 1e-6
    e["leakage"] = leak_w * t
    e["total"] = sum(e.values())
    return e, ins

if __name__ == "__main__":
    pat = sys.argv[1] if len(sys.argv) > 1 else "m5out/lpn1_*"
    print(f"{'run':24}{'V':>5}{'MHz':>7}{'ms':>9}{'dyn core uJ':>12}{'L1 uJ':>8}{'mem uJ':>8}{'leak uJ':>9}{'total uJ':>10}{'pJ/inst':>9}")
    for p in sorted(glob.glob(pat + "/stats.txt")):
        r = row(p.split("/")[-2].replace("lpn1_", ""), load(p))
        e, ins = energy(r)
        print(f"{r[0]:24}{r[1]:5.2f}{r[2]:7.1f}{r[3]:9.3f}{e['core']*1e6:12.2f}{e['L1']*1e6:8.2f}{e['memory']*1e6:8.2f}{e['leakage']*1e6:9.2f}{e['total']*1e6:10.2f}{e['total']/ins*1e12:9.1f}")
