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
uio_dict = {'ready_for_ui' : 1, 'done_load' : 2, 'CF' : 3, 'ZF' : 4, 'HF' : 5}



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
def retrieve_bit_from_8_wide_wire(wire, index):
    # Local testing might use a reverse order, in case we need to modify the order
    if LocalTest:
        return wire[index]
    else:
        return wire[7-index]
    
async def wait_until_next_t0_gltest(dut):
    if (not GLTEST):
        timeout = 0
        dut._log.info("Wait until next T0 in non-GLTEST")
        while not (dut.user_project.cb.stage.value == 5):
            await RisingEdge(dut.clk)
            dut._log.info(f"Stage={dut.user_project.cb.stage.value}")
            timeout += 1
            if (timeout > 7):
                assert False, (f"Timeout at {dut.user_project.pc.counter.value}")
    else:
        dut._log.error("Cant wait until next T0 in GLTEST")


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
        dut._log.error("GLTEST is TRUE, can't get control signals")
    else:
        control_signal_vals = dut.user_project.control_signals.value
        dut._log.info(f"Control Signals Array={control_signal_vals}")
        result_string = ""
        for signal in signal_dict:
            result_string += f"{signal}={retrieve_control_signal(control_signal_vals, signal_dict[signal])}, "
        dut._log.info(result_string)

async def log_uio_out(dut):
    uio_vals = dut.uio_out.value
    dut._log.info(f"UIO_OUT Array={uio_vals}")
    result_string = ""
    for uio_pin in uio_dict:
        result_string += f"{uio_pin}={retrieve_bit_from_8_wide_wire(uio_vals, uio_dict[uio_pin])}, "
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
        timeout = 0
        while not (retrieve_bit_from_8_wide_wire(dut.uio_out.value, uio_dict['ready_for_ui'])):
            await RisingEdge(dut.clk)
            timeout += 1
            if (timeout > 100):
                assert False, (f"Timeout at Byte {i}")
        dut._log.info(f"Loading Byte {i}")
        dut.ui_in.value = data[i]
        timeout = 0
        while not (retrieve_bit_from_8_wide_wire(dut.uio_out.value, uio_dict['done_load'])):
            await RisingEdge(dut.clk)
            if (timeout > 100):
                assert False, (f"Timeout at Byte {i}")
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
        dut._log.error("Cant dump RAM in GLTEST")
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
        dut._log.error("Cant check memory in GLTEST")
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

