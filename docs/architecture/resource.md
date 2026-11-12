# Resource System — DOS Services & File I/O

*The `op_dispatch` function is the central DOS service shim.*

---

## op_dispatch (0x2257B, 29B)

16-operation DOS services table. Dispatches via:
```asm
and cs:byte_22248, 80h    ; clear status (keep only bit 7)
call cs:op_dispatch_table[bx]  ; table at CS:0x22060; BX = byte offset (not index!)
cmp cs:byte_2224A, 0      ; error flag
jz  no_error
call error_display_terminate
test cs:byte_22248, 7Fh   ; return status
retf
```

**BX is a BYTE OFFSET** (table entries are 2B, so BX=0=entry 0, BX=2=entry 1, BX=4=entry 2...).

### Operation Table (CS:0x22060, seg020 base 0x1F6C0)

| BX | Linear EA | Function | DOS INT 21h | Certainty |
|---|---|---|---|---|
| 0x00 | 0x225F4 | `dos_mem_alloc` | AH=48h: allocate N paragraphs → AX=segment | PROVEN |
| 0x02 | 0x22626 | `dos_mem_free` | AH=49h: free segment AX | PROVEN |
| 0x04 | 0x22699 | `file_create` | AH=3Ch: create file DS:DX → AX=handle | PROVEN |
| 0x06 | 0x226B6 | `file_open` | AH=3Dh: open DS:DX (AX=0/1/2=r/w/rw) → handle | PROVEN |
| 0x08 | 0x226DF | `file_close` | AH=3Eh: close handle AX | PROVEN |
| 0x0A | 0x226E8 | `file_read` | AH=3Fh: read CX bytes into DS:DX → AX=bytes | PROVEN |
| 0x0C | 0x22712 | `file_write` | AH=40h: write CX bytes from DS:DX | PROVEN |
| 0x0E | 0x2273C | `file_lseek` | AH=42h: seek CH=method, CX:DX=offset → DX:AX=pos | PROVEN |
| 0x10 | 0x22760 | `file_find_first` | AH=4Eh: find first DS:DX pattern | PROVEN |
| 0x12 | 0x22797 | `file_find_next` | AH=4Fh: find next → AX=1 found | PROVEN |
| 0x14 | 0x227B4 | `file_get_dta` | AH=2Fh: get DTA addr → DX=seg, AX=off | PROVEN |
| 0x16 | 0x227BF | `mem_copy_fwd` | REP MOVSW+MOVSB: CX bytes DS:SI → ES:DI | PROVEN |
| 0x18 | 0x227C8 | `mem_store_fwd` | REP STOSW+STOSB: AL fill, CX bytes at ES:DI | PROVEN |
| 0x1A | 0x22818 | `dos_print_str` | AH=9: print DS:SI string | PROVEN |
| 0x1C | 0x227D3 | `file_delete` | AH=41h: delete file DS:DX | PROVEN |
| 0x1E | 0x227EC | `file_size` | lseek SEEK_END + SEEK_SET → size in AX:DX | PROVEN |

### Status / Error Globals

| CS address | Description |
|---|---|
| `cs:byte_22248` | Operation status byte (bit 7 preserved; bits 0-6 cleared then set on error) |
| `cs:byte_2224A` | Error flag: nonzero → `error_display_terminate` called |
| `cs:byte_2224B` | Timer gate: set to 1 during file_read (gates IRQ0 tick_counter) |
| `cs:byte_22249` | Error code (set by individual operations on failure) |

---

## op_dispatch Calling Variants

### 1. Direct (register-based)

```
AX = handle or type
BX = op_code (byte offset, see table above)
CX = count or param
DX = buffer offset (near, in DS)
DS = data buffer segment (must be set by caller)
→ call far ptr op_dispatch  (or push cs; call near ptr)
```

### 2. op_dispatch_far_entry (0x22598, 30B) — 54 callers

Far-callable with ALL parameters on stack. DS explicitly passed.
Used heavily by keyboard subsystem (`kb_record_commit`, `kb_record_slots_open`).

```
[bp+6]  = BX (op_code)
[bp+8]  = AX (handle)
[bp+0xA]= CX (count)
[bp+0xC]= DX (buffer offset)
[bp+0xE]= DS (buffer segment) ← explicit DS
```

### 3. op_dispatch_far_wide (0x225B6, 30B)

Far wrapper with different arg order + CH=seek_method override.
Used by `mode_slot_index_build` for double-seek operations.

```
[bp+6]  = BX (op_code)
[bp+8]  = AX (handle_ax → goes to AX)
[bp+0xA]= DX (param_dx)
[bp+0xC]= CX (param_cx)
[bp+0xE]= BX (seek_method) → BL goes to CH
```

---

## Entity Creation File Pattern

`entity_slot_create` (0x2EBCD) loads entity data from disk:

