/*
 * SPDX-License-Identifier: Apache-2.0
 */

`default_nettype none

module tt_um_ece298a_8_bit_cpu_top (
    input  wire [7:0] ui_in,        // Dedicated inputs
    output wire [7:0] uo_out,       // Dedicated outputs
    input  wire [7:0] uio_in,       // IOs: Input path
    output wire [7:0] uio_out,      // IOs: Output path
    output wire [7:0] uio_oe,       // IOs: Enable path (active high: 0=input, 1=output)
    input  wire       ena,          // always 1 when the design is powered, so you can ignore it
    input  wire       clk,          // clock
    input  wire       rst_n         // reset_n - low to reset
);
    // Bus //
    wire [7:0] bus;                 // Bus (8-bit) (High impedance when not in use)
    wire outputting_to_bus;         // Signal to determine if something is outputting to the bus   

    // Control Signals //
    wire [14:0] control_signals;    // Control Signals (15-bit), see below for the signal assignments

    // Programmer Wires //
    wire programming;               // Programming mode signal (ACTIVE-HIGH)
    wire ready_for_ui;              // Ready signal for UI (ACTIVE-HIGH)
    wire done_load;                 // Done loading signal (ACTIVE-HIGH)
    wire read_ui_in;                // Read UI input signal (ACTIVE-HIGH)    

    // Wires //
    wire [3:0] opcode;                  // opcode from IR to Control
    wire [7:0] reg_a;                   // value from Accumulator Register to ALU
    wire [7:0] reg_b;                   // value from B Register to ALU
    
    // Flags //
    wire CF;                            // Carry Flag (ALU) (ACTIVE-HIGH)
    wire ZF;                            // Zero Flag (ALU) (ACTIVE-HIGH)
    wire HF;                            // Halt Flag (CB) (ACTIVE-HIGH)
    
    // Wire between MAR and RAM //
    wire [7:0] mar_to_ram_data;         // MAR to RAM data wire
    wire [3:0] mar_to_ram_addr;         // MAR to RAM address wire

    // Control Signals for the Program Counter //
    wire Cp = control_signals[14];                  // allow the Program Counter to increment (ACTIVE-HIGH)
    wire Ep = control_signals[13] & rst_n;          // enable Program Counter output to the bus (ACTIVE-HIGH)
    wire Lp = control_signals[12];                  // enable Program Counter load from the bus (ACTIVE-HIGh)

    // Control Signals for the MAR //
    wire nLma = control_signals[11];                // enable loading of the MAR address from the bus (ACTIVE-LOW)
    wire nLmd = control_signals[10];                // enable loading of the MAR data from the bus (ACTIVE-LOW)

    // Control Signals for the RAM //
    wire nCE = control_signals[9] | !rst_n;         // enable the RAM output to the bus (ACTIVE-LOW)
    wire nLr = control_signals[8];                  // enable the RAM load from the bus (ACTIVE-LOW)

    // Control Signals for the Instruction Register //
    wire nLi = control_signals[7];                  // enable Instruction Register load from bus (ACTIVE-LOW)
    wire nEi = control_signals[6] | !rst_n;         // enable Instruction Register output to the bus (ACTIVE-LOW)
    
    // Control Signals for the Accumulator Register //
    wire nLa = control_signals[5];                  // enable Accumulator Register load from bus (ACTIVE-LOW)
    wire Ea = control_signals[4] & rst_n;           // enable Accumulator Register output to the bus (ACTIVE-HIGH)

    // Control Signals for the ALU //
    wire sub = control_signals[3];                  // perform addition when 0, perform subtraction when 1 (ACTIVE-HIGH)
    wire Eu = control_signals[2] & rst_n;           // enable ALU output to the bus (ACTIVE-HIGH)
    
    // Control Signals for the B Register //
    wire nLb = control_signals[1];                  // enable B Register load from bus (ACTIVE-LOW)
    
    // Control Signals for the Output Register //
    wire nLo = control_signals[0];                  // enable Output Register load from bus (ACTIVE-LOW)

     // Control Signals for the Bus Initialization //
    assign outputting_to_bus = (Ep | (!nCE) | (!nEi) | Ea | Eu | read_ui_in);     // Figure out if something is outputting to the bus   
    
    assign bus = (read_ui_in & rst_n) ? ui_in : 8'bZZZZZZZZ;                      // read_ui_in is a signal driven by CB and should be mutually exclusive with outputting to bus
    
    // Tri-state buffer to initialize the bus with a known value //
    assign bus = (outputting_to_bus) ? 8'bZZZZZZZZ : 8'b00000000;         // Initialize the bus with a known value if nothing is outputting to the bus

    // Program Counter //
    ProgramCounter pc(
        .bus(bus[3:0]),         // Bus (lower 4 bits)
        .clk(clk),              // Clock (Falling edge)
        .clr_n(rst_n),          // Clear (ACTIVE-LOW)
        .lp(Lp),                // Load Program Counter (ACTIVE-HIGH)
        .cp(Cp),                // Increment Program Counter (ACTIVE-HIGH)
        .ep(Ep)                 // Enable Program Counter output to the bus (ACTIVE-HIGH)
    );
    
    control_block cb(
        .clk(clk),                      // Clock
        .resetn(rst_n),                 // Reset (ACTIVE-LOW)
        .opcode(opcode[3:0]),           // Opcode from the Instruction Register
        .out(control_signals[14:0]),    // Control Signals
        .programming(programming),      // Programming mode signal (ACTIVE-HIGH)
        .done_load(done_load),          // Done loading signal (ACTIVE-HIGH)
        .read_ui_in(read_ui_in),        // Read UI input signal (ACTIVE-HIGH)
        .ready(ready_for_ui),           // Ready signal for UI (ACTIVE-HIGH)
        .HF(HF)                         // Halt Flag (ACTIVE-HIGH)
    );
    

    // ALU //
    alu alu_object(
        .clk(clk),              // Clock (Rising edge) (needed for storing CF and ZF)
        .enable_output(Eu),     // Enable ALU output to the bus (ACTIVE-HIGH)
        .reg_a(reg_a),          // Register A (8 bits)
        .reg_b(reg_b),          // Register B (8 bits)
        .sub(sub),              // Perform addition when 0, perform subtraction when 1
        .bus(bus),              // Bus (8 bits)
        .CF(CF),                // Carry Flag
        .ZF(ZF),                // Zero Flag
        .rst_n(rst_n)           // Reset (ACTIVE-LOW)
    );
    
    // Accumulator Register //
    accumulator_register accumulator_object(
        .clk(clk),              // Clock (Rising edge)
        .bus(bus),              // Bus (8 bits)
        .load(nLa),             // Enable Accumulator Register load from bus (ACTIVE-LOW)
        .enable_output(Ea),     // Enable Accumulator Register output to the bus (ACTIVE-HIGH)
        .regA(reg_a),           // Register A (8 bits)
        .rst_n(rst_n)           // Reset (ACTIVE-LOW)
    );


    // Input and MAR Register //
    input_mar_register input_mar_register(
        .clk(clk),              // Clock (Rising edge)
        .n_load_data(nLmd),     // Enable loading of the MAR data from the bus (ACTIVE-LOW)
        .n_load_addr(nLma),     // Enable loading of the MAR address from the bus (ACTIVE-LOW)
        .bus(bus),              // Bus (8 bits)
        .data(mar_to_ram_data), // MAR to RAM data wire
        .addr(mar_to_ram_addr)  // MAR to RAM address wire
    );

    // Instruction Register //
    instruction_register instruction_register(
        .clk(clk),              // Clock (Rising edge)
        .clear(~rst_n),         // Clear (ACTIVE-HIGH)
        .n_load(nLi),           // Enable Instruction Register load from bus (ACTIVE-LOW)
        .n_enable(nEi),         // Enable Instruction Register output to the bus (ACTIVE-LOW)
        .bus(bus),              // Bus (8 bits)
        .opcode(opcode)         // Opcode (4 bits)
    );
    
    // B Register //
    register b_register(
        .clk(clk),              // Clock (Rising edge)
        .n_load(nLb),           // Enable B Register load from bus (ACTIVE-LOW)
        .bus(bus),              // Bus (8 bits)
        .value(reg_b)           // Register B (8 bits)
    );
    
    // Output Register //
    register output_register(
        .clk(clk),              // Clock (Rising edge)
        .n_load(nLo),           // Enable Output Register load from bus (ACTIVE-LOW)
        .bus(bus),              // Bus (8 bits)
        .value(uo_out)          // Output Register (8 bits) (Output to the UO_OUT)
    );

    // RAM //
    tt_um_dff_mem #(
    .RAM_BYTES(16)                  // Set the RAM size to 16 bytes
    ) ram (
        .addr(mar_to_ram_addr),     // MAR to RAM address wire
        .data_in(mar_to_ram_data),  // MAR to RAM data wire
        .data_out(bus),             // Bus (8 bits)
        .lr_n(nLr),                 // enable the RAM load from the bus (ACTIVE-LOW)
        .ce_n(nCE),                 // enable the RAM output to the bus (ACTIVE-LOW)
        .clk(clk),                  // Clock (Rising edge)
        .rst_n(1'b1)                // Reset (ACTIVE-LOW) (Never reset the RAM)
    );
    assign programming = uio_in[0];     // Programming mode signal (ACTIVE-HIGH) to the UIO input 0
    assign uio_out[1] = ready_for_ui;   // Ready signal for UI (ACTIVE-HIGH) to the UIO output 1
    assign uio_out[2] = done_load;      // Done loading signal (ACTIVE-HIGH) to the UIO output 2
    assign uio_out[3] = CF;             // Carry Flag (ALU) (ACTIVE-HIGH) to the UIO output 3
    assign uio_out[4] = ZF;             // Zero Flag (ALU) (ACTIVE-HIGH) to the UIO output 4
    assign uio_out[5] = HF;             // Halt Flag (CB) (ACTIVE-HIGH) to the UIO output 5

    // Wires //
    assign uio_out[7] = 1'b0;           // Set the IO outputs to 0
    assign uio_out[6] = 1'b0;           // Set the IO outputs to 0
    assign uio_out[0] = 1'b0;           // Set the IO outputs to 0
    assign uio_oe = 8'b00111110;        // Configure the IO ports [5:1] as outputs and [0], [6],[7] as input

    wire _unused = &{uio_in[7:6], ena}; // Avoid unused variable warning

endmodule
