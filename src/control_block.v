/*
 * Copyright (c) 2024 Siddharth Nema & Gerry Chen
 * SPDX-License-Identifier: Apache-2.0
 */

`default_nettype none

module control_block (
    input wire clk,
    input wire resetn,
    input wire [3:0] opcode,
    output wire [14: 0] out,    

    // Inputs for the programmer part
    input wire programming,
    output wire done_load,
    output wire read_ui_in,
    output wire ready,
    output wire HF
);

/* Supported Instructions' Opcodes */
localparam OP_HLT = 4'h0;
// localparam OP_NOP = 4'h1;  // Comment this out to avoid error with unused param.
localparam OP_ADD = 4'h2;
localparam OP_SUB = 4'h3;
localparam OP_LDA = 4'h4;
localparam OP_OUT = 4'h5;
localparam OP_STA = 4'h6;
localparam OP_JMP = 4'h7;


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
reg hlt_flag;
reg done_load_reg;
reg read_ui_in_reg;
reg ready_reg;
/* Micro-Operation Stages */
parameter T0 = 0, T1 = 1, T2 = 2, T3 = 3, T4 = 4, T5 = 5; 

/* Stage Transition Logic */
always @(posedge clk) begin
    if (!resetn) begin           // Check if reset is asserted, if yes, put into a holding stage
      stage <= 6;
    end
 	else begin                   // If reset is not asserted, do the stages sequentially
      if (stage == 6) begin        
          stage <= 0;
        end 
        else if ((stage == T0 || stage == T1 || 
                 stage == T2 || stage == T3 || 
            stage == T4 || stage == T5) && !hlt_flag) begin
            // Valid stages
            stage <= stage + 1; // Increment to the next stage
        end 
        else if (!hlt_flag) begin
            // If the stage is not valid, set it to 6
            stage <= 6; // Set to stage 6 
        end
    end
    if (hlt_flag) begin
        stage <= 7;
    end
end

/* Micro-Operation Logic */
always @(negedge clk) begin
    control_signals <= 15'b000111111100011; // All signals are deasserted
    done_load_reg <= 0;
    read_ui_in_reg <= 0;
    ready_reg <= 0;
    if (!resetn) begin           // Check if reset is asserted, if yes, init halt reg
      hlt_flag <= 0;
    end
    
    case(stage)
        T0: begin
            control_signals[SIG_PC_EN] <= 1;
            control_signals[SIG_MAR_ADDR_LOAD_N] <= 0;
            ready_reg <= 1;
        end 
        T1: begin
            control_signals[SIG_PC_INC] <= 1;
            
        end
        T2: begin
            if (!programming) begin
                control_signals[SIG_RAM_EN_N] <= 0;
                control_signals[SIG_IR_LOAD_N] <= 0;
            end
        end
        T3: begin
            if (opcode == OP_HLT) begin
                hlt_flag <= 1;
            end
            if (!programming) begin
                case (opcode)
                    OP_ADD, OP_SUB, OP_LDA, OP_STA: begin
                        control_signals[SIG_IR_EN_N] <= 0;
                        control_signals[SIG_MAR_ADDR_LOAD_N] <= 0;
                    end
                    OP_OUT: begin
                        control_signals[SIG_REGA_EN] <= 1;
                        control_signals[SIG_OUT_LOAD_N] <= 0;
                    end
                    OP_JMP: begin
                        control_signals[SIG_IR_EN_N] <= 0;
                        control_signals[SIG_PC_LOAD] <= 1;
                    end
                    default: begin
                    // Do nothing (leave control_signals unchanged)
                    end
                endcase
            end else begin
                read_ui_in_reg <= 1;
                control_signals[SIG_MAR_MEM_LOAD_N] <= 0;
            end
        end
        T4: begin
            if (!programming) begin
                case (opcode)
                    OP_ADD, OP_SUB: begin
                        control_signals[SIG_RAM_EN_N] <= 0;
                        control_signals[SIG_REGB_LOAD_N] <= 0;
                    end
                    OP_LDA: begin
                        control_signals[SIG_RAM_EN_N] <= 0;
                        control_signals[SIG_REGA_LOAD_N] <= 0;
                    end
                    OP_STA: begin
                        control_signals[SIG_REGA_EN] <= 1;
                        control_signals[SIG_MAR_MEM_LOAD_N] <= 0;
                    end
                    default: begin
                    // Do nothing (leave control_signals unchanged)
                    end
                endcase
            end else begin
                control_signals[SIG_RAM_LOAD_N] <= 0;
                done_load_reg <= 1;
            end
        end
        T5: begin
            if (!programming) begin
                case (opcode)
                    OP_ADD: begin
                        control_signals[SIG_REGB_EN] <= 1;
                        control_signals[SIG_REGA_LOAD_N] <= 0;
                    end
                    OP_SUB: begin
                        control_signals[SIG_ADDER_SUB] <= 1;
                        control_signals[SIG_REGB_EN] <= 1;
                        control_signals[SIG_REGA_LOAD_N] <= 0;
                    end
                    OP_STA: begin
                        control_signals[SIG_RAM_LOAD_N] <= 0;
                    end
                    default: begin
                    // Do nothing (leave control_signals unchanged)
                    end
                endcase
            end
        end
        default: begin
        // Do nothing (leave control_signals unchanged)
        end
    endcase
end

assign out = control_signals;
assign done_load = done_load_reg;
assign read_ui_in = read_ui_in_reg;
assign ready = ready_reg;
assign HF = hlt_flag;

endmodule
