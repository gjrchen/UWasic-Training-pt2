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

def to_8_bit_array(value):
    return LogicArray(f'{value:08b}')

def get_control_signal_array_gltest(dut):
    nLo = dut.user_project._id("\\cb.control_signals[0]", extended = False).value             # Use the output of the control signal block because it is exactly the same wire
    nLb = dut.user_project._id("\\b_register.n_load", extended = False).value
    Eu = int(dut.user_project._id("\\cb.control_signals[2]", extended = False).value and dut.rst_n.value)
    sub = dut.user_project._id("\\alu_object.addsub.genblk1[0].fa.cin", extended = False).value
    Ea = int(dut.user_project._id("\\cb.control_signals[4]", extended = False).value and dut.rst_n.value)
    nLa = dut.user_project._id("\\accumulator_object.load", extended = False).value
    nEi = int(dut.user_project._id("\\cb.control_signals[6]", extended = False).value or (not dut.rst_n.value))
    nLi = dut.user_project._id("\\cb.control_signals[7]", extended = False).value
    nLr = dut.user_project._id("\\cb.control_signals[8]", extended = False).value
    nCE = int(dut.user_project._id("\\cb.control_signals[9]", extended = False).value or (not dut.rst_n.value))
    nLmd = dut.user_project._id("\\cb.control_signals[10]", extended = False).value
    nLma = dut.user_project._id("\\cb.control_signals[11]", extended = False).value
    Lp = dut.user_project._id("\\cb.control_signals[12]", extended = False).value
    #read_ui_in = dut.user_project._id("\\cb.read_ui_in", extended = False).value
    Ep = int(dut.user_project._id("\\cb.control_signals[13]", extended = False).value and dut.rst_n.value)
    Cp = dut.user_project._id("\\cb.control_signals[14]", extended = False).value
    #array = LogicArray(f"{nLo}{nLb}{Eu}{sub}{Ea}{nLa}{nEi}{nLi}{nLr}{nCE}{nLmd}{nLma}{Lp}{Ep}{Cp}")
    array = LogicArray(f"{Cp}{Ep}{Lp}{nLma}{nLmd}{nCE}{nLr}{nLi}{nEi}{nLa}{Ea}{sub}{Eu}{nLb}{nLo}")
    return array


def get_control_signal_array(dut):
    if (GLTEST):
        return get_control_signal_array_gltest(dut)
    else:
        return dut.user_project.control_signals.value

def get_regA_value_gltest(dut):
    regA_int = 0
    for i in range(8):
        regA_int += (dut.user_project._id(f"\\alu_object.addsub.genblk1[{i}].fa.a", extended = False).value << i)
    return to_8_bit_array(regA_int)

def get_regA_value(dut):
    if (GLTEST):
        return get_regA_value_gltest(dut)
    else:
        return dut.user_project.accumulator_object.regA.value
    
def get_regB_value_gltest(dut):
    regB_int = 0
    for i in range(8):
        regB_int += (dut.user_project._id(f"\\alu_object.addsub.op_b[{i}]", extended = False).value << i)
    return to_8_bit_array(regB_int)

def get_regB_value(dut):
    if (GLTEST):
        return get_regB_value_gltest(dut)
    else:
        return dut.user_project.b_register.value.value

def get_bus_value_gltest(dut):
    bus_int = 0
    for i in range(8):
        bus_int += (dut.user_project._id(f"\\accumulator_object.bus[{i}]", extended = False).value << i)
    return LogicArray(bus_int)

def get_bus_value(dut):
    if (GLTEST):
        return get_bus_value_gltest(dut)
    else:
        return dut.user_project.bus.value

def get_pc(dut):
    if GLTEST:
        pc = 0
        for i in range(4):
            pc |= (dut.user_project._id(f"\\pc.set_bit_{i}.S", extended = False).value << i)
        return pc
    else:
        return dut.user_project.pc.counter.value
    
def get_cb_stage(dut):
    if GLTEST:
        stage = 0
        for i in range(3):
            stage |= (dut.user_project._id(f"\\cb.stage[{i}]", extended = False).value << i)
        return stage
    else:
        return dut.user_project.cb.stage.value

def get_mar_addr(dut):
    if GLTEST:
        addr = 0
        for i in range(4):
            addr |= (dut.user_project._id(f"\\input_mar_register.addr[{i}]", extended = False).value << i)
        return to_8_bit_array(addr)
    else:
        return dut.user_project.input_mar_register.addr.value

def get_mar_data(dut):
    if GLTEST:
        data = 0
        for i in range(8):
            data |= (dut.user_project._id(f"\\input_mar_register.data[{i}]", extended = False).value << i)
        return to_8_bit_array(data)
    else:
        return dut.user_project.input_mar_register.data.value
    
def get_opcode(dut):
    if GLTEST:
        opcode = 0
        for i in range(4, 8):
            opcode |= (dut.user_project._id(f"\\instruction_register.instruction[{i}]", extended = False).value << (i - 4))
        return opcode
    else:
        return dut.user_project.cb.opcode.value
    
def bus_check(dut):
    bus = get_bus_value(dut)
    for i in range(8):
        assert bus[i] != 'x', f"Bus has X, bus[{i}]={bus[i]}"

async def check_adder_operation(operation, a, b):
    if operation == 0:
        expVal = (a + b) 
        expCF = int((expVal & 0x100) >> 8)
        expVal = expVal & 0xFF  # 8-bit overflow behavior for addition
    elif operation == 1:
        expVal = (a + ((b ^ 0xFF) + 1))
        expCF = (expVal & 0x100) >> 8
        expVal = expVal & 0xFF  # 8-bit underflow behavior for subtraction
    expZF = int(expVal == 0)
    return expVal, expCF, expZF

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
    timeout = 0
    dut._log.info("Wait until next T0 in non-GLTEST")
    while not (get_cb_stage(dut) == 5):
        await RisingEdge(dut.clk)
        dut._log.info(f"Stage={get_cb_stage(dut)}")
        timeout += 1
        if (timeout > 7):
            assert False, (f"Timeout at {get_pc(dut)}")

