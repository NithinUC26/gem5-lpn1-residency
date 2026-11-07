# LPN-1 configuration for gem5: in-order RV32IMC core, 8 KiB L1 caches, small on-chip memory,
# one DVFS operating point per run (frequency and voltage).
# Usage: build/RISCV/gem5.opt -d m5out/NAME lpn1/scripts/lpn1_run.py BINARY --freq 50 --volt 0.8
import argparse
import m5.objects as mo
from gem5.components.boards.simple_board import SimpleBoard
from gem5.components.memory.simple import SingleChannelSimpleMemory
from gem5.components.processors.base_cpu_core import BaseCPUCore
from gem5.components.processors.base_cpu_processor import BaseCPUProcessor
from gem5.components.cachehierarchies.classic.private_l1_cache_hierarchy import (
    PrivateL1CacheHierarchy,
)
from gem5.isas import ISA
from gem5.resources.resource import BinaryResource
from gem5.simulate.simulator import Simulator

p = argparse.ArgumentParser()
p.add_argument("binary")
p.add_argument("--freq", type=float, default=50, help="core clock in MHz")
p.add_argument("--volt", type=float, default=0.8, help="supply voltage in V")
p.add_argument("--l1", default="8KiB", help="size of each L1 cache")
p.add_argument("--mem", default="128KiB", help="on-chip memory size")
p.add_argument("--mem-lat", default="10ns", help="on-chip memory access latency")
p.add_argument("--power-model", action="store_true", help="attach a gem5 power model to the core")
a = p.parse_args()


class LPN1Core(BaseCPUCore):
    def __init__(self):
        super().__init__(core=mo.RiscvMinorCPU(cpu_id=0), isa=ISA.RISCV)
        c = self.core
        c.isa[0].riscv_type = "RV32"          # 32-bit RISC-V
        # single-issue pipeline
        for name in ("decodeInputWidth", "executeInputWidth", "executeIssueLimit",
                     "executeCommitLimit", "executeMemoryIssueLimit", "executeMemoryCommitLimit"):
            try:
                setattr(c, name, 1)
            except Exception as e:
                print("WARNING: could not set", name, "->", e)


class TwoWayL1(PrivateL1CacheHierarchy):
    """Same hierarchy, but both L1 caches are made 2-way set associative."""

    def incorporate_cache(self, board):
        super().incorporate_cache(board)
        for name in ("l1icaches", "l1dcaches"):
            c = getattr(self, name, None)
            if c is None:
                continue
            try:
                items = list(c)
            except TypeError:
                items = [c]
            for x in items:
                x.assoc = 2
        print("L1 associativity set to 2")


caches = TwoWayL1(l1d_size=a.l1, l1i_size=a.l1)

board = SimpleBoard(
    clk_freq=f"{a.freq}MHz",
    processor=BaseCPUProcessor(cores=[LPN1Core()]),
    memory=SingleChannelSimpleMemory(latency=a.mem_lat, latency_var="0ns",
                                     bandwidth="6.4GiB/s", size=a.mem),
    cache_hierarchy=caches,
)
board.clk_domain.voltage_domain.voltage = [f"{a.volt}V"]   # operating-point voltage (reported in stats)
if a.power_model:
    # Core power model: dynamic power = Ceff * V^2 * f * activity, static power = leakage current * V.
    # The coefficients are assumed values (see energy_model.json).
    from m5.objects import MathExprPowerModel, PowerModel

    PATH = "board.processor.cores.core"

    class CoreOn(MathExprPowerModel):
        def __init__(self, **kw):
            super().__init__(**kw)
            f = f"({PATH}.numCycles / simSeconds)"
            self.dyn = f"(0.000000000005 + 0.000000000015 * {PATH}.ipc) * voltage * voltage * {f}"
            self.st = "0.00002 * voltage"

    class Zero(MathExprPowerModel):
        def __init__(self, **kw):
            super().__init__(**kw)
            self.dyn = "0"
            self.st = "0"

    class CorePower(PowerModel):
        def __init__(self, **kw):
            super().__init__(**kw)
            # order: ON, CLK_GATED, SRAM_RETENTION, OFF
            self.pm = [CoreOn(), Zero(), Zero(), Zero()]

    board.processor.cores[0].core.power_model = [CorePower()]
    print("core power model attached")

board.set_se_binary_workload(BinaryResource(local_path=a.binary))
print(f"LPN-1: RV32 MinorCPU, {a.freq} MHz, {a.volt} V, L1 {a.l1}, memory {a.mem}")
Simulator(board=board).run()
