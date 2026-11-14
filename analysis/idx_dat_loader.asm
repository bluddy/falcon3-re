; idx_dat_loader - Loads .IDX and .DAT file pairs
; Original name: sub_1297F0
; Address: 0x1297f0 - 0x1298ab
; Size: 187 bytes
;
; This is the template function for ALL .IDX/.DAT file loading
; References:
;   0x14e771: ".`PICFONT.IDX" at 0x129809
;   0x14e781: ".`PICFONT.DAT" at 0x12985b
;

idx_dat_loader proc near

  001297F0  enter   2, 0
  001297F4  mov     ax, 7894h
  001297F7  mov     es, ax
  001297F9  cmp     es:word_78940, 0
  001297FF  jnz     short loc_129804
  00129801  jmp     locret_1298A9
  00129804  mov     ax, 602Eh
  00129807  mov     es, ax
  00129809  push    word ptr es:aPicfontIdx; ".`PICFONT.IDX"
  0012980E  push    es:word_14E76F
  00129813  push    0
  00129815  push    0
  00129817  push    6
  00129819  call    op_dispatch_far_entry
  0012981E  add     sp, 0Ah
  00129821  mov     [bp+var_2], ax
  00129824  mov     ax, 602Eh
  00129827  mov     es, ax
  00129829  push    word ptr es:dword_14E78F+2
  0012982E  push    word ptr es:dword_14E78F
  00129833  push    1Ch
  00129835  push    [bp+var_2]
  00129838  push    0Ah
  0012983A  call    op_dispatch_far_entry
  0012983F  add     sp, 0Ah
  00129842  push    ss
  00129843  lea     ax, [bp+var_2]
  00129846  push    ax
  00129847  push    0
  00129849  push    [bp+var_2]
  0012984C  push    8
  0012984E  call    op_dispatch_far_entry
  00129853  add     sp, 0Ah
  00129856  mov     ax, 602Eh
  00129859  mov     es, ax
  0012985B  push    word ptr es:aPicfontDat; ".`PICFONT.DAT"
  00129860  push    es:word_14E77F
  00129865  push    0
  00129867  push    0
  00129869  push    6
  0012986B  call    op_dispatch_far_entry
  00129870  add     sp, 0Ah
  00129873  mov     [bp+var_2], ax
  00129876  mov     ax, 602Eh
  00129879  mov     es, ax
  0012987B  push    es:word_14E7B1
  00129880  push    es:word_14E7AF
  00129885  push    1ABh
  00129888  push    [bp+var_2]
  0012988B  push    0Ah
  0012988D  call    op_dispatch_far_entry
  00129892  add     sp, 0Ah
  00129895  push    ss
  00129896  lea     ax, [bp+var_2]
  00129899  push    ax
  0012989A  push    0
  0012989C  push    [bp+var_2]
  0012989F  push    8
  001298A1  call    op_dispatch_far_entry
  001298A6  add     sp, 0Ah
  001298A9  leave
  001298AA  retf

idx_dat_loader endp

; Total: 62 instructions
