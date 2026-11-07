#!/bin/bash
# Phase 3 experiment sweep. Run from the gem5 folder after run_all.sh and validate_runs.sh:
#   ./lpn1/scripts/p3_runs.sh
# Adds: DVFS points for every kernel, and L1 size sweep (1, 2, 4 KiB) for every kernel.
G=build/RISCV/gem5.opt; S=lpn1/scripts/lpn1_run.py
for N in fir feat crc pipe; do
  B=lpn1/bin/node_${N}_c
  for P in "100 1.0" "20 0.6"; do set -- $P
    [ -f m5out/lpn1_${N}_c_f$1/stats.txt ] || $G -d m5out/lpn1_${N}_c_f$1 $S $B --freq $1 --volt $2 2>&1 | grep -E "fatal|panic"
  done
  for K in 1 2 4; do
    [ -f m5out/lpn1_${N}_c_l1_${K}k/stats.txt ] || $G -d m5out/lpn1_${N}_c_l1_${K}k $S $B --freq 50 --volt 0.8 --l1 ${K}KiB 2>&1 | grep -E "fatal|panic"
  done
  echo "done $N"
done
ls -d m5out/lpn1_*_c_* m5out/lpn1_*_c | wc -l