async def wait_until_next_t3_gltest(dut):
    timeout = 0
    dut._log.info("Wait until next T3 in non-GLTEST")
    while not (get_cb_stage(dut) == 3):
        await RisingEdge(dut.clk)
        dut._log.info(f"Stage={get_cb_stage(dut)}")
        timeout += 1
        if (timeout > 7):
            assert False, (f"Timeout at {get_pc(dut)}")


async def determine_gltest(dut):
    global GLTEST
    dut._log.info("See if the test is being run for GLTEST")
    if hasattr(dut, 'VPWR'):
        dut._log.info(f"VPWR is Defined, may not equal to 1, VPWR={dut.VPWR.value}, GLTEST=TRUE")
        GLTEST = True
    else:
        GLTEST = False
        dut._log.info("VPWR is NOT Defined, GLTEST=False")
        assert get_bus_value(dut) == get_bus_value(dut), "Something went terribly wrong"

async def log_control_signals(dut):
    control_signal_vals = get_control_signal_array(dut)
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
    for i in range(0,16):
        dut._log.info(f"RAM[{i}] = {get_ram(dut)[i]}")
    dut._log.info("RAM dump complete")

async def mem_check(dut, data):
    dut._log.info("Memory Check Start")
    for i in range(0, 16):
        assert get_ram(dut)[i].integer == data[i], f"RAM[{i}] is not equal to data[{i}], RAM[{i}]={get_ram(dut)[i]}, data[{i}]={data[i]}"
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
    pc_beginning = get_pc(dut)
    dut._log.info(f"PC={pc_beginning}")
    await wait_until_next_t3_gltest(dut)
    for i in range(20):
        await RisingEdge(dut.clk)
        assert get_cb_stage(dut) == 7, f"Stage is not 7, stage={get_cb_stage(dut)}"
        await log_control_signals(dut)
        await log_uio_out(dut)
        assert get_control_signal_array(dut) == LogicArray("000111111100011"), f"Control Signals are not correct, expected=000111111100011"
    dut._log.info(f"PC={get_pc(dut)}")
    assert pc_beginning + 1 == get_pc(dut), f"PC is not the same, pc_beginning={pc_beginning}, pc={get_pc(dut)}"
    dut._log.info("HLT Checker Complete")

async def nop_checker(dut):
    dut._log.info(f"NOP Checker Start")
    timeout = 0
    while not (get_cb_stage(dut) == 0):
        await RisingEdge(dut.clk)
        dut._log.info(f"Stage={get_cb_stage(dut)}")
        timeout += 1
        if (timeout > 2):
            assert False, (f"Timeout at {get_pc(dut)}")
    pc_beginning = get_pc(dut)
    dut._log.info(f"PC={pc_beginning}")
    dut._log.info("T0")
    assert get_cb_stage(dut) == 0, f"Stage is not 0, stage={get_cb_stage(dut)}"
    await log_control_signals(dut)
    await log_uio_out(dut)
    assert get_control_signal_array(dut) == LogicArray("010011111100011"), f"Control Signals are not correct, expected=010011111100011"
    await RisingEdge(dut.clk)
    dut._log.info("T1")
    assert get_cb_stage(dut) == 1, f"Stage is not 1, stage={get_cb_stage(dut)}"
    await log_control_signals(dut)
    await log_uio_out(dut)
    assert get_control_signal_array(dut) == LogicArray("100111111100011"), f"Control Signals are not correct, expected=100111111100011"
    await RisingEdge(dut.clk)
    dut._log.info("T2")
    assert get_cb_stage(dut) == 2, f"Stage is not 2, stage={get_cb_stage(dut)}"
    await log_control_signals(dut)
    await log_uio_out(dut)
    assert get_control_signal_array(dut) == LogicArray("000110101100011"), f"Control Signals are not correct, expected=000110101100011"
    await RisingEdge(dut.clk)
    dut._log.info("T3")
    assert get_cb_stage(dut) == 3, f"Stage is not 3, stage={get_cb_stage(dut)}"
    await log_control_signals(dut)
    await log_uio_out(dut)
    assert get_control_signal_array(dut) == LogicArray("000111111100011"), f"Control Signals are not correct, expected=000111111100011"
    assert get_opcode(dut) == 1, f"Opcode is not NOP, opcode={get_opcode(dut)}"
    await RisingEdge(dut.clk)
    dut._log.info("T4")
    assert get_cb_stage(dut) == 4, f"Stage is not 4, stage={get_cb_stage(dut)}"
    await log_control_signals(dut)
    await log_uio_out(dut)
    assert get_control_signal_array(dut) == LogicArray("000111111100011"), f"Control Signals are not correct, expected=000111111100011"
    await RisingEdge(dut.clk)
    dut._log.info("T5")
    assert get_cb_stage(dut) == 5, f"Stage is not 5, stage={get_cb_stage(dut)}"
    await log_control_signals(dut)
    await log_uio_out(dut)
    assert get_control_signal_array(dut) == LogicArray("000111111100011"), f"Control Signals are not correct, expected=000111111100011"
    await RisingEdge(dut.clk)
    dut._log.info("T6")
    assert get_cb_stage(dut) == 6, f"Stage is not 6, stage={get_cb_stage(dut)}"
    await log_control_signals(dut)
    await log_uio_out(dut)
    assert get_control_signal_array(dut) == LogicArray("000111111100011"), f"Control Signals are not correct, expected=000111111100011"
    await RisingEdge(dut.clk)
    dut._log.info(f"PC={get_pc(dut)}")
    assert get_pc(dut) == (int(pc_beginning)+1)%16, f"PC is not incremented, pc={get_pc(dut)}, pc_beginning={pc_beginning}"
    dut._log.info("NOP Checker Complete")

