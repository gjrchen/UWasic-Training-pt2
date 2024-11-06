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
LocalTest = False

signal_dict = {'nLo': 0, 'nLb': 1, 'Eu': 2, 'sub': 3, 'Ea': 4, 'nLa' : 5, 'nEi': 6, 'nLi' : 7, 'nLr' : 8, 'nCE' : 9, 'nLmd' : 10, 'nLma' : 11, 'Lp' : 12, 'Ep' : 13, 'Cp' : 14}

def setbit(current, bit_index, bit_value):
    modified = current
    if LocalTest:
        modified[bit_index] = bit_value
    else:
        modified[7-bit_index] = bit_value
    return modified
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
    dut._log.info("Beginning Initialization")
    # Need to coordinate how we initialize
    await determine_gltest(dut)
    if (GLTEST):
        dut._log.info("GLTEST is TRUE")
    else:
        dut._log.info("GLTEST is FALSE")
    
    dut._log.info(f"Initialize clock with period={CLOCK_PERIOD}{CLOCK_UNITS}")
    clock = Clock(dut.clk, CLOCK_PERIOD, units=CLOCK_UNITS)
    cocotb.start_soon(clock.start())

    dut.ui_in.value = 0
    dut.uio_in.value = 0

    dut._log.info("Enable")
    await RisingEdge(dut.clk)
    await RisingEdge(dut.clk)
    dut.ena.value = 1
    await RisingEdge(dut.clk)
    await RisingEdge(dut.clk)
    dut._log.info("Reset")
    await RisingEdge(dut.clk)
    await RisingEdge(dut.clk)
    dut.rst_n.value = 0
    await RisingEdge(dut.clk)
    await RisingEdge(dut.clk)
    assert dut.rst_n.value == 0, f"Reset is not 0, rst_n={dut.rst_n.value}"
    dut.rst_n.value = 1
    await RisingEdge(dut.clk)

    dut._log.info("Initialization Complete")

async def load_ram(dut, data):
    dut._log.info("RAM Load Start")
    assert len(data) == 16, f"Data length is not 16, len(data)={len(data)}"
    dut.uio_in.value = setbit(dut.uio_in.value, 0, 1)
    await RisingEdge(dut.clk)
    await RisingEdge(dut.clk)
    for i in range(0, 16):
        await RisingEdge(dut.clk)
        await RisingEdge(dut.clk)
        dut.ui_in.value = data[i]
        await RisingEdge(dut.clk)
        await RisingEdge(dut.clk)
        dut.uio_in.value = setbit(dut.uio_in.value, 1, 1)
        await RisingEdge(dut.clk)
        await RisingEdge(dut.clk)
        dut.uio_in.value = setbit(dut.uio_in.value, 1, 0)
        await RisingEdge(dut.clk)
        await RisingEdge(dut.clk)
        await RisingEdge(dut.clk)
        await RisingEdge(dut.clk)
        await RisingEdge(dut.clk)
        await RisingEdge(dut.clk)
        await RisingEdge(dut.clk)
        await RisingEdge(dut.clk)
        await RisingEdge(dut.clk)
        await RisingEdge(dut.clk)
        await RisingEdge(dut.clk)
        await RisingEdge(dut.clk)
        await RisingEdge(dut.clk)
    dut.uio_in.value = setbit(dut.uio_in.value, 0, 0)
    dut._log.info("RAM Load Complete")
    dut._log.info("Reset")
    await RisingEdge(dut.clk)
    await RisingEdge(dut.clk)
    dut.rst_n.value = 0
    await RisingEdge(dut.clk)
    await RisingEdge(dut.clk)
    assert dut.rst_n.value == 0, f"Reset is not 0, rst_n={dut.rst_n.value}"
    dut.rst_n.value = 1
    await RisingEdge(dut.clk)

async def dumpRAM(dut):
    dut._log.info("Dumping RAM")
    if (not GLTEST):
        for i in range(0,16):
            dut._log.info(f"RAM[{i}] = {dut.user_project.ram.RAM.value[i]}")
    else:
        dut._log.info("Cant dump RAM in GLTEST")
    dut._log.info("RAM dump complete")

async def mem_check(dut, data):
    dut._log.info("Memory Check Start")
    if (not GLTEST):
        for i in range(0, 16):
            assert dut.user_project.ram.RAM.value[i] == data[i], f"RAM[{i}] is not equal to data[{i}], RAM[{i}]={dut.user_project.ram.RAM.value[i]}, data[{i}]={data[i]}"
    else:
        dut._log.info("Cant check memory in GLTEST")
    dut._log.info("Memory Check Complete")

@cocotb.test()
async def check_gl_test(dut):
    dut._log.info("Checking if the test is being run for GLTEST")
    await determine_gltest(dut)

@cocotb.test()
async def empty_ram_test(dut):
    dut._log.info("Empty RAM Test Start")
    await init(dut)
    await log_control_signals(dut)
    await RisingEdge(dut.clk)
    await ClockCycles(dut.clk, 10)
    dut._log.info("Empty RAM Test Complete")

@cocotb.test()
async def load_ram_test(dut):
    program_data = [0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF]
    dut._log.info(f"RAM Load Test Start")
    dut._log.info(f"data_bin={[str(bin(x)) for x in program_data]}")
    dut._log.info(f"data_hex={[str(hex(x)) for x in program_data]}")
    await init(dut)
    await load_ram(dut, program_data)
    await dumpRAM(dut)
    await mem_check(dut, program_data)
    dut._log.info("RAM Load Test Complete")

@cocotb.test()
async def output_basic_test(dut):
    program_data = [0x4F, 0x50, 0x00, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xAB]
    dut._log.info(f"Output Basic Test Start")
    dut._log.info(f"data_bin={[str(bin(x)) for x in program_data]}")
    dut._log.info(f"data_hex={[str(hex(x)) for x in program_data]}")
    await init(dut)
    await load_ram(dut, program_data)
    await dumpRAM(dut)
    await mem_check(dut, program_data)
    for i in range(0, 20):
        dut._log.info(dut.uo_out.value)
        await ClockCycles(dut.clk, 2)
    ##
    dut._log.info("Output Basic Test Complete")
    

@cocotb.test()
async def test_control_signals_execution(dut):
    program_data = [0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF]
    dut._log.info(f"Control Signals during Execution Test Start")
    dut._log.info(f"data_bin={[str(bin(x)) for x in program_data]}")
    dut._log.info(f"data_hex={[str(hex(x)) for x in program_data]}")
    await init(dut)
    await load_ram(dut, program_data)
    await dumpRAM(dut)
    await mem_check(dut, program_data)

    for i in range(0, 20):
        dut._log.info(dut.uo_out.value)
        await ClockCycles(dut.clk, 2)
    ##
    dut._log.info("Control Signals during Execution Test Complete")
