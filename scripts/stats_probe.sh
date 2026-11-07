#!/bin/bash
# Show the statistics names gem5 produced for one run, so the analysis script can find them.
# Usage: ./lpn1/scripts/stats_probe.sh m5out/lpn1_pipe_c
F=$1/stats.txt
grep -E "simSeconds|simInsts|numCycles|committedInsts|committedOps|\.ipc|overallAccesses::total|overallMisses::total|numReads|numWrites|voltage|power|dynamic|static" "$F" | head -60
