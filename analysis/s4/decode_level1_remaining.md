# Level-1 Remaining Non-Wrapper Functions Decode

## sub_11A7D (0x11A7D, 106B, dyn=5, in=3, out=6)

**Bytecode (106 bytes):**
```
2ec6062000052ec6062100062ec606220007e352062e890e1a002e89361800509ae4556c1f589a37566c1fbb02009a4d566c1f8ec28bd82e8b0e1a002e8b361800e864002ea31c002e89161e0053e8d0fd5b2e8b0e1a002e8b361800e80b009a05566c1f07cbe8b8fdcb
```

**Manual decode:**
```asm
2e c6 06 20 00 05      mov byte ptr cs:[0x0020], 0x05
2e c6 06 21 00 06      mov byte ptr cs:[0x0021], 0x06
2e c6 06 22 00 07      mov byte ptr cs:[0x0022], 0x07
e3 52                  jcxz +0x52                      ; if CX=0, skip to end
06                     push es
2e 89 0e 1a 00         mov cs:[0x001A], cx             ; save CX
2e 89 36 18 00         mov cs:[0x0018], si             ; save SI
50                     push ax
9a e4 55 6c 1f         call far 1F6C:55E4              ; far call
58                     pop ax
9a 37 56 6c 1f         call far 1F6C:5637              ; far call
bb 02 00               mov bx, 0x0002
9a 4d 56 6c 1f         call far 1F6C:564D              ; far call
8e c2                  mov es, dx
8b d8                  mov bx, ax
2e 8b 0e 1a 00         mov cx, cs:[0x001A]             ; restore CX
2e 8b 36 18 00         mov si, cs:[0x0018]             ; restore SI
e8 64 00               call +0x0064                    ; near call
2e a3 1c 00            mov cs:[0x001C], ax             ; save AX result
2e 89 16 1e 00         mov cs:[0x001E], dx             ; save DX result
53                     push bx
e8 d0 fd               call -0x0230                    ; near call (sub_1085B)
5b                     pop bx
2e 8b 0e 1a 00         mov cx, cs:[0x001A]             ; restore CX again
2e 8b 36 18 00         mov si, cs:[0x0018]             ; restore SI again
e8 0b 00               call +0x000B                    ; near call
9a 05 56 6c 1f         call far 1F6C:5605              ; far call
07                     pop es
cb                     retf
e8 b8 fd               call -0x0248                    ; near call (sub_1083E)
cb                     retf
```

**Analysis:**
- Initialize CS:[0x0020-0x0022] with 5, 6, 7
- Early exit if CX=0 (jcxz)
- Save CX, SI, ES to CS-segment (0x0018-0x001A)
- Four far calls to overlay 1F6C (55E4, 5637, 564D, 5605)
- Two near calls (offsets -0x0230, +0x0064, +0x000B)
- Save results to CS:[0x001C], CS:[0x001E]
- Complex initialization with multiple subsystem calls

**Name:** `cs_state_init_overlay_1f6c_multi` (tentative)
**Category:** Complex initialization with CS-segment state setup

---

## sub_10DA7 (0x10DA7, 31B, dyn=4, in=2, out=2)

**Bytecode (31 bytes):**
```
5556579a875b6c1f9a6c0100100ac075f75f5e5dcbb448bbffffcd218bc3cb
```

**Manual decode:**
```asm
55                     push bp
56                     push si
57                     push di
9a 87 5b 6c 1f         call far 1F6C:5B87              ; far call (overlay)
9a 6c 01 00 10         call far 1000:016C              ; far call (overlay)
0a c0                  or al, al                        ; test AL
75 f7                  jnz -0x09                       ; loop back if non-zero
5f                     pop di
5e                     pop si
5d                     pop bp
cb                     retf
; --- unreachable code after retf? ---
b4 48                  mov ah, 0x48                    ; AH=48h (allocate memory)
bb ff ff               mov bx, 0xFFFF                  ; BX=FFFFh (max paragraphs)
cd 21                  int 0x21                        ; DOS INT 21h
8b c3                  mov ax, bx                      ; move result to AX
cb                     retf
```

**Analysis:**
- Save BP, SI, DI
- Call overlay 1F6C:5B87
- Loop: call 1000:016C, test AL, repeat if non-zero
- Restore registers and return
- **Unreachable code after retf:** DOS memory allocation (AH=48h, INT 21h)

**Pattern:** Polling loop waiting for overlay function to return AL=0

**Name:** `overlay_poll_loop_1000_016c` or `overlay_wait_until_ready`
**Category:** Polling/wait function with overlay calls

**Note:** The DOS memory allocation code after the retf is unreachable (dead code or analysis error?). The function effectively loops calling 1000:016C until AL=0.

---

## Summary of 7 Level-1 Non-Wrappers

**Ready to name:**

1. **sub_2241E** → `overlay_1110_conditional_dual_call` (24B, 9210 calls)
   - Conditional two-stage overlay call with flag result

2. **sub_2318C** → `cs_word_3662_add_call_store` (13B, 93 calls)
   - CS:[0x3662] read-modify-write via sub_24980

3. **sub_23199** → `cs_word_3664_add_call_store` (13B, 22 calls)
   - CS:[0x3664] read-modify-write via sub_24988

4. **sub_122AE** → `subsystem_init_multi_call` (114B, 17 calls)
   - Complex initialization (needs deeper analysis for better name)

5. **sub_11A7D** → `cs_state_init_overlay_1f6c_multi` (106B, 5 calls)
   - CS-segment state setup with 4 overlay 1F6C calls

6. **sub_10DA7** → `overlay_poll_loop_1000_016c` (31B, 4 calls)
   - Polling loop waiting for overlay function

**Deferred (boundary issue):**

7. **sub_254DC** (29B, 977 calls) - appears to be 2 functions merged
   - First 6B: dispatch stub via CS:[0x2A9C]
   - Following 23B: stack frame wrapper
   - Need to investigate if this is a boundary error

