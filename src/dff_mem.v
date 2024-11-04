`default_nettype none

module tt_um_dff_mem #(
    parameter RAM_BYTES = 16  
) (
    input  wire [7:0] ui_in,    // Dedicated inputs - connected to the input switches
    output reg  [7:0] uo_out,   // Dedicated outputs - connected to the 7 segment display
    input  wire [7:0] uio_in,   // IOs: Bidirectional Input path
    output wire [7:0] uio_out,  // IOs: Bidirectional Output path
    output wire [7:0] uio_oe,   // IOs: Bidirectional Enable path (active high: 0=input, 1=output)
    input  wire       ena,      // will go high when the design is enabled
    input  wire       clk,      // clock
    input  wire       rst_n     // reset_n - low to reset
);

  localparam addr_bits = $clog2(RAM_BYTES);

  wire [addr_bits-1:0] addr = ui_in[addr_bits-1:0];
  wire lr_n = ui_in[7];  // lr_n signal (active low)
  wire ce_n = ui_in[6];  // ce_n signal (active low)

  reg [7:0] RAM[RAM_BYTES - 1:0];

  // Assign outputs based on ce_n and lr_n control signals
  assign uio_out = (!ce_n) ? RAM[addr] : 8'bZ;  // Output data when ce_n is low
  assign uio_oe  = (!ce_n) ? 8'hFF : 8'h00;     // Enable output when ce_n is low

  always @(posedge clk) begin
    if (!rst_n) begin
      uo_out <= 8'b0;
      for (int i = 0; i < RAM_BYTES; i++) begin
        RAM[i] <= 8'b0;  // Reset RAM contents
      end
    end else begin
      if (!lr_n) begin  // Load data into RAM when lr_n is low
        RAM[addr] <= uio_in;
      end
      uo_out <= 8'b0;  // Optional: can be used for debugging or status
    end
  end

endmodule  // tt_um_dff_mem