async def add_checker(dut, address):
    dut._log.info(f"ADD Checker Start")
    timeout = 0
    while not (get_cb_stage(dut) == 0):
        await RisingEdge(dut.clk)
        dut._log.info(f"Stage={get_cb_stage(dut)}")
        timeout += 1
        if (timeout > 2):
            assert False, (f"Timeout at {get_pc(dut)}")
    pc_beginning = get_pc(dut)
    val_a = get_regA_value(dut)
    val_b = get_ram(dut)[address]
    expVal, expCF, expZF = await check_adder_operation(0, val_a.integer, val_b.integer)
    dut._log.info(f"Adder Operation: {val_a.integer} + {val_b.integer} = {expVal}, CF={expCF}, ZF={expZF}")
    dut._log.info(f"Adder Operation bin: {val_a.integer:8b} + {val_b.integer:8b} = {expVal:8b}, CF={expCF}, ZF={expZF}")
    dut._log.info(f"Adder Operation hex: {val_a.integer:02X} + {val_b.integer:02X} = {expVal:02X}, CF={expCF}, ZF={expZF}")
    dut._log.info(f"PC={pc_beginning}")
    dut._log.info("T0")
    assert get_cb_stage(dut) == 0, f"Stage is not 0, stage={get_cb_stage(dut)}"
    await log_control_signals(dut)
    await log_uio_out(dut)
    assert get_control_signal_array(dut) == LogicArray("010011111100011"), f"Control Signals are not correct, expected=010011111100011"
    await RisingEdge(dut.clk)
    dut._log.info("T1")
    assert get_cb_stage(dut) == 1, f"Stage is not 1, stage={get_cb_stage(dut)}"
    await log_control_signals(dut)
    await log_uio_out(dut)
    assert get_control_signal_array(dut) == LogicArray("100111111100011"), f"Control Signals are not correct, expected=100111111100011"
    await RisingEdge(dut.clk)
    dut._log.info("T2")
    assert get_cb_stage(dut) == 2, f"Stage is not 2, stage={get_cb_stage(dut)}"
    await log_control_signals(dut)
    await log_uio_out(dut)
    assert get_control_signal_array(dut) == LogicArray("000110101100011"), f"Control Signals are not correct, expected=000110101100011"
    await RisingEdge(dut.clk)
    dut._log.info("T3")
    assert get_cb_stage(dut) == 3, f"Stage is not 3, stage={get_cb_stage(dut)}"
    await log_control_signals(dut)
    await log_uio_out(dut)
    assert get_control_signal_array(dut) == LogicArray("000011110100011"), f"Control Signals are not correct, expected=000011110100011"
    assert get_opcode(dut) == 2, f"Opcode is not ADD, opcode={get_opcode(dut)}"
    await RisingEdge(dut.clk)
    dut._log.info("T4")
    assert get_cb_stage(dut) == 4, f"Stage is not 4, stage={get_cb_stage(dut)}"
    await log_control_signals(dut)
    await log_uio_out(dut)
    assert get_control_signal_array(dut) == LogicArray("000110111100001"), f"Control Signals are not correct, expected=000110111100001"
    assert get_mar_addr(dut).integer == address, f"Address in MAR is not correct, mar_address={get_mar_addr(dut)}, expected={address}"
    await RisingEdge(dut.clk)
    dut._log.info("T5")
    assert get_cb_stage(dut) == 5, f"Stage is not 5, stage={get_cb_stage(dut)}"
    await log_control_signals(dut)
    await log_uio_out(dut)
    assert get_control_signal_array(dut) == LogicArray("000111111000111"), f"Control Signals are not correct, expected=000111111000111"
    assert get_regB_value(dut) == val_b, f"Value in B Register is not correct, b_register={get_regB_value(dut)}, expected={val_b}"
    await RisingEdge(dut.clk)
    dut._log.info("T6")
    assert get_cb_stage(dut) == 6, f"Stage is not 6, stage={get_cb_stage(dut)}"
    await log_control_signals(dut)
    await log_uio_out(dut)
    assert get_control_signal_array(dut) == LogicArray("000111111100011"), f"Control Signals are not correct, expected=000111111100011"
    assert retrieve_bit_from_8_wide_wire(dut.uio_out.value, uio_dict['CF']) == expCF, f"Carry Out in ALU is not correct, alu_carry_out={retrieve_bit_from_8_wide_wire(dut.uio_out.value, uio_dict['CF'])}, expected={expCF}"
    assert retrieve_bit_from_8_wide_wire(dut.uio_out.value, uio_dict['ZF']) == expZF, f"Zero Flag in ALU is not correct, alu_zero_flag={retrieve_bit_from_8_wide_wire(dut.uio_out.value, uio_dict['ZF'])}, expected={expZF}"
    assert get_regA_value(dut).integer == expVal, f"Value in Accumulator is not correct, accumulator={get_regA_value(dut)}, expected={expVal}"
    await RisingEdge(dut.clk)
    dut._log.info(f"PC={get_pc(dut)}")
    assert get_pc(dut) == (int(pc_beginning)+1)%16, f"PC is not incremented, pc={get_pc(dut)}, pc_beginning={pc_beginning}"
    dut._log.info("ADD Checker Complete")

