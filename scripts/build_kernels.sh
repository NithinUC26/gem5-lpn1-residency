#!/bin/bash
# Cross-compile the sensor-node kernels for RV32 (with and without the C extension) using Docker.
# Run from the gem5 folder:  ./lpn1/scripts/build_kernels.sh
set -e
docker run --rm -v "$PWD/lpn1":/w -w /w debian:trixie bash -c '
  apt-get update -qq && apt-get install -y -qq gcc-riscv64-linux-gnu binutils-riscv64-linux-gnu >/dev/null 2>&1
  CC=riscv64-linux-gnu-gcc
  FLAGS="-O2 -mabi=ilp32 -ffreestanding -nostdlib -static -mno-relax -fno-pic -fno-stack-protector -fno-tree-loop-distribute-patterns -Wl,--no-relax -DFRAMES=${FRAMES:-20}"
  mkdir -p bin
  for K in 1:fir 2:feat 3:crc 4:pipe; do
    N=${K%%:*}; NAME=${K##*:}
    $CC $FLAGS -march=rv32imc -DKERNEL=$N src/target_main.c src/kernels.c -o bin/node_${NAME}_c
    $CC $FLAGS -march=rv32im  -DKERNEL=$N src/target_main.c src/kernels.c -o bin/node_${NAME}_nc
  done
  echo "--- ELF header and code size of the pipeline kernel (C extension on / off) ---"
  riscv64-linux-gnu-readelf -h bin/node_pipe_c | grep -E "Class|Machine|Flags"
  riscv64-linux-gnu-size bin/node_pipe_c bin/node_pipe_nc
'
echo "Host reference checksums:"
for K in 1 2 3 4; do cc -O2 -DKERNEL=$K -DFRAMES=${FRAMES:-20} lpn1/src/host_main.c lpn1/src/kernels.c -o /tmp/lpn1_host_$K && /tmp/lpn1_host_$K; done
