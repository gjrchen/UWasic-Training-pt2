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
    if LocalTest:
        return control_signal_vals[index]
    else:
        return control_signal_vals[14-index]

    

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

def get_attr(dut, value):
    if not GLTEST:
        value.split('.')
        out = dut
        for val in value:
            out = getattr(out, val)
        return out
    else:
        return dut._id(f"\\{value}", extended=False)

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
    dut.uio_in.value = setbit(dut.uio_in.value, 0, 1) # Start programming
    dut._log.info("Reset")
    dut.rst_n.value = 0
    await RisingEdge(dut.clk)
    dut.rst_n.value = 1
    for i in range(0, 16):
        while not (dut.uio_out.value & 0b00000010):
            await RisingEdge(dut.clk)
        dut._log.info(f"Loading Byte {i}")
        dut.ui_in.value = data[i]
        while not (dut.uio_out.value & 0b00000100):
            await RisingEdge(dut.clk)
    dut.uio_in.value = setbit(dut.uio_in.value, 0, 0) # Stop programming
    dut._log.info("RAM Load Complete")
    dut._log.info("Reset")
    await RisingEdge(dut.clk)
    dut.rst_n.value = 0
    await RisingEdge(dut.clk)
    assert dut.rst_n.value == 0, f"Reset is not 0, rst_n={dut.rst_n.value}"
    dut.rst_n.value = 1
    await RisingEdge(dut.clk)

async def dumpRAM(dut):
    dut._log.info("Dumping RAM")
    if (not GLTEST):
        for i in range(0,16):
            if (LocalTest):
                dut._log.info(f"RAM[{i}] = {dut.user_project.ram.RAM.value[i]}")
            else:
                dut._log.info(f"RAM[{i}] = {dut.user_project.ram.RAM.value[15-i]}")
    else:
        dut._log.info("Cant dump RAM in GLTEST")
    dut._log.info("RAM dump complete")

async def mem_check(dut, data):
    dut._log.info("Memory Check Start")
    if (not GLTEST):
        for i in range(0, 16):
            if(LocalTest):
                assert dut.user_project.ram.RAM.value[i] == data[i], f"RAM[{i}] is not equal to data[{i}], RAM[{i}]={dut.user_project.ram.RAM.value[i]}, data[{i}]={data[i]}"
            else:
                assert dut.user_project.ram.RAM.value[15-i] == data[i], f"RAM[{i}] is not equal to data[{i}], RAM[{i}]={dut.user_project.ram.RAM.value[15-i]}, data[{i}]={data[i]}"
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

def pc_value(dut):
    pc = 0
    for i in range(4):
        pc |= (dut.user_project._id(f"\\pc.set_bit_{i}.S", extended = False).value << i)
    return pc

async def hlt_checker(dut):
    dut._log.info("HLT Checker Start")
    if (not GLTEST or GLTEST):
        pc_beginning = pc_value(dut)
        await FallingEdge(dut.clk)
        await FallingEdge(dut.clk)
        dut._log.info("T0")
        await log_control_signals(dut)
        #assert dut.user_project._id("\\control_signals.value", extended = False) == LogicArray("010011111100011"), f"Control Signals are not correct, expected=010011111100011"
        await FallingEdge(dut.clk)
        dut._log.info("T1")
        await log_control_signals(dut)
        #assert dut.user_project._id("\\control_signals.value", extended = False) == LogicArray("000111111100011"), f"Control Signals are not correct, expected=000111111100011"
        #assert retrieve_control_signal(dut._id("\\user_project.control_signals.value"), 14) == 0, f"""Cp is not 0, Ep={retrieve_control_signal(dut.user_project.control_signals.value, 14)}"""
        await FallingEdge(dut.clk)
        dut._log.info("T2")
        await log_control_signals(dut)
        #assert dut.user_project._id("\\control_signals.value", extended = False) == LogicArray("000110101100011"), f"Control Signals are not correct, expected=000110101100011"
        await FallingEdge(dut.clk)
        dut._log.info("T3")
        await log_control_signals(dut)
        #assert dut.user_project._id("\\control_signals.value", extended = False) == LogicArray("000111111100011"), f"Control Signals are not correct, expected=000111111100011"
        await FallingEdge(dut.clk)
        dut._log.info("T4")
        await log_control_signals(dut)
        #assert dut.user_project._id("\\control_signals.value", extended = False) == LogicArray("000111111100011"), f"Control Signals are not correct, expected=000111111100011"
        await FallingEdge(dut.clk)
        dut._log.info("T5")
        await log_control_signals(dut)
        #assert dut.user_project._id("\\control_signals.value", extended = False) == LogicArray("000111111100011"), f"Control Signals are not correct, expected=000111111100011"
        await FallingEdge(dut.clk)
        dut._log.info("T6")
        await log_control_signals(dut)
        #assert dut.user_project._id("\\pc.counter.value", extended = False) == LogicArray("000111111100011"), f"Control Signals are not correct, expected=000111111100011"
        await FallingEdge(dut.clk)
        assert pc_beginning == pc_value(dut), f"PC is not the same, pc_beginning={pc_beginning}, pc={pc_value(dut)}"

    else:
        dut._log.info("Cant check HLT in GLTEST")
    dut._log.info("HLT Checker Complete")

