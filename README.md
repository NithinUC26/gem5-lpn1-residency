# LPN-1 Phase 2 kit
- src/: sensor-node kernels (FIR, feature extraction, CRC, full pipeline), freestanding RV32 code
- scripts/: build (Docker), gem5 configuration (lpn1_run.py), validation runs, stats probe
Steps (from the gem5 folder):
1. ./lpn1/scripts/build_kernels.sh
2. ./lpn1/scripts/run_all.sh
3. ./lpn1/scripts/stats_probe.sh m5out/lpn1_pipe_c
Expected checksums (FRAMES=20): fir 04b4fd49, feat a6c4e687, crc b7b8cf3e, pipe 6e5cc518
