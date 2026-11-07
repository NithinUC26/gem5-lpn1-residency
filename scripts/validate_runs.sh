#!/bin/bash
# Validation sweeps on the full pipeline kernel (with compressed instructions).
# Run from the gem5 folder after run_all.sh:  ./lpn1/scripts/validate_runs.sh
G=build/RISCV/gem5.opt; S=lpn1/scripts/lpn1_run.py; B=lpn1/bin/node_pipe_c
echo "--- DVFS sweep: three operating points ---"
for P in "100 1.0" "50 0.8" "20 0.6"; do set -- $P
  $G -d m5out/lpn1_pipe_c_f$1 $S $B --freq $1 --volt $2 2>&1 | grep -E "checksum|fatal|panic|associativity"
done
echo "--- Cache sensitivity: 2 KiB L1 caches ---"
$G -d m5out/lpn1_pipe_c_l1_2k $S $B --freq 50 --volt 0.8 --l1 2KiB 2>&1 | grep -E "checksum|fatal|panic"
echo "--- Optional: gem5 core power model ---"
$G -d m5out/lpn1_pipe_c_pm $S $B --freq 50 --volt 0.8 --power-model 2>&1 | grep -E "checksum|power model|fatal|panic|Error" | head -5
