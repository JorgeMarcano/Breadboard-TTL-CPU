; Test assembler program

@ALIAS ini_val 00aah
@ALIAS inc_val 00a2h
@ALIAS dec_val 00a4h

LDB 02h
STB ini_val

LRA ini_val
INC
OUTA
STA inc_val

LRA ini_val
DEC
OUTA
STA dec_val

HALT