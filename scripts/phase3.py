#!/usr/bin/env python3
"""Phase 3 analysis. Run from the gem5 folder:  python3 lpn1/scripts/phase3.py
Reads m5out/lpn1_* stats, prints tables, writes lpn1/p3_results.csv."""
import glob, json, math, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from summ import load, row

HERE = os.path.dirname(os.path.abspath(__file__))
M = json.load(open(os.path.join(HERE, "energy_model.json")))
FRAMES = 20                 # frames per run (node.h)
PERIOD_S = 0.1              # one frame every 100 ms (10 Hz sensor), assumed
WAKE_UJ = 0.5               # assumed wake-up energy per frame from retention sleep
L1_REF_KIB = 8.0
KERN = ["fir", "feat", "crc", "pipe"]
OUT = "m5out"

def run(name):
    p = f"{OUT}/lpn1_{name}/stats.txt"
    return row(name, load(p)) if os.path.exists(p) else None

def energy(r, l1_kib=8.0, banks=4, V=None, mhz=None):
    """Active-state energy (J) of a run; allows overriding V, f, L1 size, active banks."""
    _, v, f, ms, cyc, ins, ipc, ia, im, da, dm, mem = r
    V = v if V is None else V
    t = cyc / ((f if mhz is None else mhz) * 1e6)
    s = l1_kib / L1_REF_KIB
    e = {}
    e["core"] = (M["core_energy_per_inst_pJ_at_1V"] * ins + M["core_energy_per_cycle_pJ_at_1V"] * cyc) * V * V * 1e-12
    e["L1"] = M["l1_access_pJ_at_1V"] * math.sqrt(s) * (ia + da) * V * V * 1e-12
    e["mem"] = M["memory_access_pJ"] * mem * 1e-12
    leak = (M["core_leakage_uA"] * V + 2 * M["l1_leakage_uW_each_at_1V"] * s * V) * 1e-6 \
        + banks * M["memory_leakage_uW_per_bank_active"] * 1e-6
    e["leak"] = leak * t
    e["total"] = sum(e.values())
    return e, t, ins, cyc, leak

def idle_power(V, l1_kib, mode, banks):
    s = l1_kib / L1_REF_KIB
    if mode == "clockgate":      # everything powered, no switching
        return (M["core_leakage_uA"] * V + 2 * M["l1_leakage_uW_each_at_1V"] * s * V) * 1e-6 + banks * M["memory_leakage_uW_per_bank_active"] * 1e-6
    # retention: core and L1 power gated, SRAM banks in retention, always-on domain on
    return banks * M["memory_leakage_uW_per_bank_active"] * M["retention_leakage_factor"] * 1e-6 + M["always_on_uW"] * 1e-6

def frame_energy(r, l1_kib, banks, V, mhz, mode):
    e, t, ins, cyc, _ = energy(r, l1_kib, banks, V, mhz)
    tf = t / FRAMES
    ea = e["total"] / FRAMES
    ei = idle_power(V, l1_kib, mode, banks) * max(PERIOD_S - tf, 0)
    ew = WAKE_UJ * 1e-6 if mode == "retention" else 0.0
    return ea, ei, ew, tf

