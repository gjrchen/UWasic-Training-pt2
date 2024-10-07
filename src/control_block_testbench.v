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
  
  reg [3:0] opcode;
  wire [14:0] out_res;
  
  tt_um_control_block uut(
    .clk(clk), 
    .resetn(resetn),
    .opcode(opcode),
    .out(out_res)
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