async def hlt_checker(dut):
    dut._log.info("HLT Checker Start")
    if (not GLTEST):
        timeout = 0
        while not (dut.user_project.cb.stage.value == 0):
            await RisingEdge(dut.clk)
            dut._log.info(f"Stage={dut.user_project.cb.stage.value}")
            timeout += 1
            if (timeout > 2):
                assert False, (f"Timeout at {dut.user_project.pc.counter.value}")
        pc_beginning = dut.user_project.pc.counter.value
        dut._log.info(f"PC={pc_beginning}")
        dut._log.info("T0")
        assert dut.user_project.cb.stage.value == 0, f"Stage is not 0, stage={dut.user_project.cb.stage.value}"
        await log_control_signals(dut)
        await log_uio_out(dut)
        assert dut.user_project.control_signals.value == LogicArray("010011111100011"), f"Control Signals are not correct, expected=010011111100011"
        await RisingEdge(dut.clk)
        dut._log.info("T1")
        assert dut.user_project.cb.stage.value == 1, f"Stage is not 1, stage={dut.user_project.cb.stage.value}"
        await log_control_signals(dut)
        await log_uio_out(dut)
        assert dut.user_project.control_signals.value == LogicArray("000111111100011"), f"Control Signals are not correct, expected=000111111100011"
        assert retrieve_control_signal(dut.user_project.control_signals.value, 14) == 0, f"""Cp is not 0, Ep={retrieve_control_signal(dut.user_project.control_signals.value, 14)}"""
        assert retrieve_bit_from_8_wide_wire(dut.uio_out.value, uio_dict['HF']) == 1, f"""HF is not 1, HF={retrieve_bit_from_8_wide_wire(dut.uio_out.value, uio_dict['HF'])}"""
        await RisingEdge(dut.clk)
        dut._log.info("T2")
        assert dut.user_project.cb.stage.value == 2, f"Stage is not 2, stage={dut.user_project.cb.stage.value}"
        await log_control_signals(dut)
        await log_uio_out(dut)
        assert dut.user_project.control_signals.value == LogicArray("000110101100011"), f"Control Signals are not correct, expected=000110101100011"
        await RisingEdge(dut.clk)
        dut._log.info("T3")
        assert dut.user_project.cb.stage.value == 3, f"Stage is not 3, stage={dut.user_project.cb.stage.value}"
        await log_control_signals(dut)
        await log_uio_out(dut)
        assert dut.user_project.control_signals.value == LogicArray("000111111100011"), f"Control Signals are not correct, expected=000111111100011"
        assert dut.user_project.cb.opcode.value == 0, f"Opcode is not HLT, opcode={dut.user_project.cb.opcode.value}"
        await RisingEdge(dut.clk)
        dut._log.info("T4")
        assert dut.user_project.cb.stage.value == 4, f"Stage is not 4, stage={dut.user_project.cb.stage.value}"
        await log_control_signals(dut)
        await log_uio_out(dut)
        assert dut.user_project.control_signals.value == LogicArray("000111111100011"), f"Control Signals are not correct, expected=000111111100011"
        await RisingEdge(dut.clk)
        dut._log.info("T5")
        assert dut.user_project.cb.stage.value == 5, f"Stage is not 5, stage={dut.user_project.cb.stage.value}"
        await log_control_signals(dut)
        await log_uio_out(dut)
        assert dut.user_project.control_signals.value == LogicArray("000111111100011"), f"Control Signals are not correct, expected=000111111100011"
        await RisingEdge(dut.clk)
        dut._log.info("T6")
        assert dut.user_project.cb.stage.value == 6, f"Stage is not 6, stage={dut.user_project.cb.stage.value}"
        await log_control_signals(dut)
        await log_uio_out(dut)
        assert dut.user_project.control_signals.value == LogicArray("000111111100011"), f"Control Signals are not correct, expected=000111111100011"
        dut._log.info(f"PC={dut.user_project.pc.counter.value}")
        assert pc_beginning == dut.user_project.pc.counter.value, f"PC is not the same, pc_beginning={pc_beginning}, pc={dut.user_project.pc.counter.value}"

    else:
        dut._log.error("Cant check HLT in GLTEST")
    dut._log.info("HLT Checker Complete")

