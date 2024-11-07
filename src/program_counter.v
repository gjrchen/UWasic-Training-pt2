/*
 * Copyright (c) 2024 Evan & Catherine
 * SPDX-License-Identifier: Apache-2.0
 */

`default_nettype none

module j_k_logic (
  input pclr,
  input lp,
  input cp,
  input bn,
  input a,
  output j,
  output k
);
  wire plp_cp_a;
  assign plp_cp_a = ~lp & cp & a;

  assign j = (pclr & plp_cp_a) | (pclr & lp & bn);
  assign k = (~pclr) | (plp_cp_a) | (lp & ~bn);
endmodule

module JK_flip_flop(input j, input k, input clk, output reg q);

  always @ (posedge clk)
    case ({j,k})
      2'b00: q <= q;
      2'b01: q <= 0;
      2'b10: q <= 1;
      2'b11: q <= ~q;
    endcase
endmodule

module set_counter_bit(input CLR_n, input Lp, input Cp, input b, input A, input CLK, output S);

  wire j, k;
  j_k_logic jk_logic(CLR_n, Lp, Cp, b, A, j, k);
  JK_flip_flop flip_flop(j, k, CLK, S);

endmodule

module ProgramCounter (
  inout wire[3:0] bus,
  input wire clk,
  input wire clr_n,
  input wire lp,
  input wire cp,
  input wire ep
);
  wire[3:0] counter;
  set_counter_bit set_bit_0(clr_n, lp, cp, bus[0], 1'b1, clk, counter[0]);
  set_counter_bit set_bit_1(clr_n, lp, cp, bus[1], (counter[0]), clk, counter[1]);
  set_counter_bit set_bit_2(clr_n, lp, cp, bus[2], (counter[0] & counter[1]), clk, counter[2]);
  set_counter_bit set_bit_3(clr_n, lp, cp, bus[3], (counter[0] & counter[1] & counter[2]), clk, counter[3]);

  assign bus = ep ? counter : 4'bZZZZ;
endmodule