async def sub_checker(dut, address):
    dut._log.info(f"SUB Checker Start")
    timeout = 0
    while not (get_cb_stage(dut) == 0):
        await RisingEdge(dut.clk)
        dut._log.info(f"Stage={get_cb_stage(dut)}")
        timeout += 1
        if (timeout > 2):
            assert False, (f"Timeout at {get_pc(dut)}")
    pc_beginning = get_pc(dut)
    val_a = get_regA_value(dut)
    val_b = get_ram(dut)[address]
    expVal, expCF, expZF = await check_adder_operation(1, val_a.integer, val_b.integer)
    dut._log.info(f"Adder Operation: {val_a.integer} - {val_b.integer} = {expVal}, CF={expCF}, ZF={expZF}")
    dut._log.info(f"Adder Operation bin: {val_a.integer:8b} - {val_b.integer:8b} = {expVal:8b}, CF={expCF}, ZF={expZF}")
    dut._log.info(f"Adder Operation hex: {val_a.integer:02X} - {val_b.integer:02X} = {expVal:02X}, CF={expCF}, ZF={expZF}")
    dut._log.info(f"PC={pc_beginning}")
    dut._log.info("T0")
    assert get_cb_stage(dut) == 0, f"Stage is not 0, stage={get_cb_stage(dut)}"
    await log_control_signals(dut)
    await log_uio_out(dut)
    assert get_control_signal_array(dut) == LogicArray("010011111100011"), f"Control Signals are not correct, expected=010011111100011"
    await RisingEdge(dut.clk)
    dut._log.info("T1")
    assert get_cb_stage(dut) == 1, f"Stage is not 1, stage={get_cb_stage(dut)}"
    await log_control_signals(dut)
    await log_uio_out(dut)
    assert get_control_signal_array(dut) == LogicArray("100111111100011"), f"Control Signals are not correct, expected=100111111100011"
    await RisingEdge(dut.clk)
    dut._log.info("T2")
    assert get_cb_stage(dut) == 2, f"Stage is not 2, stage={get_cb_stage(dut)}"
    await log_control_signals(dut)
    await log_uio_out(dut)
    assert get_control_signal_array(dut) == LogicArray("000110101100011"), f"Control Signals are not correct, expected=000110101100011"
    await RisingEdge(dut.clk)
    dut._log.info("T3")
    assert get_cb_stage(dut) == 3, f"Stage is not 3, stage={get_cb_stage(dut)}"
    await log_control_signals(dut)
    await log_uio_out(dut)
    assert get_control_signal_array(dut) == LogicArray("000011110100011"), f"Control Signals are not correct, expected=000011110100011"
    assert get_opcode(dut) == 3, f"Opcode is not SUB, opcode={get_opcode(dut)}"
    await RisingEdge(dut.clk)
    dut._log.info("T4")
    assert get_cb_stage(dut) == 4, f"Stage is not 4, stage={get_cb_stage(dut)}"
    await log_control_signals(dut)
    await log_uio_out(dut)
    assert get_control_signal_array(dut) == LogicArray("000110111100001"), f"Control Signals are not correct, expected=000110111100001"
    assert get_mar_addr(dut).integer == address, f"Address in MAR is not correct, mar_address={get_mar_addr(dut)}, expected={address}"
    await RisingEdge(dut.clk)
    dut._log.info("T5")
    assert get_cb_stage(dut) == 5, f"Stage is not 5, stage={get_cb_stage(dut)}"
    await log_control_signals(dut)
    await log_uio_out(dut)
    assert get_control_signal_array(dut) == LogicArray("000111111001111"), f"Control Signals are not correct, expected=000111111001111"
    assert get_regB_value(dut) == val_b, f"Value in B Register is not correct, b_register={get_regB_value(dut)}, expected={val_b}"
    await RisingEdge(dut.clk)
    dut._log.info("T6")
    assert get_cb_stage(dut) == 6, f"Stage is not 6, stage={get_cb_stage(dut)}"
    await log_control_signals(dut)
    await log_uio_out(dut)
    assert get_control_signal_array(dut) == LogicArray("000111111100011"), f"Control Signals are not correct, expected=000111111100011"
    assert retrieve_bit_from_8_wide_wire(dut.uio_out.value, uio_dict['CF']) == expCF, f"Carry Out in ALU is not correct, alu_carry_out={retrieve_bit_from_8_wide_wire(dut.uio_out.value, uio_dict['CF'])}, expected={expCF}"
    assert retrieve_bit_from_8_wide_wire(dut.uio_out.value, uio_dict['ZF']) == expZF, f"Zero Flag in ALU is not correct, alu_zero_flag={retrieve_bit_from_8_wide_wire(dut.uio_out.value, uio_dict['ZF'])}, expected={expZF}"
    assert get_regA_value(dut).integer == expVal, f"Value in Accumulator is not correct, accumulator={get_regA_value(dut)}, expected={expVal}"
    await RisingEdge(dut.clk)
    dut._log.info(f"PC={get_pc(dut)}")
    assert get_pc(dut) == (int(pc_beginning)+1)%16, f"PC is not incremented, pc={get_pc(dut)}, pc_beginning={pc_beginning}"
    dut._log.info("SUB Checker Complete")

