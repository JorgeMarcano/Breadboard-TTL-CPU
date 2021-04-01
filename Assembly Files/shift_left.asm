@ALIAS start_val 50h
@ALIAS stack_page 00h
@ALIAS stack_start ffh

 LDC stack_start
 LRH stack_page
 LDA start_val

main_loop:
 PUSHX main_loop
 JMP shift_left

shift_left:
 MAB
 CMPO
 ADD
 JNC shift_left_ret
 INC
shift_left_ret:
 RET
