## Assembler

Here's a short guide on how to use assembler.py


    >python assembler.py -h
    Microprocessor code assembler. Version 0.1
    usage: assembler.py [-h] [-o OUTFILE] [-b OFFSET] [-d] [-p] [-s] [-i] [infile]

    positional arguments:
      infile                Text file with assembler program (default: None)

    optional arguments:
      -h, --help            show this help message and exit
      -o OUTFILE, --outfile OUTFILE
                            Text file with binary program (default: out.txt)
      -b OFFSET, --base OFFSET
                            Specify starting address (default: 0x0000)
      -d, --debug           Print debug information (default: False)
      -p, --print-code      Print generated code to screen (default: False)
      -s, --step-trans      Print step-by-step code translation (default: False)
      -i, --instruction-set
                            Print instruction set and exit (default: False)