async def jmp_checker(dut, address):
    dut._log.info(f"JMP Checker Start with jmp_address={address}, hex={address:01X}, bin={address:4b}")
    if (not GLTEST):
        timeout = 0
        while not (dut.user_project.cb.stage.value == 0):
            await RisingEdge(dut.clk)
            dut._log.info(f"Stage={dut.user_project.cb.stage.value}")
            timeout += 1
            if (timeout > 2):
                assert False, (f"Timeout at {dut.user_project.pc.counter.value}")
        pc_beginning = dut.user_project.pc.counter.value
        dut._log.info(f"PC={pc_beginning}")
        dut._log.info("T0")
        assert dut.user_project.cb.stage.value == 0, f"Stage is not 0, stage={dut.user_project.cb.stage.value}"
        await log_control_signals(dut)
        await log_uio_out(dut)
        assert dut.user_project.control_signals.value == LogicArray("010011111100011"), f"Control Signals are not correct, expected=010011111100011"
        await RisingEdge(dut.clk)
        dut._log.info("T1")
        assert dut.user_project.cb.stage.value == 1, f"Stage is not 1, stage={dut.user_project.cb.stage.value}"
        await log_control_signals(dut)
        await log_uio_out(dut)
        assert dut.user_project.control_signals.value == LogicArray("100111111100011"), f"Control Signals are not correct, expected=100111111100011"
        await RisingEdge(dut.clk)
        dut._log.info("T2")
        assert dut.user_project.cb.stage.value == 2, f"Stage is not 2, stage={dut.user_project.cb.stage.value}"
        await log_control_signals(dut)
        await log_uio_out(dut)
        assert dut.user_project.control_signals.value == LogicArray("000110101100011"), f"Control Signals are not correct, expected=000110101100011"
        await RisingEdge(dut.clk)
        dut._log.info("T3")
        assert dut.user_project.cb.stage.value == 3, f"Stage is not 3, stage={dut.user_project.cb.stage.value}"
        await log_control_signals(dut)
        await log_uio_out(dut)
        assert dut.user_project.control_signals.value == LogicArray("001111110100011"), f"Control Signals are not correct, expected=001111110100011"
        assert dut.user_project.cb.opcode.value == 7, f"Opcode is not JMP, opcode={dut.user_project.cb.opcode.value}"
        await RisingEdge(dut.clk)
        dut._log.info("T4")
        assert dut.user_project.cb.stage.value == 4, f"Stage is not 4, stage={dut.user_project.cb.stage.value}"
        await log_control_signals(dut)
        await log_uio_out(dut)
        assert dut.user_project.control_signals.value == LogicArray("000111111100011"), f"Control Signals are not correct, expected=000111111100011"
        await RisingEdge(dut.clk)
        dut._log.info("T5")
        assert dut.user_project.cb.stage.value == 5, f"Stage is not 5, stage={dut.user_project.cb.stage.value}"
        await log_control_signals(dut)
        await log_uio_out(dut)
        assert dut.user_project.control_signals.value == LogicArray("000111111100011"), f"Control Signals are not correct, expected=000111111100011"
        await RisingEdge(dut.clk)
        dut._log.info("T6")
        assert dut.user_project.cb.stage.value == 6, f"Stage is not 6, stage={dut.user_project.cb.stage.value}"
        await log_control_signals(dut)
        await log_uio_out(dut)
        assert dut.user_project.control_signals.value == LogicArray("000111111100011"), f"Control Signals are not correct, expected=000111111100011"
        await RisingEdge(dut.clk)
        dut._log.info(f"PC={dut.user_project.pc.counter.value}")
        assert dut.user_project.pc.counter.value == address, f"PC is not address, pc={dut.user_project.pc.counter.value}, jmp_address={address}"
    else:
        dut._log.error("Cant check JMP in GLTEST")
    dut._log.info("JMP Checker Complete")


@cocotb.test()
async def test_operation_hlt(dut):
    program_data = [0x0F, 0x0F, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF]
    dut._log.info(f"Operation HLT Test Start")
    dut._log.info(f"data_bin={[str(bin(x)) for x in program_data]}")
    dut._log.info(f"data_hex={[str(hex(x)) for x in program_data]}")
    await init(dut)
    await load_ram(dut, program_data)
    await dumpRAM(dut)
    await mem_check(dut, program_data)
    await wait_until_next_t0_gltest(dut)
    await hlt_checker(dut)
    await hlt_checker(dut)
    dut._log.info("Operation HLT Test Complete")

@cocotb.test()
async def test_operation_jmp(dut):
    program_data = [0x7E, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0x0F, 0x0F]
    dut._log.info(f"Operation JMP Test Start")
    dut._log.info(f"data_bin={[str(bin(x)) for x in program_data]}")
    dut._log.info(f"data_hex={[str(hex(x)) for x in program_data]}")
    await init(dut)
    await load_ram(dut, program_data)
    await dumpRAM(dut)
    await mem_check(dut, program_data)
    await jmp_checker(dut, program_data[0]&0x0F)
    await wait_until_next_t0_gltest(dut)
    await hlt_checker(dut)
    await hlt_checker(dut)

    dut._log.info("Operation JMP Test Complete")
