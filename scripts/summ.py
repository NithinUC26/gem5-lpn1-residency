#!/usr/bin/env python3
"""Summarize gem5 runs: python3 lpn1/scripts/summ.py 'm5out/lpn1_*'"""
import glob, re, sys

def load(path):
    d = {}
    started = False
    for line in open(path):
        if "Begin Simulation Statistics" in line:
            if started:
                break
            started = True
        m = re.match(r"^(\S+)\s+([-\d.eE+naif]+)\s", line)
        if m:
            d[m.group(1)] = m.group(2)
    return d

def get(d, pat):
    for k, v in d.items():
        if re.search(pat, k):
            return float(v)
    return float("nan")

def row(name, d):
    t = get(d, r"^simSeconds$")
    cyc = get(d, r"core\.numCycles$")
    ins = get(d, r"^simInsts$")
    return [name, get(d, r"clk_domain\.voltage_domain\.voltage$"), cyc / t / 1e6, t * 1e3, cyc, ins, ins / cyc,
            get(d, r"l1icaches\.overallAccesses::total$"), get(d, r"l1icaches\.overallMisses::total$"),
            get(d, r"l1dcaches\.overallAccesses::total$"), get(d, r"l1dcaches\.overallMisses::total$"),
            get(d, r"memory\.module\.numReads::total$") + (lambda w: 0.0 if w != w else w)(get(d, r"memory\.module\.numWrites::total$"))]

if __name__ == "__main__":
    pat = sys.argv[1] if len(sys.argv) > 1 else "m5out/lpn1_*"
    print(f"{'run':24}{'V':>5}{'MHz':>7}{'ms':>9}{'cycles':>10}{'insts':>10}{'IPC':>6}{'L1I acc':>9}{'L1I mis':>8}{'L1D acc':>9}{'L1D mis':>8}{'mem':>6}")
    for p in sorted(glob.glob(pat + "/stats.txt")):
        n = p.split("/")[-2].replace("lpn1_", "")
        r = row(n, load(p))
        print(f"{r[0]:24}{r[1]:5.2f}{r[2]:7.1f}{r[3]:9.3f}{r[4]:10.0f}{r[5]:10.0f}{r[6]:6.3f}{r[7]:9.0f}{r[8]:8.0f}{r[9]:9.0f}{r[10]:8.0f}{r[11]:6.0f}")
