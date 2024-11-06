/*
 * Copyright (c) 2024 Siddharth Nema
 * SPDX-License-Identifier: Apache-2.0
 */

`default_nettype none

module programmer (
  input wire clk,
  input wire resetn,
  input wire [7:0] ui_in,
  input wire programming,
  input wire new_byte,
  inout wire [7:0] bus,
  output wire [14: 0] out    
);

/* Output Control Signals */
localparam SIG_PC_INC = 14;             // C_P
localparam SIG_PC_EN = 13;              // E_P
localparam SIG_PC_LOAD = 12;            // L_P
localparam SIG_MAR_ADDR_LOAD_N = 11;    // \L_MA
localparam SIG_MAR_MEM_LOAD_N = 10;     // \L_MD
localparam SIG_RAM_EN_N = 9;            // \CE
localparam SIG_RAM_LOAD_N = 8;          // \L_R
localparam SIG_IR_LOAD_N = 7;           // \L_I
localparam SIG_IR_EN_N = 6;             // \E_I
localparam SIG_REGA_LOAD_N = 5;         // \L_A
localparam SIG_REGA_EN = 4;             // E_A
localparam SIG_ADDER_SUB = 3;           // S_U 
localparam SIG_REGB_EN = 2;             // E_U
localparam SIG_REGB_LOAD_N = 1;         // \L_B
localparam SIG_OUT_LOAD_N = 0;          // \L_O

  /* Internal Regs */
reg [2:0] stage;
reg [14:0] control_signals;
reg programming_stage;
reg programming_d; // delayed programming wire to check for posedge
reg [7:0] ram_input;

  /* Micro-Operation Stages */
parameter T0 = 0, T1 = 1, T2 = 2, T3 = 3, T4 = 4, T5 = 5; 


always @(posedge clk) begin
    programming_d <= programming;
  if (programming && !programming_d) begin // posedge
    programming_stage <= 1;
    ram_input <= ui_in;
  end
end

/* Stage Transition Logic */
always @(posedge clk) begin
    if (!resetn) begin           // Check if reset is asserted, if yes, put into a holding stage
      stage <= 6;
    end
 	else begin                   // If reset is not asserted, do the stages sequentially
      if (stage == 6) begin        
          stage <= 0;
        end 
        else if (stage == T0 || stage == T1 || 
                 stage == T2 || stage == T3 || 
                 stage == T4 || stage == T5) begin
            // Valid stages
            stage <= stage + 1; // Increment to the next stage
        end else begin
            // If the stage is not valid, set it to 6
            stage <= 6; // Set to stage 6 
        end
    end
end

  /* Micro-Operation Logic */
always @(negedge clk) begin
    control_signals <= 15'b000111111100011; // All signals are deasserted

    case(stage)
        T0: begin
            control_signals[SIG_PC_EN] <= 1;
            control_signals[SIG_MAR_ADDR_LOAD_N] <= 0;
        end 
        T1: begin
            if (programming_stage) begin
                control_signals[SIG_PC_INC] <= 1;
            end
        end
        T2: begin
            control_signals[SIG_RAM_EN_N] <= 0;
        end
        T3: begin
            if (programming_stage) begin
                control_signals[SIG_IR_EN_N] <= 0;
                control_signals[SIG_MAR_ADDR_LOAD_N] <= 0;
            end
        end
        T4: begin
            if (programming_stage) begin
                control_signals[SIG_REGA_EN] <= 1;
                control_signals[SIG_MAR_MEM_LOAD_N] <= 0;
            end
            default: begin
            // Do nothing (leave control_signals unchanged)
            end
        end
        T5: begin
          if (programming_stage) begin
            control_signals[SIG_RAM_LOAD_N] <= 0;
            // reset programming_stage to be ready to take a new input
            programming_stage <= 0;
          end
        end
    endcase
end

assign out = control_signals;
  
endmodule
