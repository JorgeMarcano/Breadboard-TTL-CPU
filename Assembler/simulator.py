'''
CPU Emulator
'''

import os
import sys
import argparse
from collections import namedtuple
import assembler as asm
import cmd

SRC_MICROCODE = r'..\Microcode\microcode.h'

class CmdLine(cmd.Cmd):
    intro = 'Type help or ? to list commands.\n'
    prompt = '-> '

    # Avoid repeating last commands
    # def emptyline(self):
        # pass

    def preloop(self):
        # Get base folder
        print()
        print('Entering interactive mode')
        self.print_all_help()

    # def precmd(self, line):
        # print()
        # return line

    def postcmd(self, stop, line):
        print()
        # self.print_all_help()
        # print()
        # return stop

    def print_all_help(self):
        # Print help for all commands. Inspired from cmd.py :-)
        names = self.get_names()
        cmds_doc = []
        cmds_undoc = []
        help = {}
        names.sort()
        # There can be duplicates if routines overridden
        prevname = ''
        for name in names:
            if name[:3] == 'do_':
                if name == prevname:
                    continue
                prevname = name
                cmd=name[3:]
                if cmd not in ('exit','help'):
                    print(cmd + ': ', end = '')
                    self.do_help(cmd)

    # ----- commands -----
    def do_print(self, arg):
        'Print CPU Status'
        cpu.print_cpu()

    def do_exit(self, arg):
        'Exit simulator'
        sys.exit()

    def do_load(self, arg):
        'Load a program into CPU'
        infile = input('Name of input file? ')
        offset = input('Memory offset? [0000] ')
        if not offset:
            offset = '0000'
        program = asm.translate_file(infile, offset, True, False)
        #print(asm.INST_SET)
        #print(program)
        cpu.load_rom(program)

    def do_run(self, arg):
        'Run CPU'
        print('Before CPU state')
        cpu.print_cpu()
        cpu.exec_prog()
        print('Final CPU state')
        cpu.print_cpu()

    def do_step(self, arg):
        'Run one instruction'
        # print('Before CPU state')
        # cpu.print_cpu()
        cpu.exec_one()
        print('After CPU state')
        cpu.print_cpu()

    def do_reset(self, arg):
        'Reset CPU'
        cpu.reset()

