/*
 * SPDX-License-Identifier: Apache-2.0
 */

`default_nettype none

module tt_um_ece298a_8_bit_cpu_top (
    input  wire [7:0] ui_in,     // Dedicated inputs
    output wire [7:0] uo_out,    // Dedicated outputs
    output wire [7:0] uio_out,   // IOs: Output path
    input  wire [7:0] uio_in,    // IOs: Input path - not used
    output wire [7:0] uio_oe,    // IOs: Enable path
    
    input wire clk,
    input  wire ena,             // Always 1 when the design is powered, can be ignored
    input  wire rst_n            // Reset_n - low to reset
);

    // 8-bit bus for data transmission, with a separate 4-bit connection for lower 4 bits of the bus
    wire [7:0] bus;
    wire [3:0] bus4bit = bus[3:0];

    // Control signals (15-bit wide) for CPU modules
    wire [14:0] control_signals;
    
    // Register and ALU wires
    wire [3:0] opcode;
    wire [7:0] reg_a;             // Accumulator register output to ALU
    wire [7:0] reg_b;             // B Register output to ALU
    wire CF, ZF;                  // ALU flags (Carry Flag and Zero Flag)
    
    // Connections between MAR and RAM
    wire [7:0] mar_to_ram_data;
    wire [3:0] mar_to_ram_addr;

    // Mapping control signals to descriptive names
    wire Cp   = control_signals[14];
    wire Ep   = control_signals[13];
    wire Lp   = control_signals[12];
    wire nLma = control_signals[11];
    wire nLmd = control_signals[10];
    wire nCE  = control_signals[9];
    wire nLr  = control_signals[8];
    wire nLi  = control_signals[7];
    wire nEi  = control_signals[6];
    wire nLa  = control_signals[5];
    wire Ea   = control_signals[4];
    wire sub  = control_signals[3];
    wire Eu   = control_signals[2];
    wire nLb  = control_signals[1];
    wire nLo  = control_signals[0];
    
    // Program Counter instance
    wire [3:0] pc_out;  // Program Counter output

    ProgramCounter pc(
        .bits_in(bus4bit),
        .bits_out(pc_out),      // Output to connect to bus4bit as needed
        .clk(clk),
        .clr_n(rst_n),
        .lp(Lp),
        .cp(Cp),
        .ep(Ep)
    );

    // Control Block (Generates control signals based on opcode)
    control_block cb(
        .clk(clk),
        .resetn(rst_n),
        .opcode(opcode),
        .out(control_signals)
    );

    // ALU instance
    alu alu_instance(
        .clk(clk),
        .enable_output(Eu),       // Enable ALU output to the bus (ACTIVE-HIGH)
        .reg_a(reg_a),            // Register A (8 bits)
        .reg_b(reg_b),            // Register B (8 bits)
        .sub(sub),                // 0 for addition, 1 for subtraction
        .bus(bus),                // Output to 8-bit bus
        .CF(CF),                  // Carry Flag
        .ZF(ZF)                   // Zero Flag
    );
    
    // Accumulator Register
    accumulator_register accumulator_inst(
        .clk(clk),
        .bus(bus),
        .load(nLa),               // Load from bus (ACTIVE-LOW)
        .enable_output(Ea),       // Output to bus (ACTIVE-HIGH)
        .regA(reg_a),             // Accumulator Register output
        .rst_n(rst_n)
    );

    // Input and MAR Register (Memory Address Register)
    input_mar_register mar_inst(
        .clk(clk),
        .n_load_data(nLmd),
        .n_load_addr(nLma),
        .bus(bus),
        .data(mar_to_ram_data),
        .addr(mar_to_ram_addr)
    );

    // Instruction Register (Holds the current opcode)
    instruction_register instruction_reg(
        .clk(clk),
        .clear(~rst_n),
        .n_load(nLi),
        .n_enable(nEi),
        .bus(bus),
        .opcode(opcode)
    );

    // B Register
    register b_register(
        .clk(clk),
        .n_load(nLb),
        .bus(bus),
        .value(reg_b)
    );
    
    // Output Register (connects to output pins)
    register output_register(
        .clk(clk),
        .n_load(nLo),
        .bus(bus),
        .value(uo_out)
    );

    // RAM (Data memory)
    tt_um_dff_mem #(
        .RAM_BYTES(16)            // RAM size is 16 bytes
    ) ram (
        .addr(mar_to_ram_addr),
        .data_in(mar_to_ram_data),
        .data_out(bus),
        .lr_n(nLr),
        .ce_n(nCE),
        .clk(clk),
        .rst_n(rst_n)
    );

    // Assignments for unused I/O ports
    assign uio_out = 8'b0;
    assign uio_oe  = 8'b0;
    
    // Avoid unused signal warnings
    wire _unused = &{ena, CF, ZF, ui_in, uio_in};

endmodule
