`default_nettype none
`timescale 1ns / 1ps

/* This testbench just instantiates the module and makes some convenient wires
   that can be driven / tested by the cocotb test.py.
*/
module tb ();

  // Dump the signals to a VCD file. You can view it with gtkwave.
  initial begin
    $dumpfile("tb.vcd");
    $dumpvars(0, tb);
    #1;
  end

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

endmodule