class Cpu():
    'CPU Simulator'

    DEFAULT_ROM = 'ff'
    DEFAULT_RAM = 'ff'

    def __init__(self, microcode=None, debug=False):
        self.debug = debug
        self.microcode = microcode
        self.reset()

    def reset(self):
        self.reg_a = '00'
        self.reg_b = '00'
        self.reg_c = '00'
        self.reg_d = '00'
        self.reg_o = '00'
        self.bus = ''
        self.ram_low = '00'
        self.ram_high = '00'
        self.ram_ptr = 0
        self.ram = {}
        self.pc_low = '00'
        self.pc_high = '00'
        self.pc_ptr = 0
        self.rom = {}
        self.carry_flag = False
        self.equal_flag = False
        self.halted = False

    def program_cpu(self, microcode):
        self.microcode = microcode

    def split_code(self, code):
        btc = ''
        ctb = ''
        if '&' in code:
            ctb, btc = code.split('&')
            ctb = ctb.strip()
            btc = btc.strip()
        else:
            ctb = code.strip()
        return ctb, btc

    def chip_to_bus(self, code):
        ctb, btc = self.split_code(code)
        if ctb == 'AO':  # A out
            self.bus = self.reg_a
        elif ctb == 'BO':  # B out
            self.bus = self.reg_b
        elif ctb == 'CO':  # C out
            self.bus = self.reg_c
        elif ctb == 'DO':  # D out
            self.bus = self.reg_d
        elif ctb == 'RO':  # Ram out
            self.bus = self.get_ram()
        elif ctb == 'PO':  # Program ROM out
            self.bus = self.get_rom()
        elif ctb == 'ADD': # ALU Add out
            self.bus = self.get_alu('ADD')
        elif ctb == 'SUB': # ALU Sub out
            self.bus = self.get_alu('SUB')
        elif ctb == 'NAO': # ALU Nand out
            self.bus = self.get_alu('NAND')
        elif ctb == 'DEC': # ALU Decrement out
            self.bus = self.get_alu('DEC')
        elif ctb == 'INC': # ALU Increment out
            self.bus = self.get_alu('INC')

        # Other instructions given as chip to bus but don't write to bus
        elif ctb == 'CLR': # Clear microinstruction counter
            self.reset_mic()
        elif ctb == 'PIN': # Program Counter Increment
            self.pc_inc()
        elif ctb == 'HLT': # Halt
            self.halt()
        elif ctb == 'NOP': # No operation
            pass

    def bus_to_chip(self, code):
        ctb, btc = self.split_code(code)
        if btc == 'AI':  # A clk
            self.reg_a = self.bus
        elif btc == 'BI':  # B clk
            self.reg_b = self.bus
        elif btc == 'CI':  # C clk
            self.reg_c = self.bus
        elif btc == 'DI':  # D clk
            self.reg_d = self.bus
        elif btc == 'RI':  # Ram Write
            self.set_ram(self.bus)
        elif btc == 'OI':  # Output Reg clk
            self.reg_o = self.bus
            if not self.debug:
                print('Output=', self.reg_o, '(', int(self.reg_o, 16), ')')
        elif btc == 'RLI': # Ram Low Addr clk
            self.set_ram_addr(self.bus, 'LOW')
        elif btc == 'RHI': # Ram High Addr clk
            self.set_ram_addr(self.bus, 'HIGH')
        elif btc == 'PLI': # Program Counter Low clk
            self.set_pc(self.bus, 'LOW')
        elif btc == 'PHI': # Program Counter High clk
            self.set_pc(self.bus, 'HIGH')
        elif btc == 'II': # Instruction Code Reg clk
            pass

        # Other instructions given as bus to chip
        elif btc == 'FI': # Set Flags
            # Set equal flag depending on result in bus
            if self.bus == 'ff':
                self.equal_flag = True
            else:
                self.equal_flag = False
            # Set carry flag depending on operation and reg_a and reg_b
            val_a = int(self.reg_a, 16)
            val_b = int(self.reg_b, 16)
            if ctb == 'ADD':
                self.carry_flag = (val_a + val_b) > 255
            elif ctb == 'SUB':
                self.carry_flag = val_a >= val_b
            elif ctb == 'INC': # ALU Decrement out
                self.bus = (val_a + 1) > 255
            elif ctb == 'DEC':
                self.carry_flag = val_a >= 1
            else:
                self.carry_flag = False

    def get_current_microcode(self):
        pass

    def get_ram(self):
        if self.ram_ptr in self.ram:
            return self.ram[self.ram_ptr]
        else:
            return self.DEFAULT_RAM

    def set_ram(self, value):
        self.ram[self.ram_ptr] = value

    def set_ram_addr(self, value, pos):
        if pos == 'LOW':
            self.ram_low = value
        elif pos == 'HIGH':
            self.ram_high = value
        self.ram_ptr = int(self.ram_high, 16) * 256 + int(self.ram_low, 16)

    def get_rom(self):
        if self.pc_ptr in self.rom:
            return self.rom[self.pc_ptr]
        else:
            return self.DEFAULT_ROM

    def burn_rom(self, address, value):
        self.rom[address] = value

    def set_pc(self, value, pos):
        if pos == 'LOW':
            self.pc_low = value
        elif pos == 'HIGH':
            self.pc_high = value
        self.pc_ptr = int(self.pc_high, 16) * 256 + int(self.pc_low, 16)

    def get_alu(self, oper):
        val_a = int(self.reg_a, 16)
        val_b = int(self.reg_b, 16)
        if oper == 'ADD':
            res = self.dec_to_hex((val_a + val_b) % 256)
        elif oper == 'SUB':
            res = self.dec_to_hex((val_a - val_b) % 256)
        elif oper == 'NAND':
            # TODO
            res = self.reg_a
        elif oper == 'DEC':
            res = self.dec_to_hex((val_a - 1) % 256)
        elif oper == 'INC':
            res = self.dec_to_hex((val_a + 1) % 256)
        return res

    def dec_to_hex(self, value):
        res = hex(value)[2:]
        if value < 16:
            res = '0'+ res
        return res

    def pc_inc(self):
        value_low = int(self.pc_low, 16)
        value_hi = int(self.pc_high, 16)
        value_low = value_low + 1
        if value_low == 256:
            value_low = 0
            value_hi = value_hi + 1
        self.pc_low = hex(value_low)[2:]
        self.pc_high = hex(value_hi)[2:]
        self.pc_ptr = int(self.pc_high, 16) * 256 + int(self.pc_low, 16)

    def load_rom(self, program):
        for address in program:
            prog_bytes = [program[address][i:i+2] for i in range(0, len(program[address]), 2)]
            self.load_code(address, prog_bytes)

    def load_code(self, address, code):
        cur_addr = address
        for index in range(len(code)):
            self.burn_rom(address + index, code[index])

    def exec_instr(self):
        # Retrieve instruction pointed by pc_ptr
        instr = self.get_rom()
        if self.debug:
            print('Instruction=', instr)
        if instr == 'ff':
            return False
        # Get respective microcode
        code = self.get_microcode(instr)
        # Put the common code in front
        code = ['PO & II', 'PIN'] + code
        if self.debug:
            print('Code=', code)
        # Execute all microcode
        for item in code:
            self.chip_to_bus(item)
            self.bus_to_chip(item)
        return True

    def get_microcode(self, instr):
        if not self.carry_flag and not self.equal_flag:
            return self.microcode['base'][instr]
        if self.carry_flag and not self.equal_flag:
            return self.microcode['flaggedCarry'][instr]
        if not self.carry_flag and self.equal_flag:
            return self.microcode['flaggedEqual'][instr]
        if self.carry_flag and self.equal_flag:
            return self.microcode['flaggedBoth'][instr]

    def exec_prog(self):
        print('Starting execution of program')
        while not self.halted:
            self.exec_one()

    def exec_one(self):
        ret = self.exec_instr()
        if not ret:
            self.halt()
        if self.debug:
            self.print_cpu()


    def halt(self):
        self.halted = True

    def print_cpu(self):
        print('================================')
        print('Halted?', self.halted)
        print('Reg A=', self.reg_a, '(', int(self.reg_a, 16), ')  Reg B=', self.reg_b, '(', int(self.reg_b, 16), ')')
        print('Reg C=', self.reg_c, '(', int(self.reg_c, 16), ')  Reg D=', self.reg_d, '(', int(self.reg_d, 16), ')')
        print('Output Reg=', self.reg_o, '(', int(self.reg_o, 16), ')')
        print('Bus data=', self.bus, '(', int(self.reg_o, 16), ')')
        print('Carry and Equal flags=', self.carry_flag, ',', self.equal_flag)
        print('RAM Addr=', self.ram_ptr, '(', self.ram_high, self.ram_low, ') ->', self.get_ram())
        print('RAM')
        print(self.ram)
        print('PC Addr=', self.pc_ptr, '(', self.pc_high, self.pc_low, ') ->', self.get_rom(), '=', asm.get_instr_from_code(self.get_rom()))
        print('ROM')
        print(self.rom)
        print('================================')

