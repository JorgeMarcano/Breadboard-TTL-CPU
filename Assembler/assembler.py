import os
import sys
import argparse
from collections import namedtuple

# Separators
COMMENT_SEP = ';'
LABEL_SEP = ':'
SPEC_CMD_CHAR = '@'

# Special commands

ALIAS_DEF = 'ALIAS'
BASE_ADDR = 'BASEADDR'
INC_FILE = 'INCLUDE'

# Instruction set
INST_SET = {'ADD': {'code': '00', 'params': [], 'descr': 'Set A = A + B'},
            'SUB': {'code': '01', 'params': [], 'descr': 'Set A = A - B'},
            'NAND': {'code': '02', 'params': [], 'descr': 'Set A = A NAND B'},
            'DEC': {'code': '03', 'params': [], 'descr': 'Decrement A'},
            'INC': {'code': '04', 'params': [], 'descr': 'Increment A'},
            'ADI': {'code': '05', 'params': ['value'], 'descr': 'Set A = A + value'},
            'SUI': {'code': '06', 'params': ['value'], 'descr': 'Set A = A - value'},
            'NANDI': {'code': '07', 'params': ['value'], 'descr': 'Set A = A NAND value'},
            'OR': {'code': '08', 'params': [], 'descr': 'Set A = A OR B'},
            'NOT': {'code': '09', 'params': [], 'descr': 'Set A = NOT A'},

            'LDA': {'code': '10', 'params': ['value'], 'descr': 'Load from program ROM in A'},
            'LDB': {'code': '11', 'params': ['value'], 'descr': 'Load from program ROM in B'},
            'LDC': {'code': '12', 'params': ['value'], 'descr': 'Load from program ROM in C'},
            'LDD': {'code': '13', 'params': ['value'], 'descr': 'Load from program ROM in D'},
            'LDO': {'code': '14', 'params': ['value'], 'descr': 'Load from program ROM in Output'},

            'STA': {'code': '20', 'params': ['addr'], 'descr': 'Store A in RAM'},
            'STB': {'code': '21', 'params': ['addr'], 'descr': 'Store B in RAM'},
            'STC': {'code': '22', 'params': ['addr'], 'descr': 'Store C in RAM'},
            'STD': {'code': '23', 'params': ['addr'], 'descr': 'Store D in RAM'},
            'STR': {'code': '24', 'params': ['addr', 'addr'], 'descr': 'Store RAM in RAM'},
            'STI': {'code': '25', 'params': ['value', 'addr'], 'descr': 'Store value in RAM'},

            'LRA': {'code': '30', 'params': ['addr'], 'descr': 'Load RAM in A'},
            'LRB': {'code': '31', 'params': ['addr'], 'descr': 'Load RAM in B'},
            'LRC': {'code': '32', 'params': ['addr'], 'descr': 'Load RAM in C'},
            'LRD': {'code': '33', 'params': ['addr'], 'descr': 'Load RAM in D'},
            'LRO': {'code': '34', 'params': ['addr'], 'descr': 'Load RAM in Output'},

            'MAB': {'code': '40', 'params': [], 'descr': 'Move A to B'},
            'MAC': {'code': '41', 'params': [], 'descr': 'Move A to C'},
            'MBA': {'code': '42', 'params': [], 'descr': 'Move B to A'},
            'MBC': {'code': '43', 'params': [], 'descr': 'Move B to C'},
            'MCA': {'code': '44', 'params': [], 'descr': 'Move C to A'},
            'MCB': {'code': '45', 'params': [], 'descr': 'Move C to B'},
            'SBC': {'code': '4d', 'params': [], 'descr': 'Swap B and C'},
            'SAC': {'code': '4e', 'params': [], 'descr': 'Swap A and C'},
            'SAB': {'code': '4f', 'params': [], 'descr': 'Swap A and B'},

            'PUSHA': {'code': '50', 'params': [], 'descr': 'PUSHA (previous page addr)'},
            'PUSHP': {'code': '51', 'params': ['page'], 'descr': 'PUSHP [page (high order stack addr)'},
            'POPA': {'code': '52', 'params': [], 'descr': 'POPA (previous page addr)'},
            'POPP': {'code': '53', 'params': ['page'], 'descr': 'POPP [page]'},
            'PUSHX': {'code': '54', 'params': ['addr'], 'descr': ''},
            'RET': {'code': '55', 'params': [], 'descr': ''},
            'RTC': {'code': '56', 'params': [], 'descr': ''},
            'REQ': {'code': '57', 'params': [], 'descr': ''},
            'RCE': {'code': '58', 'params': [], 'descr': ''},
            'INCS': {'code': '59', 'params': [], 'descr': ''},
            'DECS': {'code': '5a', 'params': [], 'descr': ''},
            'PEEK': {'code': '5b', 'params': [], 'descr': ''},
            'PUTA': {'code': '5c', 'params': [], 'descr': ''},
            'SRA': {'code': '5d', 'params': ['page'], 'descr': 'Set Ram Addr'},
            'LRH': {'code': '5e', 'params': ['page'], 'descr': 'Load Ram Addr High'},
            'LRL': {'code': '5f', 'params': ['page'], 'descr': 'Load Ram Addr Low)'},

            'OUTA': {'code': '7f', 'params': [], 'descr': 'Output Reg A'},

            'CMPZ': {'code': 'd0', 'params': [], 'descr': 'Compare if A is zero'},
            'CMPE': {'code': 'd1', 'params': [], 'descr': 'Compare if A and B are equal'},
            'CMPL': {'code': 'd2', 'params': [], 'descr': 'Compare if A is greater or equal to B'},
            'CMPO': {'code': 'd3', 'params': [], 'descr': 'Check if unsigned A + B overflows'},

            'JMP': {'code': 'e0', 'params': ['addr_l'], 'descr': 'Unconditional Jump'},
            'JMC': {'code': 'e1', 'params': ['addr_l'], 'descr': 'Jump if Carry flag'},
            'JME': {'code': 'e2', 'params': ['addr_l'], 'descr': 'Jump if Equal flag'},
            'JCE': {'code': 'e3', 'params': ['addr_l'], 'descr': 'Jump if Carry and Equal flags'},
            'JNC': {'code': 'e4', 'params': ['addr_l'], 'descr': 'Jump if not Carry flag'},
            'JNE': {'code': 'e5', 'params': ['addr_l'], 'descr': 'Jump if not Equal flag'},
            'JNCE': {'code': 'e6', 'params': ['addr_l'], 'descr': 'Jump if not Carry and not Equal flags'},

            'HALT': {'code': 'fe', 'params': [], 'descr': 'Halt'},
            'NOP': {'code': 'ff', 'params': [], 'descr': 'No operation'},
            }

