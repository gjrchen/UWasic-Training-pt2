/*
 * SPDX-License-Identifier: Apache-2.0
 */

`default_nettype none

module tt_um_ece298a_8_bit_cpu_top (
    input wire clk,
    
    input  wire [7:0] ui_in,    // Dedicated inputs 
    output wire [7:0] uo_out,   // Dedicated outputs 
    output wire [7:0] uio_out,  // IOs: Output path
    output wire [7:0] uio_oe,   // IOs: Enable path 

    input  wire [7:0] uio_in,   // IOs: Input path - not used
    input  wire ena,      // always 1 when the design is powered, so you can ignore it
    input  wire rst_n     // reset_n - low to reset
);
    wire bus [7:0];
    wire control_signals [14:0] = 15'b000111111100011;

    
  
endmodule
