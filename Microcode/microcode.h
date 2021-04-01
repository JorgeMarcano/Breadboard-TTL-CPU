#define AI  0b00001111  //A clk
#define BI  0b00011111  //B clk
#define CI  0b00101111  //C clk
#define DI  0b00111111  //D clk
#define RI  0b01001111  //Ram Write
#define OI  0b01011111  //Output Reg clk
#define RLI 0b01101111  //Ram Low Addr clk
#define RHI 0b01111111  //Ram High Addr clk
#define PLI 0b10001111  //Program Counter Low clk
#define PHI 0b10011111  //Program Counter High clk
#define II  0b10111111  //Instruction Code Reg clk
#define FI  0b11001111  //Set Flags

#define NOP 0b11111111  //No operation

#define AO  0b11110000  //A out
#define BO  0b11110001  //B out
#define CO  0b11110010  //C out
#define DO  0b11110011  //D out
#define RO  0b11110100  //Ram out
#define PO  0b11110101  //Program ROM out
#define ADD 0b11110110  //ALU Add out
#define SUB 0b11110111  //ALU Sub out
#define NAO 0b11111000  //ALU Nand out
#define DEC 0b11111001  //ALU Decrement out
#define INC 0b11111010  //ALU Increment out
#define CLR 0b11111011  //Clear microinstruction counter
#define PIN 0b11111100  //Program Counter Increment
#define HLT 0b11111101  //Halt

typedef unsigned char byte;
typedef unsigned int word;

typedef struct Code {
  word instr;
  byte size;
  byte* code;
} Code;

//The microcode all instructions must have
byte startCode[] = {
  PO&II, PIN
};