# Global variables
aliases = {}

class LabelManager():

    PL_H_STR = 'XXXX'

    def __init__(self, debug=False):
        self.labels = {}
        self.placeholders = {}
        self.debug = debug

    def add_label(self, name, address):
        if self.debug:
            print('Adding label', '"' + name + '"', 'pointing to address', dec_to_hex(int(address)))
        if name in self.labels:
            return False
        self.labels[name] = dec_to_hex(int(address))
        return True

    def add_placeholder(self, name, address):
        if name in self.placeholders:
            self.placeholders[name].append(dec_to_hex(int(address)))
        else:
            self.placeholders[name] = [dec_to_hex(int(address))]
        if self.debug:
            print('Adding address', dec_to_hex(int(address)), 'to placeholder', '"' + name + '"', '(', len(self.placeholders[name]), ')')
        return self.PL_H_STR

    def resolve_refs(self, code, offset):
        max_offset = offset + int(len(code)/2)
        if self.debug:
            print('Resolving references between offset=', offset, 'and max=', max_offset)
            print('Code in')
            #print(code)
            print(format_code({offset: code}, True, False, False))
        for name in self.placeholders:
            if name not in self.labels:
                return 'Error: label "' + name + '" not defined'
            for position in self.placeholders[name]:
                address = self.labels[name]
                index = (int(position, base=16) - offset) * 2
                if (index > len(code)) or (int(position, base=16) < offset):
                    if self.debug:
                        print('Address', position, 'not in code extent', offset, '-', max_offset)
                    continue
                code = code[:index + 2] + address + code[index + 6:]
                if self.debug:
                    print('Replacing ref to label', '"' + name + '"', '(' + address + ')', 'at', position)
        if self.debug:
            print('Code out')
            #print(code)
            print(format_code({offset: code}, True, False, False))
        return code

    def label_exists(self, name):
        return name in self.labels

    def placeholder_exists(self, name):
        return name in self.placeholders

    def get_label_address(self, name):
        if name in self.labels:
            return self.labels[name]
        else:
            return None

