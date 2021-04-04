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

    def do_debug(self, arg):
        'Set CPU instruction debug flag (true, false)'
        option = arg.lower()
        if option == 'true':
            cpu.set_debug(True)
        elif option == 'false':
            cpu.set_debug(False)
        else:
            print('Invalid option "' + arg + '"')

    def do_mcdebug(self, arg):
        'Set CPU microcode debug flag (true, false)'
        option = arg.lower()
        if option in ('true', 'on'):
            cpu.set_mc_debug(True)
        elif option in ('false', 'off'):
            cpu.set_mc_debug(False)
        else:
            print('Invalid option "' + arg + '"')

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
        'Run CPU program in ROM'
        print('Before CPU state')
        cpu.print_cpu()
        try:
            cpu.exec_prog()
        except KeyboardInterrupt:
            print('Interrupted...')
        print()
        print('Final CPU state')
        cpu.print_cpu()

    def do_step(self, arg):
        'Run one instruction'
        cpu.exec_one_instr()
        print()
        print('After CPU state')
        cpu.print_cpu()

    def do_mstep(self, arg):
        'Run one micro instruction'
        cpu.exec_one_microinstr()
        print()
        print('After CPU state')
        cpu.print_mcode_status()

    def do_reset(self, arg):
        'Reset CPU'
        cpu.reset()

class Cpu():
    'CPU Simulator'

    DEFAULT_ROM = 'ff'
    DEFAULT_RAM = 'ff'
    NO_OP_MAX = 10

    def __init__(self, microcode=None, debug=False, mc_debug=False):
        self.microcode = microcode
        self.debug = debug
        self.mc_debug = mc_debug
        self.rom = {}
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
        self.carry_flag = False
        self.equal_flag = False
        self.halted = False
        self.init_microcode()
        self.no_op_count = 0

    def init_microcode(self):
        self.mic = 0
        self.set_current_mcode(self.get_rom())

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
        self.init_microcode()

    def load_code(self, address, code):
        cur_addr = address
        for index in range(len(code)):
            self.burn_rom(address + index, code[index])

    # def exec_instr(self):
        # Execute all microcode
        # while self.exec_one_microinstr():
            # pass

    def exec_one_microinstr(self):
        if self.mc_debug:
            self.print_mcode_status()
        if self.mic < len(self.cur_mcode):
            self.chip_to_bus(self.cur_mcode[self.mic])
            self.bus_to_chip(self.cur_mcode[self.mic])
            self.mic = self.mic + 1
            return True
        else:
            # Current microcode is not done:
            # - Retrieve instruction pointed by pc_ptr
            # - Reset mic
            instr = self.get_rom()
            if self.debug:
                print('Loading instruction=', instr, '=', asm.get_instr_from_code(self.get_rom()))
            # Fuse to avoid infinite loops
            if instr == 'ff':
                self.no_op_count = self.no_op_count + 1
                if self.no_op_count > self.NO_OP_MAX:
                    self.halt()
                    print('Executed more that', self.NO_OP_MAX, 'NOP instructions, halting...')
            else:
                self.no_op_count = 0
            # Initialize current microcode
            self.set_current_mcode(instr)
            return False

    def set_current_mcode(self, instr):
        self.cur_mcode = self.get_microcode(instr)
        if self.mc_debug:
            print('Setting mCode=', self.cur_mcode)
        self.mic = 0

    def get_microcode(self, instr):
        if not self.carry_flag and not self.equal_flag:
            version = 'base'
        if self.carry_flag and not self.equal_flag:
            version = 'flaggedCarry'
        if not self.carry_flag and self.equal_flag:
            version = 'flaggedEqual'
        if self.carry_flag and self.equal_flag:
            version = 'flaggedBoth'
        return self.microcode[version][instr]

    def exec_prog(self):
        print('Starting execution of program')
        # Run instructions until halted
        while not self.halted:
            self.exec_one_instr()

    def exec_one_instr(self):
        while self.exec_one_microinstr():
            pass
        if self.debug:
            self.print_cpu()

    def halt(self):
        self.halted = True

    def set_debug(self, option):
        self.debug = option
    
    def set_mc_debug(self, option):
        self.mc_debug = option

    def print_mcode_status(self):
        print('--------------------------------')
        print('Microinstr ctr =', self.mic, 'Done =', self.mic >= len(self.cur_mcode))
        print('Current mcode =', list(enumerate(self.cur_mcode)))

    def print_regs_flags(self):
        print('--------------------------------')
        print('Reg A=', self.reg_a, '(', int(self.reg_a, 16), ')  Reg B=', self.reg_b, '(', int(self.reg_b, 16), ')')
        print('Reg C=', self.reg_c, '(', int(self.reg_c, 16), ')  Reg D=', self.reg_d, '(', int(self.reg_d, 16), ')')
        print('Output Reg=', self.reg_o, '(', int(self.reg_o, 16), ')')
        print('Bus data=', self.bus, '(', int(self.reg_o, 16), ')')
        print('Carry and Equal flags=', self.carry_flag, ',', self.equal_flag)

    def print_ram(self):
        print('--------------------------------')
        print('RAM Addr=', self.ram_ptr, '(', self.ram_high, self.ram_low, ') ->', self.get_ram())
        print('RAM')
        print(self.ram)

    def print_rom(self):
        print('--------------------------------')
        print('PC Addr=', self.pc_ptr, '(', self.pc_high, self.pc_low, ') ->', self.get_rom(), '=', asm.get_instr_from_code(self.get_rom()))
        print('ROM')
        print(self.rom)

    def print_cpu(self):
        print('================================')
        print('Halted?', self.halted)
        self.print_regs_flags()
        self.print_ram()
        self.print_rom()
        self.print_mcode_status()
        print('================================')

def read_args():
    parser = argparse.ArgumentParser(formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument('infile', nargs='?', type=str, default=None, help='Text file with assembler program')
    parser.add_argument('-b', '--base', type=str, help='Specify starting address for assembler', default='0x0000', dest='offset')
    parser.add_argument('-d', '--debug', action='store_true', help='Print debug information')
    parser.add_argument('-m', '--mcode-debug', action='store_true', help='Print microcode debug information')
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
    read_common = False
    for line in lines:
        # Discard comments //...
        code = line.split('//')[0].strip()
        if code:
            # If line contains startCode then the next line is the common microcode
            if 'startCode' in code:
                read_common = True
                continue
            if read_common:
                common = [x.strip() for x in code.split(',')]
                read_common = False
                continue
            # If line starts with 'Code' then it is the start of a new version
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
            seq = common + [x.strip() for x in item.split('{')[-1].split('}')[0].split(',')]
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
    cpu = Cpu(microcode, args.debug, args.mcode_debug)

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

