#!/usr/bin/python
# -*- coding: utf-8 -*-

import sys

'''
Bugs found in another disassembler:

- LDI instruction's 2nd byte isn't correctly masked apparently
- LI 0 shall be CLA, actually, even if the semantics is indeed the same
  (someone wanted to desperately sell that additional instruction at NEC :-) )

'''

input_file = sys.argv[1]
output_file = input_file + ".txt"

input_file_handle = open(input_file, "rb")
output_file_handle = open(output_file, "wb")

instructions = [];

class Instruction:

    def __init__(s):
        
        s.instruction       = None    # Contains the instruction definition
        s.opcode_data       = 0x00    # Contains the instruction data
        s.opcode_nex_data   = 0x00    # Contains the next instruction data (2-byte long instructions only)
        
        s.saved_opcode      = 0x00
        s.saved_opcode_next = 0x00

    def decode(s, opcode, opcode_next):

        for instruction in instructions:
            if (instruction.match(opcode)):
                s.instruction = instruction
                break
        
        # Decode instruction data
        s.opcode_data = s.instruction.get_data(opcode)
        # Decode instruction next data
        s.opcode_nex_data = s.instruction.get_next_data(opcode_next)
        
        # Save opcodes apart for later use
        s.saved_opcode      = opcode
        s.saved_opcode_next = opcode

    def get_instruction(s):
        return s.instruction
    
    def __str__(s):

        if (s.instruction.opcode_mask != 0xFF):
            # The opcode has extra data, append it
            instruction_data_0 = " %02X" % (s.opcode_data)
        else:
            # No extra data for the opcode
            if (s.instruction.size == 1):
                instruction_data_0 = ""
            else:
                instruction_data_0 = " "

        if (s.instruction.size == 1):
            output_buffer = "%s%s" % (s.instruction.name, instruction_data_0)
        elif (s.instruction.size == 2):
            # The opcode has an extra byte for additional data
            output_buffer = "%s%s%02X" % (s.instruction.name, instruction_data_0, s.opcode_nex_data)
        else:
            output_buffer = "ERROR"

        output_buffer += "    \t;" + s.instruction.operation

        return output_buffer

class InstructionDefinition:

    def __init__(s, name, opcode, opcode_mask, optionbits_mask, size, operation, skip, description):

        s.name              = name
        s.opcode            = opcode
        s.opcode_mask       = opcode_mask
        s.optionbits_mask   = optionbits_mask
        s.size              = size
        s.operation         = operation
        s.skip              = skip
        s.description       = description

    def match(s, opcode):

        if ((opcode & s.opcode_mask) == s.opcode):
            # Match
            return True
        else:
            # No match
            return False
    
    def get_data(s, opcode):
        # Invert the opcode mask and retrieve user bits from it
        return opcode & (~s.opcode_mask & 0xFF)

    def get_next_data(s, opcode):
        # Invert the opcode mask and retrieve user bits from it
        return opcode & s.optionbits_mask

def add_instruction(name, opcode, opcode_mask, optionbits_mask, size, operation, skip, description):
    instructions.append(InstructionDefinition(name, opcode, opcode_mask, optionbits_mask, size, operation, skip, description))

