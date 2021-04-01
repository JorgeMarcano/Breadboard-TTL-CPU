@ALIAS stack_ptr 0200h
@ALIAS curr_num 0201h
@ALIAS unflipped_page 00h
@ALIAS flipped_page 01h
@ALIAS stack_start

 LDC stack_start
 LRH unflipped_page
 LDA 02h
 PUSHA
 INC

mainloop:
 OUTA

check_prime:
 STA curr_num
 STC stack_ptr

modulo_setup:
 SAC
 LDB stack_start
 COMPE
 JME is_prime
 POPA unflipped_page
 MAB
 LRA curr_num

modulo_loop:
 SUB
 CMPZ ; If 0, divisible
 JMZ not_prime
 CMPL ; If 0, A < B and A is modulo
 JMZ modulo_setup
 JMP modulo_loop

is_prime:
 LRC stack_ptr
 LRA curr_num
 PUSHA unflipped_page
 JMP return_loc

not_prime:
 LRC stack_ptr
 LRA curr_num

return_loc:
 INC
 CMPZ
 JE flip-stack
 INC ; skip even numbers
 COMPZ
 JNE mainloop

flip_stack:
 LDB stack_start ; Set up other stack pointer

flip_loop:
 POPA unflipped_page
 SBC
 PUSHA flipped_page
 LDA ff
 COMPE
 SBC
 JNE flip-loop

; finished flipping stack (stack ptr in B)
 STB stack_ptr
 MBC
 LDB stack_start
 LRH flipped_page

print_loop:
 POPA
 OUTA
 MCA
 COMPE
 JNE print_loop
 LRC stack_ptr
 LRH flipped_page
 JMP print_loop
