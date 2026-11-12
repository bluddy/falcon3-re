# Level-2 Non-Wrapper Functions Decode

## sub_256A3 (0x256A3, 15B, dyn=10222, highest Level-2 non-wrapper)

**Bytecode (15 bytes):**
```
1ebf0e7b8edfbf87420ee82bb51fcb
```

**Manual decode:**
```asm
1e                push ds
bf 0e 7b          mov di, 0x7B0E                  ; load segment number
8e df             mov ds, di                      ; DS = 0x7B0E
bf 87 42          mov di, 0x4287                  ; load offset
0e                push cs
e8 2b b5          call +0xB52B                    ; near call (offset relative to current IP)
1f                pop ds
cb                retf
```

**Analysis:**
- Set DS to segment 0x7B0E (indexed table segment - seen in Level-0 findings)
- Load DI = 0x4287 (offset into 7B0E segment)
- Near call to function at +0xB52B offset
- Restore DS and return
- Very high call frequency (10,222 calls) suggests critical table access
- 0x7B0E segment used extensively in Level-0 (indexed dispatch tables)

**Name:** `ds_7b0e_table_access_4287` or `indexed_table_dispatch_7b0e_4287`
**Category:** Table accessor/dispatcher (very hot path)

---

## sub_2501A (0x2501A, 109B, dyn=488)

**Bytecode (109 bytes):**
```
2e87068457502bc02ea2615757068cc88ec0bf6d57b90500f3a5a4075fb001b90b00be6d572e8a240ae47507040846e2f4eb24b28084e274152ec6066157ff505351525657e862fe5f5e5a595b58fec0d0ea73e146e2ce2e803e6157007407f8582ea38457cbf9582ea38457cb
```

**Manual decode:**
```asm
2e 87 06 84 57       xchg ax, cs:[0x5784]           ; swap AX with cs:[0x5784]
50                   push ax
2b c0                sub ax, ax                     ; AX = 0
2e a2 61 57          mov cs:[0x5761], al            ; cs:[0x5761] = 0
57                   push di
06                   push es
8c c8                mov ax, cs
8e c0                mov es, ax                     ; ES = CS
bf 6d 57             mov di, 0x576D                 ; DI = 0x576D (CS-segment offset)
b9 05 00             mov cx, 0x0005                 ; CX = 5
f3 a5                rep movsw                      ; copy 5 words from DS:SI to ES:DI
a4                   movsb                          ; copy 1 byte
07                   pop es
5f                   pop di
b0 01                mov al, 0x01
b9 0b 00             mov cx, 0x000B                 ; CX = 11
be 6d 57             mov si, 0x576D                 ; SI = 0x576D (CS-segment offset)
2e 8a 24             mov ah, cs:[si]                ; AH = cs:[SI]
0a e4                or ah, ah                      ; test AH
75 07                jnz +0x07                      ; if non-zero, skip
04 08                add al, 0x08                   ; AL += 8
46                   inc si
e2 f4                loop -0x0C                     ; loop back (11 iterations)
eb 24                jmp +0x24                      ; skip to end
b2 80                mov dl, 0x80                   ; DL = 0x80
84 e2                test dl, ah                    ; test DL & AH
74 15                jz +0x15                       ; if zero
2e c6 06 61 57 ff    mov byte ptr cs:[0x5761], 0xFF ; cs:[0x5761] = 0xFF
50                   push ax
53                   push bx
51                   push cx
52                   push dx
56                   push si
57                   push di
e8 62 fe             call -0x019E                   ; near call
5f                   pop di
5e                   pop si
5a                   pop dx
59                   pop cx
5b                   pop bx
58                   pop ax
fe c0                inc al                         ; AL++
d0 ea                shr dl, 1                      ; DL >>= 1
73 e1                jnc -0x1F                      ; loop if CF=0
46                   inc si
e2 ce                loop -0x32                     ; outer loop
2e 80 3e 61 57 00    cmp byte ptr cs:[0x5761], 0x00 ; check cs:[0x5761]
74 07                jz +0x07                       ; if zero
f8                   clc                            ; clear carry
58                   pop ax
2e a3 84 57          mov cs:[0x5784], ax            ; restore cs:[0x5784]
cb                   retf
f9                   stc                            ; set carry
58                   pop ax
2e a3 84 57          mov cs:[0x5784], ax            ; restore cs:[0x5784]
cb                   retf
```

**Analysis:**
- Saves and swaps cs:[0x5784] with AX
- Clears cs:[0x5761] flag
- Copies 11 bytes (5 words + 1 byte) from DS:SI to CS:0x576D
- Iterates through the copied data:
  - Scans 11 bytes looking for non-zero bits
  - For each set bit, calls a function and increments an index
  - Sets cs:[0x5761] = 0xFF if any bit processed
- Returns with CF set/clear based on whether cs:[0x5761] was set
- Pattern: bit-scan and dispatch loop over a data structure

