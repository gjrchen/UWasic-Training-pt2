/*
 * SPDX-License-Identifier: Apache-2.0
 */

`default_nettype none

//`include "control_block.v"
//`include "program_counter.v"

module tt_um_ece298a_8_bit_cpu_top (
    input  wire [7:0] ui_in,    // Dedicated inputs 
    output wire [7:0] uo_out,   // Dedicated outputs 
    output wire [7:0] uio_out,  // IOs: Output path
    input  wire [7:0] uio_in,   // IOs: Input path - not used
    output wire [7:0] uio_oe,   // IOs: Enable path 
    
    input wire clk,
    input  wire ena,            // always 1 when the design is powered, so you can ignore it
    input  wire rst_n           // reset_n - low to reset
);

    // Bus //
    wire [7:0] bus;                 // Bus (8-bit) (High impedance when not in use)
    wire [3:0] bus4bit;             // 4-bit Bus (lower 4 bits of the 8-bit Bus) (High impedance when not in use)
    assign bus4bit = bus[3:0];      // Assign 4-bit Bus to the lower 4 bits of the 8-bit Bus 

    // Control Signals //
    wire [14:0] control_signals;

    // Registers //
    wire [7:0] regA;                // Accumulator Register
    wire [7:0] regB;                // B Register
    // ALU Flags //
    wire CF;                        // Carry Flag
    wire ZF;                        // Zero Flag


    // Control Signals for the Program Counter //
    alias Cp = control_signals[14];     // 
    alias Ep = control_signals[13];     // 
    alias Lp = control_signals[12];     // 

    // Control Signals for the RAM //
    alias nLma = control_signals[11];   // 
    alias nLmd = control_signals[10];   // 
    alias nCE = control_signals[9];     // 
    alias nLr = control_signals[8];     // 

    // Control Signals for the Instruction Register //
    alias nLi = control_signals[7];     // enable Instruction Register load from bus (ACTIVE-LOW)
    alias Ei = control_signals[6];      // enable Instruction Register output to the bus (ACTIVE-HIGH)

    // Control Signals for the Accumulator Register //
    alias nLa = control_signals[5];     // enable Accumulator Register load from bus (ACTIVE-LOW)
    alias Ea = control_signals[4];      // enable Accumulator Register output to the bus (ACTIVE-HIGH)

    // Control Signals for the ALU //
    alias sub = control_signals[3];     // perform addition when 0, perform subtraction when 1
    alias Eu = control_signals[2];      // enable ALU output to the bus (ACTIVE-HIGH)

    // Control Signals for the B Register //
    alias nLb = control_signals[1];     // enable B Register load from bus (ACTIVE-LOW)

    // Control Signals for the Output Register //
    alias nLo = control_signals[0];     // 
    
    // Program Counter //
    ProgramCounter pc(
        .bits_in(bus4bit),
        .bits_out(bus4bit),
        .clk(clk),
        .clr_n(rst_n),
        .lp(Lp),
        .cp(Cp),
        .ep(Ep)
    );

    wire [3:0] opcode;
    //assign opcode = 4'h2; // Supposed to come from IR, hardcoded for now

    control_block cb(
        .clk(clk),
        .resetn(rst_n),
        .opcode(opcode[3:0]),
        .out(control_signals[14:0])
    );

    // ALU //
    alu alu_object(
        .clk(clk),            // Clock (Rising edge) (needed for storing CF and ZF)
        .enable_output(Eu),   // Enable ALU output to the bus (ACTIVE-HIGH)
        .reg_a(regA),         // Register A (8 bits)
        .reg_b(regB),         // Register B (8 bits)
        .sub(sub),            // Perform addition when 0, perform subtraction when 1
        .bus(bus),            // Bus (8 bits)
        .CF(CF),              // Carry Flag
        .ZF(ZF)               // Zero Flag
    );
    // Accumulator Register //
    accumulator_register accumulator_object((
        .clk(clk),            // Clock (Rising edge)
        .bus(bus),            // Bus (8 bits)
        .load(nLa),           // Enable Accumulator Register load from bus (ACTIVE-LOW)
        .enable_output(Ea),   // Enable Accumulator Register output to the bus (ACTIVE-HIGH)
        .regA(regA),          // Register A (8 bits)
        .rst_n(rst_n)         // Reset (ACTIVE-LOW)
    );
        

    // Skip these for now
    //wire _unused = &{ui_in, uo_out, uio_in, ena, control_signals[11:0]};
    //assign uo_out = 8'h00;
    assign uio_out = 8'h00;
    assign uio_oe = 8'h00;
    
    //assign inputs
    assign opcode[0] = ui_in[0];
    assign opcode[1] = ui_in[1];
    assign opcode[2] = ui_in[2];
    assign opcode[3] = ui_in[3];
    //Assign outputs
    assign uo_out[0] = 0;
    assign uo_out[1] = 0;
    assign uo_out[2] = 0;
    assign uo_out[3] = 0;
    assign uo_out[4] = control_signals[12];
    assign uo_out[5] = control_signals[13];
    assign uo_out[6] = control_signals[14];
    assign uo_out[7] = 0;

endmodule
