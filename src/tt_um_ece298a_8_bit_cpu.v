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
    
    wire [3:0] bus;                                        // temporarily make the bus 4 bits wide to not have the top 4 bits undriven
    wire [14:0] control_signals;

    // Program Counter //
    ProgramCounter pc(
        .bits_in(bus[3:0]),
        .bits_out(bus[3:0]),
        .clk(clk),
        .clr_n(rst_n),
        .lp(control_signals[12]),
        .cp(control_signals[14]),
        .ep(control_signals[13])
    );

    wire [3:0] opcode;
    //assign opcode = 4'h2; // Supposed to come from IR, hardcoded for now

    control_block cb(
        .clk(clk),
        .resetn(rst_n),
        .opcode(opcode[3:0]),
        .out(control_signals[14:0])
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
    assign bus[0] = ui_in[4];
    assign bus[1] = ui_in[5];
    assign bus[2] = ui_in[6];
    assign bus[3] = ui_in[7];
    //Assign outputs
    assign uo_out[0] = 0; //bus[0];
    assign uo_out[1] = 0; //bus[1];
    assign uo_out[2] = 0; //bus[2];
    assign uo_out[3] = 0; //bus[3];
    assign uo_out[4] = control_signals[12];
    assign uo_out[5] = control_signals[13];
    assign uo_out[6] = control_signals[14];
    assign uo_out[7] = 0;

endmodule
