import serial
import sys
import time
import copy

DEBUGGING_VERBOSE = 0

port = serial.Serial("/dev/ttyUSB0", baudrate=115200, timeout=10.0)

class JMP:
    
    def __init__(s):
        
        s.address = 0
        s.offset  = 0
        s.state   = 0
        s.found_in_field = 0
        s.has_nop_after_jmp = False

    def is_jump(s, opcode, found_in_field):

        if s.state == 2:
            # Consecutive call to this method, resets JMP detection state
            s.state = 0
            s.has_nop_after_jmp = False

        if (((opcode & 0xF8) & 0xFF) == 0xA0):
            s.address = (opcode & 0x7) & 0xFF
            s.found_in_field = copy.copy(found_in_field)
            s.state = 1
        elif s.state == 1:
            s.offset = opcode
            s.state = 2
        else:
            s.state = 0

        return s.state
    
    def check_if_NOP_next(s, opcode):
        
        if (s.state == 2):
            if (opcode == 0):
                s.has_nop_after_jmp = True
    
    def __str__(s):

        output_buffer = "JMP to 0x%01X%02X (found at 0x%01X%02X). Has NOP? %d" % (s.address, s.offset, s.found_in_field.address, s.found_in_field.offset, s.has_nop_after_jmp)
        return output_buffer

class Field:

    ROM_FIELD_BYTES = 256

    def __init__(s):
        
        s.address = 0
        s.offset  = 0
        s.data = [0xFF] * s.ROM_FIELD_BYTES
        s.done = False
        s.jumps = []
        
    def __str__(s):
        
        outputBuffer = ""
        formatter = 0

        outputBuffer += "field: %d (complete %d)\n" % (s.address, s.done)
        

        for i in xrange(0, s.ROM_FIELD_BYTES):

            if ((i != 0) and ((i % 16) == 0)):
                outputBuffer += "\n"
            outputBuffer += "%02X " % s.data[i]
        
        return outputBuffer

field_dumped = [Field()] * 8

def dump_rom_print():
    
    for x in field_dumped:
        print str(x)

def dump_rom_to_bin_file(filename):

    f = open(filename, "wb")

    for x in field_dumped:
        print "dumping content of field %d to bin file..." % (x.address)
        [f.write(chr(byte)) for byte in x.data]

    f.close()

def reset():

    port.reset_input_buffer()   # discard all content now, before resetting the micro
    port.write('r') # reset the microcontroller
    if (port.read(1) != 'z'):
        print "WARNING: invalid boot character"

def enter_test_mode():
    if (DEBUGGING_VERBOSE): print "TESTMODE: ON"
    port.write('t')             # Enable TEST MODE

def exit_test_mode():
    if (DEBUGGING_VERBOSE): print "TESTMODE: OFF"
    port.write('u')             # Enable TEST MODE

def clock_cycle():
    port.write('s')             # Clock Cycle
    rcv = port.read(1)          # Read the incoming byte
    if (DEBUGGING_VERBOSE):
        # Invert the byte
        rcv = ((~ord(rcv)) & 0xFF)
        print "CLK RAW: %02X" % rcv

def clock_instructions(instruction, jump = False):

    if (DEBUGGING_VERBOSE): print "CLOCK INSTRUCTION: START"
    for x in xrange(0, instruction*4):
        clock_cycle()

    if (jump == True):
        time.sleep(0.001)
        exit_test_mode()
        time.sleep(0.001)
        clock_cycle()
        clock_cycle()
        clock_cycle()
        clock_cycle()
        clock_cycle()
        clock_cycle()
        clock_cycle()
        clock_cycle()
        time.sleep(0.001)
        enter_test_mode()
        time.sleep(0.001)
        clock_cycle()
        clock_cycle()
        clock_cycle()
        clock_cycle()
        # Consume the remaining leftover of the JMP instruction
        clock_cycle()
        clock_cycle()
        clock_cycle()
        clock_cycle()
    if (DEBUGGING_VERBOSE): print "CLOCK INSTRUCTION: END"

synched     = False;
    