async def lda_checker(dut, address):
    dut._log.info(f"LDA Checker Start")
    timeout = 0
    while not (get_cb_stage(dut) == 0):
        await RisingEdge(dut.clk)
        dut._log.info(f"Stage={get_cb_stage(dut)}")
        timeout += 1
        if (timeout > 2):
            assert False, (f"Timeout at {get_pc(dut)}")
    new_val_a = get_ram(dut)[address]
    pc_beginning = get_pc(dut)
    dut._log.info(f"PC={pc_beginning}")
    dut._log.info("T0")
    assert get_cb_stage(dut) == 0, f"Stage is not 0, stage={get_cb_stage(dut)}"
    await log_control_signals(dut)
    await log_uio_out(dut)
    assert get_control_signal_array(dut) == LogicArray("010011111100011"), f"Control Signals are not correct, expected=010011111100011"
    await RisingEdge(dut.clk)
    dut._log.info("T1")
    assert get_cb_stage(dut) == 1, f"Stage is not 1, stage={get_cb_stage(dut)}"
    await log_control_signals(dut)
    await log_uio_out(dut)
    assert get_control_signal_array(dut) == LogicArray("100111111100011"), f"Control Signals are not correct, expected=100111111100011"
    await RisingEdge(dut.clk)
    dut._log.info("T2")
    assert get_cb_stage(dut) == 2, f"Stage is not 2, stage={get_cb_stage(dut)}"
    await log_control_signals(dut)
    await log_uio_out(dut)
    assert get_control_signal_array(dut) == LogicArray("000110101100011"), f"Control Signals are not correct, expected=000110101100011"
    await RisingEdge(dut.clk)
    dut._log.info("T3")
    assert get_cb_stage(dut) == 3, f"Stage is not 3, stage={get_cb_stage(dut)}"
    await log_control_signals(dut)
    await log_uio_out(dut)
    assert get_control_signal_array(dut) == LogicArray("000011110100011"), f"Control Signals are not correct, expected=000011110100011"
    assert get_opcode(dut) == 4, f"Opcode is not LDA, opcode={get_opcode(dut)}"
    await RisingEdge(dut.clk)
    dut._log.info("T4")
    assert get_cb_stage(dut) == 4, f"Stage is not 4, stage={get_cb_stage(dut)}"
    await log_control_signals(dut)
    await log_uio_out(dut)
    assert get_control_signal_array(dut) == LogicArray("000110111000011"), f"Control Signals are not correct, expected=000110111000011"
    assert get_mar_addr(dut).integer == address, f"Address in MAR is not correct, mar_address={get_mar_addr(dut)}, expected={address}"
    await RisingEdge(dut.clk)
    dut._log.info("T5")
    assert get_cb_stage(dut) == 5, f"Stage is not 5, stage={get_cb_stage(dut)}"
    await log_control_signals(dut)
    await log_uio_out(dut)
    assert get_control_signal_array(dut) == LogicArray("000111111100011"), f"Control Signals are not correct, expected=000111111100011"
    assert get_regA_value(dut) == new_val_a, f"Value in Accumulator is not correct, accumulator={get_regA_value(dut)}, expected={new_val_a}"
    await RisingEdge(dut.clk)
    dut._log.info("T6")
    assert get_cb_stage(dut) == 6, f"Stage is not 6, stage={get_cb_stage(dut)}"
    await log_control_signals(dut)
    await log_uio_out(dut)
    assert get_control_signal_array(dut) == LogicArray("000111111100011"), f"Control Signals are not correct, expected=000111111100011"
    assert get_regA_value(dut) == new_val_a, f"Value in Accumulator is not correct, accumulator={get_regA_value(dut)}, expected={new_val_a}"
    await RisingEdge(dut.clk)
    dut._log.info(f"PC={get_pc(dut)}")
    assert get_pc(dut) == (int(pc_beginning)+1)%16, f"PC is not incremented, pc={get_pc(dut)}, pc_beginning={pc_beginning}"
    dut._log.info("LDA Checker Complete")

async def out_checker(dut):
    dut._log.info(f"OUT Checker Start")
    timeout = 0
    while not (get_cb_stage(dut) == 0):
        await RisingEdge(dut.clk)
        dut._log.info(f"Stage={get_cb_stage(dut)}")
        timeout += 1
        if (timeout > 2):
            assert False, (f"Timeout at {get_pc(dut)}")
    pc_beginning = get_pc(dut)
    val_a = get_regA_value(dut)
    dut._log.info(f"PC={pc_beginning}")
    dut._log.info("T0")
    assert get_cb_stage(dut) == 0, f"Stage is not 0, stage={get_cb_stage(dut)}"
    await log_control_signals(dut)
    await log_uio_out(dut)
    assert get_control_signal_array(dut) == LogicArray("010011111100011"), f"Control Signals are not correct, expected=010011111100011"
    await RisingEdge(dut.clk)
    dut._log.info("T1")
    assert get_cb_stage(dut) == 1, f"Stage is not 1, stage={get_cb_stage(dut)}"
    await log_control_signals(dut)
    await log_uio_out(dut)
    assert get_control_signal_array(dut) == LogicArray("100111111100011"), f"Control Signals are not correct, expected=100111111100011"
    await RisingEdge(dut.clk)
    dut._log.info("T2")
    assert get_cb_stage(dut) == 2, f"Stage is not 2, stage={get_cb_stage(dut)}"
    await log_control_signals(dut)
    await log_uio_out(dut)
    assert get_control_signal_array(dut) == LogicArray("000110101100011"), f"Control Signals are not correct, expected=000110101100011"
    await RisingEdge(dut.clk)
    dut._log.info("T3")
    assert get_cb_stage(dut) == 3, f"Stage is not 3, stage={get_cb_stage(dut)}"
    await log_control_signals(dut)
    await log_uio_out(dut)
    assert get_control_signal_array(dut) == LogicArray("000111111110010"), f"Control Signals are not correct, expected=000111111110010"
    assert get_opcode(dut) == 5, f"Opcode is not OUT, opcode={get_opcode(dut)}"
    await RisingEdge(dut.clk)
    dut._log.info("T4")
    assert get_cb_stage(dut) == 4, f"Stage is not 4, stage={get_cb_stage(dut)}"
    await log_control_signals(dut)
    await log_uio_out(dut)
    assert get_control_signal_array(dut) == LogicArray("000111111100011"), f"Control Signals are not correct, expected=000111111100011"
    assert dut.uo_out.value == val_a, f"Value in Output Register is not correct, output_register={dut.uo_out.value}, expected={val_a}"
    await RisingEdge(dut.clk)
    dut._log.info("T5")
    assert get_cb_stage(dut) == 5, f"Stage is not 5, stage={get_cb_stage(dut)}"
    await log_control_signals(dut)
    await log_uio_out(dut)
    assert get_control_signal_array(dut) == LogicArray("000111111100011"), f"Control Signals are not correct, expected=000111111100011"
    await RisingEdge(dut.clk)
    dut._log.info("T6")
    assert get_cb_stage(dut) == 6, f"Stage is not 6, stage={get_cb_stage(dut)}"
    await log_control_signals(dut)
    await log_uio_out(dut)
    assert get_control_signal_array(dut) == LogicArray("000111111100011"), f"Control Signals are not correct, expected=000111111100011"
    assert dut.uo_out.value == val_a, f"Value in UO_OUT is not correct, uo_out={dut.uo_out.value}, expected={val_a}"
    await RisingEdge(dut.clk)
    dut._log.info(f"PC={get_pc(dut)}")
    assert get_pc(dut) == (int(pc_beginning)+1)%16, f"PC is not incremented, pc={get_pc(dut)}, pc_beginning={pc_beginning}"
    dut._log.info("OUT Checker Complete")

