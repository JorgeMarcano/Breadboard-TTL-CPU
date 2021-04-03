@ALIAS stack_ptr 0200h
@ALIAS curr_num 0201h
@ALIAS unflipped_page 00h
@ALIAS flipped_page 01h
@ALIAS stack_start ffh

 LDC stack_start
 LDA 02h
 PUSHP unflipped_page
 INC

mainloop:
 OUTA

check_prime:
 STA curr_num
 STC stack_ptr

modulo_setup:
 MCA
 LDB stack_start
 CMPE
 JME is_prime
 POPP unflipped_page
 MAB
 LRA curr_num

modulo_loop:
 SUB
 CMPZ ; If 0, divisible
 JME not_prime
 CMPL ; If 0, A < B and A is modulo
 JNC modulo_setup
 JMP modulo_loop

is_prime:
 LRC stack_ptr
 LRA curr_num
 PUSHP unflipped_page
 JMP return_loc

not_prime:
 LRC stack_ptr
 LRA curr_num

return_loc:
 INC
 CMPZ
 JME flip_stack
 INC ; skip even numbers
 CMPZ
 JNE mainloop

flip_stack:
 LDB stack_start ; Set up other stack pointer

flip_loop:
 POPP unflipped_page
 OUTA
 SBC
 PUSHP flipped_page
 LDA stack_start
 CMPE
 SBC
 JNE flip_loop

; finished flipping stack (stack ptr in B)
 STB stack_ptr
 MBC
 LDB stack_start
 LRH flipped_page

print_loop:
 POPA
 OUTA
 MCA
 CMPE
 JNE print_loop
 LRC stack_ptr
 LRH flipped_page
 HALT
 JMP print_loop