def print_instr_set():
    for instr in INST_SET:
        print(instr, 'Code=' + INST_SET[instr]['code'], 'Params=', INST_SET[instr]['params'], 'Descr=' + INST_SET[instr]['descr'])

def add_alias(name, value_str, debug=False):
    if debug:
        print('Adding alias', '"' + name + '"','with value', '"' + value_str + '"')
    aliases[name] = value_str
    return True

def pre_process(line):
    'Replace aliases in line'
    for alias in aliases:
        #print('line=',line, 'alias=', alias, 'aliases[alias]=', aliases[alias])
        line = line.replace(alias, aliases[alias])
        #print('line after', line)
    return line

def parse_line(line):
    'Parse a line of code'
    label = None
    instr = None
    params = []
    code = line.split(COMMENT_SEP, maxsplit=1)
    code = code[0].strip()
    if code:
        for item in code.split():
            if item.endswith(LABEL_SEP):
                label = item[:-1]
            elif not instr:
                instr = item
            else:
                params.append(item)
    return {'label':label, 'instr':instr, 'params':params}

def validate_hex(in_str, max_len):
    if not in_str.upper().endswith('H'):
        return 'Error: Bad hex constant format (missing h)'
    if len(in_str) > (max_len + 1):
        return 'Error: Bad hex constant format (too large)'
    if len(in_str) == 1:
        return 'Error: Bad hex constant format (invalid)'
    in_str = in_str[:-1]
    return pad_hex_str(in_str, max_len)

def validate_params(command, at_address, debug):
    #print(command['instr'], command['params'])
    #print(INST_SET[command['instr']])
    if len(command['params']) != len(INST_SET[command['instr']]['params']):
        ret_str = 'Error: Parameter count mismatch for ' + command['instr']
    else:
        ret_str = ''
        for (arg, param) in zip(command['params'], INST_SET[command['instr']]['params']):
            if param == 'value':
                arg = validate_hex(arg, 2)
                ret_str = ret_str + arg
            elif param == 'addr':
                arg = validate_hex(arg, 4)
                ret_str = ret_str + arg
            elif param == 'addr_l':
                if label_mgr.label_exists(arg):
                    arg = label_mgr.get_label_address(arg) + 'h'
                else:
                    arg = label_mgr.add_placeholder(arg, at_address) + 'h'
                arg = validate_hex(arg, 4)
                ret_str = ret_str + arg
            elif param == 'page':
                arg = validate_hex(arg, 2)
                ret_str = ret_str + arg
            else:
                ret_str = 'Error: Unrecognized parameter type'
    return ret_str

def dec_to_hex(dec_value, places=4):
    hex_value = hex(dec_value)[2:]
    if len(hex_value) < places:
        while len(hex_value) < places:
            hex_value = '0' + hex_value
    return hex_value

def pad_hex_str(in_str, places=4):
    if len(in_str) < places:
        while len(in_str) < places:
            in_str = '0' + in_str
    return in_str

def pad_line(in_str, pad='ff', length=128):
    if len(in_str) < length:
        while len(in_str) < length:
            in_str = in_str + pad
    return in_str