add_instruction("CLA",0b10010000,0b11111111,0,1,"Acc ← 0","","")
add_instruction("CLC",0b00001011,0b11111111,0,1,"C ← 0","","")
add_instruction("CMA",0b00010000,0b11111111,0,1,"Acc ← ~(Acc)","","")
add_instruction("CIA",0b00010001,0b11111111,0,1,"Acc ← ~(Acc) + 1","","")
add_instruction("INC",0b00001101,0b11111111,0,1,"Acc ← (Acc) + 1, skip if carry","Carry","")
add_instruction("DEC",0b00001111,0b11111111,0,1,"Acc ← (Acc) - 1, skip if borrow","Borrow","")
add_instruction("STC",0b00011011,0b11111111,0,1,"C ← 1","","")
add_instruction("XC",0b00011010,0b11111111,0,1,"(C)↔ (C’)","","")
add_instruction("RAR",0b00110000,0b11111111,0,1,"(C ) → Acc3, (Accn) → (Accn-1), Acca → C","","4-bits in Acc rotate one bit right through the carry bit")
add_instruction("INM",0b00011101,0b11111111,0,1,"[(DP)] ← [(DP)] + 1; skip if [(DP)] = 0","[(DP)] = 0","increments 4-bit data in ram and skips if wraps around to 0")
add_instruction("DEM",0b00011111,0b11111111,0,1,"[(DP)] ← [(DP)] - 1; skip if [(DP)] = F","[(DP)] = F","decrements 4-bit data in ram and skips if wraps around to F")
add_instruction("AD",0b00001000,0b11111111,0,1,"Acc ← (acc) + [(DP]), skip on carry","Carry","")
add_instruction("ADS",0b00001001,0b11111111,0,1,"Acc, C ← (Acc) + [(DP)] + (C )","Carry","")
add_instruction("ADC",0b00011001,0b11111111,0,1,"Acc, C ← (Acc) + [(DP)] + (C )","","")
add_instruction("DAA",0b00000110,0b11111111,0,1,"Acc ← (Acc) + 6","","")
add_instruction("DAS",0b00001010,0b11111111,0,1,"Acc ← (Acc) + 10","","")
add_instruction("EXL",0b00011000,0b11111111,0,1,"Acc ← (Acc) OR ([DP])","","")
add_instruction("LI",0b10010000,0b11110000,0,1,"Acc ←  I3I2I1I0","","")
add_instruction("S",0b00000010,0b11111111,0,1,"[(DP)] ← Acc","","")
add_instruction("L",0b00111000,0b11111111,0,1,"Acc ←  [(DP)]","","")
add_instruction("LM",0b00111000,0b11111100,0,1,"Acc ←  [(DP)] ; DPh ← (DPh) OR M1M0","","")
add_instruction("X",0b00101000,0b11111111,0,1,"(Acc) ↔ [(DP)]","","")
add_instruction("XM",0b00101000,0b11111100,0,1,"(Acc) ↔ [(DP)] ; DPh ← (DPh) OR M1M0","","")
add_instruction("XD",0b00101100,0b11111111,0,1,"(Acc) ↔ [(DP)] ; DPl ← (DPl) – 1 ; skip if DPl = F","DPl = F","")
add_instruction("XMD",0b00101100,0b11111100,0,1,"(Acc) ↔ [(DP)] ; DPh ← (DPh) OR M1M0 ; DPl ← (DPl) – 1 ; skip if DPl = F","DPl = F","")
add_instruction("XI",0b00111100,0b11111111,0,1,"(Acc) ↔ [(DP)] ; DPl ← (DPl) + 1 ; skip if DPl = F","","")
add_instruction("XMI",0b00111100,0b11111100,0,1,"(Acc) ↔ [(DP)] ; DPh ← (DPh) OR M1M0 ; DPl ← (DPl) + 1 ; skip if DPl = F","","")
add_instruction("LDI",0b00010101,0b11111111,0b01111111,2,"DP ← I6 … I0","","")
add_instruction("LDZ",0b10000000,0b11110000,0,1,"DPh ← 0 ; DPl ← I3I2I1I0","","")
add_instruction("DED",0b00010011,0b11111111,0,1,"DPl ← (DPl) – 1 ; skip if (DPl) = F","(DPl) = F","")
add_instruction("IND",0b00110011,0b11111111,0,1,"DPl ← (DPl) + 1 ; skip if (DPl) = 0","(DPl) = 0","")
add_instruction("TAL",0b00000111,0b11111111,0,1,"DPl ← (Acc)","","")
add_instruction("TLA",0b00010010,0b11111111,0,1,"Acc ← (DPl)","","")
add_instruction("XHX",0b01001111,0b11111111,0,1,"(DPh) ↔ X","","")
add_instruction("XLY",0b01001110,0b11111111,0,1,"(DPh) ↔ Y","","")
add_instruction("THX",0b01000111,0b11111111,0,1,"(DPlh → X","","")
add_instruction("TLY",0b01000110,0b11111111,0,1,"(DPl) → Y","","")
add_instruction("XAZ",0b01001010,0b11111111,0,1,"(Acc) ↔ Z","","")
add_instruction("XAW",0b01001011,0b11111111,0,1,"(Acc) ↔ W","","")
add_instruction("TAZ",0b01000010,0b11111111,0,1,"(Acc) → (Z)","","")
add_instruction("TAW",0b01000011,0b11111111,0,1,"(Acc) → (W)","","")
add_instruction("XHR",0b01001101,0b11111111,0,1,"(DPh) ↔ (R )","","")
add_instruction("XLS",0b01001100,0b11111111,0,1,"(DPl) ↔ (S)","","")
add_instruction("SMB",0b01111000,0b11111100,0,1,"[DP, B1B0)] ← 1","","")
add_instruction("RMB",0b01101000,0b11111100,0,1,"[DP, B1B0)] ← 0","","")
add_instruction("TMB",0b01011000,0b11111100,0,1,"skip if [(DP, B1B0)] = 1","[(DP, B1B0)] = 1","")
add_instruction("TAB",0b00100100,0b11111100,0,1,"skip if [(Acc, B1B0)] = 1","[(Acc, B1B0)] = 1","")
add_instruction("CMB",0b00110100,0b11111100,0,1,"skip if [(Acc, B1B0)] = [(DP, B1B0)]","[(Acc, B1B0)] = [(DP, B1B0)]","")
add_instruction("SFB",0b01111100,0b11111100,0,1,"[FLAG, B1B0)] ← 1","","")
add_instruction("RFB",0b01101100,0b11111100,0,1,"[FLAG, B1B0)] ← 0","","")
add_instruction("FBT",0b01011100,0b11111100,0,1,"skip if [(FLAG, B1B0)] = 1","[(FLAG, B1B0)] = 1","")
add_instruction("FBF",0b00100000,0b11111100,0,1,"skip if [(FLAG, B1B0)] = 0","[(FLAG, B1B0)] = 0","")
add_instruction("CM",0b00001100,0b11111111,0,1,"skip if (Acc) = [(DP)]","(Acc) = [(DP)]","")
add_instruction("CI",0b00010111,0b11111111,0b00001111,2,"skip if (Acc) = I3I2I1I0","(Acc) = I3I2I1I0","")
add_instruction("CLI",0b00010110,0b11111111,0b00001111,2,"skip if (DPl) = I3I2I1I0","(DPl) = I3I2I1I0","")
add_instruction("TC",0b00000100,0b11111111,0,1,"skip if (C ) = 1","(C ) = 1","")
add_instruction("TTM",0b00000101,0b11111111,0,1,"skip if (TM F/F) = 1","(TM F/F) = 1","")
add_instruction("TIT",0b00000011,0b11111111,0,1,"skip if (INT F/F) = 1 ; INT F/F ← 0","(INT F/F) = 1","")
add_instruction("JCP",0b11000000,0b11000000,0,1,"PC ← p5 … p0","","")
add_instruction("JMP",0b10100000,0b11111000,0b11111111,2,"PC ← P10 … P0","","")
add_instruction("JPA",0b01000001,0b11111111,0,1,"PC ← A3A2A1A000","","")
add_instruction("EI",0b00110001,0b11111111,0,1,"INTE F/F ← 1","","")
add_instruction("DI",0b00000001,0b11111111,0,1,"INTE F/F ← 0","","")
add_instruction("CZP",0b10110000,0b11110000,0,1,"(PC) → STACK ; PC ← 00000P3P2P1P000","","")
add_instruction("CAL",0b10101000,0b11111000,0b11111111,2,"(PC) → STACK ; PC ← P10...P0","","")
add_instruction("RT",0b01001000,0b11111111,0,1,"PC ← (STACK)","","")
add_instruction("RTS",0b01001001,0b11111111,0,1,"PC ← (STACK) ; PC ← (PC) + 1 (, 2 maybe a jump can be skipped??)","","")
add_instruction("SEB",0b01110100,0b11111100,0,1,"PORT E (B1B0) ← 1","","")
add_instruction("REB",0b01100100,0b11111100,0,1,"PORT E (B1B0) ← 0","","")
add_instruction("SPB",0b01110000,0b11111100,0,1,"PORT (DPl, B1B0) ← 1","","")
add_instruction("RPB",0b01100000,0b11111100,0,1,"PORT (DPl, B1B0) ← 0","","")
add_instruction("TPA",0b01010100,0b11111100,0,1,"skip if (PORTA(B1B0) = 1","(PORTA(B1B0) = 1","")
add_instruction("TPB",0b01010000,0b11111100,0,1,"skip if (PORT(DPl, B1B0) = 1","(PORT(DPl, B1B0) = 1","")
add_instruction("OE",0b01000100,0b11111111,0,1,"PORT E ← (Acc)","","")
add_instruction("OP",0b00001110,0b11111111,0,1,"PORT (DPl) ← (Acc)","","")
add_instruction("OCD",0b00011110,0b11111111,0b11111111,2,"PORT C,D ← I7...I0","","")
add_instruction("IA",0b01000000,0b11111111,0,1,"(PORT A) → Acc","","")
add_instruction("IP",0b00110010,0b11111111,0,1,"(PORT (DPl)) → Acc","","")
add_instruction("STM",0b00010100,0b11111111,0b00111111,2,"TMF/F ← 0 ; TIMER ← I5...I0","","")
add_instruction("NOP",0b00000000,0b11111111,0,1,"No operation","","")

bin_content = input_file_handle.read()

i = 0
while i < len(bin_content):

    opcode      = ord(bin_content[i])
    if (i != len(bin_content) - 1):
        # Only fetch next instruction if possible
        opcode_next = ord(bin_content[i+1])

    # Write address of instruction
    output_file_handle.write("%04X:    " % i)

    # Decode instruction
    DecodedInstructionData = Instruction()
    DecodedInstructionData.decode(opcode, opcode_next)
    # Get the information on decoded instruction
    DecodedInstruction     = DecodedInstructionData.get_instruction()

    # Write content of instruction (1 or 2 bytes long)
    if (DecodedInstruction.size == 2):
        output_file_handle.write("%02X %02X" % (opcode, opcode_next))
    else:
        output_file_handle.write("%02X   " % opcode)

    if (DecodedInstruction == None):
        # Invalid instruction encountered
        print "Failed to decode instruction."
        output_file_handle.write("    Unknown instruction: %02x   " % (opcode))
    else:
        output_file_handle.write("      %s" % (str(DecodedInstructionData)))
    
    output_file_handle.write("\r\n")

    # Advance the program counter by the size of the instruction
    i += DecodedInstruction.size