//The list of instructions that depend on all flags low
Code base[] = {
  //Arithmetic instructions
  {0x00, 1, (byte[]) {ADD & AI}},                                     //ADD
  {0x01, 1, (byte[]) {SUB & AI}},                                     //SUB
  {0x02, 1, (byte[]) {NAO & AI}},                                     //NAND
  {0x03, 1, (byte[]) {DEC & AI}},                                     //DEC
  {0x04, 1, (byte[]) {INC & AI}},                                     //INC
  {0x05, 5, (byte[]) {BO & DI, PO & BI, PIN, ADD & AI, DO & BI}},     //ADI (Add literal value to A)
  {0x06, 5, (byte[]) {BO & DI, PO & BI, PIN, SUB & AI, DO & BI}},     //SUI
  {0x07, 5, (byte[]) {BO & DI, PO & BI, PIN, NAO & AI, DO & BI}},     //NANDI
  {0x08, 9, (byte[]) {BO & DI, AO & BI, NAO & BI, DO & AI, BO & DI,
                    AO & BI, NAO & BI, DO & AI, NAO & AI}},           //OR
  {0x09, 4, (byte[]) {BO & DI, AO & BI, NAO & AI, DO & BI}},          //NOT

  //Load from ROM Instructions
  {0x10, 2, (byte[]) {PO & AI, PIN}},                                 //LDA (Load from program ROM in A)
  {0x11, 2, (byte[]) {PO & BI, PIN}},                                 //LDB
  {0x12, 2, (byte[]) {PO & CI, PIN}},                                 //LDC
  {0x13, 2, (byte[]) {PO & DI, PIN}},                                 //LDD
  {0x14, 2, (byte[]) {PO & OI, PIN}},                                 //LDO

  //Store in RAM Instructions
  {0x20, 5, (byte[]) {PO & RHI, PIN, PO & RLI, PIN, AO & RI}},        //STA (Store A in RAM)
  {0x21, 5, (byte[]) {PO & RHI, PIN, PO & RLI, PIN, BO & RI}},        //STB
  {0x22, 5, (byte[]) {PO & RHI, PIN, PO & RLI, PIN, CO & RI}},        //STC
  {0x23, 5, (byte[]) {PO & RHI, PIN, PO & RLI, PIN, DO & RI}},        //STD
  {0x24, 10, (byte[]) {PO & RHI, PIN, PO & RLI, PIN, RO & DI,
                    PO & RHI, PIN, PO & RLI, PIN, DO & RI}},          //STR (Store RAM in RAM) [src] [dest]
  {0x25, 7, (byte[]) {PO & DI, PIN, PO & RHI, PIN, PO & RLI,
                    PIN, DO & RI}},                                   //STI (Store literal in RAM) [val] [dest]

  //Load from RAM Instructions
  {0x30, 5, (byte[]) {PO & RHI, PIN, PO & RLI, PIN, RO & AI}},        //LRA (Load RAM in A)
  {0x31, 5, (byte[]) {PO & RHI, PIN, PO & RLI, PIN, RO & BI}},        //LRB
  {0x32, 5, (byte[]) {PO & RHI, PIN, PO & RLI, PIN, RO & CI}},        //LRC
  {0x33, 5, (byte[]) {PO & RHI, PIN, PO & RLI, PIN, RO & DI}},        //LRD
  {0x34, 5, (byte[]) {PO & RHI, PIN, PO & RLI, PIN, RO & OI}},        //LRO

  //Move between registers
  {0x40, 1, (byte[]) {AO & BI}},                                      //MAB (Move A to B)
  {0x41, 1, (byte[]) {AO & CI}},                                      //MAC
  {0x42, 1, (byte[]) {BO & AI}},                                      //MBA
  {0x43, 1, (byte[]) {BO & CI}},                                      //MBC
  {0x44, 1, (byte[]) {CO & AI}},                                      //MCA
  {0x45, 1, (byte[]) {CO & BI}},                                      //MCB
  {0x4d, 3, (byte[]) {BO & DI, CO & BI, DO & CI}},                    //SBC (Swap B and C)
  {0x4e, 3, (byte[]) {AO & DI, CO & AI, DO & CI}},                    //SAC
  {0x4f, 3, (byte[]) {AO & DI, BO & AI, DO & BI}},                    //SAB

  //Stack Instructions
  {0x50, 6, (byte[]) {CO & RLI, AO & DI, CO & AI, DEC & CI,
                    DO & AI, AO & RI}},                               //PUSHA (previous page addr)
  {0x51, 8, (byte[]) {PO & RHI, PIN, CO & RLI, AO & DI, CO & AI,
                    DEC & CI, DO & AI, AO & RI}},                 //PUSHP [page (high order stack addr)] (PUSH with Page)
  {0x52, 4, (byte[]) {CO & AI, INC & CI, CO & RLI, RO & AI}},     //POPA (previous page addr)
  {0x53, 6, (byte[]) {PO & RHI, PIN, CO & AI, INC & CI,
                    CO & RLI, RO & AI}},                              //POPP [page] (POP with Page)
  {0x54, 11, (byte[]) {CO & RLI, PO & RI, PIN, AO & DI,
                    CO & AI, DEC & AI, AO & RLI, PO & RI, PIN,
                    DEC & CI, DO & AI}},                          //PUSHX (push 16-bit literal into ram)
  {0x55, 9, (byte[]) {AO & DI, CO & AI, INC & AI, AO & RLI, RO & PLI,
                    INC & CI, CO & RLI, RO & PHI, DO & AI}},      //RET (pop 16-bit from ram into PC)
  {0x56, 1, (byte[]) {NOP}},                                          //RTC (return if carry)
  {0x57, 1, (byte[]) {NOP}},                                          //REQ (return if equal)
  {0x58, 1, (byte[]) {NOP}},                                          //RCE (return if carry and equal)
  {0x59, 4, (byte[]) {AO & DI, CO & AI, INC & CI, DO & AI}},      //INCS (increment stack pointer)
  {0x5a, 4, (byte[]) {AO & DI, CO & AI, DEC & CI, DO & AI}},      //DECS (decrement stack pointer)
  {0x5b, 1, (byte[]) {RO & AI}},                                      //PEEK(A) (Saves whatever RAM is currently pointing to A)
  {0x5c, 1, (byte[]) {AO & RI}},                                      //PUT(A) (Saves A to wherever RAM is currently at)
  {0x5d, 4, (byte[]) {PO & RHI, PIN, PO & RLI, PIN}},                 //SRA (Set Ram Addr)
  {0x5e, 2, (byte[]) {PO & RHI, PIN}},                                //LRH (Load Ram Addr High)
  {0x5f, 2, (byte[]) {PO & RLI, PIN}},                                //LRL (Load Ram Addr Low)

  //Output Instructions
  {0x7f, 1, (byte[]) {AO & OI}},                                      //OUTA (Output Reg A)

  //Flag Instructions
  {0xd0, 1, (byte[]) {DEC & FI}}, //CMPZ => Check if A = 0 -> Sets Equal Flag (if 0, A != 0)
  {0xd1, 3, (byte[]) {DEC & AI, SUB & FI, INC & AI}}, //CMPE => Check if A = B -> Sets Equal Flag (if 0, A != B)
  {0xd2, 1, (byte[]) {SUB & FI}}, //CMPL => Check if A >= B (Less than) -> Sets Carry Flag (if 0, A < B)
  {0xd3, 1, (byte[]) {ADD & FI}}, //CMPO => Check if A + B > 255 (Overflow) -> Sets Carry Flag (unsigned only)

  //Jump Instructions
  {0xe0, 4, (byte[]) {PO & DI, PIN, PO & PLI, DO & PHI}},             //JMP (Unconditional Jump)
  {0xe1, 2, (byte[]) {PIN, PIN}},                                     //JMC (Jump if Carry flag)
  {0xe2, 2, (byte[]) {PIN, PIN}},                                     //JEQ (Jump if Equal flag)
  {0xe3, 2, (byte[]) {PIN, PIN}},                                     //JCE (Jump if Carry and Equal)
  {0xe4, 4, (byte[]) {PO & DI, PIN, PO & PLI, DO & PHI}},             //JNC (Jump if No Carry flag)
  {0xe5, 4, (byte[]) {PO & DI, PIN, PO & PLI, DO & PHI}},             //JNE (Jump if Not Equal)
  {0xe6, 4, (byte[]) {PO & DI, PIN, PO & PLI, DO & PHI}},             //JNCE (Jump if Not Carry and Equal)

  //System Instructions
  {0xfe, 1, (byte[]) {HLT}},                                          //HALT
  {0xff, 1, (byte[]) {NOP}}                                           //NOP
};