```
1. DS = 0x7075; file_open(BX=6, AX=0, DS:DX=0x4E)  ; open entity file at DS:0x4E
2. Store handle to cs:word_2EA26
3. dos_mem_alloc(BX=0, AX=N)                        ; allocate memory
4. file_read(BX=0xA, CX=4, DX=0x18)                ; read 4B header
5. dos_mem_alloc(BX=2, ...)                         ; second alloc
6. file_read(BX=0xA, CX=entity_size, DX=buf)        ; read entity record
7. file_close(BX=8)
8. Initialize FarObj from loaded data
```

The filename at `DS:0x7075:0x4E` is a 2-character entity type code (e.g. "F4", "SA").

---

## High-Level File Executor: far_op_execute (0x27703, 325B)

Opens a data file, reads 768B (0x300), dispatches to callbacks, closes.

```
cs:byte_25484 = AL (flags)
cs:word_276FF = DS, cs:word_27701 = DX (filename)

file_open(AX=0, BX=6, DS:DX=filename) → cs:word_27476 (handle)
flag2224a_clear
farptr_7b0e_43ba_const → DS:AX = pointer to 0x7B0E:0x43BA
file_read(BX=0xA, CX=0x300, DX=ptr) → 768 bytes into buffer

IF NOT (cs:byte_25484 & 8):
    dispatch_22138_stub(SI=1, BX=9)
    dispatch_22140_stub(cs:word_27472)
ELSE:
    far_cb_1, dispatch_220f0_stub, far_cb_0
    ... more data reads/writes ...

file_close (handle)
```

Callers: `far_op_execute_farptr` (from ui_loadout_menu_enter), `sub_103C99`, `sub_111AF6`.

---

## Streaming Buffer API

Budget-limited file reading via a set of CS globals.

| CS address | Name | Description |
|---|---|---|
| `cs:word_27476` | `file_handle` | Currently open file handle |
| `cs:word_2747A` | `stream_budget` | Bytes remaining to read |
| `cs:word_27480` | `stream_src_offset` | Source pointer offset for copy |
| `cs:word_27482` | `stream_src_seg` | Source pointer segment |
| `cs:word_27488` | `stream_buf_offset` | Data buffer offset |
| `cs:word_2748A` | `stream_buf_seg` | Data buffer segment |
| `cs:word_2747C` | `stream_callback` | Callback/selector word |
| `cs:word_27478` | `stream_param` | Additional parameter |

### buffer_budget_entry_block (0x275D8, 113B)

```
Entry 1 (stack args): count_ptr=[bp+6], data_ptr=[bp+0xA]
  CX = [count_ptr]              ; requested count
  CX = min(CX, cs:word_2747A)   ; clamp to budget
  cs:word_2747A -= CX           ; decrement budget
  IF CX == 0: return 0
  file_read(BX=0xA, CX=CX, DS:DX=data_ptr)   ; read from open file
  return CX (bytes actually read)

Entry 2 (stack args): count_ptr, copy_src_ptr
  Similar but copies DS:word_27480 → ES:DI via REP MOVSW
```

### buffer_callback_api_block (0x274E6, 242B)

Multi-entry method dispatch for buffer state management. 7 entry points, each
operating on a different CS global:
- Entry 1 (0x274E6): [bp+6] → `cs:word_2747C`
- Entry 2 (0x274F2): AX → `cs:word_2747C`
- Entry 3 (0x274F7): DS = `cs:word_27470`, load from `cs:[bx+7E06/7E08h]`, call `sub_2BFB9`
- Entry 4 (0x2752D): [bp+6,8] → `cs:word_2748A/27488` (buffer far ptr)
- Entry 5 (0x27541): DX:AX → `cs:word_2748A/27488`
- Entry 6 (0x2754B): [bp+6] → `cs:word_27478`
- Entry 7 (0x27557+): store from stack

---

## Mode Slot Index Build (mode_slot_index_build, 0x1B8EE, 262B, seg013)

Builds a 128-entry slot index table at `ES:0x7894:0xDDA` from a data file.

```
// Initialize table: all entries = 0xFFFF (empty)
for i = 0..0x7F:
    ES:0x7894:[0xDDA + i×2] = 0xFFFF

// Open data file
op_dispatch_far_entry(BX=6, AX=0, [DS:DX]=filename)  ; file_open
IF AX == 0xFFFF: return 0 (failure)
SI = handle

// Seek to position 2 (SEEK_SET)
op_dispatch_far_wide(BX=0xE, CH=0, CX:DX=2)

// Seek to position 0 (SEEK_SET)
op_dispatch_far_wide(BX=0xE, CH=0, CX:DX=0)

// Read slot index data
op_dispatch_far_entry(BX=0xA, AX=handle, CX=size, DS:DX=buffer)

... (file_close, return 1 on success)
```