async def sta_checker(dut, address):
    dut._log.info(f"STA Checker Start")
    timeout = 0
    while not (get_cb_stage(dut) == 0):
        await RisingEdge(dut.clk)
        dut._log.info(f"Stage={get_cb_stage(dut)}")
        timeout += 1
        if (timeout > 2):
            assert False, (f"Timeout at {get_pc(dut)}")
    pc_beginning = get_pc(dut)
    val_a = get_regA_value(dut)
    dut._log.info(f"PC={pc_beginning}")
    dut._log.info("T0")
    assert get_cb_stage(dut) == 0, f"Stage is not 0, stage={get_cb_stage(dut)}"
    await log_control_signals(dut)
    await log_uio_out(dut)
    assert get_control_signal_array(dut) == LogicArray("010011111100011"), f"Control Signals are not correct, expected=010011111100011"
    await RisingEdge(dut.clk)
    dut._log.info("T1")
    assert get_cb_stage(dut) == 1, f"Stage is not 1, stage={get_cb_stage(dut)}"
    await log_control_signals(dut)
    await log_uio_out(dut)
    assert get_control_signal_array(dut) == LogicArray("100111111100011"), f"Control Signals are not correct, expected=100111111100011"
    await RisingEdge(dut.clk)
    dut._log.info("T2")
    assert get_cb_stage(dut) == 2, f"Stage is not 2, stage={get_cb_stage(dut)}"
    await log_control_signals(dut)
    await log_uio_out(dut)
    assert get_control_signal_array(dut) == LogicArray("000110101100011"), f"Control Signals are not correct, expected=000110101100011"
    await RisingEdge(dut.clk)
    dut._log.info("T3")
    assert get_cb_stage(dut) == 3, f"Stage is not 3, stage={get_cb_stage(dut)}"
    await log_control_signals(dut)
    await log_uio_out(dut)
    assert get_control_signal_array(dut) == LogicArray("000011110100011"), f"Control Signals are not correct, expected=000011110100011"
    assert get_opcode(dut) == 6, f"Opcode is not STA, opcode={get_opcode(dut)}"
    await RisingEdge(dut.clk)
    dut._log.info("T4")
    assert get_cb_stage(dut) == 4, f"Stage is not 4, stage={get_cb_stage(dut)}"
    await log_control_signals(dut)
    await log_uio_out(dut)
    assert get_control_signal_array(dut) == LogicArray("000101111110011"), f"Control Signals are not correct, expected=000101111110011"
    assert get_mar_addr(dut).integer == address, f"Address in MAR is not correct, mar_address={get_mar_addr(dut)}, expected={address}"
    await RisingEdge(dut.clk)
    dut._log.info("T5")
    assert get_cb_stage(dut) == 5, f"Stage is not 5, stage={get_cb_stage(dut)}"
    await log_control_signals(dut)
    await log_uio_out(dut)
    assert get_control_signal_array(dut) == LogicArray("000111011100011"), f"Control Signals are not correct, expected=000111011100011"
    assert get_mar_data(dut) == val_a, f"Value in MAR is not correct, mar_data={get_mar_data(dut)}, expected={val_a}"
    await RisingEdge(dut.clk)
    dut._log.info("T6")
    assert get_cb_stage(dut) == 6, f"Stage is not 6, stage={get_cb_stage(dut)}"
    await log_control_signals(dut)
    await log_uio_out(dut)
    assert get_control_signal_array(dut) == LogicArray("000111111100011"), f"Control Signals are not correct, expected=000111111100011"
    assert get_ram(dut)[address] == val_a, f"Value in RAM is not correct, ram={get_ram(dut)[address]}, expected={val_a}"
    await RisingEdge(dut.clk)
    dut._log.info(f"PC={get_pc(dut)}")
    assert get_pc(dut) == (int(pc_beginning)+1)%16, f"PC is not incremented, pc={get_pc(dut)}, pc_beginning={pc_beginning}"
    dut._log.info("STA Checker Complete")