def main():
    global PERIOD_S
    csv = ["table,run,V,MHz,ms,insts,IPC,uJ,pJ_per_inst"]
    print("\n=== Table A: baseline, 50 MHz / 0.8 V, 8 KiB L1 (compressed build) ===")
    print(f"{'kernel':7}{'insts':>9}{'cycles':>9}{'IPC':>7}{'ms':>8}{'core':>7}{'L1':>7}{'mem':>7}{'leak':>7}{'uJ':>8}{'pJ/i':>7}{'uW':>7}{'L1I miss%':>10}{'L1D miss%':>10}")
    for k in KERN:
        r = run(f"{k}_c")
        if not r: continue
        e, t, ins, cyc, _ = energy(r)
        print(f"{k:7}{ins:9.0f}{cyc:9.0f}{r[6]:7.3f}{r[3]:8.3f}{e['core']*1e6:7.2f}{e['L1']*1e6:7.2f}{e['mem']*1e6:7.2f}{e['leak']*1e6:7.2f}{e['total']*1e6:8.2f}{e['total']/ins*1e12:7.1f}{e['total']/t*1e6:7.0f}{100*r[8]/r[7]:10.2f}{100*r[10]/r[9]:10.2f}")
        csv.append(f"A,{k}_c,{r[1]},{r[2]:.1f},{r[3]:.3f},{ins:.0f},{r[6]:.3f},{e['total']*1e6:.2f},{e['total']/ins*1e12:.1f}")

    print("\n=== Table B: DVFS (cycles must match across points) ===")
    print(f"{'kernel':7}{'point':>10}{'cycles':>9}{'ms':>9}{'uJ':>8}{'pJ/i':>7}{'uW':>7}{'EDP uJ*ms':>11}")
    for k in KERN:
        for f in ("f100", "", "f20"):
            r = run(f"{k}_c" + (f"_{f}" if f else ""))
            if not r: continue
            e, t, ins, cyc, _ = energy(r)
            print(f"{k:7}{r[2]:5.0f}/{r[1]:.1f}V{cyc:9.0f}{r[3]:9.3f}{e['total']*1e6:8.2f}{e['total']/ins*1e12:7.1f}{e['total']/t*1e6:7.0f}{e['total']*1e6*r[3]:11.1f}")
            csv.append(f"B,{k}_c_{f or 'f50'},{r[1]},{r[2]:.1f},{r[3]:.3f},{ins:.0f},{r[6]:.3f},{e['total']*1e6:.2f},{e['total']/ins*1e12:.1f}")

    print("\n=== Table C: L1 size sweep (50 MHz / 0.8 V); size-scaled L1 energy and leakage ===")
    print(f"{'kernel':7}{'L1 KiB':>7}{'cycles':>9}{'ms':>8}{'dTime%':>8}{'I miss':>8}{'D miss':>8}{'uJ':>8}{'dEnergy%':>9}")
    best = {}
    for k in KERN:
        base = run(f"{k}_c")
        if not base: continue
        eb = energy(base, 8)[0]["total"]
        for kib in (1, 2, 4, 8):
            r = base if kib == 8 else run(f"{k}_c_l1_{kib}k")
            if not r: continue
            e = energy(r, kib)[0]["total"]
            dt = 100 * (r[3] / base[3] - 1); de = 100 * (e / eb - 1)
            print(f"{k:7}{kib:7d}{r[4]:9.0f}{r[3]:8.3f}{dt:8.2f}{r[8]:8.0f}{r[10]:8.0f}{e*1e6:8.2f}{de:9.2f}")
            csv.append(f"C,{k}_l1_{kib}k,{r[1]},{r[2]:.1f},{r[3]:.3f},{r[5]:.0f},{r[6]:.3f},{e*1e6:.2f},{e/r[5]*1e12:.1f}")
            if dt <= 2.0 and (k not in best or e < best[k][1]): best[k] = (kib, e)
    print("Smallest-energy L1 size with <=2% slowdown:", {k: v[0] for k, v in best.items()})
    l1_pick = max(v[0] for v in best.values()) if best else 8   # one size for the whole node: largest needed

    print(f"\n=== Table D: optimization steps, pipeline kernel, one frame per {PERIOD_S*1e3:.0f} ms ===")
    base = run("pipe_c")
    if base:
        c0 = base[4]
        r100 = run("pipe_c_f100"); r20 = run("pipe_c_f20")
        if r100 and abs(r100[4] - c0) > 0.01 * c0:
            print("WARNING: cycles differ across DVFS points; analytic frequency scaling is approximate")
        r_l1 = base if l1_pick == 8 else run(f"pipe_c_l1_{l1_pick}k") or base
        steps = [
            ("S0 baseline: 1.0V/100MHz, 8KiB L1, 4 banks, clock-gated idle", base, 8, 4, 1.0, 100, "clockgate"),
            ("S1 + retention sleep (core/L1 power-gated)", base, 8, 4, 1.0, 100, "retention"),
            ("S2 + bank gating (1 of 4 banks)", base, 8, 1, 1.0, 100, "retention"),
            (f"S3 + L1 right-sizing ({l1_pick} KiB)", r_l1, l1_pick, 1, 1.0, 100, "retention"),
        ]
        # S4: pick the DVFS point with the lowest frame energy
        opts = [(1.0, 100), (0.8, 50), (0.6, 20)]
        cand = [(sum(frame_energy(r_l1, l1_pick, 1, V, f, "retention")[:3]), V, f) for V, f in opts]
        _, Vb, fb = min(cand)
        steps.append((f"S4 + DVFS ({fb}MHz/{Vb}V)", r_l1, l1_pick, 1, Vb, fb, "retention"))
        print(f"{'step':66}{'active':>8}{'idle':>8}{'wake':>7}{'uJ/frame':>10}{'uW avg':>8}{'frame ms':>9}{'saving':>8}")
        e0 = None
        for name, r, kib, banks, V, f, mode in steps:
            ea, ei, ew, tf = frame_energy(r, kib, banks, V, f, mode)
            tot = ea + ei + ew
            e0 = e0 or tot
            print(f"{name:66}{ea*1e6:8.3f}{ei*1e6:8.3f}{ew*1e6:7.2f}{tot*1e6:10.3f}{tot/PERIOD_S*1e6:8.1f}{tf*1e3:9.2f}{100*(1-tot/e0):7.1f}%")
            csv.append(f"D,{name[:2]},{V},{f},{tf*1e3:.3f},{r[5]/FRAMES:.0f},{r[6]:.3f},{tot*1e6:.3f},{tot/(r[5]/FRAMES)*1e12:.1f}")
        print("\nDVFS candidates (uJ/frame, retention, chosen L1 and 1 bank):")
        for c, V, f in sorted(cand, key=lambda x: -x[2]): print(f"  {f:4d} MHz / {V:.1f} V : {c*1e6:.3f}")
        print("\nSensitivity of S4 vs S0 to the frame period (saving %):")
        for per in (0.01, 0.1, 1.0):
            PERIOD_S = per
            a = sum(frame_energy(base, 8, 4, 1.0, 100, "clockgate")[:3])
            sens = []
            for V, f in opts:
                sens.append((sum(frame_energy(r_l1, l1_pick, 1, V, f, "retention")[:3]), V, f))
            b = min(sens)
            print(f"  period {per*1e3:6.0f} ms: S0 {a*1e6:8.3f} uJ -> best {b[0]*1e6:8.3f} uJ at {b[2]}MHz/{b[1]}V ({100*(1-b[0]/a):.1f}% saving)")
    open("lpn1/p3_results.csv", "w").write("\n".join(csv) + "\n")
    print("\nwrote lpn1/p3_results.csv")

if __name__ == "__main__":
    main()
