<!---

This file is used to generate your project datasheet. Please fill in the information below and delete any unused
sections.

You can also include images in this folder and reference them in the markdown. Each image must be less than
512 kb in size, and the combined size of all images must be less than 1 MB.
-->

## How it works

This project is a basic 8-bit CPU design building off the SAP-1. It is a combination of various modules developed as a part of the ECE298A Course at the University of Waterloo.

The control block is implemented using a 6 stage sequential counter for sequencing micro-instructions, and a LUT for corresponding op-code to operation(s).

The counter enumerates all values between 0 and F (15) before looping back to 0 and starting again. The counter will clear back to 0 whenever the chip is reset.

The 8-bit ripple carry adder assumes 2s complement inputs and thus supports addition and subtraction. It pushes the result to the bus via tri-state buffer. It also includes a zero flag and a carry flag to support conditional operation using an external microcontroller. These flags are synchronized to the rising edge of the clock and are updated when the adder outputs to the bus.

The accumulator register functions to store the output of the adder. It is synchronized to the positive edge of the clock. The accumulator loads and outputs its value from the bus and is connected via tri-state buffer. The accumulator’s current value is always available as an ouput (and usually connected to the Register A input of the ALU)

## Supported Instructions

| **Mnemonic**  | **Opcode** | **Function**                                             |
| ------------- | ---------- | -------------------------------------------------------- |
| HLT           | 0x0        | Stop processing                                          |
| NOP           | 0x1        | No operation                                             |
| ADD {address} | 0x2        | Add B register to A register, leaving result in A        |
| SUB {address} | 0x3        | Subtract B register from A register, leaving result in A |
| LDA {address} | 0x4        | Put RAM data at {address} into A register                |
| OUT           | 0x5        | Put A register data into Output register and display     |
| STA {address} | 0x6        | Store A register data in RAM at {address}                |
| JMP {address} | 0x7        | Change PC to {address}                                   |

### Instruction Notes

- All instructions consist of an opcode (most significant 4 bits), and an address (least significant 4 bits, where applicable)

## Control Signal Descriptions

| **Control Signal** | **Component**    | **Function**                                        |
| ------------------ | ---------------- | --------------------------------------------------- |
| CP                 | PC               | Increments the PC by 1                              |
| EP                 | PC               | Enable signal for PC to drive the bus               |
| LP                 | PC               | Tells PC to load value from the bus                 |
| nLma               | MAR              | Tells MAR when to load address from the bus         |
| nLmd               | MAR              | Tells MAR when to load memory from the bus          |
| nCE                | RAM              | Enable signal for RAM to drive the bus              |
| nLr                | RAM              | Tells RAM when to load memory from the MAR          |
| nLi                | Instruction Reg  | Tells IR when to load instruction from the bus      |
| nEi                | Instruction Reg  | Enable signal for IR to drive the bus               |
| nLa                | A Reg            | Tells A register to load data from the bus          |
| Ea                 | A Reg            | Enable signal for A register to drive the bus       |
| Su                 | Adder/Subtractor | Activate subtractor instead of adder                |
| Eu                 | B Reg / Adder    | Enable signal for Adder/Subtractor to drive the bus |
| nLb                | B Reg            | Tells B register to load data from the bus          |
| nLo                | Output Reg       | Tells Output register to load data from the bus     |

## Sequencing Details

- The control sequencer is negative edge triggered, so that control signals can be steady for the next positive clock edge, where the actions are executed.
- In each clock cycle, there can only be one source of data for the bus, however any number components can read from the bus.
- Before each run, a CLR signal is sent to the PC and the IR.

## Instruction Micro-Operations

| Stage  | **HLT**  | **NOP**  | **STA**   | **JMP**  |
| ------ | -------- | -------- | --------- | -------- |
| **T0** | Ep, nLma | Ep, nLma | Ep, nLma  | Ep, nLma |
| **T1** | Cp       | Cp       | Cp        | Cp       |
| **T2** | nCE, nLi | nCE, nLi | nCE, nLi  | nCE, nLi |
| **T3** | \*\*     | \-       | nEi, nLma | nEi, Lp  |
| **T4** | \-       | \-       | Ea, nLmd  |          |
| **T5** | \-       | \-       | nLr       |          |

| Stage  | **LDA**   | **ADD**   | **SUB**     | **OUT**  |
| ------ | --------- | --------- | ----------- | -------- |
| **T0** | Ep, nLma  | Ep, nLma  | Ep, nLma    | Ep, nLma |
| **T1** | Cp        | Cp        | Cp          | Cp       |
| **T2** | nCE, nLi  | nCE, nLi  | nCE, nLi    | nCE, nLi |
| **T3** | nEi, nLma | nEi, nLma | nEi, nLma   | Ea, nLo  |
| **T4** | nCE, nLa  | nCE, nLb  | nCE, nLb    | \-       |
| **T5** | \-        | Eu, nLa   | Su, Eu, nLa | \-       |

### Instruction Micro-Operations Notes

- First three micro-operations are common to all instructions.  
- NOP operation executes only the first three micro-operations.  
- Cp signal is not asserted during the HLT instruction in T2.
- \*\* Halt internal register is set to 1. More on this later

## Programmer

|  Stage | **Control Signals** | **Programmer specific signals** |
| ------ | ------------------- | ------------------------------- |
| **T0** | Ep, nLMA            | ready \= 1                      |
| **T1** | Cp                  | ready \= 0                      |
| **T2** | \-                  | \-                              |
| **T3** | nLmd                | read_ui_in  \= 1                |
| **T4** | nLr                 | nread_ui_in = 0, done_load \= 1 |
| **T5** | \-                  | ndone_load \= 0                 |

