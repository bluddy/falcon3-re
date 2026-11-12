# Hardware & OS Interface

---

## Timer (IRQ0): timer_tick_isr (0x22AFF, 57B)

DOS IRQ0 fires at ~18.2 Hz (PIT channel 0, default rate). The ISR runs asynchronously
to the game loop.

### Operation

```
push ax
IF cs:byte_2224B == 1:         ; timer_gate_flag set (ISR gated off)
    skip tick_counter increment
ELSE:
    cs:word_22220++             ; tick_counter (gated)
cs:word_22222++                 ; timer_divider (always)
IF cs:word_22222 & 3 == 0:     ; every 4th tick
    pop ax
    jmp loc_22B27              ; chain to BIOS timer (or joystick path)
ELSE:
    OUT 0x20, 0x20              ; send EOI to PIC
    pop ax
    iret
```

After every 4th tick, additional logic:
```
IF cs:byte_22246 == 0:         ; joystick_timer_flag clear
    jmp to joystick_gate_counter+1  ; joystick polling path
```

### Timer Globals

| CS address | Name | Description |
|---|---|---|
| `cs:byte_2224B` | `timer_gate_flag` | 1 = suppress tick_counter increment |
| `cs:word_22220` | `tick_counter` | Gated; increments each IRQ0 when gate=0 |
| `cs:word_22222` | `timer_divider` | Always increments; AND 3 == 0 → BIOS chain |
| `cs:byte_22246` | `joystick_timer_flag` | Enables joystick polling chain |

---

## Mouse: mouse_int33_dispatch (0x1018F, 120B, far)

Registered as INT 33h mouse event callback. 337K dynamic calls — most-called function.

### Entry

```
DS = arg_8 (segment of mouse event record)
SI = arg_2 (offset of mouse event record)
ES = arg_12 (extra segment)

AX = [SI+0]  ; event type
BX = [SI+2]  ; button state
CX = [SI+4]  ; X delta
...
```

### Event Type Dispatch

Checks `AX` against: 9, 0xC, 0x10, 0x14, 0x16, 0x17, 0x18, 0x19, 0x1F, 0x20, 0x21.
If matched: special path for those event types (position, button changes).
If not matched: reads [SI+2] = BX (button mask), [SI+4] = CX (delta).

INT 33h event codes that trigger the callback:
- 1 = cursor moved
- 2 = left button pressed
- 4 = left button released
- 8 = right button pressed
- 0x10 = right button released
- etc.

The specific codes 9, 0xC, 0x10, 0x14, 0x16-0x21 are probably composite event masks
for Falcon's custom mouse handling.

---

## Mouse Buttons: mouse_buttons_get (0x1016C, 35B, far)

Returns current mouse/joystick button state as 3-bit mask in AX.

```
IF cs:byte_10000 != 0:         ; INT 33h driver present
    INT 33h, AX=3              ; get position and button status
    return BX & 7              ; bits 0-2 = L/R/M buttons
ELSE:                          ; keyboard/joystick fallback
    AL = input_status_pack()   ; read joystick button latch
    return (~AL & 0xF0) >> 4  ; inverted upper nibble → 4 buttons
```

---

## Keyboard

### BDA Keyboard Flags: bda_kb_flag_get (0x24E5D, 17B, far)

Reads BIOS Data Area keyboard status byte at `0x0000:0x0417`.

```
ES = 0
BX = 0x417
AL = ES:[BX]        ; keyboard flags byte 1
AH = 0
retf
```

**BDA 0x417 bit layout** (PROVEN):
| Bit | Meaning |
|---|---|
| 7 | Insert mode active |
| 6 | CapsLock active |
| 5 | NumLock active |
| 4 | ScrollLock active |
| 3 | Alt pressed |
| 2 | Ctrl pressed |
| 1 | Left Shift pressed |
| 0 | Right Shift pressed |

Previously misnamed `bda_equipment_flag_get` — PROVEN correction: 0x417 is keyboard
flags, NOT equipment flags (which are at 0x410-0x411).

### Input Event Bitmap: flag_bits_dispatch (0x24FB9, 97B)

CS:0x5762 = 11-byte input event bitmap (88 events total).
`flag_block_merge_zero_5c63` merges/clears the bitmap.
`key_event_table_dispatch` handles each active event.

Called TWICE per flight frame with different BX/DI selector args:
- Pass 1: BX=0x135, DI=0x141
- Pass 2: BX=0x148, DI=0x176

Also called from `game_config_apply_init`.

---

## Joystick

### joystick_poll (0x1122A, 111B, far)

```
IF cs:byte_11171 == 0: return  ; joystick not configured
IF cs:byte_11175 == 0:         ; poll mode flag
    goto simpler path
IF cs:word_11176 != 0:         ; AT joystick flag
    INT 15h AH=0x84, DX=0      ; read joystick positions (AT mode)
ELSE:
    IN al, 0x201               ; read game I/O port (PC mode)
```

Counts high bits over 8 iterations (`not ax; and ax, 0xF0; mov dx, 0`) to determine which buttons are pressed. Updates:
- `cs:word_11168` = button state (packed)
- `cs:word_11102` = input status word (used by input_status_pack)

Called from timer ISR every 4th tick when `joystick_timer_flag` is set.

### joystick_axis_read_clamp (called from control_axes_read)

Reads and clamps joystick axis values to ±2048. Used when joystick is configured.
Result packed into BX (aileron), AX (elevator), CX (throttle), DX (rudder).

### input_status_pack (0x112A1, 37B, far)

Packs the joystick button latch into a single byte in AL:
```
AH = 0xF0
XCHG AH, cs:word_11102 (high byte)   ; get current state, set mask
SHL AL, 4                             ; shift low nibble
CL = AH
XCHG AH, cs:word_11102+1             ; get other byte
OR AL, AH                             ; combine
XOR CL, AL; NOT CL                   ; invert difference
OR CL, cs:word_11102+1               ; merge
return AL = CL
```

This packs joystick button state into an 8-bit value. The latch `cs:word_11102`
stores the last-read button state; the pack function creates a "changed/pressed" summary.

---

## OPL: See audio.md

---

## Program Termination: program_terminate (0x2224C, 29B, Level-5)

```
call sbi_int8_shutdown_hook    ; unhook IRQ0 (restore BIOS timer ISR)
...
INT 21h AH=0x4C, AL=0          ; DOS terminate with return code 0
```

Called by error_display_terminate and clean exit path. Unhooks all ISRs before terminating.
