/*
 * Copyright (c) 2024 Gerry Chen
 * SPDX-License-Identifier: Apache-2.0
 */

`default_nettype none
`timescale 1ns/1ps      // For simulation 


module testbench_control_block;
  
  // Init registers 
  reg resetn;
  reg clk;
  reg ena;
  ena = 1;
  
  reg [3:0] opcode;
  wire [15:0] out_res; // disregard the first bit
  wire [7:0] uio_oe;
  wire [7:0] uio_in
  
  tt_um_control_block uut(
    .clk(clk), 
    .rst_n(resetn),
    .ui_in({4'b0000, opcode}),
    .uo_out(out_res[15:8]),
    .uio_out(out_res[7:0]),
    .uio_oe(uio_oe),
    .ena(ena),
    .uio_in(uio_in),
  );
  
  // Instantiate / Generate the clock signal
  initial begin
        clk = 0;
        forever #10 clk = ~clk; // 20ns clock period = 50MHz
    end
  
  // Start testing all of the sequences
  
  initial begin
  	
    // VCD setup
      $dumpfile("dump.vcd"); 
      $dumpvars(0, testbench_control_block); // Dump all variables in this module
    
    resetn = 0; 	// Assert reset
    #30; 			// Wait some amount of time
    resetn = 1;		// Deassert reset	
    
    opcode = 4'h1; 	// NOP
    #1000;			
    opcode = 4'h2; 	// ADD
    #1000;	
    opcode = 4'h3; 	// SUB
    #1000;	
    opcode = 4'h4; 	// LDA
    #1000;	
    opcode = 4'h5; 	// OUT
    #1000;	
    opcode = 4'h6; 	// STA
    #1000;	
    opcode = 4'h7; 	// JMP
    #1000;	
    opcode = 4'h0; 	// HLT
   	#1000;	
    
    $finish; 		// Cue the end of the simulation
  end
  
  // Monitor the output signals via icarus
  always @(*) begin
    $monitor("Time: %0dns, Reset: %b, Opcode: %b, Control Signals: %b", 
             $time, resetn, opcode, out_res);
  end
  
endmodule