//The list of instructions that depend on carry flag data, in ascending order
Code flaggedCarry[] = {
  {0x56, 9, (byte[]) {AO & DI, CO & AI, INC & AI, AO & RLI, RO & PLI,
                    INC & CI, CO & RLI, RO & PHI, DO & AI}}, //RTC

  {0xe1, 4, (byte[]) {PO & DI, PIN, PO & PLI, DO & PHI}}, //JMC
  {0xe4, 2, (byte[]) {PIN, PIN}}                                          //JNC (Jump if No Carry flag)
};

//The list of instructions that depend on equal flag data, in ascending order
Code flaggedEqual[] = {
  {0x57, 9, (byte[]) {AO & DI, CO & AI, INC & AI, AO & RLI, RO & PLI,
                    INC & CI, CO & RLI, RO & PHI, DO & AI}}, //REQ

  {0xe2, 4, (byte[]) {PO & DI, PIN, PO & PLI, DO & PHI}}, //JEQ
  {0xe5, 2, (byte[]) {PIN, PIN}}                                          //JNE (Jump if Carry and Equal)
};

//The list of instructions that depend on both flag data, in ascending order
Code flaggedBoth[] = {
  {0x58, 9, (byte[]) {AO & DI, CO & AI, INC & AI, AO & RLI, RO & PLI,
                    INC & CI, CO & RLI, RO & PHI, DO & AI}}, //RCE

  {0xe3, 4, (byte[]) {PO & DI, PIN, PO & PLI, DO & PHI}}, //JCE
  {0xe6, 2, (byte[]) {PIN, PIN}}                                          //JNCE (Jump if Not Carry and Equal)
};