**Name:** `cs_bitscan_dispatch_576d` or `cs_bitfield_iterate_call`
**Category:** Bitfield scanner with callback dispatch

---

## sub_276B4 (0x276B4, 13B, dyn=194)

**Bytecode (13 bytes):**
```
558bec8b5e060ee80300905dcb
```

**Manual decode:**
```asm
55                push bp
8b ec             mov bp, sp                      ; stack frame setup
8b 5e 06          mov bx, [bp+6]                  ; load arg0 into BX
0e                push cs
e8 03 00          call +0x0003                    ; near call to next function
90                nop
5d                pop bp
cb                retf
```

**Analysis:**
- Standard stack frame prologue
- Load first argument ([bp+6]) into BX
- Near call to function at offset +3 (very close, likely nearby function)
- NOP padding
- Clean up and return
- Pattern: thin wrapper passing one argument to a near function

**Name:** `arg_forward_wrapper` or `near_call_arg_bx`
**Category:** Simple argument-forwarding wrapper

**Note:** This is so thin (13B) it's almost a stub. The real logic is in the called function at +0x0003.

---

## sub_100C1 (0x100C1, 71B, dyn=8)

**Bytecode (71 bytes):**
```
9af2616c1f2ea000002ea201000ac0741ab80300cd33f7c3030075f5b84001bb64000ee82bffb80b00cd33cb2e803e00000074122e80360100ff740ab84001bb64000ee80bffcb
```

**Manual decode:**
```asm
9a f2 61 6c 1f       call far 1F6C:61F2              ; overlay call
2e a0 00 00          mov al, cs:[0x0000]             ; read CS-segment byte
2e a2 01 00          mov cs:[0x0001], al             ; copy to cs:[0x0001]
0a c0                or al, al                       ; test AL
74 1a                jz +0x1A                        ; if zero, skip
b8 03 00             mov ax, 0x0003
cd 33                int 0x33                        ; mouse interrupt (function 3)
f7 c3 03 00          test bx, 0x0003                 ; test BX & 3
75 f5                jnz -0x0B                       ; loop if non-zero
b8 40 01             mov ax, 0x0140                  ; AX = 320
bb 64 00             mov bx, 0x0064                  ; BX = 100
0e                   push cs
e8 2b ff             call -0x00D5                    ; near call
b8 0b 00             mov ax, 0x000B
cd 33                int 0x33                        ; mouse interrupt (function 11)
cb                   retf
; --- Following code ---
2e 80 3e 00 00 00    cmp byte ptr cs:[0x0000], 0x00  ; check cs:[0x0000]
74 12                jz +0x12                        ; if zero
2e 80 36 01 00 ff    xor byte ptr cs:[0x0001], 0xFF  ; flip cs:[0x0001]
74 0a                jz +0x0A                        ; if zero after flip
b8 40 01             mov ax, 0x0140                  ; AX = 320
bb 64 00             mov bx, 0x0064                  ; BX = 100
0e                   push cs
e8 0b ff             call -0x00F5                    ; near call
cb                   retf
```

**Analysis:**
- Call overlay 1F6C:61F2
- Copy cs:[0x0000] to cs:[0x0001] and test
- If non-zero:
  - INT 33h AX=3 (get mouse position and button status)
  - Loop while BX & 3 != 0 (wait for mouse buttons released)
  - Call near function with AX=320, BX=100
  - INT 33h AX=11 (read mouse motion counters)
- Second section (may be unreachable or alternate path):
  - Flip cs:[0x0001] bit
  - Call near function with AX=320, BX=100

**Pattern:** Mouse input handler with polling loop

**Name:** `mouse_poll_wait_button_release` or `mouse_input_handler_int33`
**Category:** Input handler (mouse via INT 33h)

---

## Summary of 4 Level-2 Non-Wrappers

**Ready to name:**

1. **sub_256A3** → `indexed_table_dispatch_7b0e_4287` (15B, 10222 calls)
   - DS=7B0E segment table access at offset 0x4287
   - **Highest call frequency** of any Level-2 non-wrapper

2. **sub_2501A** → `cs_bitscan_dispatch_576d` (109B, 488 calls)
   - Bitfield scanner iterating over CS:0x576D (11 bytes)
   - Calls function for each set bit
   - Returns CF based on processing flag cs:[0x5761]

3. **sub_276B4** → `arg_forward_wrapper_near` (13B, 194 calls)
   - Thin wrapper: loads [bp+6] into BX, calls near function
   - Almost a stub

4. **sub_100C1** → `mouse_poll_wait_release_int33` (71B, 8 calls)
   - Mouse input handler using INT 33h
   - Polls mouse position (AX=3) until buttons released (BX&3==0)
   - Reads motion counters (AX=11)

**Total named:** 6 Level-1 + 4 Level-2 = **10 of 11 non-wrapper functions**

**Remaining:** sub_254DC (Level-1, 29B, 977 calls) - deferred as potential boundary error