def read_args():
    parser = argparse.ArgumentParser(formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument('infile', nargs='?', type=str, default=None, help='Text file with assembler program')
    parser.add_argument('-b', '--base', type=str, help='Specify starting address for assembler', default='0x0000', dest='offset')
    parser.add_argument('-d', '--debug', action='store_true', help='Print debug information')
    parser.add_argument('-i', '--interactive', action='store_true', help='Show prompt for interactive run')
    return parser.parse_args()

def read_microcode(file_name, debug=False):
    try:
        with open(file_name, 'r') as input_file:
            lines = [line.strip() for line in input_file]
            if debug:
                print('Read', len(lines), 'lines from file', file_name)
    except IOError:
        print('Cannot open file', file_name)
        return False
    # Process lines to obtain microcode
    all_code = {}
    code_list = []
    version = ''
    for line in lines:
        # Discard comments //...
        code = line.split('//')[0].strip()
        if code:
            # If line starts with 'Code' the it is a version start
            if code.startswith('Code'):
                version = code[5:].split('[')[0].strip()
                all_code[version] = []
            # If this is microcode line it will contain '(byte[])'
            elif '(byte[])' in code:
                all_code[version].append(code)
            # If not, but ends with a closing, then append to previous line
            elif code.endswith('}},'):
                all_code[version][-1] = all_code[version][-1] + code
    if debug:
        print('Read', len(all_code), 'microcode versions')
    # Set up the return dictionary
    microcode = {}
    for version in all_code:
        microcode[version] = {}
        for item in all_code[version]:
            #print(item)
            code = item[3:5]
            seq = [x.strip() for x in item.split('{')[-1].split('}')[0].split(',')]
            microcode[version][code] = seq
    # Add base version code to the other three versions
    if debug:
        for version in microcode:
            for code in microcode[version]:
                print(version, code, microcode[version][code])
    for code in microcode['base']:
        if code not in microcode['flaggedCarry']:
            microcode['flaggedCarry'][code] = microcode['base'][code]
        if code not in microcode['flaggedEqual']:
            microcode['flaggedEqual'][code] = microcode['base'][code]
        if code not in microcode['flaggedBoth']:
            microcode['flaggedBoth'][code] = microcode['base'][code]
    if debug:
        for version in microcode:
            for code in microcode[version]:
                print(version, code, microcode[version][code])
    return microcode

if __name__ == '__main__':
    print('Microprocessor simulator. Version 0.1')

    # Read command line arguments
    args = read_args()
    #print(args)

    # Read microcode definitions
    microcode = read_microcode(SRC_MICROCODE, args.debug)
    cpu = Cpu(microcode, args.debug)

    # Get the intput file name
    if args.infile:
        infile = args.infile
    elif not args.interactive:
        infile = input('Name of input file? ')

    # Read program to execute
    asm.label_mgr.set_debug(args.debug)
    if args.interactive:
        if args.infile:
            program = asm.translate_file(infile, args.offset, False, args.debug)
            cpu.load_rom(program)
        print('Initial CPU state')
        cpu.print_cpu()
        CmdLine().cmdloop()
    else:
        program = asm.translate_file(infile, args.offset, False, args.debug)
        #print(asm.INST_SET)
        #print(program)
        cpu.load_rom(program)
        print('Initial CPU state')
        cpu.print_cpu()
        cpu.exec_prog()
        print('Final CPU state')
        cpu.print_cpu()

