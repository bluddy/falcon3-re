# Audio System

---

## Sound Hardware

### Device Types (from sound_device_init, 0x1740D)

| AX | Mode | Initialization | Certainty |
|---|---|---|---|
| 1 | PC speaker | `always_true` (no-op) | PROVEN |
| **2** | **AdLib/OPL2 at I/O port 0x388** | `adlib_device_init(0x388)` | **PROVEN** |
| 3 | SoundBlaster (auto-detect) | `sbi_port_discover_aa` | STRONG |
| 4 | SBI verify | `sbi_reset_verify` | STRONG |

**OPL base I/O port: 0x388** (AdLib standard, confirmed by direct call).

### Mode Selector

`ds:0xAF90` = SBI mode byte:
- 0 = OPL2/AdLib (channels 0-8)
- nonzero = SoundBlaster (channels 6-9 use different register writes)

Channel limit stored at `ds:0xAE78`.

---

## OPL Register Write: opl_reg_write (0x16F10, 70B, seg006)

Writes one (address, data) pair to the OPL chip with timing delays:

```
Port = [0x7A32:0xAD50]       ; OPL base I/O port (= 0x388, PROVEN)

OUT port, reg_addr            ; write register address
IN  al, port × 6             ; delay ≥ 3.3 µs (OPL address timing)
INC port
OUT port, reg_data            ; write data
IN  al, port × 18            ; delay ≥ 23 µs (OPL data timing)
DEC port
IN  al, port × N              ; more delay
```

The delay loop count is determined by `[0x7A32:0xAD50]` (OPL port number).

---

## Channel System

### Channel Handle Convention

Audio channel handles are **byte offsets** into DS channel data tables.
For channel handle SI:

| Offset | Description | Access |
|---|---|---|
| `[SI - 0x519E]` | Key control register value | OPL 0xB0+N register data |
| `[SI - 0x5186]` | Volume level (0..127 clamped) | Per-channel volume |
| `[SI - 0x517A]` | Active/key-on flag | bit 0x20 = key-on |
| `[SI - 0x66CE]` | SB channel bitmask | (SB mode only) |
| `[SI - 0x5194]` | Note frequency | (note_seq_write path) |

The channel "index" N = SI - base_offset, where base_offset varies by function.
Check `cmp si, ds:0xAE78` to validate the handle (< max_channels).

### Volume Table

- OPL mode: register table at `DS:0x99A7` (2B per entry: OPL reg index + flags)
- SB mode: register table at `DS:0x99B9` (2B per entry)

Accessed as: `ax = si × 2 + 0x99A7_or_B9; les bx, ds:[ax]; al = es:[bx]`

---

## Channel Operations

### channel_release (0x1796C, 91B, seg007)

Silences a channel (key-off):
```
SI = channel_handle (from [bp+arg_0])
IF OPL mode (ds:0xAF90 == 0) AND SI < 9:
    [SI - 0x517A] = 0            ; clear active flag
    [SI - 0x519E] &= ~0x20       ; clear key-on bit
    opl_reg_write(addr=SI+0xB0, data=[SI-0x519E])  ; write OPL B0h+channel
ELIF SB mode AND SI <= 10:
    SB channel N-6 bitmask clear
    channel_mode_reg_write()
```

The OPL register `0xB0+N` = key-on register for channel N:
- bit 5 = key-on (1=playing, 0=released)
- bits 0-4 = octave/block number

### channel_volume_store (0x17835, 102B, seg007)

```
SI = handle; volume = arg_2 (clamped to 127)
[SI - 0x5186] = volume             ; store volume
IF OPL mode:
    ax = si × 2 + 0x99A7           ; OPL mode volume table
ELSE:
    ax = si × 2 + 0x99B9           ; SB mode volume table
les bx, ds:[ax]                    ; load register entry
al = es:[bx]                       ; first OPL register index
channel_reg_write_table(al)        ; write volume to OPL
IF es:[bx+1] != 0xFF:              ; second carrier?
    al = es:[bx+1]
    channel_reg_write_table(al)
```

### channel_note_seq_write (0x178D4, 152B, seg007)

Writes a note (key-on event) to a channel:
```
SI = handle; note = arg_2 - 12 (adjusted, clamped ≥ 0)
IF OPL mode AND SI < 9:
    [SI - 0x5194] = note           ; store note frequency
    [SI - 0x517A] = 0x20           ; set key-on flag
    channel_seq_args_hw(SI)        ; write OPL frequency + key-on registers
ELIF SB mode (ds:0xAF90 != 0):
    Channel-specific SB register writes
    ds:0xAE72 / 0xAE74 = note values for SB channels 6-9
```

---

## Audio Subsystem (seg006-seg007)

The audio code is in a dedicated overlay (seg006/seg007 = R07/sound overlay).

Key functions:

| Function | EA | Description |
|---|---|---|
| `sound_device_init` | 0x1740D | Initialize sound hardware by type code |
| `adlib_device_init` | — | Initialize AdLib at port 0x388 |
| `opl_reg_write` | 0x16F10 | Write OPL register (address + data) with delays |
| `channel_release` | 0x1796C | Silence a channel (key-off + clear flags) |
| `channel_volume_store` | 0x17835 | Set channel volume via register table |
| `channel_note_seq_write` | 0x178D4 | Write note + key-on to channel |
| `sbi_channel_event_dispatch` | — | Dispatch SBI channel event |
| `sbi_channel_release_close` | 0x1D130 | Release and close SBI channel |
| `channel_node_release_unlink` | — | Release channel node from linked list |
| `sbi_level_write_6` | 0x1D796 | Write scaled level to SBI channel 6 |
| `channel_program_pair_write` | 0x17794 | Write instrument program pair |
| `channel_program_fetch_write` | 0x1B7CE | Fetch and write instrument program |

### SBI (Sound Blaster Interface) Functions

The `sbi_*` prefix functions handle SoundBlaster-specific register access:
- `sbi_port_discover_aa` — auto-detect SB port (220h, 240h, etc.)
- `sbi_reset_verify` — verify SB reset
- `sbi_channel_flags_init` — initialize channel flags for SB mode
- `sbi_range_step_dispatch` — dispatch audio range step (Level-4, 8.7K calls)
- `sbi_range_step_far_entry` — far entry for range step (Level-5, 8.7K calls)
- `sbi_level_write_6` — write level to channel 6 at [0x7772:0xFDE8/0xFDEA]

### Segment 0x7772

The event/hardware state segment also holds SBI audio state:
- `ES:0x7772:word_at_0xFDE8` = channel 6 level word A
- `ES:0x7772:word_at_0xFDEA` = channel 6 level word B
- `ES:0x7772:word_at_0xFDE6` = SBI mode (2/3/4 = SB variants)

### state_mode_check (0x1BCC2, 56B, seg014)

Checks ES:0x7772 mode word at offset 0x27:
- 2, 3, or 4 = SoundBlaster variant active
- If SB active: `sbi_channel_release_close`, `state_pair_7981a_clear_if_set`, clear ES:0x7894:0xD18 word
