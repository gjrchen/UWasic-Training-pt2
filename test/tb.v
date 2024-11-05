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

  /// Init registers 
  reg resetn;
  reg clk;
  reg ena = 1;

  reg [7:0] ui_in;
  reg [7:0] uio_in;
  wire [7:0] uo_out;
  wire [7:0] uio_out;
  wire [7:0] uio_oe;
  
  `ifdef GL_TEST
  wire VPWR = 1'b1;
  wire VGND = 1'b0;
  `endif

  tt_um_control_block uut(
    // Include power ports for the Gate Level test:
    `ifdef GL_TEST
          .VPWR(VPWR),
          .VGND(VGND),
    `endif
    //
    .clk(clk), 
    .rst_n(resetn),
    .ui_in(ui_in),
    .uo_out(uo_out),
    .uio_out(uio_out),
    .uio_oe(uio_oe),
    .ena(ena),
    .uio_in(uio_in)
  );

endmodule
