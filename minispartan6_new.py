#!/usr/bin/env python3

import argparse
from fractions import Fraction

from migen import *
from migen.genlib.resetsync import AsyncResetSynchronizer
from migen.build.platforms import minispartan6
from migen.build.generic_platform import *


from misoc.integration.soc_core import *
from misoc.integration.builder import *

from misoc.cores.gpio import GPIOOut
import freq_count_new


# class BaseSoC(SoCSDRAM):
class BaseSoC(SoCCore):
    csr_map = {"freq_count" : 8}
    csr_map.update(SoCCore.csr_map)

    def __init__(self, **kwargs):
        clk_freq = 32*1000000
        platform = minispartan6.Platform(device="xc6slx25")
        SoCCore.__init__(self, platform, clk_freq,
                  integrated_rom_size=0x8000, **kwargs)

        leds = Cat((platform.request("user_led") for p in range(8)))
        self.submodules.leds = GPIOOut(leds)

        freq_in = [("freq_in", 0, Pins("A:0"), IOStandard("LVTTL"))]
        platform.add_extension(freq_in)
        f_in = platform.request("freq_in")
        self.submodules.freq_count = ClockDomainsRenamer({"src" : "inc", "dest" : "sys"})(freq_count_new.FrequencyCounter(clk_freq, 6, 32))

        clk32 = platform.request("clk32")
        self.clock_domains.cd_sys = ClockDomain()
        self.clock_domains.cd_por = ClockDomain()
        self.clock_domains.cd_inc = ClockDomain(reset_less=True)
        self.comb += [self.cd_inc.clk.eq(f_in)]

        pulse = Signal(reset=1)
        self.comb += [self.cd_por.clk.eq(clk32)]
        self.comb += [self.cd_sys.clk.eq(clk32)]
        self.comb += [self.cd_sys.rst.eq(pulse)]
        self.sync.por += [pulse.eq(0)]



def main():
    parser = argparse.ArgumentParser(description="MiSoC port to the MiniSpartan6")
    builder_args(parser)
    soc_core_args(parser)
    args = parser.parse_args()

    soc = BaseSoC(**soc_core_argdict(args))
    builder = Builder(soc, **builder_argdict(args))
    builder.build()


if __name__ == "__main__":
    main()
