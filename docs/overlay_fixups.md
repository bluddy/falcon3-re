# Overlay Record Fixup Analysis

## RTLink Record Structure (from 18-byte directory)

Each directory entry:
```
struct {
  uint16_t seg;        // runtime segment (para relative to load base)
  uint16_t const_12ED; // always 0x12ED
  uint32_t tail_off;   // offset from tail start (0x1FB51)
  uint16_t const_400;  // always 0x0400
  uint16_t A;          // record code/data size (bytes)
  uint16_t B;          // fixup table size? (bytes)
  uint16_t C;          // group/class: 0,5,0xD,0x10,0x12,0x1D,0xFFFF
  uint16_t id;         // thunk table index (1-based)
  uint16_t A2;         // duplicate of A
};
```

## Record Layout in Tail

For each record at `tail + tail_off`:
- `A` bytes of code/data
- Followed by `B` bytes of fixup/relocation data (format TBD)
- Then gap to next record (alignment/padding)

## Gap/Fixup Analysis (seg=1CF6, C=0)

| id | tail_off | A | B | gap to next | gap hex (first 16) |
|----|----------|---|---|-------------|-------------------|
| 3  | 0x1FB6   | 89  | 50  | 13  | 9A 87 5B 6C 0F 50 52 53 2E FF 97 00 00 |
| 4  | 0x201C   | 282 | 4   | 1   | 22 |
| 5  | 0x2137   | 277 | 108 | 27  | 80 3E 71 00 00 75 21 B0 04 0E E8 23 FD 26 80 3E |
| 6  | 0x2267   | 59  | 12  | 3   | (next record at 0x22A5) |

Observations:
- B ≠ gap size, so B is not the gap size
- Gap data appears to be relocation/fixup entries (segment:offset pairs?)
- Example: `9A 87 5B 6C` = seg=0x5B6C? off=0x879A? Or similar

## Record Layout Hypothesis

RTLink/Plus record format (from external docs):
```
struct {
  uint16_t record_id;
  uint16_t flags;
  uint32_t data_size;      // = A
  uint32_t fixup_size;     // = B
  uint8_t  data[data_size];
  uint8_t  fixups[fixup_size];
}
```

But our directory already has `id` and `A`/`B` separately, so the on-disk record might just be:
```
[data (A bytes)]
[fixups (B bytes)]
```

And the directory `tail_off` points to the start of `data`.

## Fixup Format (speculative)

Common RTLink fixup types:
- `0x00` - segment fixup (add load segment base to word at offset)
- `0x01` - offset fixup
- `0x02` - 32-bit pointer fixup
- etc.

Gap data for id3 (13 bytes): `9A 87 5B 6C 0F 50 52 53 2E FF 97 00 00`
Could be: 3 fixups of 4 bytes each + 1 byte padding? Or variable-length.

## Next Steps

1. Search RTLink/Plus documentation for fixup format
2. Parse fixups and apply to record code before IDA analysis
3. Without fixups, far calls/segment references in overlay code will be wrong
4. Consider dynamic analysis (DOSBox + debugger) to capture fixed-up code