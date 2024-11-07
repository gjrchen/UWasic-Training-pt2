# SPDX-FileCopyrightText: © 2024 Tiny Tapeout
# SPDX-License-Identifier: Apache-2.0

import cocotb
from cocotb.clock import Clock
from cocotb.triggers import ClockCycles, FallingEdge, RisingEdge
from cocotb.types.logic import Logic
from cocotb.types.logic_array import LogicArray

from random import randint, shuffle

CLOCK_PERIOD = 10  # 100 MHz
CLOCK_UNITS = "ns"

GLTEST = False
signal_dict = {'nLo': 0, 'nLb': 1, 'Eu': 2, 'sub': 3, 'Ea': 4, 'nLa' : 5, 'nEi': 6, 'nLi' : 7, 'nLr' : 8, 'nCE' : 9, 'nLmd' : 10, 'nLma' : 11, 'Lp' : 12, 'Ep' : 13, 'Cp' : 14}



def retrieve_control_signal(control_signal_vals, index):
    # Local testing might use a reverse order, in case we need to modify the order
    return control_signal_vals[index]

    

async def determine_gltest(dut):
    global GLTEST
    dut._log.info("See if the test is being run for GLTEST")
    if hasattr(dut, 'VPWR'):
        dut._log.info(f"VPWR is Defined, may not equal to 1, VPWR={dut.VPWR.value}, GLTEST=TRUE")
        GLTEST = True
    else:
        GLTEST = False
        dut._log.info("VPWR is NOT Defined, GLTEST=False")
        assert dut.user_project.bus.value == dut.user_project.bus.value, "Something went terribly wrong"

async def log_control_signals(dut):
    if (GLTEST):
        dut._log.info("GLTEST is TRUE, can't get control signals")
    else:
        control_signal_vals = dut.user_project.control_signals.value
        dut._log.info(f"Control Signals Array={control_signal_vals}")
        result_string = ""
        for signal in signal_dict:
            result_string += f"{signal}={retrieve_control_signal(control_signal_vals, signal_dict[signal])}, "
        dut._log.info(result_string)

async def init(dut):
    # Need to coordinate how we initialize
    await determine_gltest(dut)
    if (GLTEST):
        dut._log.info("GLTEST is TRUE")
    else:
        dut._log.info("GLTEST is FALSE")
    
    dut._log.info(f"Initialize clock with period={CLOCK_PERIOD} {CLOCK_UNITS}")
    clock = Clock(dut.clk, CLOCK_PERIOD, units=CLOCK_UNITS)

@cocotb.test()
async def check_gl_test(dut):
    dut._log.info("Checking if the test is being run for GLTEST")
    await determine_gltest(dut)