async def jmp_checker(dut, address):
    dut._log.info(f"JMP Checker Start with jmp_address={address}, hex={address:01X}, bin={address:4b}")
    timeout = 0
    while not (get_cb_stage(dut) == 0):
        await RisingEdge(dut.clk)
        dut._log.info(f"Stage={get_cb_stage(dut)}")
        timeout += 1
        if (timeout > 2):
            assert False, (f"Timeout at {get_pc(dut)}")
    pc_beginning = get_pc(dut)
    dut._log.info(f"PC={pc_beginning}")
    dut._log.info("T0")
    assert get_cb_stage(dut) == 0, f"Stage is not 0, stage={get_cb_stage(dut)}"
    await log_control_signals(dut)
    await log_uio_out(dut)
    assert get_control_signal_array(dut) == LogicArray("010011111100011"), f"Control Signals are not correct, expected=010011111100011"
    await RisingEdge(dut.clk)
    dut._log.info("T1")
    assert get_cb_stage(dut) == 1, f"Stage is not 1, stage={get_cb_stage(dut)}"
    await log_control_signals(dut)
    await log_uio_out(dut)
    assert get_control_signal_array(dut) == LogicArray("100111111100011"), f"Control Signals are not correct, expected=100111111100011"
    await RisingEdge(dut.clk)
    dut._log.info("T2")
    assert get_cb_stage(dut) == 2, f"Stage is not 2, stage={get_cb_stage(dut)}"
    await log_control_signals(dut)
    await log_uio_out(dut)
    assert get_control_signal_array(dut) == LogicArray("000110101100011"), f"Control Signals are not correct, expected=000110101100011"
    await RisingEdge(dut.clk)
    dut._log.info("T3")
    assert get_cb_stage(dut) == 3, f"Stage is not 3, stage={get_cb_stage(dut)}"
    await log_control_signals(dut)
    await log_uio_out(dut)
    assert get_control_signal_array(dut) == LogicArray("001111110100011"), f"Control Signals are not correct, expected=001111110100011"
    assert get_opcode(dut) == 7, f"Opcode is not JMP, opcode={get_opcode(dut)}"
    await RisingEdge(dut.clk)
    dut._log.info("T4")
    assert get_cb_stage(dut) == 4, f"Stage is not 4, stage={get_cb_stage(dut)}"
    await log_control_signals(dut)
    await log_uio_out(dut)
    assert get_control_signal_array(dut) == LogicArray("000111111100011"), f"Control Signals are not correct, expected=000111111100011"
    await RisingEdge(dut.clk)
    dut._log.info("T5")
    assert get_cb_stage(dut) == 5, f"Stage is not 5, stage={get_cb_stage(dut)}"
    await log_control_signals(dut)
    await log_uio_out(dut)
    assert get_control_signal_array(dut) == LogicArray("000111111100011"), f"Control Signals are not correct, expected=000111111100011"
    await RisingEdge(dut.clk)
    dut._log.info("T6")
    assert get_cb_stage(dut) == 6, f"Stage is not 6, stage={get_cb_stage(dut)}"
    await log_control_signals(dut)
    await log_uio_out(dut)
    assert get_control_signal_array(dut) == LogicArray("000111111100011"), f"Control Signals are not correct, expected=000111111100011"
    await RisingEdge(dut.clk)
    dut._log.info(f"PC={get_pc(dut)}")
    assert get_pc(dut) == address, f"PC is not address, pc={get_pc(dut)}, jmp_address={address}"
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
    await jmp_checker(dut, program_data[0]&0xF)
    await hlt_checker(dut)
    dut._log.info("Operation JMP Test Complete")

@cocotb.test()
async def test_operation_nop(dut):
    program_data = [0x1E, 0x1F, 0x70, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0x0F, 0x0F]
    dut._log.info(f"Operation NOP Test Start")
    dut._log.info(f"data_bin={[str(bin(x)) for x in program_data]}")
    dut._log.info(f"data_hex={[str(hex(x)) for x in program_data]}")
    await init(dut)
    await load_ram(dut, program_data)
    await dumpRAM(dut)
    await mem_check(dut, program_data)
    await nop_checker(dut)
    await nop_checker(dut)
    await jmp_checker(dut, program_data[2]&0xF)
    await nop_checker(dut)
    dut._log.info("Operation NOP Test Complete")

@cocotb.test()
async def test_operation_add(dut):
    program_data = [0x2E, 0x10, 0x70, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0x09, 0xFF]
    dut._log.info(f"Operation ADD Test Start")
    dut._log.info(f"data_bin={[str(bin(x)) for x in program_data]}")
    dut._log.info(f"data_hex={[str(hex(x)) for x in program_data]}")
    await init(dut)
    await load_ram(dut, program_data)
    await dumpRAM(dut)
    await mem_check(dut, program_data)
    await add_checker(dut, program_data[0]&0xF)
    await nop_checker(dut)
    await jmp_checker(dut, program_data[2]&0xF)
    await add_checker(dut, program_data[0]&0xF)
    dut._log.info("Operation ADD Test Complete")

@cocotb.test()
async def test_operation_add_2(dut):
    program_data = [0x2E, 0x10, 0x70, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xA9, 0xFF]
    dut._log.info(f"Operation ADD 2 Test Start")
    dut._log.info(f"data_bin={[str(bin(x)) for x in program_data]}")
    dut._log.info(f"data_hex={[str(hex(x)) for x in program_data]}")
    await init(dut)
    await load_ram(dut, program_data)
    await dumpRAM(dut)
    await mem_check(dut, program_data)
    await add_checker(dut, program_data[0]&0xF)
    await nop_checker(dut)
    await jmp_checker(dut, program_data[2]&0xF)
    await add_checker(dut, program_data[0]&0xF)
    dut._log.info("Operation ADD 2 Test Complete")