# async def jmp_checker(dut):
#     dut._log.info("JMP Checker Start")
#     if (not GLTEST):
#         pc_beginning = dut.user_project.pc.counter.value
#         await FallingEdge(dut.clk)
#         await FallingEdge(dut.clk)
#         dut._log.info("T0")
#         await log_control_signals(dut)
#         assert dut.user_project.control_signals.value == LogicArray("010011111100011"), f"Control Signals are not correct, expected=010011111100011"
#         await FallingEdge(dut.clk)
#         dut._log.info("T1")
#         await log_control_signals(dut)
#         assert dut.user_project.control_signals.value == LogicArray("100111111100011"), f"Control Signals are not correct, expected=100111111100011"
#         assert retrieve_control_signal(dut.user_project.control_signals.value, 14) == 0, f"""Cp is not 0, Ep={retrieve_control_signal(dut.user_project.control_signals.value, 14)}"""
#         await FallingEdge(dut.clk)
#         dut._log.info("T2")
#         await log_control_signals(dut)
#         assert dut.user_project.control_signals.value == LogicArray("000110101100011"), f"Control Signals are not correct, expected=000110101100011"
#         await FallingEdge(dut.clk)
#         dut._log.info("T3")
#         await log_control_signals(dut)
#         assert dut.user_project.control_signals.value == LogicArray("000011110100011"), f"Control Signals are not correct, expected=000011110100011"
#         await FallingEdge(dut.clk)
#         dut._log.info("T4")
#         await log_control_signals(dut)
#         assert dut.user_project.control_signals.value == LogicArray("000110111000011"), f"Control Signals are not correct, expected=000110111000011"
#         await FallingEdge(dut.clk)
#         dut._log.info("T5")
#         await log_control_signals(dut)
#         assert dut.user_project.control_signals.value == LogicArray("000111111100011"), f"Control Signals are not correct, expected=000111111100011"
#         await FallingEdge(dut.clk)
#         dut._log.info("T6")
#         await log_control_signals(dut)
#         assert dut.user_project.control_signals.value == LogicArray("000111111100011"), f"Control Signals are not correct, expected=000111111100011"
#         await FallingEdge(dut.clk)
#         assert pc_beginning == dut.user_project.pc.counter.value, f"PC is not the same, pc_beginning={pc_beginning}, pc={dut.user_project.pc.counter.value}"
#     else:
#         dut._log.info("Cant check JMP in GLTEST")
#     dut._log.info("JMP Checker Complete")


@cocotb.test()
async def test_operation_hlt(dut):
    program_data = [0x0F, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF]
    dut._log.info(f"Operation HLT Test Start")
    dut._log.info(f"data_bin={[str(bin(x)) for x in program_data]}")
    dut._log.info(f"data_hex={[str(hex(x)) for x in program_data]}")
    await init(dut)
    await load_ram(dut, program_data)
    await dumpRAM(dut)
    await mem_check(dut, program_data)
    await hlt_checker(dut)
    dut._log.info("Operation HLT Test Complete")
