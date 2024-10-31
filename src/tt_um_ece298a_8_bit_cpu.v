/*
 * SPDX-License-Identifier: Apache-2.0
 */

`default_nettype none

`include "control_block.v"
`include "program_counter.v"

module tt_um_ece298a_8_bit_cpu_top (
    input wire clk,
    
    input  wire [7:0] ui_in,    // Dedicated inputs 
    output wire [7:0] uo_out,   // Dedicated outputs 
    output wire [7:0] uio_out,  // IOs: Output path
    output wire [7:0] uio_oe,   // IOs: Enable path 

    input  wire [7:0] uio_in,   // IOs: Input path - not used
    input  wire ena,            // always 1 when the design is powered, so you can ignore it
    input  wire rst_n           // reset_n - low to reset
);
    wire [7:0] bus;
    wire [14:0] control_signals = 15'b000111111100011;

    ProgramCounter pc(
        bus[3:0],
        bus[3:0],
        clk,
        rst_n,
        control_signals[12],
        control_signals[14],
        control_signals[13]
    );

    wire [3:0] opcode;
    assign opcode = 4'h2; // Supposed to come from IR, hardcoded for now

    control_block cb(
        clk,
        rst_n,
        bus[7:4],
        control_signals[14:0]
    );

    // Skip these for now
    wire _unused = &{ui_in, uo_out,  uio_out, uio_oe, uio_in, ena};
  
endmodule