def process_line(line, at_address, debug=False):
    ret_str = ''
    new_offset = None
    if line.startswith(SPEC_CMD_CHAR):
        info = parse_line(line[1:])
        #print('line', line)
        #print('info', info)
        if info['label']:
            ret_str = 'Error: wrong special command syntax'
        if info['instr'] == ALIAS_DEF:
            if len(info['params']) < 2:
                ret_str = 'Error: ALIAS definition syntax'
            else:
                add_alias(info['params'][0], ' '.join(info['params'][1:]), debug)
        elif info['instr'] == INC_FILE:
            pass
            # if len(info['params']) != 1:
                # ret_str = 'Error: INC_FILE definition syntax'
            # else:
                # ret_str = translate_file(info['params'][0], at_address, debug)
        elif info['instr'] == BASE_ADDR:
            if len(info['params']) != 1:
                ret_str = 'Error: BASE_ADDR definition syntax'
            else:
                offset_val = validate_hex(info['params'][0], 4)
                if offset_val.startswith('Error'):
                    print(offset_val)
                else:
                    new_offset = int(offset_val, 16)
                    if debug:
                        print('Setting new base address to', offset_val, '(', new_offset, ')')
                    if not valid_offset(new_offset):
                        ret_str = 'Error: BASE_ADDR has to be a multiple of 64 (40h)'
        else:
            ret_str = 'Error: Unrecognized special command'
    else:
        line = pre_process(line)
        command = parse_line(line)
        if command['label']:
            if not(label_mgr.add_label(command['label'], at_address)):
                ret_str = 'Error: Duplicate label definition'
        if command['instr']:
            if command['instr'] not in INST_SET:
                ret_str = 'Error: Invalid instruction ' + command['instr']
            else:
                ret_str = validate_params(command, at_address, debug)
                if not ret_str.startswith('Error'):
                    ret_str = INST_SET[command['instr']]['code'] + ret_str
    return ret_str, new_offset

def format_code(code, ruler=False, pad=True, debug=False):
    # Separate the code in chunks of 128 chars (64 bytes)
    # Add a space every 4 chars (2 bytes)
    # Add an extra space between first and second group of 32 bytes
    # prepend with offset + 64 * (n_line -1)
    # If ruler, add horizontal ruler
    # If pad, add 'ff' until 128 chars if line is shorter
    out_str = ''
    for offset in code:
        print_list = chunks(code[offset], 128)
        if debug:
            print('Formatting code at offset=', offset)
            print(print_list)
        for count, entry in enumerate(print_list):
            if debug:
                print('chunk=', count, entry)
            if pad:
                padded_line = pad_line(entry)
            else:
                padded_line = entry
            line1 = padded_line[:64]
            line1 = ' '.join([line1[i:i+4] for i in range(0, len(line1), 4)])
            line2 = ''
            address = dec_to_hex(offset + count * 64)
            if len(padded_line) > 64:
                line2 = padded_line[64:]
                line2 = ' '.join([line2[i:i+4] for i in range(0, len(line2), 4)])
            if ruler:
                #print(address, address[-2:])
                # print(line1)
                # print(len(line1))
                start = int(address[-2:], base=16)
                ruler1 = ''.join([dec_to_hex(start + i * 4, 2) + '        ' for i in range(0, int(len(line1) / 10) + 1)])
                ruler2 = ''
                # print(line2)
                # print(len(line2))
                if line2:
                    start = start + 32
                    ruler2 = ''.join([dec_to_hex(start + i * 4, 2) + '        ' for i in range(0, int(len(line2) / 10) + 1)])
                ruler = '      ' + ruler1 + ' ' + ruler2 + '\n'
                # print(ruler1)
                # print(ruler2)
            else:
                ruler = ''
            out_str = out_str + ruler
            out_str = out_str + address + ': '
            out_str = out_str + line1 + '  ' + line2 + '\n'
    return out_str.rstrip()

def chunks(object, size):
    return [object[i:i+size] for i in range(0, len(object), size)]

def read_file(file_name, debug=False):
    try:
        with open(file_name, 'r') as input_file:
            lines = [line.rstrip() for line in input_file]
            if debug:
                print('Read', len(lines), 'lines from file', file_name)

            # Pre-process lines
            out_lines = []
            for line in lines:
                if line.startswith(SPEC_CMD_CHAR + INC_FILE):
                    info = parse_line(line[1:])
                    if info['instr'] == INC_FILE:
                        if len(info['params']) != 1:
                            print('Error: INC_FILE definition syntax')
                            return False
                        else:
                            print('Including program from file', info['params'][0])
                            inc_lines = read_file(info['params'][0], debug)
                            if not inc_lines:
                                print('Error: Empty include file')
                                return False
                            out_lines.extend(inc_lines)
                else:
                    out_lines.append(line)
            return out_lines
    except IOError:
        print('Cannot open file', file_name)
        return False

