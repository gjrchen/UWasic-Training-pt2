`default_nettype none

module tt_um_dff_mem #(
    parameter RAM_BYTES = 16  
) (
    input  wire [3:0] addr,
    input  wire [7:0] data_in,
    output wire [7:0] data_out,
    input  wire       lr_n,     //load/write enable
    input  wire       ce_n,     // read enable
    input  wire       clk,      // clock
    input  wire       rst_n     // reset_n - low to reset
);

  reg [7:0] RAM[RAM_BYTES - 1:0];

  // Assign outputs based on ce_n and lr_n control signals
  assign data_out = (!ce_n) ? RAM[addr] : 8'bZ;  // Output data when ce_n is low

  always @(posedge clk) begin
    if (!rst_n) begin
      for (int i = 0; i < RAM_BYTES; i++) begin
        RAM[i] <= 8'b0;  // Reset RAM contents
      end
    end else begin
      if (!lr_n) begin  // Load data into RAM when lr_n is low
          RAM[addr] <= data_in;
      end
    end
  end

endmodule  // tt_um_dff_mem