### Detailed Overview

T0: Control Signals the same as the typical default microinstruction – load the MAR with the address of the next instruction. Assert ready signal to alert MCU programmer (off chip) that CPU is ready to accept next line of RAM data.

T1: Increment the PC, the same as the typical default microinstruction. De-assert ready signal since the MCU programmer is polling for the rising edge.

T2: Do nothing to allow an entire clock cycle for programmer to prepare the data.

T3: Load the MAR with the data from the bus. Also, assert the read_ui_in signal which controls a series of tri-state buffers, attaches the ui_in pins straight to the bus.

T4: Load the RAM from the MAR. De-assert the read_ui_in signal (disconnect the ui_in pins from driving the bus since the ui_in pin data might be now inaccurate). Assert the done_load signal to indicate to the MCU that the chip is done with the ui_in data.

T5: De-assert done_load signal.

### Programmer Notes

The MCU must be able to provide the data to the ui_in pins (steady) between receiving the ready signal (assume worst case end of T0), and the bus needing the values (assume worst case beginning of T3).

Therefore, the MCU must be able to provide the data at a maximum of 2 clock periods.

## IO Table: PC (Program Counter)

| **Name** | **Verilog** | **Description**         | **I/O** | **Width (bits)** | **Trigger**  |
| -------- | ----------- | ----------------------- | ------- | ---------------- | ------------ |
| bus      | bus         | Connection to bus       | IO      | 4                | NA           |
| clk      | clk         | Clock signal            | I       | 1                | Falling Edge |
| clr_n    | rst_n       | Clear to 0              | I       | 1                | Active Low   |
| cp       | Ep          | Allow counter increment | I       | 1                | Active High  |
| ep       | Cp          | Output to Bus           | I       | 1                | Active High  |
| lp       | Lp          | Load from bus           | I       | 1                | Active High  |

### PC (Program Counter) Notes

- Counter increments only when Cp is asserted, otherwise it will stay at the current value.
- Ep controls whether the counter is being output to the bus. If this signal is low, our output is high impedance (Tri-State Buffers).
- When CLR is low, the counter is cleared back to 0, the program will restart.
- The program counter updates its value on the falling edge of the clock.
- Lp indicates that we want to load the value on the bus into the counter (used for jump instructions). When this is asserted, we will read from the bus and instead of incrementing the counter, we will update each flip-flop with the appropriate bit and prepare to output.
- The least significant 4 bits from the 8-bit bus will be used to store the value on the program counter (0-15). Will be read from (JMP asserted) and written to (Ep asserted).
- clr_n has precedence over all.
- Lp takes precedence over Cp.

## IO Table: Accumulator (A) Register

| **Name**      | **Verilog**      | **Description**      | **I/O**          | **Width (bits)** | **Trigger**      |
| ------------- | ---------------- | -------------------- | ---------------- | ---------------- | ---------------- |
| clk           | clk              | Clock Signal         | Input            | 1                | Rising edge      |
| bus           | bus              | Connection to bus    | IO               | 8                | NA               |
| load          | nLa              | Load from Bus        | Input            | 1                | Active Low       |
| enable_out    | Ea               | Output to Bus        | Input            | 1                | Active High      |
| Register A    | regA             | Accumulator Register | Output           | 8                | NA               |
| clear         | rst_n            | Clear Signal         | Input            | 1                | Active Low       |

### Accumulator (A) Register Notes

- The A Register updates its value on the rising edge of the clock.
- Ea controls whether the counter is being output to the bus. If this signal is low, our output is high impedance (Tri-State Buffers).
- nLa indicates that we want to load the value on the bus into the counter (used for jump instructions). When this is low, we will read from the bus and write to the register.
- When CLR is low, the register is cleared back to 0.
- (Register A) always outputs the current value of the register.

## IO Table: ALU (Adder/Subtractor)

| **Name**      | **Verilog**      | **Description**      | **I/O**          | **Width (bits)** | **Trigger**      |
| ------------- | ---------------- | -------------------- | ---------------- | ---------------- | ---------------- |
| clk           | clk              | Clock Signal         | Input            | 1                | Rising edge      |
| enable_out    | Eu               | Output to Bus        | Input            | 1                | Active High      |
| Register A    | reg_a            | Accumulator Register | Input            | 8                | NA               |
| Register B    | reg_b            | Register B           | Input            | 8                | NA               |
| subtract      | sub              | Perform Subtraction  | Input            | 1                | Active High      |
| bus           | bus              | Connection to bus    | Output           | 8                | NA               |
| Carry Out     | CF               | Carry-out flag       | Output           | 1                | Active High      |
| Result Zero   | ZF               | Zero flag            | Output           | 1                | Active High      |

### ALU (Adder/Subtractor) Notes

- Eu controls whether the counter is being output to the bus. If this signal is low, our output is high impedance (Tri-State Buffers).
- A Register and B Register always provide the ALU with their current values.
- When sub is not asserted, the ALU will perform addition: Result = A + B
- When sub is asserted, the ALU will perform subtraction by taking 2s complement of operand B: Result = A - B = A + !B + 1
- Carry Out and Result Zero flags are updated on rising clock edge

## How to test

Provide input of op-code. Check that the correct output bits are being asserted/deasserted properly.
