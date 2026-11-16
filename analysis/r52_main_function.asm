; r52_data_fragment
; Address: 0x180ed0 - 0x181b7d
; Size: 3245 bytes

00180ED0  enter   0Eh, 0
00180ED4  push    si
00180ED5  push    di
00180ED6  mov     ax, 7894h
00180ED9  mov     es, ax
00180EDB  mov     es:word_79B60, 0
00180EE2  mov     ax, 7894h
00180EE5  mov     es, ax
00180EE7  mov     es:word_79E86, 0
00180EEE  call    state_word_26400_get_zero
00180EF3  call    ui_pilot_images_load_all
00180EF8  mov     ax, 4FC2h
00180EFB  mov     es, ax
00180EFD  push    es:word_13E030
00180F02  call    state_byte_25488_set_arg
00180F07  pop     cx
00180F08  mov     ax, 7894h
00180F0B  mov     es, ax
00180F0D  mov     ax, word ptr es:dword_79E3A+2
00180F11  mov     dx, word ptr es:dword_79E3A
00180F16  add     dx, 3Dh ; '='
00180F19  mov     word ptr [bp+var_E+2], ax
00180F1C  mov     word ptr [bp+var_E], dx
00180F1F  mov     ax, 602Eh
00180F22  mov     es, ax
00180F24  test    es:word_14F8BE, 4
00180F2B  jnz     short loc_180F30
00180F2D  jmp     loc_18105D
00180F30  mov     es, ax
00180F32  xor     es:word_14F8BE, 4
00180F39  xor     si, si
00180F3B  jmp     short loc_180F71
00180F3D  mov     ax, si
00180F3F  mov     dx, 42h ; 'B'
00180F42  imul    dx
00180F44  les     bx, [bp+var_E]
00180F47  add     bx, ax
00180F49  mov     byte ptr es:[bx+3Fh], 0FFh
00180F4E  mov     ax, si
00180F50  mov     dx, 42h ; 'B'
00180F53  imul    dx
00180F55  mov     bx, word ptr [bp+var_E]
00180F58  add     bx, ax
00180F5A  mov     byte ptr es:[bx+40h], 0FFh
00180F5F  mov     ax, si
00180F61  mov     dx, 42h ; 'B'
00180F64  imul    dx
00180F66  mov     bx, word ptr [bp+var_E]
00180F69  add     bx, ax
00180F6B  mov     byte ptr es:[bx+41h], 0FFh
00180F70  inc     si
00180F71  mov     ax, 7894h
00180F74  mov     es, ax
00180F76  les     bx, es:dword_79E3A
00180F7B  cmp     es:[bx+0A8Dh], si
00180F80  ja      short loc_180F3D
00180F82  mov     [bp+var_8], 0
00180F87  mov     [bp+var_A], 0
00180F8C  mov     ax, 7894h
00180F8F  mov     es, ax
00180F91  mov     es:word_79B62, 0
00180F98  jmp     loc_181045
00180F9B  call    data_structure_processor
00180FA0  mov     [bp+var_4], ax
00180FA3  mov     [bp+var_6], 0
00180FA8  jmp     loc_181030
00180FAB  inc     [bp+var_8]
00180FAE  mov     ax, [bp+var_8]
00180FB1  mov     dx, 42h ; 'B'
00180FB4  imul    dx
00180FB6  les     bx, [bp+var_E]
00180FB9  add     bx, ax
00180FBB  cmp     byte ptr es:[bx+26h], 0
00180FC0  jnz     short loc_180FD6
00180FC2  mov     ax, [bp+var_8]
00180FC5  mov     dx, 42h ; 'B'
00180FC8  imul    dx
00180FCA  mov     bx, word ptr [bp+var_E]
00180FCD  add     bx, ax
00180FCF  cmp     byte ptr es:[bx+25h], 45h ; 'E'
00180FD4  jnb     short loc_180FE3
00180FD6  mov     ax, 7894h
00180FD9  mov     es, ax
00180FDB  cmp     es:graphics_mode_flag, 0
00180FE1  jz      short loc_180FAB
00180FE3  mov     ax, [bp+var_8]
00180FE6  mov     dx, 42h ; 'B'
00180FE9  imul    dx
00180FEB  les     bx, [bp+var_E]
00180FEE  add     bx, ax
00180FF0  mov     ax, 7894h
00180FF3  push    es
00180FF4  mov     es, ax
00180FF6  mov     al, byte ptr es:word_79B62
00180FFA  pop     es
00180FFB  mov     es:[bx+3Fh], al
00180FFF  mov     ax, [bp+var_8]
00181002  mov     dx, 42h ; 'B'
00181005  imul    dx
00181007  les     bx, [bp+var_E]
0018100A  add     bx, ax
0018100C  mov     al, byte ptr [bp+var_6]
0018100F  mov     es:[bx+40h], al
00181013  mov     ax, [bp+var_8]
00181016  mov     dx, 42h ; 'B'
00181019  imul    dx
0018101B  mov     bx, word ptr [bp+var_E]
0018101E  add     bx, ax
00181020  mov     al, byte ptr [bp+var_A]
00181023  mov     es:[bx+41h], al
00181027  inc     [bp+var_A]
0018102A  inc     [bp+var_8]
0018102D  inc     [bp+var_6]
00181030  mov     ax, [bp+var_6]
00181033  cmp     ax, [bp+var_4]
00181036  jge     short loc_18103B
00181038  jmp     loc_180FAE
0018103B  mov     ax, 7894h
0018103E  mov     es, ax
00181040  inc     es:word_79B62
00181045  mov     ax, 7894h
00181048  mov     es, ax
0018104A  mov     ax, es:word_79B62
0018104E  mov     dx, 7894h
00181051  mov     es, dx
00181053  cmp     ax, es:word_79EEC
00181058  jge     short loc_18105D
0018105A  jmp     loc_180F9B
0018105D  mov     ax, 7894h
00181060  mov     es, ax
00181062  mov     es:word_79B62, 0
00181069  mov     ax, 7894h
0018106C  mov     es, ax
0018106E  mov     es:word_79E88, 0
00181075  mov     ax, 7894h
00181078  mov     es, ax
0018107A  mov     es:word_79F34, 0
00181081  mov     ax, 7894h
00181084  mov     es, ax
00181086  mov     es:word_79D20, 0
0018108D  mov     ax, 7894h
00181090  mov     es, ax
00181092  mov     es:word_79D1E, 0
00181099  mov     ax, 7894h
0018109C  mov     es, ax
0018109E  mov     es:word_79E32, 0
001810A5  mov     ax, 7894h
001810A8  mov     es, ax
001810AA  mov     ax, es:word_79B62
001810AE  mov     dx, 82h
001810B1  imul    dx
001810B3  mov     dx, 7894h
001810B6  mov     es, dx
001810B8  les     bx, es:dword_79BEC
001810BD  add     bx, ax
001810BF  mov     al, es:[bx+4]
001810C3  cbw
001810C4  mov     di, ax
001810C6  mov     dx, di
001810C8  dec     dx
001810C9  imul    dx
001810CB  mov     bx, 2
001810CE  cwd
001810CF  idiv    bx
001810D1  mov     di, ax
001810D3  xor     si, si
001810D5  jmp     short loc_181125
001810D7  mov     ax, si
001810D9  mov     dx, 42h ; 'B'
001810DC  imul    dx
001810DE  les     bx, [bp+var_E]
001810E1  add     bx, ax
001810E3  cmp     byte ptr es:[bx+3Fh], 0FFh
001810E8  jnz     short loc_181124
001810EA  mov     ax, si
001810EC  mov     dx, 42h ; 'B'
001810EF  imul    dx
001810F1  mov     bx, word ptr [bp+var_E]
001810F4  add     bx, ax
001810F6  cmp     byte ptr es:[bx+26h], 1
001810FB  jg      short loc_181124
001810FD  mov     ax, 7894h
00181100  mov     es, ax
00181102  mov     ax, es:word_79D1E
00181106  mov     dx, 14h
00181109  imul    dx
0018110B  mov     dx, 7894h
0018110E  mov     es, dx
00181110  les     bx, es:dword_79D3E
00181115  add     bx, ax
00181117  mov     es:[bx], si
0018111A  mov     ax, 7894h
0018111D  mov     es, ax
0018111F  inc     es:word_79D1E
00181124  inc     si
00181125  mov     ax, 7894h
00181128  mov     es, ax
0018112A  les     bx, es:dword_79E3A
0018112F  cmp     es:[bx+0A8Dh], si
00181134  ja      short loc_1810D7
00181136  push    5
00181138  call    far ptr sub_2C351
0018113D  pop     cx
0018113E  mov     ax, 4FC2h
00181141  mov     es, ax
00181143  mov     es:word_13E94E, 4FC2h
0018114A  mov     es:word_13E94C, 600h
00181151  xor     si, si
00181153  jmp     short loc_181187
00181155  mov     ax, si
00181157  mov     dx, 1Ch
0018115A  imul    dx
0018115C  mov     dx, 4FC2h
0018115F  mov     bx, ax
00181161  mov     es, dx
00181163  mov     word ptr es:[bx+606h], 4FC2h
0018116A  mov     word ptr es:[bx+604h], 0A68h
00181171  mov     ax, si
00181173  mov     dx, 1Ch
00181176  imul    dx
00181178  mov     dx, 4FC2h
0018117B  mov     bx, ax
0018117D  mov     es, dx
0018117F  mov     word ptr es:[bx+608h], 0Ah
00181186  inc     si
00181187  cmp     si, 0Bh
0018118A  jl      short loc_181155
0018118C  mov     ax, 7894h
0018118F  mov     es, ax
00181191  mov     word ptr es:dword_79E68+2, 4FC2h
00181198  mov     word ptr es:dword_79E68, 600h
0018119F  mov     ax, 7894h
001811A2  mov     es, ax
001811A4  mov     word ptr es:dword_79E2C+2, 4FC2h
001811AB  mov     word ptr es:dword_79E2C, 718h
001811B2  mov     es, ax
001811B4  les     bx, es:dword_79E2C
001811B9  push    word ptr es:[bx+2]
001811BD  mov     es, ax
001811BF  les     bx, es:dword_79E2C
001811C4  push    word ptr es:[bx]
001811C7  call    ui_coordinate_transform
001811CC  pop     cx
001811CD  pop     cx
001811CE  mov     ax, 7894h
001811D1  mov     es, ax
001811D3  mov     es:word_79E9C, 3
001811DA  call    ui_text_render_setup
001811DF  mov     ax, 7894h
001811E2  mov     es, ax
001811E4  mov     ax, es:word_79B62
001811E8  mov     dx, 82h
001811EB  imul    dx
001811ED  mov     dx, 7894h
001811F0  mov     es, dx
001811F2  les     bx, es:dword_79BEC
001811F7  add     bx, ax
001811F9  mov     al, es:[bx+4]
001811FD  cbw
001811FE  mov     [bp+var_4], ax
00181201  call    loc_676AF+4
00181206  push    [bp+var_4]
00181209  call    sub_1338D3
0018120E  pop     cx
0018120F  call    sub_12805C
00181214  call    sub_12DB63
00181219  mov     ax, 7894h
0018121C  mov     es, ax
0018121E  cmp     es:word_79B6C, 0
00181224  jz      short loc_181229
00181226  jmp     loc_181436
00181229  mov     ax, 7894h
0018122C  mov     es, ax
0018122E  cmp     es:graphics_mode_flag, 0
00181234  jz      short loc_181239
00181236  jmp     loc_181436
00181239  mov     ax, 7894h
0018123C  mov     es, ax
0018123E  cmp     es:word_79E80, 0
00181244  jnz     short loc_181256
00181246  mov     ax, 7894h
00181249  mov     es, ax
0018124B  cmp     es:word_79E7E, 0
00181251  jnz     short loc_181256
00181253  jmp     loc_181433
00181256  xor     si, si
00181258  jmp     loc_18142B
0018125B  mov     bx, si
0018125D  mov     ax, 4FC2h
00181260  mov     es, ax
00181262  mov     al, es:[bx+di+2B8h]
00181267  mov     ah, 0
00181269  mov     dx, 7894h
0018126C  mov     es, dx
0018126E  cmp     ax, es:word_79E80
00181273  jle     short loc_181278
00181275  jmp     loc_18142A
00181278  mov     ax, 4FC2h
0018127B  mov     es, ax
0018127D  mov     al, es:[bx+di+2B8h]
00181282  mov     ah, 0
00181284  add     ax, 20h ; ' '
00181287  mov     es, dx
00181289  cmp     ax, es:word_79E80
0018128E  jg      short loc_181293
00181290  jmp     loc_18142A
00181293  mov     ax, 4FC2h
00181296  mov     es, ax
00181298  mov     al, es:[bx+di+2DCh]
0018129D  mov     ah, 0
0018129F  mov     dx, 7894h
001812A2  mov     es, dx
001812A4  cmp     ax, es:word_79E7E
001812A9  jle     short loc_1812AE
001812AB  jmp     loc_18142A
001812AE  mov     ax, 4FC2h
001812B1  mov     es, ax
001812B3  mov     al, es:[bx+di+2DCh]
001812B8  mov     ah, 0
001812BA  add     ax, 20h ; ' '
001812BD  mov     es, dx
001812BF  cmp     ax, es:word_79E7E
001812C4  jg      short loc_1812C9
001812C6  jmp     loc_18142A
001812C9  mov     ax, 7894h
001812CC  mov     es, ax
001812CE  mov     es:word_79E88, si
001812D3  xor     si, si
001812D5  jmp     loc_18135C
001812D8  mov     ax, si
001812DA  mov     dx, 42h ; 'B'
001812DD  imul    dx
001812DF  les     bx, [bp+var_E]
001812E2  add     bx, ax
001812E4  mov     al, es:[bx+3Fh]
001812E8  cbw
001812E9  mov     dx, 7894h
001812EC  mov     es, dx
001812EE  cmp     ax, es:word_79B62
001812F3  jnz     short loc_18135B
001812F5  mov     ax, si
001812F7  mov     dx, 42h ; 'B'
001812FA  imul    dx
001812FC  les     bx, [bp+var_E]
001812FF  add     bx, ax
00181301  mov     al, es:[bx+40h]
00181305  cbw
00181306  mov     dx, 7894h
00181309  mov     es, dx
0018130B  cmp     ax, es:word_79E88
00181310  jnz     short loc_18135B
00181312  mov     ax, si
00181314  mov     dx, 42h ; 'B'
00181317  imul    dx
00181319  les     bx, [bp+var_E]
0018131C  add     bx, ax
0018131E  mov     byte ptr es:[bx+3Fh], 0FFh
00181323  mov     ax, si
00181325  mov     dx, 42h ; 'B'
00181328  imul    dx
0018132A  mov     bx, word ptr [bp+var_E]
0018132D  add     bx, ax
0018132F  mov     byte ptr es:[bx+40h], 0FFh
00181334  mov     ax, si
00181336  mov     dx, 42h ; 'B'
00181339  imul    dx
0018133B  mov     bx, word ptr [bp+var_E]
0018133E  add     bx, ax
00181340  mov     al, es:[bx+41h]
00181344  cbw
00181345  mov     [bp+var_4], ax
00181348  mov     ax, si
0018134A  mov     dx, 42h ; 'B'
0018134D  imul    dx
0018134F  mov     bx, word ptr [bp+var_E]
00181352  add     bx, ax
00181354  mov     byte ptr es:[bx+41h], 0FFh
00181359  jmp     short loc_181370
0018135B  inc     si
0018135C  mov     ax, 7894h
0018135F  mov     es, ax
00181361  les     bx, es:dword_79E3A
00181366  cmp     es:[bx+0A8Dh], si
0018136B  jbe     short loc_181370
0018136D  jmp     loc_1812D8
00181370  mov     ax, 7894h
00181373  mov     es, ax
00181375  mov     ax, es:word_79D20
00181379  mov     dx, 14h
0018137C  imul    dx
0018137E  mov     dx, 7894h
00181381  mov     es, dx
00181383  les     bx, es:dword_79D3E
00181388  add     bx, ax
0018138A  mov     ax, es:[bx]
0018138D  mov     dx, 42h ; 'B'
00181390  imul    dx
00181392  les     bx, [bp+var_E]
00181395  add     bx, ax
00181397  mov     ax, 7894h
0018139A  push    es
0018139B  mov     es, ax
0018139D  mov     al, byte ptr es:word_79B62
001813A1  pop     es
001813A2  mov     es:[bx+3Fh], al
001813A6  mov     ax, 7894h
001813A9  mov     es, ax
001813AB  mov     ax, es:word_79D20
001813AF  mov     dx, 14h
001813B2  imul    dx
001813B4  mov     dx, 7894h
001813B7  mov     es, dx
001813B9  les     bx, es:dword_79D3E
001813BE  add     bx, ax
001813C0  mov     ax, es:[bx]
001813C3  mov     dx, 42h ; 'B'
001813C6  imul    dx
001813C8  les     bx, [bp+var_E]
001813CB  add     bx, ax
001813CD  mov     ax, 7894h
001813D0  push    es
001813D1  mov     es, ax
001813D3  mov     al, byte ptr es:word_79E88
001813D7  pop     es
001813D8  mov     es:[bx+40h], al
001813DC  mov     ax, 7894h
001813DF  mov     es, ax
001813E1  mov     ax, es:word_79D20
001813E5  mov     dx, 14h
001813E8  imul    dx
001813EA  mov     dx, 7894h
001813ED  mov     es, dx
001813EF  les     bx, es:dword_79D3E
001813F4  add     bx, ax
001813F6  mov     ax, es:[bx]
001813F9  mov     dx, 42h ; 'B'
001813FC  imul    dx
001813FE  les     bx, [bp+var_E]
00181401  add     bx, ax
00181403  mov     al, byte ptr [bp+var_4]
00181406  mov     es:[bx+41h], al
0018140A  mov     ax, 7894h
0018140D  mov     es, ax
0018140F  mov     ax, es:word_79D20
00181413  mov     dx, 14h
00181416  imul    dx
00181418  mov     dx, 7894h
0018141B  mov     es, dx
0018141D  les     bx, es:dword_79D3E
00181422  add     bx, ax
00181424  mov     es:[bx], si
00181427  mov     si, 8
0018142A  inc     si
0018142B  cmp     si, [bp+var_4]
0018142E  jge     short loc_181433
00181430  jmp     loc_18125B
00181433  jmp     def_1814BE; jumptable 001814BE default case
00181436  mov     ax, 7894h
00181439  mov     es, ax
0018143B  cmp     es:word_79B6C, 32h ; '2'
00181441  jnz     short loc_181490
00181443  mov     ax, 7894h
00181446  mov     es, ax
00181448  mov     ax, es:input_scan_code_queue
0018144C  cmp     ax, 1
0018144F  jz      short loc_18146B
00181451  cmp     ax, 3
00181454  jz      short loc_18145D
00181456  cmp     ax, 0FFh
00181459  jz      short loc_181485
0018145B  jmp     short loc_18148D
0018145D  mov     ax, 7894h
00181460  mov     es, ax
00181462  mov     es:current_view_index, 0Ah
00181469  jmp     short loc_1814AA
0018146B  push    9
0018146D  call    loc_676E7
00181472  pop     cx
00181473  call    sub_12805C
00181478  call    menu_cursor_position_set
0018147D  mov     [bp+var_2], 1
00181482  jmp     loc_181B43
00181485  call    sub_11D274
0018148A  jmp     loc_1811DF
0018148D  jmp     def_1814BE; jumptable 001814BE default case
00181490  mov     ax, 7894h
00181493  mov     es, ax
00181495  cmp     es:word_79B6C, 34h ; '4'
0018149B  jz      short loc_1814AA
0018149D  mov     es, ax
0018149F  cmp     es:word_79B6C, 36h ; '6'
001814A5  jz      short loc_1814AA
001814A7  jmp     loc_1811DF
001814AA  mov     ax, 7894h
001814AD  mov     es, ax
001814AF  mov     bx, es:current_view_index
001814B4  cmp     bx, 0Ah; switch 11 cases
001814B7  jbe     short loc_1814BC
001814B9  jmp     def_1814BE; jumptable 001814BE default case
001814BC  shl     bx, 1
001814BE  jmp     cs:jpt_1814BE[bx]; switch jump
001814C3  mov     ax, 7894h; jumptable 001814BE case 0
001814C6  mov     es, ax
001814C8  cmp     es:graphics_mode_flag, 0
001814CE  jz      short loc_1814D3
001814D0  jmp     loc_1811DF
001814D3  mov     ax, 7894h
001814D6  mov     es, ax
001814D8  cmp     es:word_79E80, 12Ch
001814DF  jl      short loc_18155A
001814E1  mov     ax, 7894h
001814E4  mov     es, ax
001814E6  push    es:current_view_index
001814EB  call    loc_676E7
001814F0  pop     cx
001814F1  call    sub_12805C
001814F6  jmp     short loc_18154A
001814F8  mov     ax, 7894h
001814FB  mov     es, ax
001814FD  cmp     es:word_79D20, 0
00181503  jle     short loc_18152B
00181505  mov     es, ax
00181507  dec     es:word_79D20
0018150C  mov     ax, 7894h
0018150F  mov     es, ax
00181511  mov     ax, es:word_79E32
00181515  mov     dx, 7894h
00181518  mov     es, dx
0018151A  cmp     ax, es:word_79D20
0018151F  jle     short loc_18152B
00181521  mov     ax, 7894h
00181524  mov     es, ax
00181526  dec     es:word_79E32
0018152B  call    loc_679D7+4
00181530  mov     ax, 7894h
00181533  mov     es, ax
00181535  push    es:current_view_index
0018153A  call    loc_676E7
0018153F  pop     cx
00181540  call    sub_12805C
00181545  call    input_poll_handler; Main keyboard input handler. Processes all keyboard input.
0018154A  mov     ax, 7894h
0018154D  mov     es, ax
0018154F  cmp     es:input_flag_pending_1, 0
00181555  jnz     short loc_1814F8
00181557  jmp     loc_1816EF
0018155A  mov     ax, 7894h
0018155D  mov     es, ax
0018155F  sub     es:word_79E7E, 14h
00181565  mov     es, ax
00181567  mov     ax, es:word_79E7E
0018156B  mov     bx, 10h
0018156E  cwd
0018156F  idiv    bx
00181571  mov     ax, 7894h
00181574  mov     es, ax
00181576  mov     es:word_79E7E, dx
0018157B  mov     es, ax
0018157D  mov     ax, es:word_79E7E
00181581  mov     bx, 8
00181584  cwd
00181585  idiv    bx
00181587  mov     dx, 7894h
0018158A  mov     es, dx
0018158C  mov     es:word_79E7E, ax
00181590  mov     ax, 7894h
00181593  mov     es, ax
00181595  cmp     es:word_79E7E, 1
0018159B  jnz     short loc_1815B2
0018159D  mov     ax, 7894h
001815A0  mov     es, ax
001815A2  mov     ax, es:word_79E32
001815A6  mov     dx, 7894h
001815A9  mov     es, dx
001815AB  mov     es:word_79D20, ax
001815AF  jmp     def_1814BE; jumptable 001814BE default case
001815B2  jmp     def_1814BE; jumptable 001814BE default case
001815B5  mov     ax, 7894h; jumptable 001814BE cases 1-4
001815B8  mov     es, ax
001815BA  cmp     es:graphics_mode_flag, 0
001815C0  jz      short loc_1815C5
001815C2  jmp     loc_1811DF
001815C5  mov     ax, 7894h
001815C8  mov     es, ax
001815CA  cmp     es:word_79E80, 12Ch
001815D1  jge     short loc_18164A
001815D3  mov     ax, 7894h
001815D6  mov     es, ax
001815D8  sub     es:word_79E7E, 14h
001815DE  mov     es, ax
001815E0  mov     ax, es:word_79E7E
001815E4  mov     bx, 10h
001815E7  cwd
001815E8  idiv    bx
001815EA  mov     ax, 7894h
001815ED  mov     es, ax
001815EF  mov     es:word_79E7E, dx
001815F4  mov     es, ax
001815F6  mov     ax, es:word_79E7E
001815FA  mov     bx, 8
001815FD  cwd
001815FE  idiv    bx
00181600  mov     dx, 7894h
00181603  mov     es, dx
00181605  mov     es:word_79E7E, ax
00181609  mov     ax, 7894h
0018160C  mov     es, ax
0018160E  mov     ax, es:current_view_index
00181612  shl     ax, 1
00181614  mov     dx, 7894h
00181617  mov     es, dx
00181619  mov     dx, es:word_79E32
0018161E  add     dx, ax
00181620  mov     ax, 7894h
00181623  mov     es, ax
00181625  add     dx, es:word_79E7E
0018162A  dec     dx
0018162B  mov     ax, 7894h
0018162E  mov     es, ax
00181630  mov     es:word_79D20, dx
00181635  mov     es, ax
00181637  mov     ax, es:word_79D20
0018163B  mov     dx, 7894h
0018163E  mov     es, dx
00181640  cmp     ax, es:word_79D1E
00181645  jl      short loc_18164A
00181647  jmp     loc_181764
0018164A  jmp     def_1814BE; jumptable 001814BE default case
0018164D  mov     ax, 7894h; jumptable 001814BE case 5
00181650  mov     es, ax
00181652  cmp     es:graphics_mode_flag, 0
00181658  jz      short loc_18165D
0018165A  jmp     loc_1811DF
0018165D  mov     ax, 7894h
00181660  mov     es, ax
00181662  cmp     es:word_79E80, 12Ch
00181669  jge     short loc_18166E
0018166B  jmp     loc_1816F7
0018166E  mov     ax, 7894h
00181671  mov     es, ax
00181673  push    es:current_view_index
00181678  call    loc_676E7
0018167D  pop     cx
0018167E  call    sub_12805C
00181683  jmp     short loc_1816E2
00181685  mov     ax, 7894h
00181688  mov     dx, 7894h
0018168B  mov     es, dx
0018168D  mov     dx, es:word_79D1E
00181692  dec     dx
00181693  mov     es, ax
00181695  cmp     es:word_79D20, dx
0018169A  jge     short loc_1816C3
0018169C  mov     es, ax
0018169E  inc     es:word_79D20
001816A3  mov     ax, 7894h
001816A6  mov     dx, 7894h
001816A9  mov     es, dx
001816AB  mov     dx, es:word_79D20
001816B0  add     dx, 0FFF7h
001816B3  mov     es, ax
001816B5  cmp     es:word_79E32, dx
001816BA  jge     short loc_1816C3
001816BC  mov     es, ax
001816BE  inc     es:word_79E32
001816C3  call    loc_679D7+4
001816C8  mov     ax, 7894h
001816CB  mov     es, ax
001816CD  push    es:current_view_index
001816D2  call    loc_676E7
001816D7  pop     cx
001816D8  call    sub_12805C
001816DD  call    input_poll_handler; Main keyboard input handler. Processes all keyboard input.
001816E2  mov     ax, 7894h
001816E5  mov     es, ax
001816E7  cmp     es:input_flag_pending_1, 0
001816ED  jnz     short loc_181685
001816EF  call    undoc_130B39
001816F4  jmp     loc_1811DF
001816F7  mov     ax, 7894h
001816FA  mov     es, ax
001816FC  sub     es:word_79E7E, 14h
00181702  mov     es, ax
00181704  mov     ax, es:word_79E7E
00181708  mov     bx, 10h
0018170B  cwd
0018170C  idiv    bx
0018170E  mov     ax, 7894h
00181711  mov     es, ax
00181713  mov     es:word_79E7E, dx
00181718  mov     es, ax
0018171A  mov     ax, es:word_79E7E
0018171E  mov     bx, 8
00181721  cwd
00181722  idiv    bx
00181724  mov     dx, 7894h
00181727  mov     es, dx
00181729  mov     es:word_79E7E, ax
0018172D  mov     ax, 7894h
00181730  mov     es, ax
00181732  cmp     es:word_79E7E, 0
00181738  jnz     short loc_181771
0018173A  mov     ax, 7894h
0018173D  mov     es, ax
0018173F  mov     ax, es:word_79E32
00181743  add     ax, 9
00181746  mov     dx, 7894h
00181749  mov     es, dx
0018174B  mov     es:word_79D20, ax
0018174F  mov     ax, 7894h
00181752  mov     es, ax
00181754  mov     ax, es:word_79D20
00181758  mov     dx, 7894h
0018175B  mov     es, dx
0018175D  cmp     ax, es:word_79D1E
00181762  jl      short loc_181771
00181764  mov     ax, 7894h
00181767  mov     es, ax
00181769  mov     ax, es:word_79D1E
0018176D  dec     ax
0018176E  jmp     loc_1815A6
00181771  jmp     def_1814BE; jumptable 001814BE default case
00181774  mov     ax, 7894h; jumptable 001814BE case 6
00181777  mov     es, ax
00181779  cmp     es:word_79EEC, 1
0018177F  jg      short loc_181784
00181781  jmp     loc_1811DF
00181784  mov     ax, 7894h
00181787  mov     es, ax
00181789  push    es:current_view_index
0018178E  call    loc_676E7
00181793  pop     cx
00181794  call    sub_12805C
00181799  call    menu_cursor_position_set
0018179E  mov     ax, 7894h
001817A1  mov     es, ax
001817A3  cmp     es:word_79B6C, 36h ; '6'
001817A9  jnz     short loc_1817D4
001817AB  mov     ax, 7894h
001817AE  mov     es, ax
001817B0  dec     es:word_79B62
001817B5  mov     es, ax
001817B7  cmp     es:word_79B62, 0
001817BD  jge     short loc_1817FC
001817BF  mov     ax, 7894h
001817C2  mov     es, ax
001817C4  mov     ax, es:word_79EEC
001817C8  dec     ax
001817C9  mov     dx, 7894h
001817CC  mov     es, dx
001817CE  mov     es:word_79B62, ax
001817D2  jmp     short loc_1817FC
001817D4  mov     ax, 7894h
001817D7  mov     es, ax
001817D9  inc     es:word_79B62
001817DE  mov     es, ax
001817E0  mov     ax, es:word_79B62
001817E4  mov     dx, 7894h
001817E7  mov     es, dx
001817E9  cmp     ax, es:word_79EEC
001817EE  jl      short loc_1817FC
001817F0  mov     ax, 7894h
001817F3  mov     es, ax
001817F5  mov     es:word_79B62, 0
001817FC  mov     ax, 7894h
001817FF  mov     es, ax
00181801  mov     ax, es:word_79B62
00181805  mov     dx, 82h
00181808  imul    dx
0018180A  mov     dx, 7894h
0018180D  mov     es, dx
0018180F  les     bx, es:dword_79BEC
00181814  add     bx, ax
00181816  mov     al, es:[bx+4]
0018181A  cbw
0018181B  mov     di, ax
0018181D  mov     dx, di
0018181F  dec     dx
00181820  imul    dx
00181822  mov     bx, 2
00181825  cwd
00181826  idiv    bx
00181828  mov     di, ax
0018182A  jmp     loc_1811DF
0018182D  mov     ax, 7894h; jumptable 001814BE case 7
00181830  mov     es, ax
00181832  push    es:current_view_index
00181837  call    loc_676E7
0018183C  pop     cx
0018183D  call    sub_12805C
00181842  call    menu_cursor_position_set
00181847  mov     ax, 4FC2h
0018184A  mov     es, ax
0018184C  push    es:word_13E012
00181851  call    ui_font_config_apply
00181856  pop     cx
00181857  mov     ax, 4FC2h
0018185A  mov     es, ax
0018185C  push    es:word_13E012
00181861  call    far ptr menu_finalize_render
00181866  pop     cx
00181867  call    far ptr sub_2C3F1
0018186C  call    ui_pilot_images_load_all
00181871  mov     ax, 4FC2h
00181874  mov     es, ax
00181876  push    es:word_13E012
0018187B  call    sub_2C761; Overlay bridge trampoline (8B, 14 calls)
00181880  pop     cx
00181881  mov     ax, 4FC2h
00181884  mov     es, ax
00181886  push    es:word_13E012
0018188B  call    undoc_132012
00181890  pop     cx
00181891  push    5
00181893  call    far ptr sub_2C351
00181898  pop     cx
00181899  mov     ax, 7894h
0018189C  mov     es, ax
0018189E  mov     es:word_79D1E, 0
001818A5  mov     ax, 7894h
001818A8  mov     es, ax
001818AA  mov     es:word_79D20, 0
001818B1  mov     ax, 7894h
001818B4  mov     es, ax
001818B6  mov     es:word_79E32, 0
001818BD  xor     si, si
001818BF  jmp     short loc_18190F
001818C1  mov     ax, si
001818C3  mov     dx, 42h ; 'B'
001818C6  imul    dx
001818C8  les     bx, [bp+var_E]
001818CB  add     bx, ax
001818CD  cmp     byte ptr es:[bx+3Fh], 0FFh
001818D2  jnz     short loc_18190E
001818D4  mov     ax, si
001818D6  mov     dx, 42h ; 'B'
001818D9  imul    dx
001818DB  mov     bx, word ptr [bp+var_E]
001818DE  add     bx, ax
001818E0  cmp     byte ptr es:[bx+26h], 1
001818E5  jg      short loc_18190E
001818E7  mov     ax, 7894h
001818EA  mov     es, ax
001818EC  mov     ax, es:word_79D1E
001818F0  mov     dx, 14h
001818F3  imul    dx
001818F5  mov     dx, 7894h
001818F8  mov     es, dx
001818FA  les     bx, es:dword_79D3E
001818FF  add     bx, ax
00181901  mov     es:[bx], si
00181904  mov     ax, 7894h
00181907  mov     es, ax
00181909  inc     es:word_79D1E
0018190E  inc     si
0018190F  mov     ax, 7894h
00181912  mov     es, ax
00181914  les     bx, es:dword_79E3A
00181919  cmp     es:[bx+0A8Dh], si
0018191E  ja      short loc_1818C1
00181920  mov     ax, 4FC2h
00181923  mov     es, ax
00181925  mov     es:word_13E94E, 4FC2h
0018192C  mov     es:word_13E94C, 600h
00181933  xor     si, si
00181935  jmp     short loc_181969
00181937  mov     ax, si
00181939  mov     dx, 1Ch
0018193C  imul    dx
0018193E  mov     dx, 4FC2h
00181941  mov     bx, ax
00181943  mov     es, dx
00181945  mov     word ptr es:[bx+606h], 4FC2h
0018194C  mov     word ptr es:[bx+604h], 0A68h
00181953  mov     ax, si
00181955  mov     dx, 1Ch
00181958  imul    dx
0018195A  mov     dx, 4FC2h
0018195D  mov     bx, ax
0018195F  mov     es, dx
00181961  mov     word ptr es:[bx+608h], 0Ah
00181968  inc     si
00181969  cmp     si, 0Bh
0018196C  jl      short loc_181937
0018196E  jmp     loc_181ABC
00181971  mov     ax, 7894h; jumptable 001814BE case 8
00181974  mov     es, ax
00181976  push    es:current_view_index
0018197B  call    loc_676E7
00181980  pop     cx
00181981  call    sub_12805C
00181986  call    menu_cursor_position_set
0018198B  mov     ax, 4FC2h
0018198E  mov     es, ax
00181990  push    es:word_13E012
00181995  call    ui_font_config_apply
0018199A  pop     cx
0018199B  mov     ax, 4FC2h
0018199E  mov     es, ax
001819A0  push    es:word_13E012
001819A5  call    far ptr menu_finalize_render
001819AA  pop     cx
001819AB  call    temp_file_handler
001819B0  call    far ptr sub_2C72F
001819B5  call    undoc_13C868
001819BA  mov     ax, 4FC2h
001819BD  mov     es, ax
001819BF  push    es:word_13E012
001819C4  call    undoc_132012
001819C9  pop     cx
001819CA  mov     ax, 4FC2h
001819CD  mov     es, ax
001819CF  push    es:word_13E012
001819D4  call    sub_2C761; Overlay bridge trampoline (8B, 14 calls)
001819D9  pop     cx
001819DA  call    ui_pilot_images_load_all
001819DF  push    5
001819E1  call    far ptr sub_2C351
001819E6  pop     cx
001819E7  mov     ax, 7894h
001819EA  mov     es, ax
001819EC  mov     es:word_79D1E, 0
001819F3  mov     ax, 7894h
001819F6  mov     es, ax
001819F8  mov     es:word_79D20, 0
001819FF  mov     ax, 7894h
00181A02  mov     es, ax
00181A04  mov     es:word_79E32, 0
00181A0B  xor     si, si
00181A0D  jmp     short loc_181A5D
00181A0F  mov     ax, si
00181A11  mov     dx, 42h ; 'B'
00181A14  imul    dx
00181A16  les     bx, [bp+var_E]
00181A19  add     bx, ax
00181A1B  cmp     byte ptr es:[bx+3Fh], 0FFh
00181A20  jnz     short loc_181A5C
00181A22  mov     ax, si
00181A24  mov     dx, 42h ; 'B'
00181A27  imul    dx
00181A29  mov     bx, word ptr [bp+var_E]
00181A2C  add     bx, ax
00181A2E  cmp     byte ptr es:[bx+26h], 1
00181A33  jg      short loc_181A5C
00181A35  mov     ax, 7894h
00181A38  mov     es, ax
00181A3A  mov     ax, es:word_79D1E
00181A3E  mov     dx, 14h
00181A41  imul    dx
00181A43  mov     dx, 7894h
00181A46  mov     es, dx
00181A48  les     bx, es:dword_79D3E
00181A4D  add     bx, ax
00181A4F  mov     es:[bx], si
00181A52  mov     ax, 7894h
00181A55  mov     es, ax
00181A57  inc     es:word_79D1E
00181A5C  inc     si
00181A5D  mov     ax, 7894h
00181A60  mov     es, ax
00181A62  les     bx, es:dword_79E3A
00181A67  cmp     es:[bx+0A8Dh], si
00181A6C  ja      short loc_181A0F
00181A6E  mov     ax, 4FC2h
00181A71  mov     es, ax
00181A73  mov     es:word_13E94E, 4FC2h
00181A7A  mov     es:word_13E94C, 600h
00181A81  xor     si, si
00181A83  jmp     short loc_181AB7
00181A85  mov     ax, si
00181A87  mov     dx, 1Ch
00181A8A  imul    dx
00181A8C  mov     dx, 4FC2h
00181A8F  mov     bx, ax
00181A91  mov     es, dx
00181A93  mov     word ptr es:[bx+606h], 4FC2h
00181A9A  mov     word ptr es:[bx+604h], 0A68h
00181AA1  mov     ax, si
00181AA3  mov     dx, 1Ch
00181AA6  imul    dx
00181AA8  mov     dx, 4FC2h
00181AAB  mov     bx, ax
00181AAD  mov     es, dx
00181AAF  mov     word ptr es:[bx+608h], 0Ah
00181AB6  inc     si
00181AB7  cmp     si, 0Bh
00181ABA  jl      short loc_181A85
00181ABC  mov     ax, 7894h
00181ABF  mov     es, ax
00181AC1  mov     word ptr es:dword_79E68+2, 4FC2h
00181AC8  mov     word ptr es:dword_79E68, 600h
00181ACF  mov     ax, 7894h
00181AD2  mov     es, ax
00181AD4  mov     word ptr es:dword_79E2C+2, 4FC2h
00181ADB  mov     word ptr es:dword_79E2C, 718h
00181AE2  mov     es, ax
00181AE4  les     bx, es:dword_79E2C
00181AE9  push    word ptr es:[bx+2]
00181AED  mov     es, ax
00181AEF  les     bx, es:dword_79E2C
00181AF4  push    word ptr es:[bx]
00181AF7  call    ui_coordinate_transform
00181AFC  pop     cx
00181AFD  pop     cx
00181AFE  mov     ax, 7894h
00181B01  mov     es, ax
00181B03  mov     es:word_79E9C, 3
00181B0A  jmp     loc_1811DF
00181B0D  mov     ax, 7894h; jumptable 001814BE case 9
00181B10  mov     es, ax
00181B12  push    es:current_view_index
00181B17  jmp     loc_18146D
00181B1A  mov     ax, 7894h; jumptable 001814BE case 10
00181B1D  mov     es, ax
00181B1F  push    es:current_view_index
00181B24  call    loc_676E7
00181B29  pop     cx
00181B2A  call    sub_12805C
00181B2F  call    menu_cursor_position_set
00181B34  mov     [bp+var_2], 2
00181B39  jmp     short loc_181B43
00181B3B  call    menu_cursor_position_set; jumptable 001814BE default case
00181B40  jmp     loc_1811DF
00181B43  mov     ax, 4FC2h
00181B46  mov     es, ax
00181B48  push    es:word_13E012
00181B4D  call    ui_font_config_apply
00181B52  pop     cx
00181B53  mov     ax, 4FC2h
00181B56  mov     es, ax
00181B58  push    es:word_13E012
00181B5D  call    far ptr menu_finalize_render
00181B62  pop     cx
00181B63  mov     ax, 4FC2h
00181B66  mov     es, ax
00181B68  mov     es:word_13E94E, 4FC2h
00181B6F  mov     es:word_13E94C, 7C0h
00181B76  mov     ax, [bp+var_2]
00181B79  pop     di
00181B7A  pop     si
00181B7B  leave
00181B7C  retf
