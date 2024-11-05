`default_nettype none

module tt_um_ece298a_8_bit_cpu_top (
    input  wire [7:0] ui_in,
    output wire [7:0] uo_out,
    output wire [7:0] uio_out,
    input  wire [7:0] uio_in,
    output wire [7:0] uio_oe,
    input wire clk,
    input  wire ena,
    input  wire rst_n
);

    wire [7:0] bus;
    wire [3:0] pc_in;
    wire [3:0] pc_out;
    assign pc_in = bus[3:0];

    wire [14:0] control_signals;
    wire [3:0] opcode;
    wire [7:0] reg_a;
    wire [7:0] reg_b;
    wire CF;
    wire ZF;

    wire [7:0] mar_to_ram_data;
    wire [3:0] mar_to_ram_addr;

    wire Cp = control_signals[14];
    wire Ep = control_signals[13];
    wire Lp = control_signals[12];
    wire nLma = control_signals[11];
    wire nLmd = control_signals[10];
    wire nCE = control_signals[9];
    wire nLr = control_signals[8];
    wire nLi = control_signals[7];
    wire nEi = control_signals[6];
    wire nLa = control_signals[5];
    wire Ea = control_signals[4];
    wire sub = control_signals[3];
    wire Eu = control_signals[2];
    wire nLb = control_signals[1];
    wire nLo = control_signals[0];

    ProgramCounter pc(
        .bits_in(pc_in),
        .bits_out(pc_out),
        .clk(clk),
        .clr_n(rst_n),
        .lp(Lp),
        .cp(Cp),
        .ep(Ep)
    );

    control_block cb(
        .clk(clk),
        .resetn(rst_n),
        .opcode(opcode),
        .out(control_signals)
    );

    alu alu_object(
        .clk(clk),
        .enable_output(Eu),
        .reg_a(reg_a),
        .reg_b(reg_b),
        .sub(sub),
        .bus(bus),
        .CF(CF),
        .ZF(ZF)
    );

    accumulator_register accumulator_object(
        .clk(clk),
        .bus(bus),
        .load(nLa),
        .enable_output(Ea),
        .regA(reg_a),
        .rst_n(rst_n)
    );

    input_mar_register input_mar_register(
        .clk(clk),
        .n_load_data(nLmd),
        .n_load_addr(nLma),
        .bus(bus),
        .data(mar_to_ram_data),
        .addr(mar_to_ram_addr)
    );

    instruction_register instruction_register(
        .clk(clk),
        .clear(~rst_n),
        .n_load(nLi),
        .n_enable(nEi),
        .bus(bus),
        .opcode(opcode)
    );

    register b_register(
        .clk(clk),
        .n_load(nLb),
        .bus(bus),
        .value(reg_b)
    );

    register output_register(
        .clk(clk),
        .n_load(nLo),
        .bus(bus),
        .value(uo_out)
    );

    tt_um_dff_mem #(
    .RAM_BYTES(16)
    ) ram (
        .addr(mar_to_ram_addr),     
        .data_in(mar_to_ram_data), 
        .data_out(bus), 
        .lr_n(nLr),     
        .ce_n(nCE),     
        .clk(clk),       
        .rst_n(rst_n)    
    );

    assign uio_out = 0;
    assign uio_oe  = 0;

    wire _unused = &{ena, CF, ZF, ui_in, uio_in};

endmodule

