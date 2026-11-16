; game_mode_r53_main_coordinator
; Address: 0x1820b0
; Size: 12693 bytes
; Instructions: 3846
; Calls: 342

001820B0  enter   16h, 0
001820B4  push    si
001820B5  push    di
001820B6  push    8
001820B8  call    far ptr sub_2C351
001820BD  pop     cx
001820BE  call    undoc_133535
001820C3  mov     ax, 7894h
001820C6  mov     es, ax
001820C8  cmp     es:graphics_mode_flag, 0
001820CE  jz      short loc_182107
001820D0  mov     ax, 7894h
001820D3  mov     es, ax
001820D5  cmp     es:byte_7A302, 0
001820DB  jz      short loc_182107
001820DD  mov     ax, 4FC2h
001820E0  mov     es, ax
001820E2  push    es:word_13E012
001820E7  call    sub_2C761; Overlay bridge trampoline (8B, 14 calls)
001820EC  pop     cx
001820ED  mov     ax, 7894h
001820F0  mov     es, ax
001820F2  dec     es:word_79EEC
001820F7  mov     ax, 4FC2h
001820FA  mov     es, ax
001820FC  push    es:word_13E012
00182101  call    far ptr menu_finalize_render
00182106  pop     cx
00182107  call    ui_text_render_setup
0018210C  mov     ax, 7894h
0018210F  mov     es, ax
00182111  mov     ax, word ptr es:dword_79E3A+2
00182115  mov     dx, word ptr es:dword_79E3A
0018211A  add     dx, 3Dh ; '='
0018211D  mov     bx, 6E1Eh
00182120  mov     es, bx
00182122  mov     word ptr es:byte_6E1C9+49h, ax
00182126  mov     word ptr es:byte_6E1C9+47h, dx
0018212B  mov     ax, 6E1Eh
0018212E  mov     es, ax
00182130  mov     word ptr es:byte_6E1C9+17h, 0
00182137  jmp     short loc_182172
00182139  mov     ax, 6E1Eh
0018213C  mov     es, ax
0018213E  mov     bx, word ptr es:byte_6E1C9+17h
00182143  lea     ax, [bp+var_12]
00182146  add     bx, ax
00182148  mov     byte ptr ss:[bx], 1
0018214C  mov     ax, 6E1Eh
0018214F  mov     es, ax
00182151  mov     ax, word ptr es:byte_6E1C9+17h
00182155  shl     ax, 1
00182157  mov     dx, 6E1Eh
0018215A  mov     es, dx
0018215C  les     bx, dword ptr es:loc_6E2A1+3
00182161  add     bx, ax
00182163  mov     word ptr es:[bx], 0FFFFh
00182168  mov     ax, 6E1Eh
0018216B  mov     es, ax
0018216D  inc     word ptr es:byte_6E1C9+17h
00182172  mov     ax, 6E1Eh
00182175  mov     es, ax
00182177  cmp     word ptr es:byte_6E1C9+17h, 8
0018217D  jl      short loc_182139
0018217F  mov     es, ax
00182181  mov     word ptr es:byte_6E1C9+17h, 0
00182188  jmp     short loc_1821F0
0018218A  mov     ax, 6E1Eh
0018218D  mov     es, ax
0018218F  mov     ax, word ptr es:byte_6E1C9+17h
00182193  mov     dx, 42h ; 'B'
00182196  imul    dx
00182198  mov     dx, 6E1Eh
0018219B  mov     es, dx
0018219D  les     bx, dword ptr es:byte_6E1C9+47h
001821A2  add     bx, ax
001821A4  cmp     byte ptr es:[bx+41h], 0FFh
001821A9  jz      short loc_1821E6
001821AB  mov     ax, 6E1Eh
001821AE  mov     es, ax
001821B0  mov     ax, word ptr es:byte_6E1C9+17h
001821B4  mov     dx, 42h ; 'B'
001821B7  imul    dx
001821B9  mov     dx, 6E1Eh
001821BC  mov     es, dx
001821BE  les     bx, dword ptr es:byte_6E1C9+47h
001821C3  add     bx, ax
001821C5  mov     al, es:[bx+41h]
001821C9  cbw
001821CA  shl     ax, 1
001821CC  mov     dx, 6E1Eh
001821CF  mov     es, dx
001821D1  les     bx, dword ptr es:loc_6E2A1+3
001821D6  add     bx, ax
001821D8  mov     ax, 6E1Eh
001821DB  push    es
001821DC  mov     es, ax
001821DE  mov     ax, word ptr es:byte_6E1C9+17h
001821E2  pop     es
001821E3  mov     es:[bx], ax
001821E6  mov     ax, 6E1Eh
001821E9  mov     es, ax
001821EB  inc     word ptr es:byte_6E1C9+17h
001821F0  mov     ax, 7894h
001821F3  mov     es, ax
001821F5  les     bx, es:dword_79E3A
001821FA  mov     ax, es:[bx+0A8Dh]
001821FF  mov     dx, 6E1Eh
00182202  mov     es, dx
00182204  cmp     ax, word ptr es:byte_6E1C9+17h
00182209  jbe     short loc_18220E
0018220B  jmp     loc_18218A
0018220E  mov     ax, 7894h
00182211  mov     es, ax
00182213  cmp     es:word_79B56, 1
00182219  jnz     short loc_182229
0018221B  mov     ax, 7894h
0018221E  mov     es, ax
00182220  mov     es:word_79B60, 0FFFFh
00182227  jmp     short loc_182235
00182229  mov     ax, 7894h
0018222C  mov     es, ax
0018222E  mov     es:word_79B60, 28h ; '('
00182235  mov     ax, 7894h
00182238  mov     es, ax
0018223A  mov     es:word_79E86, 1
00182241  mov     ax, 7894h
00182244  mov     es, ax
00182246  mov     es:word_79B5A, 1
0018224D  mov     ax, 7894h
00182250  mov     es, ax
00182252  mov     es:word_79B62, 0
00182259  mov     ax, 7894h
0018225C  mov     es, ax
0018225E  mov     es:word_79D6A, 0
00182265  call    far ptr sub_1364BA
0018226A  mov     ax, 7894h
0018226D  mov     es, ax
0018226F  mov     ax, es:word_79B62
00182273  mov     dx, 82h
00182276  imul    dx
00182278  mov     dx, 7894h
0018227B  mov     es, dx
0018227D  les     bx, es:dword_79BEC
00182282  add     bx, ax
00182284  cmp     byte ptr es:[bx+15h], 1
00182289  jg      short loc_18228E
0018228B  jmp     loc_183A14
0018228E  mov     ax, 7894h
00182291  mov     es, ax
00182293  mov     es:word_79B74, 2
0018229A  mov     ax, 7894h
0018229D  mov     es, ax
0018229F  mov     es:word_79BD6, 0FFFFh
001822A6  mov     ax, 4FC2h
001822A9  mov     es, ax
001822AB  mov     es:word_13E006, 0
001822B2  mov     ax, 4FC2h
001822B5  mov     es, ax
001822B7  mov     es:word_13E008, 0
001822BE  call    sub_13504F
001822C3  mov     ax, 7894h
001822C6  mov     es, ax
001822C8  mov     es:word_79E32, 0
001822CF  mov     ax, 7894h
001822D2  mov     es, ax
001822D4  mov     es:word_79D1E, 0
001822DB  push    7894h
001822DE  push    0F32h
001822E1  mov     ax, 6E1Eh
001822E4  mov     es, ax
001822E6  push    word ptr es:loc_6E2E3+2
001822EB  push    word ptr es:loc_6E2E3
001822F0  call    string_copy_with_offset
001822F5  add     sp, 8
001822F8  push    0
001822FA  push    7894h
001822FD  push    0F32h
00182300  call    sub_135C57
00182305  add     sp, 6
00182308  mov     dx, 7894h
0018230B  mov     es, dx
0018230D  mov     es:word_79D1E, ax
00182311  call    undoc_11D941
00182316  call    undoc_12661D
0018231B  push    1
0018231D  call    loc_69C25
00182322  pop     cx
00182323  call    sub_12805C
00182328  mov     ax, 6E1Eh
0018232B  mov     es, ax
0018232D  mov     word ptr es:byte_6E1C9+17h, 0
00182334  jmp     short loc_18237F
00182336  mov     ax, 6E1Eh
00182339  mov     es, ax
0018233B  mov     ax, word ptr es:byte_6E1C9+17h
0018233F  mov     dx, 1Ch
00182342  imul    dx
00182344  mov     dx, 4FC2h
00182347  mov     bx, ax
00182349  mov     es, dx
0018234B  mov     word ptr es:[bx+606h], 4FC2h
00182352  mov     word ptr es:[bx+604h], 0A68h
00182359  mov     ax, 6E1Eh
0018235C  mov     es, ax
0018235E  mov     ax, word ptr es:byte_6E1C9+17h
00182362  mov     dx, 1Ch
00182365  imul    dx
00182367  mov     dx, 4FC2h
0018236A  mov     bx, ax
0018236C  mov     es, dx
0018236E  mov     word ptr es:[bx+608h], 7
00182375  mov     ax, 6E1Eh
00182378  mov     es, ax
0018237A  inc     word ptr es:byte_6E1C9+17h
0018237F  mov     ax, 6E1Eh
00182382  mov     es, ax
00182384  cmp     word ptr es:byte_6E1C9+17h, 0Bh
0018238A  jl      short loc_182336
0018238C  mov     ax, 4FC2h
0018238F  mov     es, ax
00182391  mov     es:word_13E94E, 4FC2h
00182398  mov     es:word_13E94C, 7C0h
0018239F  mov     ax, 7894h
001823A2  mov     es, ax
001823A4  mov     word ptr es:dword_79E68+2, 4FC2h
001823AB  mov     word ptr es:dword_79E68, 600h
001823B2  mov     ax, 7894h
001823B5  mov     es, ax
001823B7  mov     word ptr es:dword_79E2C+2, 4FC2h
001823BE  mov     word ptr es:dword_79E2C, 6C4h
001823C5  mov     es, ax
001823C7  les     bx, es:dword_79E2C
001823CC  push    word ptr es:[bx+2]
001823D0  mov     es, ax
001823D2  les     bx, es:dword_79E2C
001823D7  push    word ptr es:[bx]
001823DA  call    ui_coordinate_transform
001823DF  pop     cx
001823E0  pop     cx
001823E1  mov     ax, 7894h
001823E4  mov     es, ax
001823E6  mov     es:word_79E9C, 2
001823ED  mov     ax, 7894h
001823F0  mov     es, ax
001823F2  cmp     es:word_79B56, 1
001823F8  jz      short loc_182408
001823FA  call    loc_6CB67+1
001823FF  mov     dx, 602Eh
00182402  mov     es, dx
00182404  mov     es:word_14F8A9, ax
00182408  mov     [bp+var_A], 0
0018240D  jmp     short loc_182423
0018240F  mov     ax, 602Eh
00182412  mov     es, ax
00182414  les     bx, es:dword_151B42
00182419  add     bx, [bp+var_A]
0018241C  mov     byte ptr es:[bx], 0
00182420  inc     [bp+var_A]
00182423  cmp     [bp+var_A], 3Fh ; '?'
00182427  jl      short loc_18240F
00182429  mov     ax, 7894h
0018242C  mov     es, ax
0018242E  mov     ax, es:word_79F14
00182432  mov     dx, 7894h
00182435  mov     es, dx
00182437  sub     ax, es:game_status_word
0018243C  push    ax
0018243D  call    loc_6DCB2+3
00182442  pop     cx
00182443  xor     si, si
00182445  jmp     def_1824F6; jumptable 001824F6 default case, cases 1-5
00182448  call    undoc_11D941
0018244D  call    undoc_12661D
00182452  push    1; jump table for switch statement
00182454  call    loc_69C25
00182459  pop     cx
0018245A  call    sub_12805C
0018245F  call    sub_12DB63
00182464  mov     ax, 7894h
00182467  mov     es, ax
00182469  cmp     es:word_79B6C, 32h ; '2'
0018246F  jnz     short loc_1824C8
00182471  mov     ax, 7894h
00182474  mov     es, ax
00182476  mov     ax, es:input_scan_code_queue; INPUT DISPATCHER: Handle view keys (scan 0x03,0x04)
0018247A  mov     [bp+var_14], ax
0018247D  mov     cx, 4
00182480  mov     bx, 3225h; Load dispatch table address (4 entries: 0x01,0x03,0x04,0xFF)
00182483  mov     ax, cs:[bx]
00182486  cmp     ax, [bp+var_14]
00182489  jz      short loc_182491; JUMP TABLE DISPATCH: jmp to handler at [bx+8]
0018248B  inc     bx
0018248C  inc     bx
0018248D  loop    loc_182483
0018248F  jmp     short loc_1824C0
00182491  jmp     word ptr cs:[bx+8]; JUMP TABLE DISPATCH: jmp to handler at [bx+8]
00182495  mov     ax, 7894h
00182498  mov     es, ax
0018249A  mov     es:current_view_index, 7; VIEW KEY HANDLER: Set current_view_index = 7 (likely ground or external view)
001824A1  jmp     short loc_1824E2
001824A3  push    8; VIEW KEY HANDLER: Push view index 8, call view setup (likely padlock view)
001824A5  call    far ptr loc_69CBE
001824AA  pop     cx
001824AB  call    sub_12805C
001824B0  call    menu_cursor_position_set
001824B5  jmp     loc_18523C
001824B8  call    loc_6C7E8
001824BD  jmp     def_1824F6; jumptable 001824F6 default case, cases 1-5
001824C0  call    menu_cursor_position_set
001824C5  jmp     def_1824F6; jumptable 001824F6 default case, cases 1-5
001824C8  mov     ax, 7894h
001824CB  mov     es, ax
001824CD  cmp     es:word_79B6C, 34h ; '4'
001824D3  jz      short loc_1824E2
001824D5  mov     es, ax
001824D7  cmp     es:word_79B6C, 36h ; '6'
001824DD  jz      short loc_1824E2
001824DF  jmp     def_1824F6; jumptable 001824F6 default case, cases 1-5
001824E2  mov     ax, 7894h
001824E5  mov     es, ax
001824E7  mov     bx, es:current_view_index
001824EC  cmp     bx, 8; switch 9 cases
001824EF  jbe     short loc_1824F4
001824F1  jmp     def_1824F6; jumptable 001824F6 default case, cases 1-5
001824F4  shl     bx, 1
001824F6  jmp     cs:jpt_1824F6[bx]; switch jump
001824FB  mov     ax, 7894h; jumptable 001824F6 case 0
001824FE  mov     es, ax
00182500  cmp     es:word_79E80, 12Ch
00182507  jge     short loc_18250C
00182509  jmp     def_1824F6; jumptable 001824F6 default case, cases 1-5
0018250C  mov     ax, 7894h
0018250F  mov     es, ax
00182511  push    es:current_view_index
00182516  call    far ptr loc_69CBE
0018251B  pop     cx
0018251C  call    sub_12805C
00182521  jmp     short loc_182556
00182523  mov     ax, 7894h
00182526  mov     es, ax
00182528  cmp     es:word_79E32, 0
0018252E  jle     short loc_182537
00182530  mov     es, ax
00182532  dec     es:word_79E32
00182537  call    far ptr loc_69EA9
0018253C  mov     ax, 7894h
0018253F  mov     es, ax
00182541  push    es:current_view_index
00182546  call    far ptr loc_69CBE
0018254B  pop     cx
0018254C  call    sub_12805C
00182551  call    input_poll_handler; Main keyboard input handler. Processes all keyboard input.
00182556  mov     ax, 7894h
00182559  mov     es, ax
0018255B  cmp     es:input_flag_pending_1, 0
00182561  jnz     short loc_182523
00182563  jmp     short loc_1825D9
00182565  mov     ax, 7894h; jumptable 001824F6 case 6
00182568  mov     es, ax
0018256A  cmp     es:word_79E80, 12Ch
00182571  jge     short loc_182576
00182573  jmp     def_1824F6; jumptable 001824F6 default case, cases 1-5
00182576  mov     ax, 7894h
00182579  mov     es, ax
0018257B  push    es:current_view_index
00182580  call    far ptr loc_69CBE
00182585  pop     cx
00182586  call    sub_12805C
0018258B  jmp     short loc_1825CC
0018258D  mov     ax, 7894h
00182590  mov     dx, 7894h
00182593  mov     es, dx
00182595  mov     dx, es:word_79D1E
0018259A  add     dx, 0FFF5h
0018259D  mov     es, ax
0018259F  cmp     es:word_79E32, dx
001825A4  jge     short loc_1825AD
001825A6  mov     es, ax
001825A8  inc     es:word_79E32
001825AD  call    far ptr loc_69EA9
001825B2  mov     ax, 7894h
001825B5  mov     es, ax
001825B7  push    es:current_view_index
001825BC  call    far ptr loc_69CBE
001825C1  pop     cx
001825C2  call    sub_12805C
001825C7  call    input_poll_handler; Main keyboard input handler. Processes all keyboard input.
001825CC  mov     ax, 7894h
001825CF  mov     es, ax
001825D1  cmp     es:input_flag_pending_1, 0
001825D7  jnz     short loc_18258D
001825D9  call    undoc_130B39
001825DE  jmp     short def_1824F6; jumptable 001824F6 default case, cases 1-5
001825E0  push    7; jumptable 001824F6 case 7
001825E2  call    far ptr loc_69CBE
001825E7  pop     cx
001825E8  call    sub_12805C
001825ED  call    menu_cursor_position_set
001825F2  mov     si, 1
001825F5  jmp     short def_1824F6; jumptable 001824F6 default case, cases 1-5
001825F7  jmp     loc_1824A3; jumptable 001824F6 case 8
001825FA  or      si, si; jumptable 001824F6 default case, cases 1-5
001825FC  jnz     short loc_182601
001825FE  jmp     loc_182448
00182601  xor     si, si
00182603  call    sub_135DF4; Utility function (473B, 16 calls) - needs investigation
00182608  mov     ax, 7894h
0018260B  mov     es, ax
0018260D  mov     es:word_79B74, 2
00182614  mov     ax, 7894h
00182617  mov     es, ax
00182619  mov     es:word_79BD6, 0FFFFh
00182620  mov     ax, 7894h
00182623  mov     es, ax
00182625  mov     es:word_79E32, 0
0018262C  mov     ax, 7894h
0018262F  mov     es, ax
00182631  mov     es:word_79D1E, 0
00182638  push    7894h
0018263B  push    0F32h
0018263E  mov     ax, 6E1Eh
00182641  mov     es, ax
00182643  push    word ptr es:loc_6E2E9
00182648  push    word ptr es:loc_6E2E6+1
0018264D  call    string_copy_with_offset
00182652  add     sp, 8
00182655  push    7894h
00182658  push    0F32h
0018265B  mov     ax, 602Eh
0018265E  mov     es, ax
00182660  push    word ptr es:aJ0+2; ".`\n"
00182665  push    word ptr es:aJ0; "J0.`\n"
0018266A  push    7894h
0018266D  push    0F32h
00182670  call    string_concatenate
00182675  add     sp, 0Ch
00182678  push    7894h
0018267B  push    0F32h
0018267E  mov     ax, 602Eh
00182681  mov     es, ax
00182683  push    word ptr es:aJ0+2; ".`\n"
00182688  push    word ptr es:aJ0; "J0.`\n"
0018268D  push    7894h
00182690  push    0F32h
00182693  call    string_concatenate
00182698  add     sp, 0Ch
0018269B  push    7894h
0018269E  push    0F32h
001826A1  mov     ax, 6E1Eh
001826A4  mov     es, ax
001826A6  push    word ptr es:loc_6E2ED
001826AB  push    word ptr es:loc_6E2EA+1
001826B0  push    7894h
001826B3  push    0F32h
001826B6  call    string_concatenate
001826BB  add     sp, 0Ch
001826BE  push    7894h
001826C1  push    0F32h
001826C4  mov     ax, 602Eh
001826C7  mov     es, ax
001826C9  push    word ptr es:aJ0+2; ".`\n"
001826CE  push    word ptr es:aJ0; "J0.`\n"
001826D3  push    7894h
001826D6  push    0F32h
001826D9  call    string_concatenate
001826DE  add     sp, 0Ch
001826E1  push    0
001826E3  push    7894h
001826E6  push    0F32h
001826E9  call    sub_135C57
001826EE  add     sp, 6
001826F1  mov     dx, 7894h
001826F4  mov     es, dx
001826F6  mov     es:word_79D1E, ax
001826FA  push    0
001826FC  call    loc_69C25
00182701  pop     cx
00182702  mov     ax, 6E1Eh
00182705  mov     es, ax
00182707  mov     word ptr es:byte_6E1C9+23h, 1
0018270E  call    undoc_12661D
00182713  call    sub_12805C
00182718  mov     ax, 6E1Eh
0018271B  mov     es, ax
0018271D  mov     word ptr es:byte_6E1C9+17h, 0
00182724  mov     ax, 6E1Eh
00182727  mov     es, ax
00182729  mov     word ptr es:byte_6E1C9+35h, 7FFFh
00182730  mov     ax, 6E1Eh
00182733  mov     es, ax
00182735  mov     word ptr es:byte_6E1C9+37h, 7FFFh
0018273C  mov     [bp+var_6], 0
00182741  mov     [bp+var_4], 1
00182746  call    sub_13DB56; Set CS:byte_13DABA to 0xFF (7B, 20 calls)
0018274B  jmp     loc_1837B0
0018274E  mov     ax, 7894h
00182751  mov     es, ax
00182753  push    es:word_79E72
00182758  push    es:word_79E70
0018275D  call    sub_13DAD0; Utility function (133B, 16 calls) - needs investigation
00182762  pop     cx
00182763  pop     cx
00182764  mov     bx, 6E1Eh
00182767  mov     es, bx
00182769  mov     word ptr es:byte_6E1C9+1Dh, dx
0018276E  mov     word ptr es:byte_6E1C9+1Bh, ax
00182772  mov     ax, 6E1Eh
00182775  mov     es, ax
00182777  les     bx, dword ptr es:byte_6E1C9+1Bh
0018277C  mov     al, es:[bx]
0018277F  mov     ah, 0
00182781  and     ax, 7
00182784  mov     bx, ax
00182786  cmp     bx, 7; switch 8 cases
00182789  jbe     short loc_18278E
0018278B  jmp     def_182790; jumptable 00182790 default case, cases 1,6
0018278E  shl     bx, 1
00182790  jmp     cs:jpt_182790[bx]; switch jump
00182795  cmp     [bp+var_4], 0; jumptable 00182790 case 0
00182799  jnz     short loc_18279E
0018279B  jmp     loc_182BFC
0018279E  mov     ax, 6E1Eh
001827A1  mov     es, ax
001827A3  inc     word ptr es:byte_6E1C9+1Bh
001827A8  mov     es, ax
001827AA  mov     ax, word ptr es:byte_6E1C9+1Dh
001827AE  mov     dx, word ptr es:byte_6E1C9+1Bh
001827B3  mov     bx, 6E1Eh
001827B6  mov     es, bx
001827B8  mov     word ptr es:byte_6E1C9+21h, ax
001827BC  mov     word ptr es:byte_6E1C9+1Fh, dx
001827C1  mov     ax, 6E1Eh
001827C4  mov     es, ax
001827C6  les     bx, dword ptr es:byte_6E1C9+1Fh
001827CB  mov     ax, es:[bx]
001827CE  mov     dx, 6E1Eh
001827D1  mov     es, dx
001827D3  mov     word ptr es:loc_6E2A1+1, ax
001827D7  push    0FFC0h
001827D9  mov     ax, 6E1Eh
001827DC  mov     es, ax
001827DE  mov     ax, word ptr es:loc_6E2A1+1
001827E2  cwd
001827E3  push    dx
001827E4  push    ax
001827E5  call    sub_13DD40
001827EA  add     sp, 6
001827ED  mov     bx, 6E1Eh
001827F0  mov     es, bx
001827F2  mov     word ptr es:byte_6E1C9+43h, dx
001827F7  mov     word ptr es:byte_6E1C9+41h, ax
001827FB  push    0CDh
001827FE  mov     ax, 6E1Eh
00182801  mov     es, ax
00182803  push    word ptr es:byte_6E1C9+43h
00182808  push    word ptr es:byte_6E1C9+41h
0018280D  call    sub_13DD83
00182812  add     sp, 6
00182815  mov     dx, 6E1Eh
00182818  mov     es, dx
0018281A  mov     word ptr es:loc_6E2A1+1, ax
0018281E  mov     ax, 6E1Eh
00182821  mov     es, ax
00182823  add     word ptr es:byte_6E1C9+1Fh, 2
00182829  mov     es, ax
0018282B  les     bx, dword ptr es:byte_6E1C9+1Fh
00182830  mov     ax, es:[bx]
00182833  mov     dx, 6E1Eh
00182836  mov     es, dx
00182838  mov     word ptr es:loc_6E2A0, ax
0018283C  push    40h ; '@'
0018283E  mov     ax, 6E1Eh
00182841  mov     es, ax
00182843  mov     ax, word ptr es:loc_6E2A0
00182847  cwd
00182848  push    dx
00182849  push    ax
0018284A  call    sub_13DD40
0018284F  add     sp, 6
00182852  mov     bx, 6E1Eh
00182855  mov     es, bx
00182857  mov     word ptr es:byte_6E1C9+31h, dx
0018285C  mov     word ptr es:byte_6E1C9+2Fh, ax
00182860  push    0CDh
00182863  mov     ax, 6E1Eh
00182866  mov     es, ax
00182868  push    word ptr es:byte_6E1C9+31h
0018286D  push    word ptr es:byte_6E1C9+2Fh
00182872  call    sub_13DD83
00182877  add     sp, 6
0018287A  mov     dx, 6E1Eh
0018287D  mov     es, dx
0018287F  mov     word ptr es:loc_6E2A0, ax
00182883  mov     ax, 6E1Eh
00182886  mov     es, ax
00182888  add     word ptr es:byte_6E1C9+1Fh, 2
0018288E  mov     es, ax
00182890  mov     ax, word ptr es:byte_6E1C9+21h
00182894  mov     dx, word ptr es:byte_6E1C9+1Fh
00182899  mov     bx, 6E1Eh
0018289C  mov     es, bx
0018289E  mov     word ptr es:byte_6E1C9+1Dh, ax
001828A2  mov     word ptr es:byte_6E1C9+1Bh, dx
001828A7  mov     ax, 6E1Eh
001828AA  mov     es, ax
001828AC  cmp     word ptr es:byte_6E1C9+35h, 7FFFh
001828B3  jnz     short loc_1828B8
001828B5  jmp     loc_182BD5
001828B8  mov     es, ax
001828BA  mov     ax, word ptr es:byte_6E1C9+35h
001828BE  mov     dx, 4FC2h
001828C1  mov     es, dx
001828C3  sub     ax, es:word_13E00E
001828C8  cwd
001828C9  mov     bx, 6E1Eh
001828CC  mov     es, bx
001828CE  mov     word ptr es:byte_6E1C9+2Dh, dx
001828D3  mov     word ptr es:byte_6E1C9+2Bh, ax
001828D7  push    0EFh
001828DA  mov     ax, 6E1Eh
001828DD  mov     es, ax
001828DF  push    word ptr es:byte_6E1C9+2Dh
001828E4  push    word ptr es:byte_6E1C9+2Bh
001828E9  call    sub_13DD40
001828EE  add     sp, 6
001828F1  mov     bx, 6E1Eh
001828F4  mov     es, bx
001828F6  mov     word ptr es:byte_6E1C9+2Dh, dx
001828FB  mov     word ptr es:byte_6E1C9+2Bh, ax
001828FF  mov     ax, 7894h
00182902  mov     es, ax
00182904  mov     bx, es:word_79B5E
00182909  shl     bx, 1
0018290B  mov     ax, 4FC2h
0018290E  mov     es, ax
00182910  push    word ptr es:[bx+158h]
00182915  mov     ax, 6E1Eh
00182918  mov     es, ax
0018291A  push    word ptr es:byte_6E1C9+2Dh
0018291F  push    word ptr es:byte_6E1C9+2Bh
00182924  call    sub_13DD83
00182929  add     sp, 6
0018292C  mov     bx, 6E1Eh
0018292F  mov     es, bx
00182931  mov     word ptr es:byte_6E1C9+2Dh, dx
00182936  mov     word ptr es:byte_6E1C9+2Bh, ax
0018293A  mov     ax, 6E1Eh
0018293D  mov     es, ax
0018293F  mov     ax, word ptr es:byte_6E1C9+37h
00182943  mov     dx, 4FC2h
00182946  mov     es, dx
00182948  sub     ax, es:word_13E010
0018294D  cwd
0018294E  mov     bx, 6E1Eh
00182951  mov     es, bx
00182953  mov     word ptr es:byte_6E1C9+3Fh, dx
00182958  mov     word ptr es:byte_6E1C9+3Dh, ax
0018295C  push    0C7h
0018295F  mov     ax, 6E1Eh
00182962  mov     es, ax
00182964  push    word ptr es:byte_6E1C9+3Fh
00182969  push    word ptr es:byte_6E1C9+3Dh
0018296E  call    sub_13DD40
00182973  add     sp, 6
00182976  mov     bx, 6E1Eh
00182979  mov     es, bx
0018297B  mov     word ptr es:byte_6E1C9+3Fh, dx
00182980  mov     word ptr es:byte_6E1C9+3Dh, ax
00182984  mov     ax, 7894h
00182987  mov     es, ax
00182989  mov     bx, es:word_79B5E
0018298E  shl     bx, 1
00182990  mov     ax, 4FC2h
00182993  mov     es, ax
00182995  push    word ptr es:[bx+158h]
0018299A  mov     ax, 6E1Eh
0018299D  mov     es, ax
0018299F  push    word ptr es:byte_6E1C9+3Fh
001829A4  push    word ptr es:byte_6E1C9+3Dh
001829A9  call    sub_13DD83
001829AE  add     sp, 6
001829B1  mov     bx, 6E1Eh
001829B4  mov     es, bx
001829B6  mov     word ptr es:byte_6E1C9+3Fh, dx
001829BB  mov     word ptr es:byte_6E1C9+3Dh, ax
001829BF  mov     ax, 6E1Eh
001829C2  mov     es, ax
001829C4  mov     ax, word ptr es:loc_6E2A0
001829C8  mov     dx, 4FC2h
001829CB  mov     es, dx
001829CD  sub     ax, es:word_13E00E
001829D2  cwd
001829D3  mov     bx, 6E1Eh
001829D6  mov     es, bx
001829D8  mov     word ptr es:byte_6E1C9+31h, dx
001829DD  mov     word ptr es:byte_6E1C9+2Fh, ax
001829E1  push    0EFh
001829E4  mov     ax, 6E1Eh
001829E7  mov     es, ax
001829E9  push    word ptr es:byte_6E1C9+31h
001829EE  push    word ptr es:byte_6E1C9+2Fh
001829F3  call    sub_13DD40
001829F8  add     sp, 6
001829FB  mov     bx, 6E1Eh
001829FE  mov     es, bx
00182A00  mov     word ptr es:byte_6E1C9+31h, dx
00182A05  mov     word ptr es:byte_6E1C9+2Fh, ax
00182A09  mov     ax, 7894h
00182A0C  mov     es, ax
00182A0E  mov     bx, es:word_79B5E
00182A13  shl     bx, 1
00182A15  mov     ax, 4FC2h
00182A18  mov     es, ax
00182A1A  push    word ptr es:[bx+158h]
00182A1F  mov     ax, 6E1Eh
00182A22  mov     es, ax
00182A24  push    word ptr es:byte_6E1C9+31h
00182A29  push    word ptr es:byte_6E1C9+2Fh
00182A2E  call    sub_13DD83
00182A33  add     sp, 6
00182A36  mov     bx, 6E1Eh
00182A39  mov     es, bx
00182A3B  mov     word ptr es:byte_6E1C9+31h, dx
00182A40  mov     word ptr es:byte_6E1C9+2Fh, ax
00182A44  mov     ax, 6E1Eh
00182A47  mov     es, ax
00182A49  mov     ax, word ptr es:loc_6E2A1+1
00182A4D  mov     dx, 4FC2h
00182A50  mov     es, dx
00182A52  sub     ax, es:word_13E010
00182A57  cwd
00182A58  mov     bx, 6E1Eh
00182A5B  mov     es, bx
00182A5D  mov     word ptr es:byte_6E1C9+43h, dx
00182A62  mov     word ptr es:byte_6E1C9+41h, ax
00182A66  push    0C7h
00182A69  mov     ax, 6E1Eh
00182A6C  mov     es, ax
00182A6E  push    word ptr es:byte_6E1C9+43h
00182A73  push    word ptr es:byte_6E1C9+41h
00182A78  call    sub_13DD40
00182A7D  add     sp, 6
00182A80  mov     bx, 6E1Eh
00182A83  mov     es, bx
00182A85  mov     word ptr es:byte_6E1C9+43h, dx
00182A8A  mov     word ptr es:byte_6E1C9+41h, ax
00182A8E  mov     ax, 7894h
00182A91  mov     es, ax
00182A93  mov     bx, es:word_79B5E
00182A98  shl     bx, 1
00182A9A  mov     ax, 4FC2h
00182A9D  mov     es, ax
00182A9F  push    word ptr es:[bx+158h]
00182AA4  mov     ax, 6E1Eh
00182AA7  mov     es, ax
00182AA9  push    word ptr es:byte_6E1C9+43h
00182AAE  push    word ptr es:byte_6E1C9+41h
00182AB3  call    sub_13DD83
00182AB8  add     sp, 6
00182ABB  mov     bx, 6E1Eh
00182ABE  mov     es, bx
00182AC0  mov     word ptr es:byte_6E1C9+43h, dx
00182AC5  mov     word ptr es:byte_6E1C9+41h, ax
00182AC9  push    6E1Eh
00182ACC  push    2Ah ; '*'
00182ACF  push    6E1Eh
00182AD2  push    18h
00182AD5  push    6E1Eh
00182AD8  push    26h ; '&'
00182ADB  push    6E1Eh
00182ADE  push    14h
00182AE1  call    vector_arithmetic_complex; Complex vector/coordinate arithmetic (1085B, 24 calls)
00182AE6  add     sp, 10h
00182AE9  or      ax, ax
00182AEB  jnz     short loc_182AF0
00182AED  jmp     loc_182BD5
00182AF0  mov     ax, 6E1Eh
00182AF3  mov     es, ax
00182AF5  mov     ax, word ptr es:byte_6E1C9+2Bh
00182AF9  mov     dx, 6E1Eh
00182AFC  mov     es, dx
00182AFE  mov     word ptr es:byte_6E1C9+29h, ax
00182B02  mov     ax, 6E1Eh
00182B05  mov     es, ax
00182B07  mov     ax, word ptr es:byte_6E1C9+2Fh
00182B0B  mov     dx, 6E1Eh
00182B0E  mov     es, dx
00182B10  mov     word ptr es:byte_6E1C9+39h, ax
00182B14  mov     ax, 6E1Eh
00182B17  mov     es, ax
00182B19  mov     ax, word ptr es:byte_6E1C9+3Dh
00182B1D  mov     dx, 6E1Eh
00182B20  mov     es, dx
00182B22  mov     word ptr es:byte_6E1C9+33h, ax
00182B26  mov     ax, 6E1Eh
00182B29  mov     es, ax
00182B2B  mov     ax, word ptr es:byte_6E1C9+41h
00182B2F  mov     dx, 6E1Eh
00182B32  mov     es, dx
00182B34  mov     word ptr es:byte_6E1C9+3Bh, ax
00182B38  push    6E1Eh
00182B3B  push    24h ; '$'
00182B3E  push    6E1Eh
00182B41  push    22h ; '"'
00182B44  push    6E1Eh
00182B47  push    1Ch
00182B4A  push    6E1Eh
00182B4D  push    12h
00182B50  call    graphics_clip_processor
00182B55  add     sp, 10h
00182B58  or      ax, ax
00182B5A  jnz     short loc_182BD5
00182B5C  mov     ax, 4FC2h
00182B5F  mov     es, ax
00182B61  push    es:word_13E032
00182B66  mov     ax, 6E1Eh
00182B69  mov     es, ax
00182B6B  push    word ptr es:byte_6E1C9+3Bh
00182B70  mov     ax, 6E1Eh
00182B73  mov     es, ax
00182B75  push    word ptr es:byte_6E1C9+39h
00182B7A  mov     ax, 6E1Eh
00182B7D  mov     es, ax
00182B7F  push    word ptr es:byte_6E1C9+33h
00182B84  mov     ax, 6E1Eh
00182B87  mov     es, ax
00182B89  push    word ptr es:byte_6E1C9+29h
00182B8E  call    undoc_127FC4; Utility function (50B, 18 calls) - needs investigation
00182B93  add     sp, 0Ah
00182B96  call    sub_12805C
00182B9B  mov     ax, 4FC2h
00182B9E  mov     es, ax
00182BA0  push    es:word_13E018
00182BA5  mov     ax, 6E1Eh
00182BA8  mov     es, ax
00182BAA  push    word ptr es:byte_6E1C9+3Bh
00182BAF  mov     ax, 6E1Eh
00182BB2  mov     es, ax
00182BB4  push    word ptr es:byte_6E1C9+39h
00182BB9  mov     ax, 6E1Eh
00182BBC  mov     es, ax
00182BBE  push    word ptr es:byte_6E1C9+33h
00182BC3  mov     ax, 6E1Eh
00182BC6  mov     es, ax
00182BC8  push    word ptr es:byte_6E1C9+29h
00182BCD  call    undoc_127FC4; Utility function (50B, 18 calls) - needs investigation
00182BD2  add     sp, 0Ah
00182BD5  mov     ax, 6E1Eh
00182BD8  mov     es, ax
00182BDA  mov     ax, word ptr es:loc_6E2A0
00182BDE  mov     dx, 6E1Eh
00182BE1  mov     es, dx
00182BE3  mov     word ptr es:byte_6E1C9+35h, ax
00182BE7  mov     ax, 6E1Eh
00182BEA  mov     es, ax
00182BEC  mov     ax, word ptr es:loc_6E2A1+1
00182BF0  mov     dx, 6E1Eh
00182BF3  mov     es, dx
00182BF5  mov     word ptr es:byte_6E1C9+37h, ax
00182BF9  jmp     def_182790; jumptable 00182790 default case, cases 1,6
00182BFC  jmp     loc_182E98
00182BFF  mov     ax, 6E1Eh; jumptable 00182790 case 2
00182C02  mov     es, ax
00182C04  les     bx, dword ptr es:byte_6E1C9+1Bh
00182C09  mov     al, es:[bx]
00182C0C  mov     ah, 0
00182C0E  mov     dx, 6E1Eh
00182C11  mov     es, dx
00182C13  mov     word ptr es:byte_6E1C9+45h, ax
00182C17  mov     ax, 6E1Eh
00182C1A  mov     es, ax
00182C1C  sar     word ptr es:byte_6E1C9+45h, 3
00182C22  mov     es, ax
00182C24  and     word ptr es:byte_6E1C9+45h, 7
00182C2B  mov     es, ax
00182C2D  mov     ax, word ptr es:byte_6E1C9+45h
00182C31  shl     ax, 1
00182C33  mov     dx, 6E1Eh
00182C36  mov     es, dx
00182C38  les     bx, dword ptr es:loc_6E2A1+3
00182C3D  add     bx, ax
00182C3F  cmp     word ptr es:[bx], 0FFFFh
00182C43  jnz     short loc_182C48
00182C45  jmp     loc_182E98
00182C48  mov     ax, 6E1Eh
00182C4B  mov     es, ax
00182C4D  inc     word ptr es:byte_6E1C9+1Bh
00182C52  mov     es, ax
00182C54  inc     word ptr es:byte_6E1C9+1Bh
00182C59  mov     es, ax
00182C5B  les     bx, dword ptr es:byte_6E1C9+1Bh
00182C60  mov     al, es:[bx]
00182C63  mov     ah, 0
00182C65  mov     dx, 6E1Eh
00182C68  mov     es, dx
00182C6A  mov     es:word_6E2B8, ax
00182C6E  mov     ax, 6E1Eh
00182C71  mov     es, ax
00182C73  inc     word ptr es:byte_6E1C9+1Bh
00182C78  mov     es, ax
00182C7A  inc     word ptr es:byte_6E1C9+1Bh
00182C7F  mov     es, ax
00182C81  les     bx, dword ptr es:byte_6E1C9+1Bh
00182C86  mov     al, es:[bx]
00182C89  mov     ah, 0
00182C8B  mov     [bp+var_8], ax
00182C8E  and     [bp+var_8], 3Fh
00182C93  mov     ax, 602Eh
00182C96  mov     es, ax
00182C98  les     bx, es:dword_151B42
00182C9D  add     bx, [bp+var_8]
00182CA0  cmp     byte ptr es:[bx], 0
00182CA4  jz      short loc_182CA9
00182CA6  jmp     def_182790; jumptable 00182790 default case, cases 1,6
00182CA9  mov     ax, 602Eh
00182CAC  mov     es, ax
00182CAE  les     bx, es:dword_151B42
00182CB3  add     bx, [bp+var_8]
00182CB6  mov     byte ptr es:[bx], 2
00182CBA  mov     ax, 6E1Eh
00182CBD  mov     es, ax
00182CBF  inc     word ptr es:byte_6E1C9+1Bh
00182CC4  mov     ax, 6E1Eh
00182CC7  mov     es, ax
00182CC9  mov     al, byte ptr es:word_6E2B8
00182CCD  push    ax
00182CCE  call    sub_127E5A; Calculate indexed pointer from table (116B, 16 calls)
00182CD3  pop     cx
00182CD4  mov     bx, 6E1Eh
00182CD7  mov     es, bx
00182CD9  mov     word ptr es:byte_6E1C9+27h, dx
00182CDE  mov     word ptr es:byte_6E1C9+25h, ax
00182CE2  push    7894h
00182CE5  push    0F32h
00182CE8  mov     ax, 602Eh
00182CEB  mov     es, ax; jump table for switch statement
00182CED  push    word ptr es:a2_0+1; ".` "
00182CF2  push    word ptr es:byte_151860
00182CF7  mov     ax, 6E1Eh
00182CFA  mov     es, ax
00182CFC  mov     ax, word ptr es:byte_6E1C9+45h
00182D00  shl     ax, 1
00182D02  mov     dx, 6E1Eh
00182D05  mov     es, dx
00182D07  les     bx, dword ptr es:loc_6E2A1+3
00182D0C  add     bx, ax
00182D0E  mov     ax, es:[bx]
00182D11  mov     dx, 42h ; 'B'
00182D14  imul    dx
00182D16  mov     dx, 6E1Eh
00182D19  mov     es, dx
00182D1B  les     bx, dword ptr es:byte_6E1C9+47h
00182D20  add     bx, ax
00182D22  mov     al, es:[bx+1]
00182D26  cbw
00182D27  shl     ax, 2
00182D2A  mov     dx, 602Eh
00182D2D  mov     bx, ax
00182D2F  mov     es, dx
00182D31  push    word ptr es:[bx+1AD8h]
00182D36  push    word ptr es:[bx+1AD6h]
00182D3B  call    string_concatenate
00182D40  add     sp, 0Ch
00182D43  push    7894h
00182D46  push    0F32h
00182D49  mov     ax, 6E1Eh
00182D4C  mov     es, ax
00182D4E  mov     ax, word ptr es:byte_6E1C9+45h
00182D52  shl     ax, 1
00182D54  mov     dx, 6E1Eh
00182D57  mov     es, dx
00182D59  les     bx, dword ptr es:loc_6E2A1+3
00182D5E  add     bx, ax
00182D60  mov     ax, es:[bx]
00182D63  mov     dx, 42h ; 'B'
00182D66  imul    dx
00182D68  mov     dx, 6E1Eh
00182D6B  mov     es, dx
00182D6D  mov     dx, word ptr es:byte_6E1C9+47h
00182D72  add     dx, ax
00182D74  inc     dx
00182D75  inc     dx
00182D76  push    word ptr es:byte_6E1C9+49h
00182D7B  push    dx
00182D7C  push    7894h
00182D7F  push    0F32h
00182D82  call    string_concatenate
00182D87  add     sp, 0Ch
00182D8A  mov     ax, 6E1Eh
00182D8D  mov     es, ax
00182D8F  cmp     es:word_6E2B8, 20h ; ' '
00182D95  jge     short loc_182DBA
00182D97  push    7894h
00182D9A  push    0F32h
00182D9D  mov     ax, 6E1Eh
00182DA0  mov     es, ax
00182DA2  push    word ptr es:loc_6E385
00182DA7  push    word ptr es:loc_6E380+3
00182DAC  push    7894h
00182DAF  push    0F32h
00182DB2  call    string_concatenate
00182DB7  add     sp, 0Ch
00182DBA  mov     ax, 602Eh
00182DBD  mov     es, ax
00182DBF  les     bx, es:dword_151B86
00182DC4  add     bx, [bp+var_8]
00182DC7  cmp     byte ptr es:[bx], 0
00182DCB  jl      short loc_182DDD
00182DCD  mov     es, ax
00182DCF  les     bx, es:dword_151B86
00182DD4  add     bx, [bp+var_8]
00182DD7  cmp     byte ptr es:[bx], 3
00182DDB  jle     short loc_182DF4
00182DDD  push    7894h
00182DE0  push    0F32h
00182DE3  mov     ax, 6E1Eh
00182DE6  mov     es, ax
00182DE8  push    word ptr es:loc_6E371
00182DED  push    word ptr es:loc_6E36C+3
00182DF2  jmp     short loc_182E1F
00182DF4  push    7894h
00182DF7  push    0F32h
00182DFA  mov     ax, 602Eh
00182DFD  mov     es, ax
00182DFF  les     bx, es:dword_151B86
00182E04  add     bx, [bp+var_8]
00182E07  mov     al, es:[bx]
00182E0A  cbw
00182E0B  shl     ax, 2
00182E0E  mov     dx, 6E1Eh
00182E11  mov     bx, ax
00182E13  mov     es, dx
00182E15  push    word ptr es:[bx+191h]
00182E1A  push    word ptr es:[bx+18Fh]
00182E1F  push    7894h
00182E22  push    0F32h
00182E25  call    string_concatenate
00182E2A  add     sp, 0Ch
00182E2D  push    7894h
00182E30  push    0F32h
00182E33  mov     ax, 6E1Eh
00182E36  mov     es, ax
00182E38  push    word ptr es:byte_6E1C9+27h
00182E3D  push    word ptr es:byte_6E1C9+25h
00182E42  push    7894h
00182E45  push    0F32h
00182E48  call    string_concatenate
00182E4D  add     sp, 0Ch
00182E50  mov     ax, 6E1Eh
00182E53  mov     es, ax
00182E55  cmp     es:word_6E2B8, 20h ; ' '
00182E5B  jge     short loc_182E80
00182E5D  push    7894h
00182E60  push    0F32h
00182E63  mov     ax, 6E1Eh
00182E66  mov     es, ax
00182E68  push    word ptr es:loc_6E387+2
00182E6D  push    word ptr es:loc_6E387
00182E72  push    7894h
00182E75  push    0F32h
00182E78  call    string_concatenate
00182E7D  add     sp, 0Ch
00182E80  push    7894h
00182E83  push    0F32h
00182E86  mov     ax, 602Eh
00182E89  mov     es, ax
00182E8B  push    es:word_1516B9
00182E90  push    es:word_1516B7
00182E95  jmp     loc_183091
00182E98  mov     ax, 6E1Eh
00182E9B  mov     es, ax
00182E9D  add     word ptr es:byte_6E1C9+1Bh, 5
00182EA3  jmp     def_182790; jumptable 00182790 default case, cases 1,6
00182EA6  mov     ax, 6E1Eh; jumptable 00182790 case 3
00182EA9  mov     es, ax
00182EAB  les     bx, dword ptr es:byte_6E1C9+1Bh
00182EB0  mov     al, es:[bx]
00182EB3  mov     ah, 0
00182EB5  mov     dx, 6E1Eh
00182EB8  mov     es, dx
00182EBA  mov     word ptr es:byte_6E1C9+45h, ax
00182EBE  mov     ax, 6E1Eh
00182EC1  mov     es, ax
00182EC3  sar     word ptr es:byte_6E1C9+45h, 3
00182EC9  mov     es, ax
00182ECB  and     word ptr es:byte_6E1C9+45h, 7
00182ED2  mov     es, ax
00182ED4  mov     ax, word ptr es:byte_6E1C9+45h
00182ED8  and     ax, 7
00182EDB  shl     ax, 1
00182EDD  mov     dx, 6E1Eh
00182EE0  mov     es, dx
00182EE2  les     bx, dword ptr es:loc_6E2A1+3
00182EE7  add     bx, ax
00182EE9  cmp     word ptr es:[bx], 0FFFFh
00182EED  jnz     short loc_182EF2
00182EEF  jmp     def_182790; jumptable 00182790 default case, cases 1,6
00182EF2  mov     ax, 6E1Eh
00182EF5  mov     es, ax
00182EF7  inc     word ptr es:byte_6E1C9+1Bh
00182EFC  mov     es, ax
00182EFE  inc     word ptr es:byte_6E1C9+1Bh
00182F03  mov     es, ax
00182F05  les     bx, dword ptr es:byte_6E1C9+1Bh
00182F0A  mov     al, es:[bx]
00182F0D  mov     ah, 0
00182F0F  mov     dx, 6E1Eh
00182F12  mov     es, dx
00182F14  mov     es:word_6E2B8, ax
00182F18  mov     ax, 6E1Eh
00182F1B  mov     es, ax
00182F1D  and     es:word_6E2B8, 3Fh
00182F24  mov     es, ax
00182F26  or      es:word_6E2B8, 40h
00182F2D  mov     ax, 6E1Eh
00182F30  mov     es, ax
00182F32  inc     word ptr es:byte_6E1C9+1Bh
00182F37  mov     ax, 6E1Eh
00182F3A  mov     es, ax
00182F3C  mov     al, byte ptr es:word_6E2B8
00182F40  push    ax
00182F41  call    sub_127E5A; Calculate indexed pointer from table (116B, 16 calls)
00182F46  pop     cx
00182F47  mov     bx, 6E1Eh
00182F4A  mov     es, bx
00182F4C  mov     word ptr es:byte_6E1C9+27h, dx
00182F51  mov     word ptr es:byte_6E1C9+25h, ax
00182F55  push    7894h
00182F58  push    0F32h
00182F5B  mov     ax, 602Eh
00182F5E  mov     es, ax
00182F60  push    word ptr es:a2_0+1; ".` "
00182F65  push    word ptr es:byte_151860
00182F6A  mov     ax, 6E1Eh
00182F6D  mov     es, ax
00182F6F  mov     ax, word ptr es:byte_6E1C9+45h
00182F73  shl     ax, 1
00182F75  mov     dx, 6E1Eh
00182F78  mov     es, dx
00182F7A  les     bx, dword ptr es:loc_6E2A1+3
00182F7F  add     bx, ax
00182F81  mov     ax, es:[bx]
00182F84  mov     dx, 42h ; 'B'
00182F87  imul    dx
00182F89  mov     dx, 6E1Eh
00182F8C  mov     es, dx
00182F8E  les     bx, dword ptr es:byte_6E1C9+47h
00182F93  add     bx, ax
00182F95  mov     al, es:[bx+1]
00182F99  cbw
00182F9A  shl     ax, 2
00182F9D  mov     dx, 602Eh
00182FA0  mov     bx, ax
00182FA2  mov     es, dx
00182FA4  push    word ptr es:[bx+1AD8h]
00182FA9  push    word ptr es:[bx+1AD6h]
00182FAE  call    string_concatenate
00182FB3  add     sp, 0Ch
00182FB6  push    7894h
00182FB9  push    0F32h
00182FBC  mov     ax, 6E1Eh
00182FBF  mov     es, ax
00182FC1  mov     ax, word ptr es:byte_6E1C9+45h
00182FC5  shl     ax, 1
00182FC7  mov     dx, 6E1Eh
00182FCA  mov     es, dx
00182FCC  les     bx, dword ptr es:loc_6E2A1+3
00182FD1  add     bx, ax
00182FD3  mov     ax, es:[bx]
00182FD6  mov     dx, 42h ; 'B'
00182FD9  imul    dx
00182FDB  mov     dx, 6E1Eh
00182FDE  mov     es, dx
00182FE0  mov     dx, word ptr es:byte_6E1C9+47h
00182FE5  add     dx, ax
00182FE7  inc     dx
00182FE8  inc     dx
00182FE9  push    word ptr es:byte_6E1C9+49h
00182FEE  push    dx
00182FEF  push    7894h
00182FF2  push    0F32h
00182FF5  call    string_concatenate
00182FFA  add     sp, 0Ch
00182FFD  push    7894h
00183000  push    0F32h
00183003  mov     ax, 602Eh
00183006  mov     es, ax
00183008  push    word ptr es:a2_0+1; ".` "
0018300D  push    word ptr es:byte_151860
00183012  push    7894h
00183015  push    0F32h
00183018  call    string_concatenate
0018301D  add     sp, 0Ch
00183020  mov     ax, 6E1Eh
00183023  mov     es, ax
00183025  and     es:word_6E2B8, 3Fh
0018302C  mov     es, ax
0018302E  cmp     es:word_6E2B8, 20h ; ' '
00183034  jge     short loc_183059
00183036  push    7894h
00183039  push    0F32h
0018303C  mov     ax, 6E1Eh
0018303F  mov     es, ax
00183041  push    word ptr es:loc_6E385
00183046  push    word ptr es:loc_6E380+3
0018304B  push    7894h
0018304E  push    0F32h
00183051  call    string_concatenate
00183056  add     sp, 0Ch
00183059  push    7894h
0018305C  push    0F32h
0018305F  mov     ax, 6E1Eh
00183062  mov     es, ax
00183064  push    word ptr es:loc_6E2FC+1
00183069  push    word ptr es:loc_6E2FB
0018306E  push    7894h
00183071  push    0F32h
00183074  call    string_concatenate
00183079  add     sp, 0Ch
0018307C  push    7894h
0018307F  push    0F32h
00183082  mov     ax, 6E1Eh
00183085  mov     es, ax
00183087  push    word ptr es:byte_6E1C9+27h
0018308C  push    word ptr es:byte_6E1C9+25h
00183091  push    7894h
00183094  push    0F32h
00183097  call    string_concatenate
0018309C  add     sp, 0Ch
0018309F  push    7894h
001830A2  push    0F32h
001830A5  mov     ax, 602Eh
001830A8  mov     es, ax
001830AA  push    word ptr es:aJ0+2; ".`\n"
001830AF  push    word ptr es:aJ0; "J0.`\n"
001830B4  push    7894h
001830B7  push    0F32h
001830BA  call    string_concatenate
001830BF  add     sp, 0Ch
001830C2  push    7894h
001830C5  push    0F32h
001830C8  mov     ax, 602Eh
001830CB  mov     es, ax
001830CD  push    word ptr es:aJ0+2; ".`\n"
001830D2  push    word ptr es:aJ0; "J0.`\n"
001830D7  push    7894h
001830DA  push    0F32h
001830DD  call    string_concatenate
001830E2  add     sp, 0Ch
001830E5  mov     ax, 7894h
001830E8  mov     es, ax
001830EA  push    es:word_79D1E
001830EF  push    7894h
001830F2  push    0F32h
001830F5  call    sub_135C57
001830FA  add     sp, 6
001830FD  mov     dx, 7894h
00183100  mov     es, dx
00183102  mov     es:word_79D1E, ax
00183106  mov     [bp+var_6], 0Fh
0018310B  jmp     def_182790; jumptable 00182790 default case, cases 1,6
0018310E  mov     ax, 6E1Eh; jumptable 00182790 case 4
00183111  mov     es, ax
00183113  les     bx, dword ptr es:byte_6E1C9+1Bh
00183118  mov     al, es:[bx]
0018311B  mov     ah, 0
0018311D  mov     dx, 6E1Eh
00183120  mov     es, dx
00183122  mov     word ptr es:byte_6E1C9+45h, ax
00183126  mov     ax, 6E1Eh
00183129  mov     es, ax
0018312B  sar     word ptr es:byte_6E1C9+45h, 3
00183131  mov     es, ax
00183133  and     word ptr es:byte_6E1C9+45h, 7
0018313A  mov     ax, 6E1Eh
0018313D  mov     es, ax
0018313F  les     bx, dword ptr es:byte_6E1C9+1Bh
00183144  mov     al, es:[bx]
00183147  mov     ah, 0
00183149  mov     dx, 6E1Eh
0018314C  mov     es, dx
0018314E  mov     word ptr es:byte_6E1C9+4Dh, ax
00183152  mov     ax, 6E1Eh
00183155  mov     es, ax
00183157  sar     word ptr es:byte_6E1C9+4Dh, 6
0018315D  mov     es, ax
0018315F  and     word ptr es:byte_6E1C9+4Dh, 1
00183166  mov     ax, 6E1Eh
00183169  mov     es, ax
0018316B  inc     word ptr es:byte_6E1C9+1Bh
00183170  mov     es, ax
00183172  inc     word ptr es:byte_6E1C9+1Bh
00183177  push    7894h
0018317A  push    0F32h
0018317D  mov     ax, 602Eh
00183180  mov     es, ax
00183182  push    word ptr es:a2_0+1; ".` "
00183187  push    word ptr es:byte_151860
0018318C  mov     ax, 6E1Eh
0018318F  mov     es, ax
00183191  mov     ax, word ptr es:byte_6E1C9+45h
00183195  shl     ax, 1
00183197  mov     dx, 6E1Eh
0018319A  mov     es, dx
0018319C  les     bx, dword ptr es:loc_6E2A1+3
001831A1  add     bx, ax
001831A3  mov     ax, es:[bx]
001831A6  mov     dx, 42h ; 'B'
001831A9  imul    dx
001831AB  mov     dx, 6E1Eh
001831AE  mov     es, dx
001831B0  les     bx, dword ptr es:byte_6E1C9+47h
001831B5  add     bx, ax
001831B7  mov     al, es:[bx+1]
001831BB  cbw
001831BC  shl     ax, 2
001831BF  mov     dx, 602Eh
001831C2  mov     bx, ax
001831C4  mov     es, dx
001831C6  push    word ptr es:[bx+1AD8h]
001831CB  push    word ptr es:[bx+1AD6h]
001831D0  call    string_concatenate
001831D5  add     sp, 0Ch
001831D8  push    7894h
001831DB  push    0F32h
001831DE  mov     ax, 6E1Eh
001831E1  mov     es, ax
001831E3  mov     ax, word ptr es:byte_6E1C9+45h
001831E7  shl     ax, 1
001831E9  mov     dx, 6E1Eh
001831EC  mov     es, dx
001831EE  les     bx, dword ptr es:loc_6E2A1+3
001831F3  add     bx, ax
001831F5  mov     ax, es:[bx]
001831F8  mov     dx, 42h ; 'B'
001831FB  imul    dx
001831FD  mov     dx, 6E1Eh
00183200  mov     es, dx
00183202  mov     dx, word ptr es:byte_6E1C9+47h
00183207  add     dx, ax
00183209  inc     dx
0018320A  inc     dx
0018320B  push    word ptr es:byte_6E1C9+49h
00183210  push    dx
00183211  push    7894h
00183214  push    0F32h
00183217  call    string_concatenate
0018321C  add     sp, 0Ch
0018321F  push    7894h
00183222  push    0F32h
00183225  mov     ax, 602Eh
00183228  mov     es, ax
0018322A  push    word ptr es:a2_0+1; ".` "
0018322F  push    word ptr es:byte_151860
00183234  push    7894h
00183237  push    0F32h
0018323A  call    string_concatenate
0018323F  add     sp, 0Ch
00183242  mov     ax, 6E1Eh
00183245  mov     es, ax
00183247  cmp     word ptr es:byte_6E1C9+4Dh, 0
0018324D  jnz     short loc_183266
0018324F  push    7894h
00183252  push    0F32h
00183255  mov     ax, 6E1Eh
00183258  mov     es, ax
0018325A  push    word ptr es:loc_6E301
0018325F  push    word ptr es:loc_6E2FF
00183264  jmp     short loc_18327B
00183266  push    7894h
00183269  push    0F32h
0018326C  mov     ax, 6E1Eh
0018326F  mov     es, ax
00183271  push    word ptr es:loc_6E303+2
00183276  push    word ptr es:loc_6E303
0018327B  push    7894h
0018327E  push    0F32h
00183281  call    string_concatenate
00183286  add     sp, 0Ch
00183289  push    7894h
0018328C  push    0F32h
0018328F  mov     ax, 602Eh
00183292  mov     es, ax
00183294  push    word ptr es:aJ0+2; ".`\n"
00183299  push    word ptr es:aJ0; jumptable 00186D81 case 0
0018329E  push    7894h
001832A1  push    0F32h
001832A4  call    string_concatenate
001832A9  add     sp, 0Ch
001832AC  push    7894h
001832AF  push    0F32h
001832B2  mov     ax, 602Eh
001832B5  mov     es, ax
001832B7  push    word ptr es:aJ0+2; ".`\n"
001832BC  push    word ptr es:aJ0; "J0.`\n"
001832C1  push    7894h
001832C4  push    0F32h
001832C7  call    string_concatenate
001832CC  add     sp, 0Ch
001832CF  mov     [bp+var_6], 0Fh
001832D4  mov     ax, 6E1Eh
001832D7  mov     es, ax
001832D9  mov     ax, word ptr es:byte_6E1C9+45h
001832DD  shl     ax, 1
001832DF  mov     dx, 6E1Eh
001832E2  mov     es, dx
001832E4  les     bx, dword ptr es:loc_6E2A1+3
001832E9  add     bx, ax
001832EB  cmp     word ptr es:[bx], 0FFFFh
001832EF  jnz     short loc_1832F4
001832F1  jmp     def_182790; jumptable 00182790 default case, cases 1,6
001832F4  jmp     loc_1836F1
001832F7  mov     ax, 6E1Eh; jumptable 00182790 case 5
001832FA  mov     es, ax
001832FC  les     bx, dword ptr es:byte_6E1C9+1Bh
00183301  mov     al, es:[bx]
00183304  mov     ah, 0
00183306  mov     dx, 6E1Eh
00183309  mov     es, dx
0018330B  mov     word ptr es:byte_6E1C9+45h, ax
0018330F  mov     ax, 6E1Eh
00183312  mov     es, ax
00183314  sar     word ptr es:byte_6E1C9+45h, 3
0018331A  mov     es, ax
0018331C  and     word ptr es:byte_6E1C9+45h, 7
00183323  mov     ax, 6E1Eh
00183326  mov     es, ax
00183328  les     bx, dword ptr es:byte_6E1C9+1Bh
0018332D  mov     al, es:[bx]
00183330  mov     ah, 0
00183332  mov     dx, 6E1Eh
00183335  mov     es, dx
00183337  mov     word ptr es:byte_6E1C9+4Dh, ax
0018333B  mov     ax, 6E1Eh
0018333E  mov     es, ax
00183340  sar     word ptr es:byte_6E1C9+4Dh, 6
00183346  mov     es, ax
00183348  and     word ptr es:byte_6E1C9+4Dh, 3
0018334F  mov     ax, 6E1Eh
00183352  mov     es, ax
00183354  inc     word ptr es:byte_6E1C9+1Bh
00183359  mov     es, ax
0018335B  les     bx, dword ptr es:byte_6E1C9+1Bh
00183360  mov     al, es:[bx]
00183363  mov     ah, 0
00183365  mov     dx, 6E1Eh
00183368  mov     es, dx
0018336A  mov     es:word_6E2B8, ax
0018336E  mov     ax, 6E1Eh
00183371  mov     es, ax
00183373  test    es:word_6E2B8, 80h
0018337A  jz      short loc_1833BE
0018337C  mov     es, ax
0018337E  and     es:word_6E2B8, 3Fh
00183385  mov     es, ax
00183387  cmp     es:word_6E2B8, 33h ; '3'
0018338D  jge     short loc_1833B1; jumptable 001833A0 cases 39-43,48
0018338F  mov     es, ax
00183391  mov     bx, es:word_6E2B8
00183396  sub     bx, 27h ; '''; switch 10 cases
00183399  cmp     bx, 9
0018339C  ja      short def_1833A0; jumptable 001833A0 default case, cases 44-47
0018339E  shl     bx, 1
001833A0  jmp     cs:jpt_1833A0[bx]; switch jump
001833A5  mov     ax, 6E1Eh; jumptable 001833A0 default case, cases 44-47
001833A8  mov     es, ax
001833AA  mov     es:word_6E2B8, 29h ; ')'
001833B1  mov     ax, 6E1Eh; jumptable 001833A0 cases 39-43,48
001833B4  mov     es, ax
001833B6  add     es:word_6E2B8, 40h ; '@'
001833BC  jmp     short loc_1833CA
001833BE  mov     ax, 6E1Eh
001833C1  mov     es, ax
001833C3  and     es:word_6E2B8, 3Fh
001833CA  mov     ax, 6E1Eh
001833CD  mov     es, ax
001833CF  mov     al, byte ptr es:word_6E2B8
001833D3  push    ax
001833D4  call    sub_127E5A; Calculate indexed pointer from table (116B, 16 calls)
001833D9  pop     cx
001833DA  mov     bx, 6E1Eh
001833DD  mov     es, bx
001833DF  mov     word ptr es:byte_6E1C9+27h, dx
001833E4  mov     word ptr es:byte_6E1C9+25h, ax
001833E8  mov     ax, 6E1Eh
001833EB  mov     es, ax
001833ED  inc     word ptr es:byte_6E1C9+1Bh
001833F2  push    7894h
001833F5  push    0F32h
001833F8  mov     ax, 602Eh
001833FB  mov     es, ax
001833FD  push    word ptr es:a2_0+1; ".` "
00183402  push    word ptr es:byte_151860
00183407  mov     ax, 6E1Eh
0018340A  mov     es, ax
0018340C  mov     ax, word ptr es:byte_6E1C9+45h
00183410  shl     ax, 1
00183412  mov     dx, 6E1Eh
00183415  mov     es, dx
00183417  les     bx, dword ptr es:loc_6E2A1+3
0018341C  add     bx, ax
0018341E  mov     ax, es:[bx]
00183421  mov     dx, 42h ; 'B'
00183424  imul    dx
00183426  mov     dx, 6E1Eh
00183429  mov     es, dx
0018342B  les     bx, dword ptr es:byte_6E1C9+47h
00183430  add     bx, ax
00183432  mov     al, es:[bx+1]
00183436  cbw
00183437  shl     ax, 2
0018343A  mov     dx, 602Eh
0018343D  mov     bx, ax
0018343F  mov     es, dx
00183441  push    word ptr es:[bx+1AD8h]
00183446  push    word ptr es:[bx+1AD6h]
0018344B  call    string_concatenate
00183450  add     sp, 0Ch
00183453  push    7894h
00183456  push    0F32h
00183459  mov     ax, 6E1Eh
0018345C  mov     es, ax
0018345E  mov     ax, word ptr es:byte_6E1C9+45h
00183462  shl     ax, 1
00183464  mov     dx, 6E1Eh
00183467  mov     es, dx
00183469  les     bx, dword ptr es:loc_6E2A1+3
0018346E  add     bx, ax
00183470  mov     ax, es:[bx]
00183473  mov     dx, 42h ; 'B'
00183476  imul    dx
00183478  mov     dx, 6E1Eh
0018347B  mov     es, dx
0018347D  mov     dx, word ptr es:byte_6E1C9+47h
00183482  add     dx, ax
00183484  inc     dx
00183485  inc     dx
00183486  push    word ptr es:byte_6E1C9+49h
0018348B  push    dx
0018348C  push    7894h
0018348F  push    0F32h
00183492  call    string_concatenate
00183497  add     sp, 0Ch
0018349A  push    7894h
0018349D  push    0F32h
001834A0  mov     ax, 602Eh
001834A3  mov     es, ax
001834A5  push    word ptr es:a2_0+1; ".` "
001834AA  push    word ptr es:byte_151860
001834AF  push    7894h
001834B2  push    0F32h
001834B5  call    string_concatenate
001834BA  add     sp, 0Ch
001834BD  mov     ax, 6E1Eh
001834C0  mov     es, ax
001834C2  mov     ax, es:word_6E2B8
001834C6  mov     dx, 7891h
001834C9  mov     es, dx
001834CB  cmp     ax, es:word_78910
001834D0  jnz     short loc_1834D5
001834D2  jmp     loc_183631
001834D5  push    7894h
001834D8  push    0F32h
001834DB  mov     ax, 6E1Eh
001834DE  mov     es, ax
001834E0  push    word ptr es:loc_6E307+2
001834E5  push    word ptr es:loc_6E307
001834EA  push    7894h
001834ED  push    0F32h
001834F0  call    string_concatenate
001834F5  add     sp, 0Ch
001834F8  push    7894h
001834FB  push    0F32h
001834FE  mov     ax, 6E1Eh
00183501  mov     es, ax
00183503  push    word ptr es:byte_6E1C9+27h
00183508  push    word ptr es:byte_6E1C9+25h
0018350D  push    7894h
00183510  push    0F32h
00183513  call    string_concatenate
00183518  add     sp, 0Ch
0018351B  push    7894h
0018351E  push    0F32h
00183521  mov     ax, 602Eh
00183524  mov     es, ax
00183526  push    word ptr es:a2_0+1; ".` "
0018352B  push    word ptr es:byte_151860
00183530  push    7894h
00183533  push    0F32h
00183536  call    string_concatenate
0018353B  add     sp, 0Ch
0018353E  mov     ax, 6E1Eh
00183541  mov     es, ax
00183543  mov     ax, word ptr es:byte_6E1C9+45h
00183547  shl     ax, 1
00183549  mov     dx, 6E1Eh
0018354C  mov     es, dx
0018354E  les     bx, dword ptr es:loc_6E2A1+3
00183553  add     bx, ax
00183555  mov     ax, es:[bx]
00183558  mov     dx, 42h ; 'B'
0018355B  imul    dx
0018355D  mov     dx, 6E1Eh
00183560  mov     es, dx
00183562  les     bx, dword ptr es:byte_6E1C9+47h
00183567  add     bx, ax
00183569  mov     al, es:[bx+26h]
0018356D  cbw
0018356E  and     ax, 7
00183571  cmp     ax, 6
00183574  jnz     short loc_183579
00183576  jmp     loc_18361A
00183579  push    7894h
0018357C  push    0F32h
0018357F  mov     ax, 602Eh
00183582  mov     es, ax
00183584  push    es:word_1516C5
00183589  push    es:word_1516C3
0018358E  push    7894h
00183591  push    0F32h
00183594  call    string_concatenate
00183599  add     sp, 0Ch
0018359C  push    7894h
0018359F  push    0F32h
001835A2  mov     ax, 6E1Eh
001835A5  mov     es, ax
001835A7  mov     ax, word ptr es:byte_6E1C9+45h
001835AB  shl     ax, 1
001835AD  mov     dx, 6E1Eh
001835B0  mov     es, dx
001835B2  les     bx, dword ptr es:loc_6E2A1+3
001835B7  add     bx, ax
001835B9  mov     ax, es:[bx]
001835BC  mov     dx, 42h ; 'B'
001835BF  imul    dx
001835C1  mov     dx, 6E1Eh
001835C4  mov     es, dx
001835C6  les     bx, dword ptr es:byte_6E1C9+47h
001835CB  add     bx, ax
001835CD  mov     al, es:[bx+26h]
001835D1  cbw
001835D2  and     ax, 0Fh
001835D5  shl     ax, 2
001835D8  mov     dx, 602Eh
001835DB  mov     bx, ax
001835DD  mov     es, dx
001835DF  push    word ptr es:[bx+1B9Bh]
001835E4  push    word ptr es:[bx+1B99h]
001835E9  push    7894h
001835EC  push    0F32h
001835EF  call    string_concatenate
001835F4  add     sp, 0Ch
001835F7  push    7894h
001835FA  push    0F32h
001835FD  mov     ax, 602Eh
00183600  mov     es, ax
00183602  push    es:word_1516CB
00183607  push    es:word_1516C9
0018360C  push    7894h
0018360F  push    0F32h
00183612  call    string_concatenate
00183617  add     sp, 0Ch
0018361A  push    7894h
0018361D  push    0F32h
00183620  mov     ax, 602Eh
00183623  mov     es, ax
00183625  push    es:word_1516B9
0018362A  push    es:word_1516B7
0018362F  jmp     short loc_183646
00183631  push    7894h
00183634  push    0F32h
00183637  mov     ax, 6E1Eh
0018363A  mov     es, ax
0018363C  push    word ptr es:loc_6E3A0+1
00183641  push    word ptr es:loc_6E39A+5
00183646  push    7894h
00183649  push    0F32h
0018364C  call    string_concatenate
00183651  add     sp, 0Ch
00183654  push    7894h
00183657  push    0F32h
0018365A  mov     ax, 602Eh
0018365D  mov     es, ax
0018365F  push    word ptr es:aJ0+2; ".`\n"
00183664  push    word ptr es:aJ0; "J0.`\n"
00183669  push    7894h
0018366C  push    0F32h
0018366F  call    string_concatenate
00183674  add     sp, 0Ch
00183677  push    7894h
0018367A  push    0F32h
0018367D  mov     ax, 602Eh
00183680  mov     es, ax
00183682  push    word ptr es:aJ0+2; ".`\n"
00183687  push    word ptr es:aJ0; "J0.`\n"
0018368C  push    7894h
0018368F  push    0F32h
00183692  call    string_concatenate
00183697  add     sp, 0Ch
0018369A  mov     ax, 6E1Eh
0018369D  mov     es, ax
0018369F  cmp     word ptr es:byte_6E1C9+4Dh, 0
001836A5  jz      short def_182790; jumptable 00182790 default case, cases 1,6
001836A7  mov     ax, 6E1Eh
001836AA  mov     es, ax
001836AC  mov     bx, word ptr es:byte_6E1C9+45h
001836B1  lea     ax, [bp+var_12]
001836B4  add     bx, ax
001836B6  cmp     byte ptr ss:[bx], 0
001836BA  jz      short def_182790; jumptable 00182790 default case, cases 1,6
001836BC  mov     [bp+var_6], 1Eh
001836C1  mov     ax, 6E1Eh
001836C4  mov     es, ax
001836C6  mov     ax, word ptr es:byte_6E1C9+45h
001836CA  shl     ax, 1
001836CC  mov     dx, 6E1Eh
001836CF  mov     es, dx
001836D1  les     bx, dword ptr es:loc_6E2A1+3
001836D6  add     bx, ax
001836D8  cmp     word ptr es:[bx], 0FFFFh
001836DC  jz      short def_182790; jumptable 00182790 default case, cases 1,6
001836DE  mov     ax, 6E1Eh
001836E1  mov     es, ax
001836E3  mov     bx, word ptr es:byte_6E1C9+45h
001836E8  lea     ax, [bp+var_12]
001836EB  add     bx, ax
001836ED  mov     byte ptr ss:[bx], 0
001836F1  mov     ax, 7894h
001836F4  mov     es, ax
001836F6  push    es:word_79D1E
001836FB  push    7894h
001836FE  push    0F32h
00183701  call    sub_135C57
00183706  add     sp, 6
00183709  mov     dx, 7894h
0018370C  mov     es, dx
0018370E  mov     es:word_79D1E, ax
00183712  jmp     short def_182790; jumptable 00182790 default case, cases 1,6
00183714  mov     si, 1; jumptable 00182790 case 7
00183717  mov     ax, 7894h; jumptable 00182790 default case, cases 1,6
0018371A  mov     es, ax
0018371C  mov     ax, es:word_79D1E
00183720  add     ax, 0FFF5h
00183723  mov     dx, 7894h
00183726  mov     es, dx
00183728  mov     es:word_79E32, ax
0018372C  mov     ax, 7894h
0018372F  mov     es, ax
00183731  cmp     es:word_79E32, 0
00183737  jge     short loc_183742
00183739  mov     es, ax
0018373B  mov     es:word_79E32, 0
00183742  push    1
00183744  call    loc_69C25
00183749  pop     cx
0018374A  call    input_poll_handler; Main keyboard input handler. Processes all keyboard input.
0018374F  mov     ax, 7894h
00183752  mov     es, ax
00183754  cmp     es:graphics_mode_flag, 0
0018375A  jz      short loc_183763
0018375C  mov     [bp+var_A], 0
00183761  jmp     short loc_18376B
00183763  call    font_file_parser
00183768  mov     [bp+var_A], ax
0018376B  cmp     [bp+var_A], 1Ch
0018376F  jz      short loc_183777
00183771  cmp     [bp+var_A], 1
00183775  jnz     short loc_18378B
00183777  mov     [bp+var_4], 0
0018377C  call    far_cb_1
00183781  call    undoc_11D20D
00183786  call    far_cb_0
0018378B  cmp     [bp+var_4], 0
0018378F  jz      short loc_183796
00183791  call    sub_12805C
00183796  cmp     [bp+var_6], 0
0018379A  jz      short loc_1837B0
0018379C  cmp     [bp+var_4], 0
001837A0  jz      short loc_1837B0
001837A2  push    [bp+var_6]
001837A5  call    sub_134BF0
001837AA  pop     cx
001837AB  mov     [bp+var_6], 0
001837B0  or      si, si
001837B2  jnz     short loc_1837B7
001837B4  jmp     loc_18274E
001837B7  mov     ax, 6E1Eh
001837BA  mov     es, ax
001837BC  push    es:word_6E2A6
001837C1  push    word ptr es:loc_6E2A1+3
001837C6  push    ss
001837C7  lea     ax, [bp+var_12]
001837CA  push    ax
001837CB  call    far ptr loc_6DB11+2
001837D0  add     sp, 8
001837D3  mov     ax, 7894h
001837D6  mov     es, ax
001837D8  mov     ax, es:word_79D1E
001837DC  add     ax, 0FFF5h
001837DF  mov     dx, 7894h
001837E2  mov     es, dx
001837E4  mov     es:word_79E32, ax
001837E8  mov     ax, 7894h
001837EB  mov     es, ax
001837ED  cmp     es:word_79E32, 0
001837F3  jge     short loc_1837FE
001837F5  mov     es, ax
001837F7  mov     es:word_79E32, 0
001837FE  call    sub_13DB56; Set CS:byte_13DABA to 0xFF (7B, 20 calls)
00183803  xor     si, si
00183805  call    menu_cursor_position_set
0018380A  jmp     def_1838E7; jumptable 001838E7 default case, cases 1-5
0018380D  push    1
0018380F  call    loc_69C25
00183814  pop     cx
00183815  call    sub_12805C
0018381A  call    sub_12DB63
0018381F  mov     ax, 7894h
00183822  mov     es, ax
00183824  cmp     es:word_79B6C, 32h ; '2'
0018382A  jz      short loc_18382F
0018382C  jmp     loc_1838B9
0018382F  mov     ax, 7894h
00183832  mov     es, ax
00183834  mov     ax, es:input_scan_code_queue
00183838  cmp     ax, 1
0018383B  jz      short loc_183857
0018383D  cmp     ax, 3
00183840  jz      short loc_183849
00183842  cmp     ax, 0FFh
00183845  jz      short loc_18385A
00183847  jmp     short loc_1838B6
00183849  mov     ax, 7894h
0018384C  mov     es, ax
0018384E  mov     es:current_view_index, 7
00183855  jmp     short loc_1838D3
00183857  jmp     loc_1824A3; VIEW KEY HANDLER: Push view index 8, call view setup (likely padlock view)
0018385A  mov     ax, 4FC2h
0018385D  mov     es, ax
0018385F  push    es:word_13E012
00183864  call    sub_2C761; Overlay bridge trampoline (8B, 14 calls)
00183869  pop     cx
0018386A  mov     ax, 7894h
0018386D  mov     es, ax
0018386F  les     bx, es:menu_state_ptr
00183874  dec     word ptr es:[bx]
00183877  mov     ax, 4FC2h
0018387A  mov     es, ax
0018387C  push    es:word_13E012
00183881  call    far ptr menu_finalize_render
00183886  pop     cx
00183887  call    sub_11D274
0018388C  mov     ax, 7894h
0018388F  mov     es, ax
00183891  les     bx, es:menu_state_ptr
00183896  inc     word ptr es:[bx]
00183899  mov     ax, 4FC2h
0018389C  mov     es, ax
0018389E  push    es:word_13E012
001838A3  call    far ptr menu_finalize_render
001838A8  pop     cx
001838A9  call    undoc_12661D
001838AE  call    sub_12805C
001838B3  jmp     def_1838E7; jumptable 001838E7 default case, cases 1-5
001838B6  jmp     loc_183805
001838B9  mov     ax, 7894h
001838BC  mov     es, ax
001838BE  cmp     es:word_79B6C, 34h ; '4'
001838C4  jz      short loc_1838D3
001838C6  mov     es, ax
001838C8  cmp     es:word_79B6C, 36h ; '6'
001838CE  jz      short loc_1838D3
001838D0  jmp     def_1838E7; jumptable 001838E7 default case, cases 1-5
001838D3  mov     ax, 7894h
001838D6  mov     es, ax
001838D8  mov     bx, es:current_view_index
001838DD  cmp     bx, 8; switch 9 cases
001838E0  jbe     short loc_1838E5
001838E2  jmp     def_1838E7; jumptable 001838E7 default case, cases 1-5
001838E5  shl     bx, 1
001838E7  jmp     cs:jpt_1838E7[bx]; switch jump
001838EC  mov     ax, 7894h; jumptable 001838E7 case 0
001838EF  mov     es, ax
001838F1  cmp     es:word_79E80, 12Ch
001838F8  jge     short loc_1838FD
001838FA  jmp     def_1838E7; jumptable 001838E7 default case, cases 1-5
001838FD  mov     ax, 7894h
00183900  mov     es, ax
00183902  push    es:current_view_index
00183907  call    far ptr loc_69CBE
0018390C  pop     cx
0018390D  call    sub_12805C
00183912  jmp     short loc_183947
00183914  mov     ax, 7894h
00183917  mov     es, ax
00183919  cmp     es:word_79E32, 0
0018391F  jle     short loc_183928
00183921  mov     es, ax
00183923  dec     es:word_79E32
00183928  call    far ptr loc_69EA9
0018392D  mov     ax, 7894h
00183930  mov     es, ax
00183932  push    es:current_view_index
00183937  call    far ptr loc_69CBE
0018393C  pop     cx
0018393D  call    sub_12805C
00183942  call    input_poll_handler; Main keyboard input handler. Processes all keyboard input.
00183947  mov     ax, 7894h
0018394A  mov     es, ax
0018394C  cmp     es:input_flag_pending_1, 0
00183952  jnz     short loc_183914
00183954  jmp     short loc_1839CA
00183956  mov     ax, 7894h; jumptable 001838E7 case 6
00183959  mov     es, ax
0018395B  cmp     es:word_79E80, 12Ch
00183962  jge     short loc_183967
00183964  jmp     def_1838E7; jumptable 001838E7 default case, cases 1-5
00183967  mov     ax, 7894h
0018396A  mov     es, ax
0018396C  push    es:current_view_index
00183971  call    far ptr loc_69CBE
00183976  pop     cx
00183977  call    sub_12805C
0018397C  jmp     short loc_1839BD
0018397E  mov     ax, 7894h
00183981  mov     dx, 7894h
00183984  mov     es, dx
00183986  mov     dx, es:word_79D1E
0018398B  add     dx, 0FFF5h
0018398E  mov     es, ax
00183990  cmp     es:word_79E32, dx
00183995  jge     short loc_18399E
00183997  mov     es, ax
00183999  inc     es:word_79E32
0018399E  call    far ptr loc_69EA9
001839A3  mov     ax, 7894h
001839A6  mov     es, ax
001839A8  push    es:current_view_index
001839AD  call    far ptr loc_69CBE
001839B2  pop     cx
001839B3  call    sub_12805C
001839B8  call    input_poll_handler; Main keyboard input handler. Processes all keyboard input.
001839BD  mov     ax, 7894h
001839C0  mov     es, ax
001839C2  cmp     es:input_flag_pending_1, 0
001839C8  jnz     short loc_18397E
001839CA  call    undoc_130B39
001839CF  jmp     short def_1838E7; jumptable 001838E7 default case, cases 1-5
001839D1  mov     ax, 7894h; jumptable 001838E7 case 7
001839D4  mov     es, ax
001839D6  push    es:current_view_index
001839DB  call    far ptr loc_69CBE
001839E0  dw 9A59h; jump table for switch statement
001839E2  db 8Ch, 1, 0C1h, 39h
001839E6  call    menu_cursor_position_set
001839EB  mov     ax, 7894h
001839EE  mov     es, ax
001839F0  cmp     es:word_79B56, 1
001839F6  jnz     short near ptr loc_1839FA+1
001839F8  dw offset loc_183299; jump table for switch statement
001839FA  out     0BEh, ax; Interrupt Controller #2, 8259A
001839FC  add     [bx+si], ax
001839FE  jmp     short def_1838E7; jumptable 001838E7 default case, cases 1-5
00183A00  mov     ax, 7894h; jumptable 001838E7 case 8
00183A03  mov     es, ax
00183A05  push    es:current_view_index
00183A0A  jmp     loc_1824A5
00183A0D  or      si, si; jumptable 001838E7 default case, cases 1-5
00183A0F  jnz     short loc_183A14
00183A11  jmp     loc_18380D
00183A14  mov     ax, 7894h
00183A17  mov     es, ax
00183A19  cmp     es:word_79B56, 1
00183A1F  jnz     short loc_183A24
00183A21  jmp     loc_18523C
00183A24  mov     ax, 7894h
00183A27  mov     es, ax
00183A29  mov     es:word_79D1E, 0
00183A30  mov     ax, 7894h
00183A33  mov     es, ax
00183A35  mov     es:word_79E32, 0
00183A3C  push    7894h
00183A3F  push    0F32h
00183A42  mov     ax, 602Eh
00183A45  mov     es, ax
00183A47  push    word ptr es:aJ0+2; ".`\n"
00183A4C  push    word ptr es:aJ0; "J0.`\n"
00183A51  mov     ax, 6E1Eh
00183A54  mov     es, ax
00183A56  push    word ptr es:loc_6E317+2
00183A5B  push    word ptr es:loc_6E317
00183A60  call    string_concatenate
00183A65  add     sp, 0Ch
00183A68  mov     ax, 7894h
00183A6B  mov     es, ax
00183A6D  push    es:word_79D1E
00183A72  push    7894h
00183A75  push    0F32h
00183A78  call    sub_135C57
00183A7D  add     sp, 6
00183A80  mov     dx, 7894h
00183A83  mov     es, dx
00183A85  mov     es:word_79D1E, ax
00183A89  mov     ax, 6E1Eh
00183A8C  mov     es, ax
00183A8E  mov     word ptr es:byte_6E1C9+17h, 0
00183A95  jmp     loc_183F4D
00183A98  mov     ax, 6E1Eh
00183A9B  mov     es, ax
00183A9D  mov     ax, word ptr es:byte_6E1C9+17h
00183AA1  mov     dx, 42h ; 'B'
00183AA4  imul    dx
00183AA6  mov     dx, 6E1Eh
00183AA9  mov     es, dx
00183AAB  les     bx, dword ptr es:byte_6E1C9+47h
00183AB0  add     bx, ax
00183AB2  cmp     byte ptr es:[bx+32h], 0FFh
00183AB7  jnz     short loc_183ADD
00183AB9  mov     ax, 6E1Eh
00183ABC  mov     es, ax
00183ABE  mov     ax, word ptr es:byte_6E1C9+17h
00183AC2  mov     dx, 42h ; 'B'
00183AC5  imul    dx
00183AC7  mov     dx, 6E1Eh
00183ACA  mov     es, dx
00183ACC  les     bx, dword ptr es:byte_6E1C9+47h
00183AD1  add     bx, ax
00183AD3  cmp     byte ptr es:[bx+33h], 0FFh
00183AD8  jnz     short loc_183ADD
00183ADA  jmp     loc_183D8A
00183ADD  push    7894h
00183AE0  push    0F32h
00183AE3  mov     ax, 602Eh
00183AE6  mov     es, ax
00183AE8  push    word ptr es:a2_0+1; ".` "
00183AED  push    word ptr es:byte_151860
00183AF2  mov     ax, 6E1Eh
00183AF5  mov     es, ax
00183AF7  mov     ax, word ptr es:byte_6E1C9+17h
00183AFB  mov     dx, 42h ; 'B'
00183AFE  imul    dx
00183B00  mov     dx, 6E1Eh
00183B03  mov     es, dx
00183B05  les     bx, dword ptr es:byte_6E1C9+47h
00183B0A  add     bx, ax
00183B0C  mov     al, es:[bx+1]
00183B10  cbw
00183B11  shl     ax, 2
00183B14  mov     dx, 602Eh
00183B17  mov     bx, ax
00183B19  mov     es, dx
00183B1B  push    word ptr es:[bx+1AD8h]
00183B20  push    word ptr es:[bx+1AD6h]
00183B25  call    string_concatenate
00183B2A  add     sp, 0Ch
00183B2D  push    7894h
00183B30  push    0F32h
00183B33  mov     ax, 6E1Eh
00183B36  mov     es, ax
00183B38  mov     ax, word ptr es:byte_6E1C9+17h
00183B3C  mov     dx, 42h ; 'B'
00183B3F  imul    dx
00183B41  mov     dx, 6E1Eh
00183B44  mov     es, dx
00183B46  mov     dx, word ptr es:byte_6E1C9+47h
00183B4B  add     dx, ax
00183B4D  inc     dx
00183B4E  inc     dx
00183B4F  push    word ptr es:byte_6E1C9+49h
00183B54  push    dx
00183B55  push    7894h
00183B58  push    0F32h
00183B5B  call    string_concatenate
00183B60  add     sp, 0Ch
00183B63  push    7894h
00183B66  push    0F32h
00183B69  mov     ax, 602Eh
00183B6C  mov     es, ax
00183B6E  push    word ptr es:a2_0+1; ".` "
00183B73  push    word ptr es:byte_151860
00183B78  push    7894h
00183B7B  push    0F32h
00183B7E  call    string_concatenate
00183B83  add     sp, 0Ch
00183B86  push    7894h
00183B89  push    0F32h
00183B8C  mov     ax, 6E1Eh
00183B8F  mov     es, ax
00183B91  push    word ptr es:sub_6E31D
00183B96  push    word ptr es:loc_6E317+4
00183B9B  push    7894h
00183B9E  push    0F32h
00183BA1  call    string_concatenate
00183BA6  add     sp, 0Ch
00183BA9  push    7894h
00183BAC  push    0F32h
00183BAF  mov     ax, 602Eh
00183BB2  mov     es, ax
00183BB4  push    word ptr es:aJ0+2; ".`\n"
00183BB9  push    word ptr es:aJ0; "J0.`\n"
00183BBE  push    7894h
00183BC1  push    0F32h
00183BC4  call    string_concatenate
00183BC9  add     sp, 0Ch
00183BCC  mov     ax, 6E1Eh
00183BCF  mov     es, ax
00183BD1  mov     ax, word ptr es:byte_6E1C9+17h
00183BD5  mov     dx, 42h ; 'B'
00183BD8  imul    dx
00183BDA  mov     dx, 6E1Eh
00183BDD  mov     es, dx
00183BDF  les     bx, dword ptr es:byte_6E1C9+47h
00183BE4  add     bx, ax
00183BE6  cmp     byte ptr es:[bx+33h], 0FFh
00183BEB  jz      short loc_183C45
00183BED  mov     ax, 6E1Eh
00183BF0  mov     es, ax
00183BF2  mov     ax, word ptr es:byte_6E1C9+17h
00183BF6  mov     dx, 42h ; 'B'
00183BF9  imul    dx
00183BFB  mov     dx, 6E1Eh
00183BFE  mov     es, dx
00183C00  les     bx, dword ptr es:byte_6E1C9+47h
00183C05  add     bx, ax
00183C07  mov     al, es:[bx+33h]
00183C0B  cbw
00183C0C  mov     dx, 6E1Eh
00183C0F  mov     es, dx
00183C11  mov     word ptr es:byte_6E1C9+4Dh, ax
00183C15  push    7894h
00183C18  push    0F32h
00183C1B  mov     ax, 6E1Eh
00183C1E  mov     es, ax
00183C20  mov     bx, word ptr es:byte_6E1C9+4Dh
00183C25  shl     bx, 2
00183C28  mov     ax, 6E1Eh
00183C2B  mov     es, ax
00183C2D  push    word ptr es:[bx+141h]
00183C32  push    word ptr es:[bx+13Fh]
00183C37  push    7894h
00183C3A  push    0F32h
00183C3D  call    string_concatenate
00183C42  add     sp, 0Ch
00183C45  mov     ax, 6E1Eh
00183C48  mov     es, ax
00183C4A  mov     ax, word ptr es:byte_6E1C9+17h
00183C4E  mov     dx, 42h ; 'B'
00183C51  imul    dx
00183C53  mov     dx, 6E1Eh
00183C56  mov     es, dx
00183C58  les     bx, dword ptr es:byte_6E1C9+47h
00183C5D  add     bx, ax
00183C5F  cmp     byte ptr es:[bx+32h], 0FFh
00183C64  jz      short loc_183CAA
00183C66  mov     ax, 6E1Eh
00183C69  mov     es, ax
00183C6B  mov     ax, word ptr es:byte_6E1C9+17h
00183C6F  mov     dx, 42h ; 'B'
00183C72  imul    dx
00183C74  mov     dx, 6E1Eh
00183C77  mov     es, dx
00183C79  les     bx, dword ptr es:byte_6E1C9+47h
00183C7E  add     bx, ax
00183C80  cmp     byte ptr es:[bx+33h], 0FFh
00183C85  jz      short loc_183CAA
00183C87  push    7894h
00183C8A  push    0F32h
00183C8D  mov     ax, 4FC2h
00183C90  mov     es, ax
00183C92  push    word ptr es:byte_13DFC6
00183C97  push    es:word_13DFC4
00183C9C  push    7894h
00183C9F  push    0F32h
00183CA2  call    string_concatenate
00183CA7  add     sp, 0Ch
00183CAA  mov     ax, 6E1Eh
00183CAD  mov     es, ax
00183CAF  mov     ax, word ptr es:byte_6E1C9+17h
00183CB3  mov     dx, 42h ; 'B'
00183CB6  imul    dx
00183CB8  mov     dx, 6E1Eh
00183CBB  mov     es, dx
00183CBD  les     bx, dword ptr es:byte_6E1C9+47h
00183CC2  add     bx, ax
00183CC4  cmp     byte ptr es:[bx+32h], 0FFh
00183CC9  jz      short loc_183D23
00183CCB  mov     ax, 6E1Eh
00183CCE  mov     es, ax
00183CD0  mov     ax, word ptr es:byte_6E1C9+17h
00183CD4  mov     dx, 42h ; 'B'
00183CD7  imul    dx
00183CD9  mov     dx, 6E1Eh
00183CDC  mov     es, dx
00183CDE  les     bx, dword ptr es:byte_6E1C9+47h
00183CE3  add     bx, ax
00183CE5  mov     al, es:[bx+32h]
00183CE9  cbw
00183CEA  mov     dx, 6E1Eh
00183CED  mov     es, dx
00183CEF  mov     word ptr es:byte_6E1C9+4Dh, ax
00183CF3  push    7894h
00183CF6  push    0F32h
00183CF9  mov     ax, 6E1Eh
00183CFC  mov     es, ax
00183CFE  mov     bx, word ptr es:byte_6E1C9+4Dh
00183D03  shl     bx, 2
00183D06  mov     ax, 6E1Eh
00183D09  mov     es, ax
00183D0B  push    word ptr es:[bx+141h]
00183D10  push    word ptr es:[bx+13Fh]
00183D15  push    7894h
00183D18  push    0F32h
00183D1B  call    string_concatenate
00183D20  add     sp, 0Ch
00183D23  push    7894h
00183D26  push    0F32h
00183D29  mov     ax, 602Eh
00183D2C  mov     es, ax
00183D2E  push    word ptr es:aJ0+2; ".`\n"
00183D33  push    word ptr es:aJ0; "J0.`\n"
00183D38  push    7894h
00183D3B  push    0F32h
00183D3E  call    string_concatenate
00183D43  add     sp, 0Ch
00183D46  push    7894h
00183D49  push    0F32h
00183D4C  mov     ax, 602Eh
00183D4F  mov     es, ax
00183D51  push    word ptr es:aJ0+2; ".`\n"
00183D56  push    word ptr es:aJ0; "J0.`\n"
00183D5B  push    7894h
00183D5E  push    0F32h
00183D61  call    string_concatenate
00183D66  add     sp, 0Ch
00183D69  mov     ax, 7894h
00183D6C  mov     es, ax
00183D6E  push    es:word_79D1E
00183D73  push    7894h
00183D76  push    0F32h
00183D79  call    sub_135C57
00183D7E  add     sp, 6
00183D81  mov     dx, 7894h
00183D84  mov     es, dx
00183D86  mov     es:word_79D1E, ax
00183D8A  mov     ax, 6E1Eh
00183D8D  mov     es, ax
00183D8F  mov     ax, word ptr es:byte_6E1C9+17h
00183D93  mov     dx, 42h ; 'B'
00183D96  imul    dx
00183D98  mov     dx, 6E1Eh
00183D9B  mov     es, dx
00183D9D  les     bx, dword ptr es:byte_6E1C9+47h
00183DA2  add     bx, ax
00183DA4  mov     al, es:[bx+26h]
00183DA8  cbw
00183DA9  and     ax, 1Fh
00183DAC  cmp     ax, 6
00183DAF  jz      short loc_183DB4
00183DB1  jmp     loc_183F43
00183DB4  push    7894h
00183DB7  push    0F32h
00183DBA  mov     ax, 602Eh
00183DBD  mov     es, ax
00183DBF  push    word ptr es:a2_0+1; ".` "
00183DC4  push    word ptr es:byte_151860
00183DC9  mov     ax, 6E1Eh
00183DCC  mov     es, ax
00183DCE  mov     ax, word ptr es:byte_6E1C9+17h
00183DD2  mov     dx, 42h ; 'B'
00183DD5  imul    dx
00183DD7  mov     dx, 6E1Eh
00183DDA  mov     es, dx
00183DDC  les     bx, dword ptr es:byte_6E1C9+47h
00183DE1  add     bx, ax
00183DE3  mov     al, es:[bx+1]
00183DE7  cbw
00183DE8  shl     ax, 2
00183DEB  mov     dx, 602Eh
00183DEE  mov     bx, ax
00183DF0  mov     es, dx
00183DF2  push    word ptr es:[bx+1AD8h]
00183DF7  push    word ptr es:[bx+1AD6h]
00183DFC  call    string_concatenate
00183E01  add     sp, 0Ch
00183E04  push    7894h
00183E07  push    0F32h
00183E0A  mov     ax, 6E1Eh
00183E0D  mov     es, ax
00183E0F  mov     ax, word ptr es:byte_6E1C9+17h
00183E13  mov     dx, 42h ; 'B'
00183E16  imul    dx
00183E18  mov     dx, 6E1Eh
00183E1B  mov     es, dx
00183E1D  mov     dx, word ptr es:byte_6E1C9+47h
00183E22  add     dx, ax
00183E24  inc     dx
00183E25  inc     dx
00183E26  push    word ptr es:byte_6E1C9+49h
00183E2B  push    dx
00183E2C  push    7894h
00183E2F  push    0F32h
00183E32  call    string_concatenate
00183E37  add     sp, 0Ch
00183E3A  push    7894h
00183E3D  push    0F32h
00183E40  mov     ax, 6E1Eh
00183E43  mov     es, ax
00183E45  push    word ptr es:loc_6E38C+1
00183E4A  push    word ptr es:loc_6E387+4
00183E4F  push    7894h
00183E52  push    0F32h
00183E55  call    string_concatenate
00183E5A  add     sp, 0Ch
00183E5D  mov     ax, 6E1Eh
00183E60  mov     es, ax
00183E62  mov     ax, word ptr es:byte_6E1C9+17h
00183E66  mov     dx, 42h ; 'B'
00183E69  imul    dx
00183E6B  mov     dx, 6E1Eh
00183E6E  mov     es, dx
00183E70  les     bx, dword ptr es:byte_6E1C9+47h
00183E75  add     bx, ax
00183E77  test    byte ptr es:[bx+26h], 0F0h
00183E7C  jz      short loc_183EDC
00183E7E  mov     ax, 6E1Eh
00183E81  mov     es, ax
00183E83  mov     ax, word ptr es:byte_6E1C9+17h
00183E87  mov     dx, 42h ; 'B'
00183E8A  imul    dx
00183E8C  mov     dx, 6E1Eh
00183E8F  mov     es, dx
00183E91  les     bx, dword ptr es:byte_6E1C9+47h
00183E96  add     bx, ax
00183E98  mov     al, es:[bx+26h]
00183E9C  cbw
00183E9D  and     ax, 0F0h
00183EA0  sar     ax, 5
00183EA3  mov     dx, 7894h
00183EA6  mov     es, dx
00183EA8  mov     es:word_79E80, ax
00183EAC  push    7894h
00183EAF  push    0F32h
00183EB2  mov     ax, 7894h
00183EB5  mov     es, ax
00183EB7  mov     bx, es:word_79E80
00183EBC  shl     bx, 2
00183EBF  mov     ax, 6E1Eh
00183EC2  mov     es, ax
00183EC4  push    word ptr es:[bx+1ADh]
00183EC9  push    word ptr es:[bx+1ABh]
00183ECE  push    7894h
00183ED1  push    0F32h
00183ED4  call    string_concatenate
00183ED9  add     sp, 0Ch
00183EDC  push    7894h
00183EDF  push    0F32h
00183EE2  mov     ax, 602Eh
00183EE5  mov     es, ax
00183EE7  push    word ptr es:aJ0+2; ".`\n"
00183EEC  push    word ptr es:aJ0; "J0.`\n"
00183EF1  push    7894h
00183EF4  push    0F32h
00183EF7  call    string_concatenate
00183EFC  add     sp, 0Ch
00183EFF  push    7894h
00183F02  push    0F32h
00183F05  mov     ax, 602Eh
00183F08  mov     es, ax
00183F0A  push    word ptr es:aJ0+2; ".`\n"
00183F0F  push    word ptr es:aJ0; "J0.`\n"
00183F14  push    7894h
00183F17  push    0F32h
00183F1A  call    string_concatenate
00183F1F  add     sp, 0Ch
00183F22  mov     ax, 7894h
00183F25  mov     es, ax
00183F27  push    es:word_79D1E
00183F2C  push    7894h
00183F2F  push    0F32h
00183F32  call    sub_135C57
00183F37  add     sp, 6
00183F3A  mov     dx, 7894h
00183F3D  mov     es, dx
00183F3F  mov     es:word_79D1E, ax
00183F43  mov     ax, 6E1Eh
00183F46  mov     es, ax
00183F48  inc     word ptr es:byte_6E1C9+17h
00183F4D  mov     ax, 7894h
00183F50  mov     es, ax
00183F52  les     bx, es:dword_79E3A
00183F57  mov     ax, es:[bx+0A8Dh]
00183F5C  mov     dx, 6E1Eh
00183F5F  mov     es, dx
00183F61  cmp     ax, word ptr es:byte_6E1C9+17h
00183F66  jbe     short loc_183F6B
00183F68  jmp     loc_183A98
00183F6B  call    sub_135DF4; Utility function (473B, 16 calls) - needs investigation
00183F70  xor     si, si
00183F72  jmp     def_184067; jumptable 00184067 default case, cases 1-5
00183F75  call    undoc_11D941
00183F7A  call    undoc_12661D
00183F7F  push    1
00183F81  call    loc_69C25
00183F86  pop     cx
00183F87  call    sub_12805C
00183F8C  call    sub_12DB63
00183F91  mov     ax, 7894h
00183F94  mov     es, ax
00183F96  cmp     es:word_79B6C, 32h ; '2'
00183F9C  jz      short loc_183FA1
00183F9E  jmp     loc_184039
00183FA1  mov     ax, 7894h
00183FA4  mov     es, ax
00183FA6  mov     ax, es:input_scan_code_queue
00183FAA  mov     [bp+var_16], ax
00183FAD  mov     cx, 4
00183FB0  mov     bx, 31CDh
00183FB3  mov     ax, cs:[bx]
00183FB6  cmp     ax, [bp+var_16]
00183FB9  jz      short loc_183FC1
00183FBB  inc     bx
00183FBC  inc     bx
00183FBD  loop    loc_183FB3
00183FBF  jmp     short loc_184031
00183FC1  jmp     word ptr cs:[bx+8]
00183FC5  mov     ax, 7894h
00183FC8  mov     es, ax
00183FCA  mov     es:current_view_index, 7
00183FD1  jmp     loc_184053
00183FD4  jmp     loc_1824A3; VIEW KEY HANDLER: Push view index 8, call view setup (likely padlock view)
00183FD7  call    loc_6CA42+1
00183FDC  jmp     def_184067; jumptable 00184067 default case, cases 1-5
00183FDF  mov     ax, 4FC2h
00183FE2  mov     es, ax
00183FE4  push    es:word_13E012
00183FE9  call    sub_2C761; Overlay bridge trampoline (8B, 14 calls)
00183FEE  pop     cx
00183FEF  mov     ax, 7894h
00183FF2  mov     es, ax
00183FF4  les     bx, es:menu_state_ptr
00183FF9  dec     word ptr es:[bx]
00183FFC  mov     ax, 4FC2h
00183FFF  mov     es, ax
00184001  push    es:word_13E012
00184006  call    far ptr menu_finalize_render
0018400B  pop     cx
0018400C  call    sub_11D274
00184011  mov     ax, 7894h
00184014  mov     es, ax
00184016  les     bx, es:menu_state_ptr
0018401B  inc     word ptr es:[bx]
0018401E  mov     ax, 4FC2h
00184021  mov     es, ax
00184023  push    es:word_13E012
00184028  call    far ptr menu_finalize_render
0018402D  pop     cx
0018402E  jmp     def_184067; jumptable 00184067 default case, cases 1-5
00184031  call    menu_cursor_position_set
00184036  jmp     def_184067; jumptable 00184067 default case, cases 1-5
00184039  mov     ax, 7894h
0018403C  mov     es, ax
0018403E  cmp     es:word_79B6C, 34h ; '4'
00184044  jz      short loc_184053
00184046  mov     es, ax
00184048  cmp     es:word_79B6C, 36h ; '6'
0018404E  jz      short loc_184053
00184050  jmp     def_184067; jumptable 00184067 default case, cases 1-5
00184053  mov     ax, 7894h
00184056  mov     es, ax
00184058  mov     bx, es:current_view_index
0018405D  cmp     bx, 8; switch 9 cases
00184060  jbe     short loc_184065
00184062  jmp     def_184067; jumptable 00184067 default case, cases 1-5
00184065  shl     bx, 1
00184067  jmp     cs:jpt_184067[bx]; switch jump
0018406C  mov     ax, 7894h; jumptable 00184067 case 0
0018406F  mov     es, ax
00184071  cmp     es:word_79E80, 12Ch
00184078  jge     short loc_18407D
0018407A  jmp     def_184067; jumptable 00184067 default case, cases 1-5
0018407D  mov     ax, 7894h
00184080  mov     es, ax
00184082  push    es:current_view_index
00184087  call    far ptr loc_69CBE
0018408C  pop     cx
0018408D  call    sub_12805C
00184092  jmp     short loc_1840C7
00184094  mov     ax, 7894h
00184097  mov     es, ax
00184099  cmp     es:word_79E32, 0
0018409F  jle     short loc_1840A8
001840A1  mov     es, ax
001840A3  dec     es:word_79E32
001840A8  call    far ptr loc_69EA9
001840AD  mov     ax, 7894h
001840B0  mov     es, ax
001840B2  push    es:current_view_index
001840B7  call    far ptr loc_69CBE
001840BC  pop     cx
001840BD  call    sub_12805C
001840C2  call    input_poll_handler; Main keyboard input handler. Processes all keyboard input.
001840C7  mov     ax, 7894h
001840CA  mov     es, ax
001840CC  cmp     es:input_flag_pending_1, 0
001840D2  jnz     short loc_184094
001840D4  jmp     short loc_18414A
001840D6  mov     ax, 7894h; jumptable 00184067 case 6
001840D9  mov     es, ax
001840DB  cmp     es:word_79E80, 12Ch
001840E2  jge     short loc_1840E7
001840E4  jmp     def_184067; jumptable 00184067 default case, cases 1-5
001840E7  mov     ax, 7894h
001840EA  mov     es, ax
001840EC  push    es:current_view_index
001840F1  call    far ptr loc_69CBE
001840F6  pop     cx
001840F7  call    sub_12805C
001840FC  jmp     short loc_18413D
001840FE  mov     ax, 7894h
00184101  mov     dx, 7894h
00184104  mov     es, dx
00184106  mov     dx, es:word_79D1E
0018410B  add     dx, 0FFF5h
0018410E  mov     es, ax
00184110  cmp     es:word_79E32, dx
00184115  jge     short loc_18411E
00184117  mov     es, ax
00184119  inc     es:word_79E32
0018411E  call    far ptr loc_69EA9
00184123  mov     ax, 7894h
00184126  mov     es, ax
00184128  push    es:current_view_index
0018412D  call    far ptr loc_69CBE
00184132  pop     cx
00184133  call    sub_12805C
00184138  call    input_poll_handler; Main keyboard input handler. Processes all keyboard input.
0018413D  mov     ax, 7894h
00184140  mov     es, ax
00184142  cmp     es:input_flag_pending_1, 0
00184148  jnz     short loc_1840FE
0018414A  call    undoc_130B39
0018414F  jmp     short def_184067; jumptable 00184067 default case, cases 1-5
00184151  push    7; jumptable 00184067 case 7
00184153  call    far ptr loc_69CBE
00184158  pop     cx
00184159  call    sub_12805C
0018415E  call    menu_cursor_position_set
00184163  mov     si, 1
00184166  jmp     short def_184067; jumptable 00184067 default case, cases 1-5
00184168  jmp     loc_1824A3; jumptable 00184067 case 8
0018416B  or      si, si; jumptable 00184067 default case, cases 1-5
0018416D  jnz     short loc_184172
0018416F  jmp     loc_183F75
00184172  mov     ax, 7894h
00184175  mov     es, ax
00184177  mov     es:word_79E32, 0
0018417E  mov     ax, 7894h
00184181  mov     es, ax
00184183  cmp     es:word_79B56, 1
00184189  jz      short loc_184199
0018418B  call    loc_6CB67+1
00184190  mov     dx, 602Eh
00184193  mov     es, dx
00184195  mov     es:word_14F8A9, ax
00184199  push    7894h
0018419C  push    0F32h
0018419F  mov     ax, 6E1Eh
001841A2  mov     es, ax
001841A4  push    es:word_6E767
001841A9  push    es:word_6E765
001841AE  call    string_copy_with_offset
001841B3  add     sp, 8
001841B6  push    7894h
001841B9  push    0F32h
001841BC  mov     ax, 602Eh
001841BF  mov     es, ax
001841C1  push    word ptr es:aJ0+2; ".`\n"
001841C6  push    word ptr es:aJ0; "J0.`\n"
001841CB  push    7894h
001841CE  push    0F32h
001841D1  call    string_concatenate
001841D6  add     sp, 0Ch
001841D9  mov     ax, 602Eh
001841DC  mov     es, ax
001841DE  cmp     es:word_14F8A9, 0
001841E4  jnz     short loc_1841FD
001841E6  push    7894h
001841E9  push    0F32h
001841EC  mov     ax, 6E1Eh
001841EF  mov     es, ax
001841F1  push    es:word_6E783
001841F6  push    es:word_6E781
001841FB  jmp     short loc_184212
001841FD  push    7894h
00184200  push    0F32h
00184203  mov     ax, 6E1Eh
00184206  mov     es, ax
00184208  push    es:word_6E787
0018420D  push    es:word_6E785
00184212  push    7894h
00184215  push    0F32h
00184218  call    string_concatenate
0018421D  add     sp, 0Ch
00184220  push    7894h
00184223  push    0F32h
00184226  mov     ax, 602Eh
00184229  mov     es, ax
0018422B  push    word ptr es:aJ0+2; ".`\n"
00184230  push    word ptr es:aJ0; "J0.`\n"
00184235  push    7894h
00184238  push    0F32h
0018423B  call    string_concatenate
00184240  add     sp, 0Ch
00184243  push    0
00184245  push    7894h
00184248  push    0F32h
0018424B  call    sub_135C57
00184250  add     sp, 6
00184253  mov     dx, 7894h
00184256  mov     es, dx
00184258  mov     es:word_79D1E, ax
0018425C  mov     ax, 7894h
0018425F  mov     es, ax
00184261  mov     es:byte_79872, 0
00184267  mov     ax, 602Eh
0018426A  mov     es, ax
0018426C  cmp     es:word_14F8A9, 0
00184272  jz      short loc_184290
00184274  push    7894h
00184277  push    0F32h
0018427A  mov     ax, 602Eh
0018427D  mov     es, ax
0018427F  push    es:word_151C15
00184284  mov     ax, 602Eh
00184287  mov     es, ax
00184289  push    es:word_14F8A9
0018428E  jmp     short loc_1842AC
00184290  mov     ax, 602Eh
00184293  mov     es, ax
00184295  cmp     es:word_14F8AB, 0
0018429B  jz      short loc_1842D7
0018429D  push    7894h
001842A0  push    0F32h
001842A3  push    0
001842A5  mov     es, ax
001842A7  push    es:word_14F8AB
001842AC  call    loc_6AD84
001842B1  add     sp, 8
001842B4  push    7894h
001842B7  push    0F32h
001842BA  mov     ax, 602Eh
001842BD  mov     es, ax
001842BF  push    word ptr es:aJ0+2; ".`\n"
001842C4  push    word ptr es:aJ0; "J0.`\n"
001842C9  push    7894h
001842CC  push    0F32h
001842CF  call    string_concatenate
001842D4  add     sp, 0Ch
001842D7  push    7894h
001842DA  push    0F32h
001842DD  mov     ax, 602Eh
001842E0  mov     es, ax
001842E2  push    word ptr es:aJ0+2; ".`\n"
001842E7  push    word ptr es:aJ0; "J0.`\n"
001842EC  push    7894h
001842EF  push    0F32h
001842F2  call    string_concatenate
001842F7  add     sp, 0Ch
001842FA  push    7894h
001842FD  push    0F32h
00184300  mov     ax, 6E1Eh
00184303  mov     es, ax
00184305  push    es:word_6E76B
0018430A  push    es:word_6E769
0018430F  push    7894h
00184312  push    0F32h
00184315  call    string_concatenate
0018431A  add     sp, 0Ch
0018431D  mov     ax, 7894h
00184320  mov     es, ax
00184322  push    es:word_79D1E
00184327  push    7894h
0018432A  push    0F32h
0018432D  call    sub_135C57
00184332  add     sp, 6
00184335  mov     dx, 7894h
00184338  mov     es, dx
0018433A  mov     es:word_79D1E, ax
0018433E  mov     ax, 7894h
00184341  mov     es, ax
00184343  mov     es:byte_79872, 0
00184349  mov     di, 1
0018434C  mov     [bp+var_2], 20h ; ' '
00184351  jmp     loc_184427
00184354  mov     ax, 6E1Eh
00184357  mov     es, ax
00184359  les     bx, dword ptr es:byte_6E1C9+4Fh
0018435E  add     bx, [bp+var_2]
00184361  cmp     byte ptr es:[bx], 0
00184365  jnz     short loc_18436A
00184367  jmp     loc_184424
0018436A  xor     di, di
0018436C  mov     al, byte ptr [bp+var_2]
0018436F  push    ax
00184370  call    sub_127E5A; Calculate indexed pointer from table (116B, 16 calls)
00184375  pop     cx
00184376  mov     bx, 6E1Eh
00184379  mov     es, bx
0018437B  mov     word ptr es:byte_6E1C9+27h, dx
00184380  mov     word ptr es:byte_6E1C9+25h, ax
00184384  push    602Eh
00184387  push    1400h
0018438A  mov     ax, 6E1Eh
0018438D  mov     es, ax
0018438F  les     bx, dword ptr es:byte_6E1C9+4Fh
00184394  add     bx, [bp+var_2]
00184397  mov     al, es:[bx]
0018439A  mov     ah, 0
0018439C  push    ax
0018439D  call    int_to_string_converter
001843A2  add     sp, 6
001843A5  push    7894h
001843A8  push    0F32h
001843AB  push    ds
001843AC  push    (offset asc_8477E - offset byte_7A320); " : " ...
001843AF  mov     ax, 6E1Eh
001843B2  mov     es, ax
001843B4  push    word ptr es:byte_6E1C9+27h
001843B9  push    word ptr es:byte_6E1C9+25h
001843BE  call    string_concatenate
001843C3  add     sp, 0Ch
001843C6  push    7894h
001843C9  push    0F32h
001843CC  push    602Eh
001843CF  push    1400h
001843D2  push    7894h
001843D5  push    0F32h
001843D8  call    string_concatenate
001843DD  add     sp, 0Ch
001843E0  push    7894h
001843E3  push    0F32h
001843E6  mov     ax, 602Eh
001843E9  mov     es, ax
001843EB  push    word ptr es:aJ0+2; ".`\n"
001843F0  push    word ptr es:aJ0; "J0.`\n"
001843F5  push    7894h
001843F8  push    0F32h
001843FB  call    string_concatenate
00184400  add     sp, 0Ch
00184403  mov     ax, 7894h
00184406  mov     es, ax
00184408  push    es:word_79D1E
0018440D  push    7894h
00184410  push    0F32h
00184413  call    sub_135C57
00184418  add     sp, 6
0018441B  mov     dx, 7894h
0018441E  mov     es, dx
00184420  mov     es:word_79D1E, ax
00184424  inc     [bp+var_2]
00184427  cmp     [bp+var_2], 40h ; '@'
0018442B  jge     short loc_184430
0018442D  jmp     loc_184354
00184430  or      di, di
00184432  jz      short loc_184476
00184434  push    7894h
00184437  push    0F32h
0018443A  mov     ax, 602Eh
0018443D  mov     es, ax
0018443F  push    es:word_1516B9
00184444  push    es:word_1516B7
00184449  push    ds
0018444A  push    (offset aNone - offset byte_7A320); "NONE" ...
0018444D  call    string_concatenate
00184452  add     sp, 0Ch
00184455  mov     ax, 7894h
00184458  mov     es, ax
0018445A  push    es:word_79D1E
0018445F  push    7894h
00184462  push    0F32h
00184465  call    sub_135C57
0018446A  add     sp, 6
0018446D  mov     dx, 7894h
00184470  mov     es, dx
00184472  mov     es:word_79D1E, ax
00184476  mov     di, 1
00184479  push    7894h
0018447C  push    0F32h
0018447F  mov     ax, 6E1Eh
00184482  mov     es, ax
00184484  push    es:word_6E76F
00184489  push    es:word_6E76D
0018448E  mov     ax, 602Eh
00184491  mov     es, ax
00184493  push    word ptr es:aJ0+2; ".`\n"
00184498  push    word ptr es:aJ0; "J0.`\n"
0018449D  call    string_concatenate
001844A2  add     sp, 0Ch
001844A5  mov     ax, 7894h
001844A8  mov     es, ax
001844AA  push    es:word_79D1E
001844AF  push    7894h
001844B2  push    0F32h
001844B5  call    sub_135C57
001844BA  add     sp, 6
001844BD  mov     dx, 7894h
001844C0  mov     es, dx
001844C2  mov     es:word_79D1E, ax
001844C6  mov     [bp+var_2], 0
001844CB  jmp     loc_1845A1
001844CE  mov     ax, 6E1Eh
001844D1  mov     es, ax
001844D3  les     bx, dword ptr es:byte_6E1C9+4Fh
001844D8  add     bx, [bp+var_2]
001844DB  cmp     byte ptr es:[bx], 0
001844DF  jnz     short loc_1844E4
001844E1  jmp     loc_18459E
001844E4  xor     di, di
001844E6  mov     al, byte ptr [bp+var_2]
001844E9  push    ax
001844EA  call    sub_127E5A; Calculate indexed pointer from table (116B, 16 calls)
001844EF  pop     cx
001844F0  mov     bx, 6E1Eh
001844F3  mov     es, bx
001844F5  mov     word ptr es:byte_6E1C9+27h, dx
001844FA  mov     word ptr es:byte_6E1C9+25h, ax
001844FE  push    602Eh
00184501  push    1400h
00184504  mov     ax, 6E1Eh
00184507  mov     es, ax
00184509  les     bx, dword ptr es:byte_6E1C9+4Fh
0018450E  add     bx, [bp+var_2]
00184511  mov     al, es:[bx]
00184514  mov     ah, 0
00184516  push    ax
00184517  call    int_to_string_converter
0018451C  add     sp, 6
0018451F  push    7894h
00184522  push    0F32h
00184525  push    ds
00184526  push    (offset asc_84787 - offset byte_7A320); " : " ...
00184529  mov     ax, 6E1Eh
0018452C  mov     es, ax
0018452E  push    word ptr es:byte_6E1C9+27h
00184533  push    word ptr es:byte_6E1C9+25h
00184538  call    string_concatenate
0018453D  add     sp, 0Ch
00184540  push    7894h
00184543  push    0F32h
00184546  push    602Eh
00184549  push    1400h
0018454C  push    7894h
0018454F  push    0F32h
00184552  call    string_concatenate
00184557  add     sp, 0Ch
0018455A  push    7894h
0018455D  push    0F32h
00184560  mov     ax, 602Eh
00184563  mov     es, ax
00184565  push    word ptr es:aJ0+2; ".`\n"
0018456A  push    word ptr es:aJ0; "J0.`\n"
0018456F  push    7894h
00184572  push    0F32h
00184575  call    string_concatenate
0018457A  add     sp, 0Ch
0018457D  mov     ax, 7894h
00184580  mov     es, ax
00184582  push    es:word_79D1E
00184587  push    7894h
0018458A  push    0F32h
0018458D  call    sub_135C57
00184592  add     sp, 6
00184595  mov     dx, 7894h
00184598  mov     es, dx
0018459A  mov     es:word_79D1E, ax
0018459E  inc     [bp+var_2]
001845A1  cmp     [bp+var_2], 20h ; ' '
001845A5  jge     short loc_1845AA
001845A7  jmp     loc_1844CE
001845AA  or      di, di
001845AC  jz      short loc_1845F0
001845AE  push    7894h
001845B1  push    0F32h
001845B4  mov     ax, 602Eh
001845B7  mov     es, ax
001845B9  push    es:word_1516B9
001845BE  push    es:word_1516B7
001845C3  push    ds
001845C4  push    (offset aNone_0 - offset byte_7A320); "NONE" ...
001845C7  call    string_concatenate
001845CC  add     sp, 0Ch
001845CF  mov     ax, 7894h
001845D2  mov     es, ax
001845D4  push    es:word_79D1E
001845D9  push    7894h
001845DC  push    0F32h
001845DF  call    sub_135C57
001845E4  add     sp, 6
001845E7  mov     dx, 7894h
001845EA  mov     es, dx
001845EC  mov     es:word_79D1E, ax
001845F0  mov     di, 1
001845F3  push    7894h
001845F6  push    0F32h
001845F9  mov     ax, 6E1Eh
001845FC  mov     es, ax
001845FE  push    es:word_6E773
00184603  push    es:word_6E771
00184608  mov     ax, 602Eh
0018460B  mov     es, ax
0018460D  push    word ptr es:aJ0+2; ".`\n"
00184612  push    word ptr es:aJ0; "J0.`\n"
00184617  call    string_concatenate
0018461C  add     sp, 0Ch
0018461F  mov     ax, 7894h
00184622  mov     es, ax
00184624  push    es:word_79D1E
00184629  push    7894h
0018462C  push    0F32h
0018462F  call    sub_135C57
00184634  add     sp, 6
00184637  mov     dx, 7894h
0018463A  mov     es, dx
0018463C  mov     es:word_79D1E, ax
00184640  mov     [bp+var_2], 20h ; ' '
00184645  jmp     loc_18471D
00184648  mov     ax, 6E1Eh
0018464B  mov     es, ax
0018464D  les     bx, dword ptr es:byte_6E1C9+93h
00184652  add     bx, [bp+var_2]
00184655  cmp     byte ptr es:[bx], 0
00184659  jnz     short loc_18465E
0018465B  jmp     loc_18471A
0018465E  xor     di, di
00184660  mov     al, byte ptr [bp+var_2]
00184663  or      al, 40h
00184665  push    ax
00184666  call    sub_127E5A; Calculate indexed pointer from table (116B, 16 calls)
0018466B  pop     cx
0018466C  mov     bx, 6E1Eh
0018466F  mov     es, bx
00184671  mov     word ptr es:byte_6E1C9+27h, dx
00184676  mov     word ptr es:byte_6E1C9+25h, ax
0018467A  push    602Eh
0018467D  push    1400h
00184680  mov     ax, 6E1Eh
00184683  mov     es, ax
00184685  les     bx, dword ptr es:byte_6E1C9+93h
0018468A  add     bx, [bp+var_2]
0018468D  mov     al, es:[bx]
00184690  mov     ah, 0
00184692  push    ax
00184693  call    int_to_string_converter
00184698  add     sp, 6
0018469B  push    7894h
0018469E  push    0F32h
001846A1  push    ds
001846A2  push    (offset asc_84790 - offset byte_7A320); " : " ...
001846A5  mov     ax, 6E1Eh
001846A8  mov     es, ax
001846AA  push    word ptr es:byte_6E1C9+27h
001846AF  push    word ptr es:byte_6E1C9+25h
001846B4  call    string_concatenate
001846B9  add     sp, 0Ch
001846BC  push    7894h
001846BF  push    0F32h
001846C2  push    602Eh
001846C5  push    1400h
001846C8  push    7894h
001846CB  push    0F32h
001846CE  call    string_concatenate
001846D3  add     sp, 0Ch
001846D6  push    7894h
001846D9  push    0F32h
001846DC  mov     ax, 602Eh
001846DF  mov     es, ax
001846E1  push    word ptr es:aJ0+2; ".`\n"
001846E6  push    word ptr es:aJ0; "J0.`\n"
001846EB  push    7894h
001846EE  push    0F32h
001846F1  call    string_concatenate
001846F6  add     sp, 0Ch
001846F9  mov     ax, 7894h
001846FC  mov     es, ax
001846FE  push    es:word_79D1E
00184703  push    7894h
00184706  push    0F32h
00184709  call    sub_135C57
0018470E  add     sp, 6
00184711  mov     dx, 7894h
00184714  mov     es, dx
00184716  mov     es:word_79D1E, ax
0018471A  inc     [bp+var_2]
0018471D  cmp     [bp+var_2], 40h ; '@'
00184721  jge     short loc_184726
00184723  jmp     loc_184648
00184726  or      di, di
00184728  jz      short loc_18476C
0018472A  push    7894h
0018472D  push    0F32h
00184730  mov     ax, 602Eh
00184733  mov     es, ax
00184735  push    es:word_1516B9
0018473A  push    es:word_1516B7
0018473F  push    ds
00184740  push    (offset aNone_1 - offset byte_7A320); "NONE" ...
00184743  call    string_concatenate
00184748  add     sp, 0Ch
0018474B  mov     ax, 7894h
0018474E  mov     es, ax
00184750  push    es:word_79D1E
00184755  push    7894h
00184758  push    0F32h
0018475B  call    sub_135C57
00184760  add     sp, 6
00184763  mov     dx, 7894h
00184766  mov     es, dx
00184768  mov     es:word_79D1E, ax
0018476C  mov     di, 1
0018476F  push    7894h
00184772  push    0F32h
00184775  mov     ax, 6E1Eh
00184778  mov     es, ax
0018477A  push    es:word_6E777
0018477F  push    es:word_6E775
00184784  mov     ax, 602Eh
00184787  mov     es, ax
00184789  push    word ptr es:aJ0+2; ".`\n"
0018478E  push    word ptr es:aJ0; "J0.`\n"
00184793  call    string_concatenate
00184798  add     sp, 0Ch
0018479B  mov     ax, 7894h
0018479E  mov     es, ax
001847A0  push    es:word_79D1E
001847A5  push    7894h
001847A8  push    0F32h
001847AB  call    sub_135C57
001847B0  add     sp, 6
001847B3  mov     dx, 7894h
001847B6  mov     es, dx
001847B8  mov     es:word_79D1E, ax
001847BC  mov     [bp+var_2], 0
001847C1  jmp     loc_184899
001847C4  mov     ax, 6E1Eh
001847C7  mov     es, ax
001847C9  les     bx, dword ptr es:byte_6E1C9+93h
001847CE  add     bx, [bp+var_2]
001847D1  cmp     byte ptr es:[bx], 0
001847D5  jnz     short loc_1847DA
001847D7  jmp     loc_184896
001847DA  xor     di, di
001847DC  mov     al, byte ptr [bp+var_2]
001847DF  or      al, 40h
001847E1  push    ax
001847E2  call    sub_127E5A; Calculate indexed pointer from table (116B, 16 calls)
001847E7  pop     cx
001847E8  mov     bx, 6E1Eh
001847EB  mov     es, bx
001847ED  mov     word ptr es:byte_6E1C9+27h, dx
001847F2  mov     word ptr es:byte_6E1C9+25h, ax
001847F6  push    602Eh
001847F9  push    1400h
001847FC  mov     ax, 6E1Eh
001847FF  mov     es, ax
00184801  les     bx, dword ptr es:byte_6E1C9+93h
00184806  add     bx, [bp+var_2]
00184809  mov     al, es:[bx]
0018480C  mov     ah, 0
0018480E  push    ax
0018480F  call    int_to_string_converter
00184814  add     sp, 6
00184817  push    7894h
0018481A  push    0F32h
0018481D  push    ds
0018481E  push    (offset asc_84799 - offset byte_7A320); " : " ...
00184821  mov     ax, 6E1Eh
00184824  mov     es, ax
00184826  push    word ptr es:byte_6E1C9+27h
0018482B  push    word ptr es:byte_6E1C9+25h
00184830  call    string_concatenate
00184835  add     sp, 0Ch
00184838  push    7894h
0018483B  push    0F32h
0018483E  push    602Eh
00184841  push    1400h
00184844  push    7894h
00184847  push    0F32h
0018484A  call    string_concatenate
0018484F  add     sp, 0Ch
00184852  push    7894h
00184855  push    0F32h
00184858  mov     ax, 602Eh
0018485B  mov     es, ax
0018485D  push    word ptr es:aJ0+2; ".`\n"
00184862  push    word ptr es:aJ0; "J0.`\n"
00184867  push    7894h
0018486A  push    0F32h
0018486D  call    string_concatenate
00184872  add     sp, 0Ch
00184875  mov     ax, 7894h
00184878  mov     es, ax
0018487A  push    es:word_79D1E
0018487F  push    7894h
00184882  push    0F32h
00184885  call    sub_135C57
0018488A  add     sp, 6
0018488D  mov     dx, 7894h
00184890  mov     es, dx
00184892  mov     es:word_79D1E, ax
00184896  inc     [bp+var_2]
00184899  cmp     [bp+var_2], 20h ; ' '
0018489D  jge     short loc_1848A2
0018489F  jmp     loc_1847C4
001848A2  or      di, di
001848A4  jz      short loc_1848E8
001848A6  push    7894h
001848A9  push    0F32h
001848AC  mov     ax, 602Eh
001848AF  mov     es, ax
001848B1  push    es:word_1516B9
001848B6  push    es:word_1516B7
001848BB  push    ds
001848BC  push    (offset aNone_2 - offset byte_7A320); "NONE" ...
001848BF  call    string_concatenate
001848C4  add     sp, 0Ch
001848C7  mov     ax, 7894h
001848CA  mov     es, ax
001848CC  push    es:word_79D1E
001848D1  push    7894h
001848D4  push    0F32h
001848D7  call    sub_135C57
001848DC  add     sp, 6
001848DF  mov     dx, 7894h
001848E2  mov     es, dx
001848E4  mov     es:word_79D1E, ax
001848E8  push    7894h
001848EB  push    0F32h
001848EE  mov     ax, 6E1Eh
001848F1  mov     es, ax
001848F3  push    es:word_6E77B
001848F8  push    es:word_6E779
001848FD  mov     ax, 602Eh
00184900  mov     es, ax
00184902  push    word ptr es:aJ0+2; ".`\n"
00184907  push    word ptr es:aJ0; "J0.`\n"
0018490C  call    string_concatenate
00184911  add     sp, 0Ch
00184914  push    7894h
00184917  push    0F32h
0018491A  mov     ax, 602Eh
0018491D  mov     es, ax
0018491F  push    word ptr es:aJ0+2; ".`\n"
00184924  push    word ptr es:aJ0; "J0.`\n"
00184929  push    7894h
0018492C  push    0F32h
0018492F  call    string_concatenate
00184934  add     sp, 0Ch
00184937  mov     ax, 7894h
0018493A  mov     es, ax
0018493C  push    es:word_79D1E
00184941  push    7894h
00184944  push    0F32h
00184947  call    sub_135C57
0018494C  add     sp, 6
0018494F  mov     dx, 7894h
00184952  mov     es, dx
00184954  mov     es:word_79D1E, ax
00184958  mov     [bp+var_2], 0
0018495D  jmp     loc_184AAF
00184960  mov     ax, [bp+var_2]
00184963  shl     ax, 1
00184965  mov     dx, 6E1Eh
00184968  mov     es, dx
0018496A  les     bx, dword ptr es:loc_6E2A1+3
0018496F  add     bx, ax
00184971  cmp     word ptr es:[bx], 0FFFFh
00184975  jnz     short loc_18497A
00184977  jmp     loc_184AAC
0018497A  push    7894h
0018497D  push    0F32h
00184980  mov     ax, 602Eh
00184983  mov     es, ax
00184985  push    word ptr es:a2_0+1; ".` "
0018498A  push    word ptr es:byte_151860
0018498F  mov     ax, [bp+var_2]
00184992  shl     ax, 1
00184994  mov     es, dx
00184996  les     bx, dword ptr es:loc_6E2A1+3
0018499B  add     bx, ax
0018499D  mov     ax, es:[bx]
001849A0  mov     dx, 42h ; 'B'
001849A3  imul    dx
001849A5  mov     dx, 6E1Eh
001849A8  mov     es, dx
001849AA  les     bx, dword ptr es:byte_6E1C9+47h
001849AF  add     bx, ax
001849B1  mov     al, es:[bx+1]
001849B5  cbw
001849B6  shl     ax, 2
001849B9  mov     dx, 602Eh
001849BC  mov     bx, ax
001849BE  mov     es, dx
001849C0  push    word ptr es:[bx+1AD8h]
001849C5  push    word ptr es:[bx+1AD6h]
001849CA  call    string_concatenate
001849CF  add     sp, 0Ch
001849D2  push    7894h
001849D5  push    0F32h
001849D8  mov     ax, [bp+var_2]
001849DB  shl     ax, 1
001849DD  mov     dx, 6E1Eh
001849E0  mov     es, dx
001849E2  les     bx, dword ptr es:loc_6E2A1+3
001849E7  add     bx, ax
001849E9  mov     ax, es:[bx]
001849EC  mov     dx, 42h ; 'B'
001849EF  imul    dx
001849F1  mov     dx, 6E1Eh
001849F4  mov     es, dx
001849F6  mov     dx, word ptr es:byte_6E1C9+47h
001849FB  add     dx, ax
001849FD  inc     dx
001849FE  inc     dx
001849FF  push    word ptr es:byte_6E1C9+49h
00184A04  push    dx
00184A05  push    7894h
00184A08  push    0F32h
00184A0B  call    string_concatenate
00184A10  add     sp, 0Ch
00184A13  push    7894h
00184A16  push    0F32h
00184A19  mov     ax, 6E1Eh
00184A1C  mov     es, ax
00184A1E  push    es:word_6E83F
00184A23  push    es:word_6E83D
00184A28  push    7894h
00184A2B  push    0F32h
00184A2E  call    string_concatenate
00184A33  add     sp, 0Ch
00184A36  push    7894h
00184A39  push    0F32h
00184A3C  mov     ax, [bp+var_2]
00184A3F  shl     ax, 1
00184A41  mov     dx, 6E1Eh
00184A44  mov     es, dx
00184A46  les     bx, dword ptr es:loc_6E2A1+3
00184A4B  add     bx, ax
00184A4D  mov     ax, es:[bx]
00184A50  mov     dx, 42h ; 'B'
00184A53  imul    dx
00184A55  mov     dx, 6E1Eh
00184A58  mov     es, dx
00184A5A  les     bx, dword ptr es:byte_6E1C9+47h
00184A5F  add     bx, ax
00184A61  mov     al, es:[bx+26h]
00184A65  cbw
00184A66  and     ax, 0Fh
00184A69  shl     ax, 2
00184A6C  mov     dx, 602Eh
00184A6F  mov     bx, ax
00184A71  mov     es, dx
00184A73  push    word ptr es:[bx+1B9Bh]
00184A78  push    word ptr es:[bx+1B99h]
00184A7D  push    7894h
00184A80  push    0F32h
00184A83  call    string_concatenate
00184A88  add     sp, 0Ch
00184A8B  mov     ax, 7894h
00184A8E  mov     es, ax
00184A90  push    es:word_79D1E
00184A95  push    7894h
00184A98  push    0F32h
00184A9B  call    sub_135C57
00184AA0  add     sp, 6
00184AA3  mov     dx, 7894h
00184AA6  mov     es, dx
00184AA8  mov     es:word_79D1E, ax
00184AAC  inc     [bp+var_2]
00184AAF  cmp     [bp+var_2], 8
00184AB3  jge     short loc_184AB8
00184AB5  jmp     loc_184960
00184AB8  mov     ax, 4FC2h
00184ABB  mov     es, ax
00184ABD  mov     es:word_13E006, 0
00184AC4  mov     ax, 4FC2h
00184AC7  mov     es, ax
00184AC9  mov     es:word_13E008, 0
00184AD0  call    sub_13504F
00184AD5  call    undoc_12661D
00184ADA  xor     si, si
00184ADC  jmp     def_184BBE; jumptable 00184BBE default case, cases 1-5
00184ADF  call    undoc_11D941
00184AE4  call    undoc_12661D
00184AE9  push    1
00184AEB  call    loc_69C25
00184AF0  pop     cx
00184AF1  call    sub_12805C
00184AF6  call    sub_12DB63
00184AFB  mov     ax, 7894h
00184AFE  mov     es, ax
00184B00  cmp     es:word_79B6C, 32h ; '2'
00184B06  jz      short loc_184B0B
00184B08  jmp     loc_184B90
00184B0B  mov     ax, 7894h
00184B0E  mov     es, ax
00184B10  mov     ax, es:input_scan_code_queue
00184B14  cmp     ax, 1
00184B17  jz      short loc_184B33
00184B19  cmp     ax, 3
00184B1C  jz      short loc_184B25
00184B1E  cmp     ax, 0FFh
00184B21  jz      short loc_184B36
00184B23  jmp     short loc_184B88
00184B25  mov     ax, 7894h
00184B28  mov     es, ax
00184B2A  mov     es:current_view_index, 7
00184B31  jmp     short loc_184BAA
00184B33  jmp     loc_1824A3; VIEW KEY HANDLER: Push view index 8, call view setup (likely padlock view)
00184B36  mov     ax, 4FC2h
00184B39  mov     es, ax
00184B3B  push    es:word_13E012
00184B40  call    sub_2C761; Overlay bridge trampoline (8B, 14 calls)
00184B45  pop     cx
00184B46  mov     ax, 7894h
00184B49  mov     es, ax
00184B4B  les     bx, es:menu_state_ptr
00184B50  dec     word ptr es:[bx]
00184B53  mov     ax, 4FC2h
00184B56  mov     es, ax
00184B58  push    es:word_13E012
00184B5D  call    far ptr menu_finalize_render
00184B62  pop     cx
00184B63  call    sub_11D274
00184B68  mov     ax, 7894h
00184B6B  mov     es, ax
00184B6D  les     bx, es:menu_state_ptr
00184B72  inc     word ptr es:[bx]
00184B75  mov     ax, 4FC2h
00184B78  mov     es, ax
00184B7A  push    es:word_13E012
00184B7F  call    far ptr menu_finalize_render
00184B84  pop     cx
00184B85  jmp     def_184BBE; jumptable 00184BBE default case, cases 1-5
00184B88  call    menu_cursor_position_set
00184B8D  jmp     def_184BBE; jumptable 00184BBE default case, cases 1-5
00184B90  mov     ax, 7894h
00184B93  mov     es, ax
00184B95  cmp     es:word_79B6C, 34h ; '4'
00184B9B  jz      short loc_184BAA
00184B9D  mov     es, ax
00184B9F  cmp     es:word_79B6C, 36h ; '6'
00184BA5  jz      short loc_184BAA
00184BA7  jmp     def_184BBE; jumptable 00184BBE default case, cases 1-5
00184BAA  mov     ax, 7894h
00184BAD  mov     es, ax
00184BAF  mov     bx, es:current_view_index
00184BB4  cmp     bx, 8; switch 9 cases
00184BB7  jbe     short loc_184BBC
00184BB9  jmp     def_184BBE; jumptable 00184BBE default case, cases 1-5
00184BBC  shl     bx, 1
00184BBE  jmp     cs:jpt_184BBE[bx]; switch jump
00184BC3  mov     ax, 7894h; jumptable 00184BBE case 0
00184BC6  mov     es, ax
00184BC8  cmp     es:word_79E80, 12Ch
00184BCF  jge     short loc_184BD4
00184BD1  jmp     def_184BBE; jumptable 00184BBE default case, cases 1-5
00184BD4  mov     ax, 7894h
00184BD7  mov     es, ax
00184BD9  push    es:current_view_index
00184BDE  call    far ptr loc_69E0E+1
00184BE3  pop     cx
00184BE4  call    sub_12805C
00184BE9  jmp     short loc_184C1E
00184BEB  mov     ax, 7894h
00184BEE  mov     es, ax
00184BF0  cmp     es:word_79E32, 0
00184BF6  jle     short loc_184BFF
00184BF8  mov     es, ax
00184BFA  dec     es:word_79E32
00184BFF  call    far ptr loc_69EA9
00184C04  mov     ax, 7894h
00184C07  mov     es, ax
00184C09  push    es:current_view_index
00184C0E  call    far ptr loc_69E0E+1
00184C13  pop     cx
00184C14  call    sub_12805C
00184C19  call    input_poll_handler; Main keyboard input handler. Processes all keyboard input.
00184C1E  mov     ax, 7894h
00184C21  mov     es, ax
00184C23  cmp     es:input_flag_pending_1, 0
00184C29  jnz     short loc_184BEB
00184C2B  jmp     short loc_184CA1
00184C2D  mov     ax, 7894h; jumptable 00184BBE case 6
00184C30  mov     es, ax
00184C32  cmp     es:word_79E80, 12Ch
00184C39  jge     short loc_184C3E
00184C3B  jmp     def_184BBE; jumptable 00184BBE default case, cases 1-5
00184C3E  mov     ax, 7894h
00184C41  mov     es, ax
00184C43  push    es:current_view_index
00184C48  call    far ptr loc_69E0E+1
00184C4D  pop     cx
00184C4E  call    sub_12805C
00184C53  jmp     short loc_184C94
00184C55  mov     ax, 7894h
00184C58  mov     dx, 7894h
00184C5B  mov     es, dx
00184C5D  mov     dx, es:word_79D1E
00184C62  add     dx, 0FFF4h
00184C65  mov     es, ax
00184C67  cmp     es:word_79E32, dx
00184C6C  jge     short loc_184C75
00184C6E  mov     es, ax
00184C70  inc     es:word_79E32
00184C75  call    far ptr loc_69EA9
00184C7A  mov     ax, 7894h
00184C7D  mov     es, ax
00184C7F  push    es:current_view_index
00184C84  call    far ptr loc_69E0E+1
00184C89  pop     cx
00184C8A  call    sub_12805C
00184C8F  call    input_poll_handler; Main keyboard input handler. Processes all keyboard input.
00184C94  mov     ax, 7894h
00184C97  mov     es, ax
00184C99  cmp     es:input_flag_pending_1, 0
00184C9F  jnz     short loc_184C55
00184CA1  call    undoc_130B39
00184CA6  jmp     short def_184BBE; jumptable 00184BBE default case, cases 1-5
00184CA8  push    7; jumptable 00184BBE case 7
00184CAA  call    far ptr loc_69CBE
00184CAF  pop     cx
00184CB0  call    sub_12805C
00184CB5  call    menu_cursor_position_set
00184CBA  mov     si, 1
00184CBD  jmp     short def_184BBE; jumptable 00184BBE default case, cases 1-5
00184CBF  jmp     loc_1824A3; jumptable 00184BBE case 8
00184CC2  or      si, si; jumptable 00184BBE default case, cases 1-5
00184CC4  jnz     short loc_184CC9
00184CC6  jmp     loc_184ADF
00184CC9  call    ui_string_formatter_interactive
00184CCE  mov     ax, 7894h
00184CD1  mov     es, ax
00184CD3  mov     es:word_79B74, 8
00184CDA  mov     ax, 7894h
00184CDD  mov     es, ax
00184CDF  mov     es:word_79BD6, 0FFFFh
00184CE6  mov     ax, 7894h
00184CE9  mov     es, ax
00184CEB  mov     es:word_79B5A, 2
00184CF2  mov     ax, 7894h
00184CF5  mov     es, ax
00184CF7  mov     es:word_79E32, 0
00184CFE  mov     ax, 7894h
00184D01  mov     es, ax
00184D03  mov     es:word_79D1E, 0
00184D0A  mov     ax, 7894h
00184D0D  mov     es, ax
00184D0F  mov     es:word_79B60, 0
00184D16  mov     ax, 7894h
00184D19  mov     es, ax
00184D1B  mov     es:word_79E86, 1
00184D22  mov     ax, 4FC2h
00184D25  mov     es, ax
00184D27  mov     es:word_13E006, 0
00184D2E  mov     ax, 4FC2h
00184D31  mov     es, ax
00184D33  mov     es:word_13E008, 0
00184D3A  mov     ax, 7894h
00184D3D  mov     es, ax
00184D3F  mov     es:word_79B5E, 0
00184D46  call    sub_13504F
00184D4B  mov     ax, 602Eh
00184D4E  mov     es, ax
00184D50  test    es:word_14F8BE, 20h
00184D57  jnz     short loc_184D5C
00184D59  jmp     loc_184E02
00184D5C  call    undoc_11D20D
00184D61  call    sub_12805C
00184D66  call    far ptr sub_2C725
00184D6B  push    7894h
00184D6E  push    0F32h
00184D71  mov     ax, 602Eh
00184D74  mov     es, ax
00184D76  push    word ptr es:aMap+1; ".`.MAP"
00184D7B  push    word ptr es:byte_151349
00184D80  mov     ax, 602Eh
00184D83  mov     es, ax
00184D85  push    word ptr es:aOccupy+1; ".`OCCUPY"
00184D8A  push    word ptr es:byte_151274
00184D8F  call    string_concatenate
00184D94  add     sp, 0Ch
00184D97  call    mouse_gate_far_entry
00184D9C  push    7894h
00184D9F  push    0F32h
00184DA2  push    0
00184DA4  push    0
00184DA6  push    4
00184DA8  call    op_dispatch_far_entry
00184DAD  add     sp, 0Ah
00184DB0  mov     dx, 6E1Eh
00184DB3  mov     es, dx
00184DB5  mov     word ptr es:byte_6E1C9+4Bh, ax
00184DB9  cmp     ax, 0FFFFh
00184DBC  jz      short loc_184E07
00184DBE  mov     ax, 7894h
00184DC1  mov     es, ax
00184DC3  push    word ptr es:dword_79D92+2
00184DC8  push    word ptr es:dword_79D92
00184DCD  push    0BB84h
00184DD0  mov     ax, 6E1Eh
00184DD3  mov     es, ax
00184DD5  push    word ptr es:byte_6E1C9+4Bh
00184DDA  push    0Ch
00184DDC  call    op_dispatch_far_entry
00184DE1  add     sp, 0Ah
00184DE4  push    6E1Eh
00184DE7  push    34h ; '4'
00184DEA  push    0
00184DEC  mov     ax, 6E1Eh
00184DEF  mov     es, ax
00184DF1  push    word ptr es:byte_6E1C9+4Bh
00184DF6  push    8
00184DF8  call    op_dispatch_far_entry
00184DFD  add     sp, 0Ah
00184E00  jmp     short loc_184E07
00184E02  call    far ptr tail_bridge_to_ui_menu_frame_enter_b
00184E07  call    ui_text_render_setup
00184E0C  push    7894h
00184E0F  push    0F32h
00184E12  mov     ax, 6E1Eh
00184E15  mov     es, ax
00184E17  push    word ptr es:loc_6E33B+2
00184E1C  push    word ptr es:loc_6E33B
00184E21  call    string_copy_with_offset
00184E26  add     sp, 8
00184E29  push    7894h
00184E2C  push    0F32h
00184E2F  mov     ax, 602Eh
00184E32  mov     es, ax
00184E34  push    word ptr es:aJ0+2; ".`\n"
00184E39  push    word ptr es:aJ0; "J0.`\n"
00184E3E  push    7894h
00184E41  push    0F32h
00184E44  call    string_concatenate
00184E49  add     sp, 0Ch
00184E4C  push    7894h
00184E4F  push    0F32h
00184E52  mov     ax, 602Eh
00184E55  mov     es, ax
00184E57  push    word ptr es:aJ0+2; ".`\n"
00184E5C  push    word ptr es:aJ0; "J0.`\n"
00184E61  push    7894h
00184E64  push    0F32h
00184E67  call    string_concatenate
00184E6C  add     sp, 0Ch
00184E6F  push    7894h
00184E72  push    0F32h
00184E75  mov     ax, 6E1Eh
00184E78  mov     es, ax
00184E7A  push    word ptr es:loc_6E340+1
00184E7F  push    word ptr es:loc_6E33B+4
00184E84  push    7894h
00184E87  push    0F32h
00184E8A  call    string_concatenate
00184E8F  add     sp, 0Ch
00184E92  push    0
00184E94  call    loc_6A173+3
00184E99  pop     cx
00184E9A  mov     dx, 6E1Eh
00184E9D  mov     es, dx
00184E9F  mov     word ptr es:byte_6E1C9+17h, ax
00184EA3  push    602Eh
00184EA6  push    1400h
00184EA9  mov     ax, 6E1Eh
00184EAC  mov     es, ax
00184EAE  push    word ptr es:byte_6E1C9+17h
00184EB3  call    int_to_string_converter
00184EB8  add     sp, 6
00184EBB  push    7894h
00184EBE  push    0F32h
00184EC1  push    602Eh
00184EC4  push    1400h
00184EC7  push    7894h
00184ECA  push    0F32h
00184ECD  call    string_concatenate
00184ED2  add     sp, 0Ch
00184ED5  push    7894h
00184ED8  push    0F32h
00184EDB  mov     ax, 6E1Eh
00184EDE  mov     es, ax
00184EE0  push    word ptr es:loc_6E346+3
00184EE5  push    word ptr es:loc_6E346+1
00184EEA  push    7894h
00184EED  push    0F32h
00184EF0  call    string_concatenate
00184EF5  add     sp, 0Ch
00184EF8  push    7894h
00184EFB  push    0F32h
00184EFE  mov     ax, 602Eh
00184F01  mov     es, ax
00184F03  push    word ptr es:aJ0+2; ".`\n"
00184F08  push    word ptr es:aJ0; "J0.`\n"
00184F0D  push    7894h
00184F10  push    0F32h
00184F13  call    string_concatenate
00184F18  add     sp, 0Ch
00184F1B  push    7894h
00184F1E  push    0F32h
00184F21  mov     ax, 602Eh
00184F24  mov     es, ax
00184F26  push    word ptr es:aJ0+2; ".`\n"
00184F2B  push    word ptr es:aJ0; "J0.`\n"
00184F30  push    7894h
00184F33  push    0F32h
00184F36  call    string_concatenate
00184F3B  add     sp, 0Ch
00184F3E  push    7894h
00184F41  push    0F32h
00184F44  mov     ax, 6E1Eh
00184F47  mov     es, ax
00184F49  push    word ptr es:undoc_6E343+2
00184F4E  push    word ptr es:undoc_6E343
00184F53  push    7894h
00184F56  push    0F32h
00184F59  call    string_concatenate
00184F5E  add     sp, 0Ch
00184F61  push    1
00184F63  call    loc_6A173+3
00184F68  pop     cx
00184F69  mov     dx, 6E1Eh
00184F6C  mov     es, dx
00184F6E  mov     word ptr es:byte_6E1C9+17h, ax
00184F72  push    602Eh
00184F75  push    1400h
00184F78  mov     ax, 6E1Eh
00184F7B  mov     es, ax
00184F7D  push    word ptr es:byte_6E1C9+17h
00184F82  call    int_to_string_converter
00184F87  add     sp, 6
00184F8A  push    7894h
00184F8D  push    0F32h
00184F90  push    602Eh
00184F93  push    1400h
00184F96  push    7894h
00184F99  push    0F32h
00184F9C  call    string_concatenate
00184FA1  add     sp, 0Ch
00184FA4  push    7894h
00184FA7  push    0F32h
00184FAA  mov     ax, 6E1Eh
00184FAD  mov     es, ax
00184FAF  push    word ptr es:loc_6E346+3
00184FB4  push    word ptr es:loc_6E346+1
00184FB9  push    7894h
00184FBC  push    0F32h
00184FBF  call    string_concatenate
00184FC4  add     sp, 0Ch
00184FC7  push    7894h
00184FCA  push    0F32h
00184FCD  mov     ax, 602Eh
00184FD0  mov     es, ax
00184FD2  push    word ptr es:aJ0+2; ".`\n"
00184FD7  push    word ptr es:aJ0; "J0.`\n"
00184FDC  push    7894h
00184FDF  push    0F32h
00184FE2  call    string_concatenate
00184FE7  add     sp, 0Ch
00184FEA  push    0
00184FEC  push    7894h
00184FEF  push    0F32h
00184FF2  call    sub_135C57
00184FF7  add     sp, 6
00184FFA  mov     dx, 7894h
00184FFD  mov     es, dx
00184FFF  mov     es:word_79D1E, ax
00185003  mov     ax, 4FC2h
00185006  mov     es, ax
00185008  mov     es:word_13E006, 0
0018500F  mov     ax, 4FC2h
00185012  mov     es, ax
00185014  mov     es:word_13E008, 0
0018501B  call    sub_13504F
00185020  call    undoc_12661D
00185025  call    ui_text_render_setup
0018502A  push    9
0018502C  call    far ptr sub_2C351
00185031  pop     cx
00185032  push    1
00185034  call    far ptr loc_69D4C
00185039  pop     cx
0018503A  call    sub_12805C
0018503F  xor     si, si
00185041  call    undoc_11D941
00185046  jmp     loc_1851CC
00185049  call    sub_12805C
0018504E  call    sub_12DB63
00185053  mov     ax, 7894h
00185056  mov     es, ax
00185058  cmp     es:word_79B6C, 32h ; '2'
0018505E  jz      short loc_185063
00185060  jmp     loc_1850E9
00185063  mov     ax, 7894h
00185066  mov     es, ax
00185068  mov     ax, es:input_scan_code_queue
0018506C  cmp     ax, 1
0018506F  jz      short loc_18507D
00185071  cmp     ax, 3
00185074  jz      short loc_18507D
00185076  cmp     ax, 0FFh
00185079  jz      short loc_185082
0018507B  jmp     short loc_1850E6
0018507D  push    2
0018507F  jmp     loc_1851A0
00185082  mov     ax, 4FC2h
00185085  mov     es, ax
00185087  push    es:word_13E012
0018508C  call    sub_2C761; Overlay bridge trampoline (8B, 14 calls)
00185091  pop     cx
00185092  mov     ax, 7894h
00185095  mov     es, ax
00185097  les     bx, es:menu_state_ptr
0018509C  dec     word ptr es:[bx]
0018509F  mov     ax, 4FC2h
001850A2  mov     es, ax
001850A4  push    es:word_13E012
001850A9  call    far ptr menu_finalize_render
001850AE  pop     cx
001850AF  call    sub_11D274
001850B4  mov     ax, 7894h
001850B7  mov     es, ax
001850B9  les     bx, es:menu_state_ptr
001850BE  inc     word ptr es:[bx]
001850C1  mov     ax, 4FC2h
001850C4  mov     es, ax
001850C6  push    es:word_13E012
001850CB  call    far ptr menu_finalize_render
001850D0  pop     cx
001850D1  call    undoc_12661D
001850D6  push    1
001850D8  call    far ptr loc_69D4C
001850DD  pop     cx
001850DE  call    sub_12805C
001850E3  jmp     loc_1851CC
001850E6  jmp     def_185117; jumptable 00185117 default case, cases 1-5
001850E9  mov     ax, 7894h
001850EC  mov     es, ax
001850EE  cmp     es:word_79B6C, 34h ; '4'
001850F4  jz      short loc_185103
001850F6  mov     es, ax
001850F8  cmp     es:word_79B6C, 36h ; '6'
001850FE  jz      short loc_185103
00185100  jmp     loc_1851CC
00185103  mov     ax, 7894h
00185106  mov     es, ax
00185108  mov     bx, es:current_view_index
0018510D  cmp     bx, 9; switch 10 cases
00185110  jbe     short loc_185115
00185112  jmp     def_185117; jumptable 00185117 default case, cases 1-5
00185115  shl     bx, 1
00185117  jmp     cs:jpt_185117[bx]; switch jump
0018511C  mov     ax, 7894h; jumptable 00185117 cases 0,6
0018511F  mov     es, ax
00185121  cmp     es:word_79E80, 12Ch
00185128  jge     short loc_18512D
0018512A  jmp     loc_1851CC
0018512D  mov     ax, 7894h
00185130  mov     es, ax
00185132  push    es:current_view_index
00185137  call    far ptr loc_69CBE
0018513C  pop     cx
0018513D  call    sub_12805C
00185142  jmp     short loc_185149
00185144  call    input_poll_handler; Main keyboard input handler. Processes all keyboard input.
00185149  mov     ax, 7894h
0018514C  mov     es, ax
0018514E  cmp     es:input_flag_pending_1, 0
00185154  jnz     short loc_185144
00185156  call    undoc_130B39
0018515B  jmp     short loc_1851CC
0018515D  mov     ax, 7894h; jumptable 00185117 case 7
00185160  mov     es, ax
00185162  push    es:current_view_index
00185167  call    far ptr loc_69E0E+1
0018516C  pop     cx
0018516D  call    undoc_133535
00185172  call    sub_135DF4; Utility function (473B, 16 calls) - needs investigation
00185177  call    campaign_save_temp_file_write
0018517C  call    mission_temp_file_load
00185181  call    sub_12805C
00185186  call    menu_cursor_position_set
0018518B  push    8
0018518D  call    far ptr sub_2C351
00185192  pop     cx
00185193  jmp     loc_18210C
00185196  mov     ax, 7894h; jumptable 00185117 case 8
00185199  mov     es, ax
0018519B  push    es:current_view_index
001851A0  call    far ptr loc_69E0E+1
001851A5  jmp     loc_1824AA
001851A8  mov     ax, 7894h; jumptable 00185117 case 9
001851AB  mov     es, ax
001851AD  push    es:current_view_index
001851B2  call    far ptr loc_69E0E+1
001851B7  pop     cx
001851B8  call    sub_12805C
001851BD  call    menu_cursor_position_set
001851C2  mov     si, 1
001851C5  jmp     short loc_1851CC
001851C7  call    menu_cursor_position_set; jumptable 00185117 default case, cases 1-5
001851CC  or      si, si
001851CE  jnz     short loc_1851D3
001851D0  jmp     loc_185049
001851D3  mov     ax, 7894h
001851D6  mov     es, ax
001851D8  mov     es:word_79B60, 28h ; '('
001851DF  mov     ax, 7894h
001851E2  mov     es, ax
001851E4  mov     es:word_79E86, 1
001851EB  mov     ax, 7894h
001851EE  mov     es, ax
001851F0  mov     es:word_79B74, 2
001851F7  mov     ax, 7894h
001851FA  mov     es, ax
001851FC  mov     es:word_79BD6, 0FFFFh
00185203  mov     ax, 7894h
00185206  mov     es, ax
00185208  mov     es:word_79B5A, 2
0018520F  mov     ax, 7894h
00185212  mov     es, ax
00185214  mov     es:word_79E32, 0
0018521B  mov     ax, 7894h
0018521E  mov     es, ax
00185220  mov     es:word_79D1E, 0
00185227  call    far ptr sub_2C3E7
0018522C  push    3
0018522E  call    loc_6A9A2
00185233  pop     cx
00185234  push    0
00185236  call    far ptr sub_2C351
0018523B  pop     cx
0018523C  call    far ptr sub_2C3E7
00185241  pop     di
00185242  pop     si
00185243  leave
00185244  retf
