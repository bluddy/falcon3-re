; squad_campaign_file_loader
; Address: 0x6A651 - 0x6AE59
; Size: 2056 bytes

0006A651  enter   6, 0
0006A655  push    si
0006A656  push    di
0006A657  mov     di, [bp+arg_0]
0006A65A  call    flag2224a_clear; Clear flag 2224a
0006A65F  mov     ax, 4FC2h
0006A662  mov     es, ax
0006A664  push    es:word_13E016; Push word_13E016 (dispatch parameter)
0006A669  call    dispatch_220f0_invoke_1arg
0006A66E  pop     cx
0006A66F  mov     ax, 7894h
0006A672  mov     es, ax
0006A674  mov     ax, word ptr es:dword_79E60+2; Load dword_79E60 base pointer
0006A678  mov     dx, word ptr es:dword_79E60
0006A67D  add     dx, 7530h; Add offset 0x7530 (30,000 bytes)
0006A681  mov     [bp+var_4], ax
0006A684  mov     [bp+var_6], dx
0006A687  mov     ax, 602Eh
0006A68A  mov     es, ax
0006A68C  push    word ptr es:current_menu_slot_ptr+2; Load current_menu_slot_ptr (squadron selection)
0006A691  push    word ptr es:current_menu_slot_ptr
0006A696  push    di
0006A697  call    int_to_string_converter; Convert squadron number to string (0-N)
0006A69C  add     sp, 6
0006A69F  push    7894h
0006A6A2  push    0F32h; Target buffer at 7894:0F32
0006A6A5  mov     ax, 602Eh
0006A6A8  mov     es, ax
0006A6AA  push    word ptr es:current_menu_slot_ptr+2
0006A6AF  push    word ptr es:current_menu_slot_ptr
0006A6B4  mov     ax, 602Eh
0006A6B7  mov     es, ax
0006A6B9  push    word ptr es:aSSquad+2; String '.`SQUAD' / 'S-.`SQUAD'
0006A6BE  push    word ptr es:aSSquad; "S-.`SQUAD"
0006A6C3  call    string_concatenate; Concatenate: buffer + slot + 'SQUAD'
0006A6C8  add     sp, 0Ch
0006A6CB  push    7894h
0006A6CE  push    0F32h
0006A6D1  mov     ax, 602Eh
0006A6D4  mov     es, ax
0006A6D6  push    word ptr es:aCam+1; String '.`.CAM'
0006A6DB  push    word ptr es:byte_151325
0006A6E0  push    7894h
0006A6E3  push    0F32h
0006A6E6  call    string_concatenate; Concatenate: buffer + '.CAM'
0006A6EB  add     sp, 0Ch
0006A6EE  push    7894h
0006A6F1  push    0F32h
0006A6F4  push    0
0006A6F6  push    2
0006A6F8  push    6
0006A6FA  call    op_dispatch_far_entry; op_dispatch operation 6 (OPEN file)
0006A6FF  add     sp, 0Ah
0006A702  mov     [bp+var_2], ax; Store file handle in var_2
0006A705  cmp     ax, 0FFFFh; Check if open failed (0xFFFF)
0006A708  jz      short loc_6A777
0006A70A  push    [bp+var_4]
0006A70D  push    [bp+var_6]
0006A710  push    0FFFFh
0006A712  push    [bp+var_2]
0006A715  push    0Ah
0006A717  call    op_dispatch_far_entry; op_dispatch operation 10 (READ)
0006A71C  add     sp, 0Ah
0006A71F  mov     si, ax
0006A721  push    ss
0006A722  lea     ax, [bp+var_2]
0006A725  push    ax
0006A726  push    0
0006A728  push    [bp+var_2]
0006A72B  push    8
0006A72D  call    op_dispatch_far_entry; op_dispatch operation 8 (READ)
0006A732  add     sp, 0Ah
0006A735  call    flag2224a_set; Set flag 2224a
0006A73A  push    ds
0006A73B  push    0A34Ah
0006A73E  push    0
0006A740  push    0
0006A742  push    4
0006A744  call    op_dispatch_far_entry; op_dispatch operation 4 (OPEN another file)
0006A749  add     sp, 0Ah
0006A74C  mov     [bp+var_2], ax
0006A74F  push    [bp+var_4]
0006A752  push    [bp+var_6]
0006A755  push    si
0006A756  push    [bp+var_2]
0006A759  push    0Ch
0006A75B  call    op_dispatch_far_entry; op_dispatch operation 12 (READ)
0006A760  add     sp, 0Ah
0006A763  push    ss
0006A764  lea     ax, [bp+var_2]
0006A767  push    ax
0006A768  push    0
0006A76A  push    [bp+var_2]
0006A76D  push    8
0006A76F  call    op_dispatch_far_entry
0006A774  add     sp, 0Ah
0006A777  mov     ax, 602Eh
0006A77A  mov     es, ax
0006A77C  push    word ptr es:current_menu_slot_ptr+2
0006A781  push    word ptr es:current_menu_slot_ptr
0006A786  push    di
0006A787  call    int_to_string_converter
0006A78C  add     sp, 6
0006A78F  push    7894h
0006A792  push    0F32h
0006A795  mov     ax, 602Eh
0006A798  mov     es, ax
0006A79A  push    word ptr es:current_menu_slot_ptr+2
0006A79F  push    word ptr es:current_menu_slot_ptr
0006A7A4  mov     ax, 602Eh
0006A7A7  mov     es, ax
0006A7A9  push    word ptr es:aSSquad+2; ".`SQUAD"
0006A7AE  push    word ptr es:aSSquad; "S-.`SQUAD"
0006A7B3  call    string_concatenate
0006A7B8  add     sp, 0Ch
0006A7BB  push    7894h
0006A7BE  push    0F32h
0006A7C1  mov     ax, 602Eh
0006A7C4  mov     es, ax
0006A7C6  push    word ptr es:aSqu+1; ".`.SQU"
0006A7CB  push    word ptr es:byte_151393
0006A7D0  push    7894h
0006A7D3  push    0F32h
0006A7D6  call    string_concatenate
0006A7DB  add     sp, 0Ch
0006A7DE  push    7894h
0006A7E1  push    0F32h
0006A7E4  push    0
0006A7E6  push    2
0006A7E8  push    6
0006A7EA  call    op_dispatch_far_entry
0006A7EF  add     sp, 0Ah
0006A7F2  mov     [bp+var_2], ax
0006A7F5  cmp     ax, 0FFFFh
0006A7F8  jz      short loc_6A867
0006A7FA  push    [bp+var_4]
0006A7FD  push    [bp+var_6]
0006A800  push    0FFFFh
0006A802  push    [bp+var_2]
0006A805  push    0Ah
0006A807  call    op_dispatch_far_entry
0006A80C  add     sp, 0Ah
0006A80F  mov     si, ax
0006A811  push    ss
0006A812  lea     ax, [bp+var_2]
0006A815  push    ax
0006A816  push    0
0006A818  push    [bp+var_2]
0006A81B  push    8
0006A81D  call    op_dispatch_far_entry
0006A822  add     sp, 0Ah
0006A825  call    flag2224a_set
0006A82A  push    ds
0006A82B  push    0A355h
0006A82E  push    0
0006A830  push    0
0006A832  push    4
0006A834  call    op_dispatch_far_entry
0006A839  add     sp, 0Ah
0006A83C  mov     [bp+var_2], ax
0006A83F  push    [bp+var_4]
0006A842  push    [bp+var_6]
0006A845  push    si
0006A846  push    [bp+var_2]
0006A849  push    0Ch
0006A84B  call    op_dispatch_far_entry
0006A850  add     sp, 0Ah
0006A853  push    ss
0006A854  lea     ax, [bp+var_2]
0006A857  push    ax
0006A858  push    0
0006A85A  push    [bp+var_2]
0006A85D  push    8
0006A85F  call    op_dispatch_far_entry
0006A864  add     sp, 0Ah
0006A867  call    flag2224a_clear
0006A86C  mov     ax, 602Eh
0006A86F  mov     es, ax
0006A871  push    word ptr es:current_menu_slot_ptr+2
0006A876  push    word ptr es:current_menu_slot_ptr
0006A87B  push    di
0006A87C  call    int_to_string_converter
0006A881  add     sp, 6
0006A884  push    7894h
0006A887  push    0F32h
0006A88A  mov     ax, 602Eh
0006A88D  mov     es, ax
0006A88F  push    word ptr es:current_menu_slot_ptr+2
0006A894  push    word ptr es:current_menu_slot_ptr
0006A899  mov     ax, 602Eh
0006A89C  mov     es, ax
0006A89E  push    word ptr es:aSSquad+2; ".`SQUAD"
0006A8A3  push    word ptr es:aSSquad; "S-.`SQUAD"
0006A8A8  call    string_concatenate
0006A8AD  add     sp, 0Ch
0006A8B0  push    7894h
0006A8B3  push    0F32h
0006A8B6  mov     ax, 602Eh
0006A8B9  mov     es, ax
0006A8BB  push    word ptr es:aMis+1; ".`.MIS"
0006A8C0  push    word ptr es:byte_151352
0006A8C5  push    7894h
0006A8C8  push    0F32h
0006A8CB  call    string_concatenate
0006A8D0  add     sp, 0Ch
0006A8D3  push    7894h
0006A8D6  push    0F32h
0006A8D9  push    0
0006A8DB  push    2
0006A8DD  push    6
0006A8DF  call    op_dispatch_far_entry
0006A8E4  add     sp, 0Ah
0006A8E7  mov     [bp+var_2], ax
0006A8EA  cmp     ax, 0FFFFh
0006A8ED  jz      short loc_6A95C
0006A8EF  push    [bp+var_4]
0006A8F2  push    [bp+var_6]
0006A8F5  push    0FFFFh
0006A8F7  push    [bp+var_2]
0006A8FA  push    0Ah
0006A8FC  call    op_dispatch_far_entry
0006A901  add     sp, 0Ah
0006A904  mov     si, ax
0006A906  push    ss
0006A907  lea     ax, [bp+var_2]
0006A90A  push    ax
0006A90B  push    0
0006A90D  push    [bp+var_2]
0006A910  push    8
0006A912  call    op_dispatch_far_entry
0006A917  add     sp, 0Ah
0006A91A  call    flag2224a_set
0006A91F  push    ds
0006A920  push    0A360h
0006A923  push    0
0006A925  push    0
0006A927  push    4
0006A929  call    op_dispatch_far_entry
0006A92E  add     sp, 0Ah
0006A931  mov     [bp+var_2], ax
0006A934  push    [bp+var_4]
0006A937  push    [bp+var_6]
0006A93A  push    si
0006A93B  push    [bp+var_2]
0006A93E  push    0Ch
0006A940  call    op_dispatch_far_entry
0006A945  add     sp, 0Ah
0006A948  push    ss
0006A949  lea     ax, [bp+var_2]
0006A94C  push    ax
0006A94D  push    0
0006A94F  push    [bp+var_2]
0006A952  push    8
0006A954  call    op_dispatch_far_entry
0006A959  add     sp, 0Ah
0006A95C  call    flag2224a_clear
0006A961  mov     ax, 602Eh
0006A964  mov     es, ax
0006A966  push    word ptr es:current_menu_slot_ptr+2
0006A96B  push    word ptr es:current_menu_slot_ptr
0006A970  push    di
0006A971  call    int_to_string_converter
0006A976  add     sp, 6
0006A979  push    7894h
0006A97C  push    0F32h
0006A97F  mov     ax, 602Eh
0006A982  mov     es, ax
0006A984  push    word ptr es:current_menu_slot_ptr+2
0006A989  push    word ptr es:current_menu_slot_ptr
0006A98E  mov     ax, 602Eh
0006A991  mov     es, ax
0006A993  push    word ptr es:aSSquad+2; ".`SQUAD"
0006A998  push    word ptr es:aSSquad; "S-.`SQUAD"
0006A99D  call    string_concatenate
0006A9A2  add     sp, 0Ch
0006A9A5  push    7894h
0006A9A8  push    0F32h
0006A9AB  mov     ax, 602Eh
0006A9AE  mov     es, ax
0006A9B0  push    word ptr es:aMtv+1; ".`.MTV"
0006A9B5  push    word ptr es:byte_151365
0006A9BA  push    7894h
0006A9BD  push    0F32h
0006A9C0  call    string_concatenate
0006A9C5  add     sp, 0Ch
0006A9C8  push    7894h
0006A9CB  push    0F32h
0006A9CE  push    0
0006A9D0  push    2
0006A9D2  push    6
0006A9D4  call    op_dispatch_far_entry
0006A9D9  add     sp, 0Ah
0006A9DC  mov     [bp+var_2], ax
0006A9DF  cmp     ax, 0FFFFh
0006A9E2  jz      short loc_6AA51
0006A9E4  push    [bp+var_4]
0006A9E7  push    [bp+var_6]
0006A9EA  push    0FFFFh
0006A9EC  push    [bp+var_2]
0006A9EF  push    0Ah
0006A9F1  call    op_dispatch_far_entry
0006A9F6  add     sp, 0Ah
0006A9F9  mov     si, ax
0006A9FB  push    ss
0006A9FC  lea     ax, [bp+var_2]
0006A9FF  push    ax
0006AA00  push    0
0006AA02  push    [bp+var_2]
0006AA05  push    8
0006AA07  call    op_dispatch_far_entry
0006AA0C  add     sp, 0Ah
0006AA0F  call    flag2224a_set
0006AA14  push    ds
0006AA15  push    0A36Bh
0006AA18  push    0
0006AA1A  push    2
0006AA1C  push    4
0006AA1E  call    op_dispatch_far_entry
0006AA23  add     sp, 0Ah
0006AA26  mov     [bp+var_2], ax
0006AA29  push    [bp+var_4]
0006AA2C  push    [bp+var_6]
0006AA2F  push    si
0006AA30  push    [bp+var_2]
0006AA33  push    0Ch
0006AA35  call    op_dispatch_far_entry
0006AA3A  add     sp, 0Ah
0006AA3D  push    ss
0006AA3E  lea     ax, [bp+var_2]
0006AA41  push    ax
0006AA42  push    0
0006AA44  push    [bp+var_2]
0006AA47  push    8
0006AA49  call    op_dispatch_far_entry
0006AA4E  add     sp, 0Ah
0006AA51  call    flag2224a_clear
0006AA56  mov     ax, 602Eh
0006AA59  mov     es, ax
0006AA5B  push    word ptr es:current_menu_slot_ptr+2
0006AA60  push    word ptr es:current_menu_slot_ptr
0006AA65  push    di
0006AA66  call    int_to_string_converter
0006AA6B  add     sp, 6
0006AA6E  push    7894h
0006AA71  push    0F32h
0006AA74  mov     ax, 602Eh
0006AA77  mov     es, ax
0006AA79  push    word ptr es:current_menu_slot_ptr+2
0006AA7E  push    word ptr es:current_menu_slot_ptr
0006AA83  mov     ax, 602Eh
0006AA86  mov     es, ax
0006AA88  push    word ptr es:aSSquad+2; ".`SQUAD"
0006AA8D  push    word ptr es:aSSquad; "S-.`SQUAD"
0006AA92  call    string_concatenate
0006AA97  add     sp, 0Ch
0006AA9A  push    7894h
0006AA9D  push    0F32h
0006AAA0  mov     ax, 602Eh
0006AAA3  mov     es, ax
0006AAA5  push    word ptr es:aWar+1; ".`.WAR"
0006AAAA  push    word ptr es:byte_1513B8
0006AAAF  push    7894h
0006AAB2  push    0F32h
0006AAB5  call    string_concatenate
0006AABA  add     sp, 0Ch
0006AABD  push    7894h
0006AAC0  push    0F32h
0006AAC3  push    0
0006AAC5  push    2
0006AAC7  push    6
0006AAC9  call    op_dispatch_far_entry
0006AACE  add     sp, 0Ah
0006AAD1  mov     [bp+var_2], ax
0006AAD4  cmp     ax, 0FFFFh
0006AAD7  jz      short loc_6AB46
0006AAD9  push    [bp+var_4]
0006AADC  push    [bp+var_6]
0006AADF  push    0FFFFh
0006AAE1  push    [bp+var_2]
0006AAE4  push    0Ah
0006AAE6  call    op_dispatch_far_entry
0006AAEB  add     sp, 0Ah
0006AAEE  mov     si, ax
0006AAF0  push    ss
0006AAF1  lea     ax, [bp+var_2]
0006AAF4  push    ax
0006AAF5  push    0
0006AAF7  push    [bp+var_2]
0006AAFA  push    8
0006AAFC  call    op_dispatch_far_entry
0006AB01  add     sp, 0Ah
0006AB04  call    flag2224a_set
0006AB09  push    ds
0006AB0A  push    0A376h
0006AB0D  push    0
0006AB0F  push    0
0006AB11  push    4
0006AB13  call    op_dispatch_far_entry
0006AB18  add     sp, 0Ah
0006AB1B  mov     [bp+var_2], ax
0006AB1E  push    [bp+var_4]
0006AB21  push    [bp+var_6]
0006AB24  push    si
0006AB25  push    [bp+var_2]
0006AB28  push    0Ch
0006AB2A  call    op_dispatch_far_entry
0006AB2F  add     sp, 0Ah
0006AB32  push    ss
0006AB33  lea     ax, [bp+var_2]
0006AB36  push    ax
0006AB37  push    0
0006AB39  push    [bp+var_2]
0006AB3C  push    8
0006AB3E  call    op_dispatch_far_entry
0006AB43  add     sp, 0Ah
0006AB46  call    flag2224a_clear
0006AB4B  mov     ax, 602Eh
0006AB4E  mov     es, ax
0006AB50  push    word ptr es:current_menu_slot_ptr+2
0006AB55  push    word ptr es:current_menu_slot_ptr
0006AB5A  push    di
0006AB5B  call    int_to_string_converter
0006AB60  add     sp, 6
0006AB63  push    7894h
0006AB66  push    0F32h
0006AB69  mov     ax, 602Eh
0006AB6C  mov     es, ax
0006AB6E  dd 0FE36FF26h
0006AB72  adc     sp, ds:36FFh
0006AB76  cld
0006AB77  adc     di, [bx+si+602Eh]
0006AB7B  mov     es, ax
0006AB7D  push    word ptr es:aSSquad+2; ".`SQUAD"
0006AB82  push    word ptr es:aSSquad; "S-.`SQUAD"
0006AB87  call    string_concatenate
0006AB8C  add     sp, 0Ch
0006AB8F  push    7894h
0006AB92  push    0F32h
0006AB95  mov     ax, 602Eh
0006AB98  mov     es, ax
0006AB9A  push    word ptr es:a7Shp+2; ".`.SHP"
0006AB9F  push    word ptr es:a7Shp; "7..`.SHP"
0006ABA4  push    7894h
0006ABA7  push    0F32h
0006ABAA  call    string_concatenate
0006ABAF  add     sp, 0Ch
0006ABB2  push    7894h
0006ABB5  push    0F32h
0006ABB8  push    0
0006ABBA  push    2
0006ABBC  push    6
0006ABBE  call    op_dispatch_far_entry
0006ABC3  add     sp, 0Ah
0006ABC6  mov     [bp+var_2], ax
0006ABC9  cmp     ax, 0FFFFh
0006ABCC  jz      short loc_6AC3B
0006ABCE  push    [bp+var_4]
0006ABD1  push    [bp+var_6]
0006ABD4  push    0FFFFh
0006ABD6  push    [bp+var_2]
0006ABD9  push    0Ah
0006ABDC  fsubr   dword ptr ds:1F6Ch
0006ABE0  add     sp, 0Ah
0006ABE3  mov     si, ax
0006ABE5  push    ss
0006ABE6  lea     ax, [bp+var_2]
0006ABE9  push    ax
0006ABEA  push    0
0006ABEC  push    [bp+var_2]
0006ABF0  or      [bp+si+arg_2ED2], bl
0006ABF4  insb
0006ABF5  pop     ds
0006ABF6  add     sp, 0Ah
0006ABF9  call    flag2224a_set
0006ABFE  push    ds
0006ABFF  push    0A381h
0006AC02  push    0
0006AC04  push    0
0006AC06  push    4
0006AC08  call    op_dispatch_far_entry
0006AC0D  add     sp, 0Ah
0006AC10  mov     [bp+var_2], ax
0006AC13  push    [bp+var_4]
0006AC16  push    [bp+var_6]
0006AC19  push    si
0006AC1A  push    [bp+var_2]
0006AC1D  push    0Ch
0006AC1F  call    op_dispatch_far_entry
0006AC24  add     sp, 0Ah
0006AC27  push    ss
0006AC28  lea     ax, [bp+var_2]
0006AC2B  push    ax
0006AC2C  push    0
0006AC2E  push    [bp+var_2]
0006AC31  push    8
0006AC33  call    op_dispatch_far_entry
0006AC38  add     sp, 0Ah
0006AC3B  call    flag2224a_clear
0006AC40  mov     ax, 602Eh
0006AC43  mov     es, ax
0006AC45  push    word ptr es:current_menu_slot_ptr+2
0006AC4A  push    word ptr es:current_menu_slot_ptr
0006AC4F  push    di
0006AC50  call    int_to_string_converter
0006AC55  add     sp, 6
0006AC58  push    7894h
0006AC5B  push    0F32h
0006AC5E  mov     ax, 602Eh
0006AC61  mov     es, ax
0006AC63  push    word ptr es:current_menu_slot_ptr+2
0006AC68  push    word ptr es:current_menu_slot_ptr
0006AC6D  mov     ax, 602Eh
0006AC70  mov     es, ax
0006AC72  push    word ptr es:aSSquad+2; ".`SQUAD"
0006AC77  push    word ptr es:aSSquad; "S-.`SQUAD"
0006AC7C  call    string_concatenate
0006AC81  add     sp, 0Ch
0006AC84  push    7894h
0006AC87  push    0F32h
0006AC8A  mov     ax, 602Eh
0006AC8D  mov     es, ax
0006AC8F  push    word ptr es:aTsk+2; ".`.TSK"
0006AC94  push    word ptr es:aTsk; "...`.TSK"
0006AC99  push    7894h
0006AC9C  push    0F32h
0006AC9F  call    string_concatenate
0006ACA4  add     sp, 0Ch
0006ACA7  push    7894h
0006ACAA  push    0F32h
0006ACAD  push    0
0006ACAF  push    2
0006ACB1  push    6
0006ACB3  call    op_dispatch_far_entry
0006ACB8  add     sp, 0Ah
0006ACBB  mov     [bp+var_2], ax
0006ACBE  cmp     ax, 0FFFFh
0006ACC1  jz      short loc_6AD30
0006ACC3  push    [bp+var_4]
0006ACC6  push    [bp+var_6]
0006ACC9  push    0FFFFh
0006ACCB  push    [bp+var_2]
0006ACCE  push    0Ah
0006ACD0  call    op_dispatch_far_entry
0006ACD5  add     sp, 0Ah
0006ACD8  mov     si, ax
0006ACDA  push    ss
0006ACDB  lea     ax, [bp+var_2]
0006ACDE  push    ax
0006ACDF  push    0
0006ACE1  push    [bp+var_2]
0006ACE4  push    8
0006ACE6  call    op_dispatch_far_entry
0006ACEB  add     sp, 0Ah
0006ACEE  call    flag2224a_set
0006ACF3  push    ds
0006ACF4  push    0A38Ch
0006ACF7  push    0
0006ACF9  push    0
0006ACFB  push    4
0006ACFD  call    op_dispatch_far_entry
0006AD02  add     sp, 0Ah
0006AD05  mov     [bp+var_2], ax
0006AD08  push    [bp+var_4]
0006AD0B  push    [bp+var_6]
0006AD0E  push    si
0006AD0F  push    [bp+var_2]
0006AD12  push    0Ch
0006AD14  call    op_dispatch_far_entry
0006AD19  add     sp, 0Ah
0006AD1C  push    ss
0006AD1D  lea     ax, [bp+var_2]
0006AD20  push    ax
0006AD21  push    0
0006AD23  push    [bp+var_2]
0006AD26  push    8
0006AD28  call    op_dispatch_far_entry
0006AD2D  add     sp, 0Ah
0006AD30  call    flag2224a_clear
0006AD35  mov     ax, 602Eh
0006AD38  mov     es, ax
0006AD3A  push    word ptr es:current_menu_slot_ptr+2
0006AD3F  push    word ptr es:current_menu_slot_ptr
0006AD44  push    di
0006AD45  call    int_to_string_converter
0006AD4A  add     sp, 6
0006AD4D  push    7894h
0006AD50  push    0F32h
0006AD53  mov     ax, 602Eh
0006AD56  mov     es, ax
0006AD58  push    word ptr es:current_menu_slot_ptr+2
0006AD5D  push    word ptr es:current_menu_slot_ptr
0006AD62  mov     ax, 602Eh
0006AD65  mov     es, ax
0006AD67  push    word ptr es:aSSquad+2; ".`SQUAD"
0006AD6C  push    word ptr es:aSSquad; "S-.`SQUAD"
0006AD71  call    string_concatenate
0006AD76  add     sp, 0Ch
0006AD79  push    7894h
0006AD7C  push    0F32h
0006AD7F  mov     ax, 602Eh
0006AD82  mov     es, ax
0006AD84  push    word ptr es:aVTrg+2; ".`.TRG"
0006AD89  push    word ptr es:aVTrg; "v..`.TRG"
0006AD8E  push    7894h
0006AD91  push    0F32h
0006AD94  call    string_concatenate
0006AD99  add     sp, 0Ch
0006AD9C  push    7894h
0006AD9F  push    0F32h
0006ADA2  push    0
0006ADA4  push    2
0006ADA6  push    6
0006ADA8  call    op_dispatch_far_entry
0006ADAD  add     sp, 0Ah
0006ADB0  mov     [bp+var_2], ax
0006ADB3  cmp     ax, 0FFFFh
0006ADB6  jz      short loc_6AE25
0006ADB8  push    [bp+var_4]
0006ADBB  push    [bp+var_6]
0006ADBE  push    0FFFFh
0006ADC0  push    [bp+var_2]
0006ADC3  push    0Ah
0006ADC5  call    op_dispatch_far_entry
0006ADCA  add     sp, 0Ah
0006ADCD  mov     si, ax
0006ADCF  push    ss
0006ADD0  lea     ax, [bp+var_2]
0006ADD3  push    ax
0006ADD4  push    0
0006ADD6  push    [bp+var_2]
0006ADD9  push    8
0006ADDB  call    op_dispatch_far_entry
0006ADE0  add     sp, 0Ah
0006ADE3  call    flag2224a_set
0006ADE8  push    ds
0006ADE9  push    0A397h
0006ADEC  push    0
0006ADEE  push    0
0006ADF0  push    4
0006ADF2  call    op_dispatch_far_entry
0006ADF7  add     sp, 0Ah
0006ADFA  mov     [bp+var_2], ax
0006ADFD  push    [bp+var_4]
0006AE00  push    [bp+var_6]
0006AE03  push    si
0006AE04  push    [bp+var_2]
0006AE07  push    0Ch
0006AE09  call    op_dispatch_far_entry
0006AE0E  add     sp, 0Ah
0006AE11  push    ss
0006AE12  lea     ax, [bp+var_2]
0006AE15  push    ax
0006AE16  push    0
0006AE18  push    [bp+var_2]
0006AE1B  push    8
0006AE1D  call    op_dispatch_far_entry
0006AE22  add     sp, 0Ah
0006AE25  call    flag2224a_set
0006AE2A  mov     ax, 4FC2h
0006AE2D  mov     es, ax
0006AE2F  mov     ax, es:word_13E012
0006AE33  mov     dx, 7894h
0006AE36  mov     es, dx
0006AE38  mov     es:word_7A2B6, ax
0006AE3E  dec     di
0006AE3F  mov     es, ax
0006AE41  mov     word ptr es:132h, 6
0006AE48  mov     es, ax
0006AE4A  push    word ptr es:132h
0006AE4F  call    ui_font_config_apply
0006AE54  pop     cx
0006AE55  pop     di
0006AE56  pop     si
0006AE57  leave
0006AE58  retf
