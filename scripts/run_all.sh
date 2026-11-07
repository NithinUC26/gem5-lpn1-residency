#!/bin/bash
# Validation runs: every kernel, with and without compressed instructions, at the middle operating point.
# Run from the gem5 folder:  ./lpn1/scripts/run_all.sh
G=build/RISCV/gem5.opt; S=lpn1/scripts/lpn1_run.py
for N in fir feat crc pipe; do
  for V in c nc; do
    echo "=== node_${N}_${V} ==="
    $G -d m5out/lpn1_${N}_${V} $S lpn1/bin/node_${N}_${V} --freq 50 --volt 0.8 2>&1 | grep -E "checksum|LPN-1|WARNING|fatal|panic|Exiting"
  done
done