def valid_offset(offset):
    return (offset % 64) == 0

def translate_code(assembler_code, offset, steps=False, debug=False):
    # Validate offset (has to be a valid page)
    cur_address = offset
    #code = ''
    code = {}
    code[offset] = ''
    line_no = 0
    if debug:
        print('line (address) instruction -> code')
    #print(assembler_code)
    for line in assembler_code:
        line_no = line_no + 1
        if not line:
            continue
        ret_str, new_offset = process_line(line, str(cur_address), debug)
        if ret_str.startswith('Error'):
            print(line_no, '(' + dec_to_hex(cur_address) + ')', line)
            print('Error found:', ret_str)
            return False
        if debug or steps:
            print(line_no, '(' + dec_to_hex(cur_address) + ')', line, '->', ret_str)
        if new_offset:
            offset = new_offset
            cur_address = offset
            code[offset] = ''
        else:
            code[offset] = code[offset] + ret_str
            cur_address = cur_address + int(len(ret_str)/2)
    # Resolve the label references
    code_out = {}
    for offset in code:
        # Remove empty sequences
        if not code[offset]:
            if debug:
                print('Removing empty sequence at offset=', offset)
            continue
        code_out[offset] = label_mgr.resolve_refs(code[offset], offset)
        if code_out[offset].startswith('Error'):
            print(code_out[offset])
            return ''
    return code_out

def write_code(outfile, code, debug=False):
    code = format_code(code, ruler=False, debug=debug)
    if debug:
        print('Writing code:')
        print(code)
    code = code.split('\n')
    try:
        with open(outfile, 'w') as out_file:
            line_no = 0
            for line in code:
                line_no = line_no + 1
                out_file.write(line + '\n')
        suffix = 's' if line_no > 1 else ''
        print('Wrote', line_no, 'line' + suffix + ' in file', outfile)
        return True
    except IOError:
        print('Cannot open file', out_file)
        return False

def read_args():
    parser = argparse.ArgumentParser(formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument('infile', nargs='?', type=str, default=None, help='Text file with assembler program')
    parser.add_argument('-o', '--outfile', type=str, default='out.txt', help='Text file with binary program')
    parser.add_argument('-b', '--base', type=str, help='Specify starting address', default='0x0000', dest='offset')
    parser.add_argument('-d', '--debug', action='store_true', help='Print debug information')
    parser.add_argument('-p', '--print-code', action='store_true', help='Print generated code to screen')
    parser.add_argument('-s', '--step-trans', action='store_true', help='Print step-by-step code translation', dest='steps')
    parser.add_argument('-i', '--instruction-set', action='store_true', help='Print instruction set and exit')
    return parser.parse_args()

def translate_file(infile, offset, steps=False, debug=False):
    print('Reading program from file', infile)
    lines = read_file(infile, debug)
    if not lines:
        print('Errors found, exiting')
        sys.exit()

    # Translate into binary code
    code = translate_code(lines, int(offset, 16), steps, debug)
    if not code:
        print('Errors found, exiting')
        sys.exit()
    return code

if __name__ == '__main__':
    print('Microprocessor code assembler. Version 0.1')

    # Read command line arguments
    args = read_args()

    # Init handlers
    label_mgr = LabelManager(args.debug)

    # Print instruction if needed
    if args.instruction_set:
        print_instr_set()
        sys.exit()

    # Validate given offset
    if not valid_offset(int(args.offset, 16)):
        print('Offset has to be a multiple of 64 (40h), given', int(offset, 16))
        print('Errors found, exiting')
        sys.exit()

    # Get the intput file name
    if args.infile:
        infile = args.infile
    else:
        infile = input('Name of input file? ')

    code = translate_file(infile, args.offset, args.steps, args.debug)

    # Format and save
    code_len = sum([len(code[offset]) for offset in code])
    print('Code length is', code_len, 'chars')
    ret = write_code(args.outfile, code, args.debug)
    if args.print_code:
        print(format_code(code, ruler=True, debug=args.debug))
    if ret:
        print('Done!')
    else:
        print('Could not save code in file', args.outfile)