def dump_rom(field = 0):

    global first_round          # The initial synch should be only necessary at the first round
    global synched              # The initial synch should be only necessary at the first round

    skip_counter = 0
    formatter = 0
    first_round = True
    
    currentField = Field()
    currentJMP   = JMP()
    
    currentField.address = field

    while 1:
        
        # Clock Cycle
        port.write('s')     # send synchronization byte
        # Read the instruction byte
        rcv = port.read(1)
        rcv = ord(rcv)

        # Invert the byte
        rcv = ((~rcv) & 0xFF)
        if (DEBUGGING_VERBOSE): print "RAW: %02X" % rcv

        if (rcv == 0x00 and synched == False):
            if (DEBUGGING_VERBOSE): print "synching", hex(rcv)
            skip_counter = 0
            pass
        else:
            if (DEBUGGING_VERBOSE): print "synched", hex(rcv)
            synched = True
            skip_counter+=1

            if (skip_counter >= 4):
                skip_counter = 0

                currentField.data[currentField.offset] = rcv;

                # Check if it is a JMP instruction
                currentJMP.check_if_NOP_next(rcv)
                if (currentJMP.has_nop_after_jmp == True):
                    currentField.jumps[-1].has_nop_after_jmp = True

                if (currentJMP.is_jump(rcv, currentField) == 2):
                    currentField.jumps.append(copy.copy(currentJMP))

                currentField.offset += 1
                
                if (currentField.offset >= Field.ROM_FIELD_BYTES):
                    currentField.done = True;

        sent_cmd = False
        
        if (currentField.done == True):
            field_dumped[currentField.address] = copy.copy(currentField)   # Save the dumped field apart
            print str(currentField)                             # Print it
            break

reset()                             # reset microcontroller and target microcontroller
JMPSelection = Field()              # start FIELD 0

dump_rom(JMPSelection.address)      # dump FIELD 0

AUTOMATIC_SEQUENCE_ID = 0
AUTOMATIC_SEQUENCE_NONE = []
AUTOMATIC_SEQUENCE_024 = [1, 2, 3, 1, 3, 6, 3, 2, 1, 5, 99]             # Unknown device
AUTOMATIC_SEQUENCE_200 = [1, 0, 1, 8, 2, 4, 7, 0, 99]                   # Sony TA-AX 44
AUTOMATIC_SEQUENCE_200_ALTERNATIVE = [9, 1, 8, 12, 4, 7, 0, 99]         # Alternative sequence used for verification
AUTOMATIC_SEQUENCE_TESTING_FIELD_200_0 = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]

AUTOMATIC_SEQUENCE = AUTOMATIC_SEQUENCE_024                        # Selected dumper sequence

while 1:

    selection = 0

    for x in field_dumped[JMPSelection.address].jumps:
        print "%d. %s" % (selection, str(x))
        selection+=1
    print "99. Abort dump, print dump and bin dump"

    infoStr = "Currently dumped fields: "
    for x in field_dumped:
        if x.done:
            infoStr += "%01X " % (x.address)
    print infoStr

    print "Enter selection:"

    if (AUTOMATIC_SEQUENCE_ID < len(AUTOMATIC_SEQUENCE)):
        # automatic sequence active, select using it
        selection = AUTOMATIC_SEQUENCE[AUTOMATIC_SEQUENCE_ID]
        AUTOMATIC_SEQUENCE_ID += 1
    else:
        # user selection
        selection = input()
    
    print "Selected: %d" % selection

    if (selection == 99):
        dump_rom_print()
        dump_rom_to_bin_file("D553C-ROM.bin")
        break;
    else:

        JMPSelection = field_dumped[JMPSelection.address].jumps[selection]

        print "Clocking to", str(JMPSelection)

        print JMPSelection.found_in_field.offset

        if (JMPSelection.found_in_field.offset >= 2):
            # Need to just count from start of field to offset
            instructions_to_jump = JMPSelection.found_in_field.offset - 2
        else:
            # Need to count up to the end minus the overflow (either 0, 1 or 2)
            instructions_to_jump = 256 - JMPSelection.found_in_field.offset

        clock_instructions(instructions_to_jump, True)     # Clock up to the JMP instruction and finally run it

        clock_instructions(256 - JMPSelection.offset)      # synch with the start of the field

        dump_rom(JMPSelection.address)                     # dump the currently selected page
