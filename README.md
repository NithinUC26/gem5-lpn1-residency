# LPN-1: A Low-Power RISC-V Microprocessor Modeled in gem5

Residency Project, Computer Architecture and Design (MSCS-531-M40).
LPN-1 is an in-order, single-issue RV32IMC core for an IoT sensor node, modeled in gem5 v25.1.0.1 (MinorCPU, 8 KiB 2-way L1 caches, 128 KiB on-chip memory, three DVFS points).

## Contents
- `src/`: sensor-node kernels (FIR filter, feature extraction, CRC-16, full pipeline), freestanding RV32 C code
- `scripts/`
  - `build_kernels.sh`: builds the kernels in Docker (RV32IMC and RV32IM)
  - `lpn1_run.py`: gem5 configuration (core, caches, memory, DVFS, power model)
  - `run_all.sh`, `validate_runs.sh`, `stats_probe.sh`: Phase 2 validation runs
  - `p3_runs.sh`, `phase3.py`: Phase 3 experiments and analysis
  - `energy.py`, `energy_model.json`, `summ.py`: energy model and stats summary
- `bin/`: compiled RV32 programs
- `results/`: `stats.txt` and `config.ini` from the runs
- `reports/`: Phase 1 to 3 reports (PDF)

## How to reproduce
Clone this repo as `lpn1/` inside your gem5 folder (gem5 built with `scons build/RISCV/gem5.opt`). Docker is needed for the build step. Run from the gem5 folder:
1. `./lpn1/scripts/build_kernels.sh`
2. `./lpn1/scripts/run_all.sh` (all kernels, checksum check)
3. `./lpn1/scripts/validate_runs.sh` (DVFS sweep, 2 KiB L1 test)
4. `./lpn1/scripts/p3_runs.sh` (DVFS points and L1 size sweep, all kernels)
5. `python3 lpn1/scripts/phase3.py` (tables, optimization steps, `p3_results.csv`)

Expected checksums (FRAMES=20): fir 04b4fd49, feat a6c4e687, crc b7b8cf3e, pipe 6e5cc518.

## Main results (pipeline kernel, one frame every 100 ms)
- Energy per frame: 9.19 µJ (baseline) to 1.94 µJ (78.9% lower)
- Average power: 91.9 µW to 19.4 µW
- Steps: retention sleep, one active SRAM bank, 1 KiB L1 caches, 0.6 V/20 MHz

## Notes
- Energy values are model estimates from assumed coefficients (`energy_model.json`), not silicon measurements.
- Retention sleep, bank gating, and wake-up energy are analytic; gem5 does not simulate them.
- gem5's power-model expression parser rejects scientific notation, so coefficients are written as plain decimals.