@cocotb.test()
async def test_operation_sub(dut):
    program_data = [0x3E, 0x10, 0x70, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0x09, 0xFF]
    dut._log.info(f"Operation SUB Test Start")
    dut._log.info(f"data_bin={[str(bin(x)) for x in program_data]}")
    dut._log.info(f"data_hex={[str(hex(x)) for x in program_data]}")
    await init(dut)
    await load_ram(dut, program_data)
    await dumpRAM(dut)
    await mem_check(dut, program_data)
    await sub_checker(dut, program_data[0]&0xF)
    await nop_checker(dut)
    await jmp_checker(dut, program_data[2]&0xF)
    await sub_checker(dut, program_data[0]&0xF)
    dut._log.info("Operation SUB Test Complete")

@cocotb.test()
async def test_operation_sub_add(dut):
    program_data = [0x3E, 0x10, 0x2E, 0x00, 0x00, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0x09, 0xFF]
    dut._log.info(f"Operation SUB ADD Test Start")
    dut._log.info(f"data_bin={[str(bin(x)) for x in program_data]}")
    dut._log.info(f"data_hex={[str(hex(x)) for x in program_data]}")
    await init(dut)
    await load_ram(dut, program_data)
    await dumpRAM(dut)
    await mem_check(dut, program_data)
    await sub_checker(dut, program_data[0]&0xF)
    await nop_checker(dut)
    await add_checker(dut, program_data[0]&0xF)
    await hlt_checker(dut)
    dut._log.info("Operation SUB ADD Test Complete")

@cocotb.test()
async def test_operation_lda(dut):
    program_data = [0x4E, 0x2F, 0x1F, 0x00, 0x00, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0x09, 0xFF]
    dut._log.info(f"Operation LDA Test Start")
    dut._log.info(f"data_bin={[str(bin(x)) for x in program_data]}")
    dut._log.info(f"data_hex={[str(hex(x)) for x in program_data]}")
    await init(dut)
    await load_ram(dut, program_data)
    await dumpRAM(dut)
    await mem_check(dut, program_data)
    await lda_checker(dut, program_data[0]&0xF)
    await add_checker(dut, program_data[1]&0xF)
    await nop_checker(dut)
    await hlt_checker(dut)
    dut._log.info("Operation LDA Test Complete")

@cocotb.test()
async def test_operation_out(dut):
    program_data = [0x4E, 0x2F, 0x5F, 0x00, 0x00, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0x09, 0xFF]
    dut._log.info(f"Operation OUT Test Start")
    dut._log.info(f"data_bin={[str(bin(x)) for x in program_data]}")
    dut._log.info(f"data_hex={[str(hex(x)) for x in program_data]}")
    await init(dut)
    await load_ram(dut, program_data)
    await dumpRAM(dut)
    await mem_check(dut, program_data)
    await lda_checker(dut, program_data[0]&0xF)
    await add_checker(dut, program_data[1]&0xF)
    await out_checker(dut)
    await hlt_checker(dut)
    dut._log.info("Operation OUT Test Complete")

@cocotb.test()
async def test_operation_sta(dut):
    program_data = [0x4E, 0x2F, 0x5F, 0x60, 0x00, 0x00, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0x09, 0xFF]
    dut._log.info(f"Operation STA Test Start")
    dut._log.info(f"data_bin={[str(bin(x)) for x in program_data]}")
    dut._log.info(f"data_hex={[str(hex(x)) for x in program_data]}")
    await init(dut)
    await load_ram(dut, program_data)
    await dumpRAM(dut)
    await mem_check(dut, program_data)
    await lda_checker(dut, program_data[0]&0xF)
    await add_checker(dut, program_data[1]&0xF)
    await out_checker(dut)
    await sta_checker(dut, program_data[3]&0xF)
    await hlt_checker(dut)
    await dumpRAM(dut)
    dut._log.info("Operation STA Test Complete")

def get_ram(dut):
    ram = [LogicArray] * 16
    if (LocalTest):
        ram = dut.user_project.ram.RAM.value
    else:
        if (GLTEST):
            for i in range(16):
                result = 0
                for j in range(8):
                    result |= (dut.user_project._id(f"\\ram.RAM[{i}][{j}]", extended = False).value << j)
                ram[i] = to_8_bit_array(result)
        else: 
            for i in range(16):
                ram[15 - i] = dut.user_project.ram.RAM.value[i]

    return ram


@cocotb.test()
async def memory_load_and_verify_outputs(dut):
    # Define the program data (as per the layout specified above)
    program_data = [
        0x10,  # NOP
        0x73,  # JMP 0x3
        0x00,  # HLT
        0x4F,  # LDA 0xF
        0x2E,  # ADD 0xE
        0x6D,  # STA 0xD
        0x50,  # OUT
        0x3F,  # SUB 0xF
        0x50,  # OUT
        0x4D,  # LDA 0xD
        0x50,  # OUT
        0x72,  # JMP 0x2
        0x10,  # NOP
        0x00,  # Padding/empty instruction
        0x02,  # Constant 2 (data)
        0x01   # Constant 1 (data)
    ]
    dut._log.info(f"Comprehensive Test Start")
    dut._log.info(f"data_bin={[str(bin(x)) for x in program_data]}")
    dut._log.info(f"data_hex={[str(hex(x)) for x in program_data]}")
    
    # Initialize and load the program data into RAM
    await init(dut)
    await load_ram(dut, program_data)
    await dumpRAM(dut)
    await mem_check(dut, program_data)

    await nop_checker(dut)
    await jmp_checker(dut, 0x3)
    await lda_checker(dut, 0xF)
    await add_checker(dut, 0xE)
    await sta_checker(dut, 0xD)
    await out_checker(dut)
    await sub_checker(dut, 0xF)
    await out_checker(dut)
    await lda_checker(dut, 0xD)
    await out_checker(dut)
    await jmp_checker(dut, 0x2)
    await dumpRAM(dut)
    dut._log.info("Comprehensive Test Complete")
