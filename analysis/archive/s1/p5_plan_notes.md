# P5 fix plan — findings 178 and 179

## Addresses confirmed by probe

### r30_record_link (finding 178a — TRIM + REBASE)
- Currently at 0x6940E..0x69462 (84 B), starts with garbled `add [bp-73h]` (bytes 00 56 8D)
- Real start: 0x6940B — bytes C8 06 00 00 = `enter 6, 0`
- Bytes 0x6940B..0x6940D (C8 06 00) are INSIDE ui_loadout_menu_enter (fn=0x683c5)
- Bytes at 0x69407: `1F 5E C9 CB` = pop ds / pop si / leave / retf
  → retf is at 0x6940A (1 byte), so ui_loadout_menu_enter can safely end at 0x6940B

**Two-step fix:**
1. TRIM ui_loadout_menu_enter from 0x6940E → 0x6940B  
   tuple: `(0x683C5, 0x6940E, 0x6940B, 0x6940B, 0x6940E)`  
   (words_hi=new_end: zero-width word range, so trim_state "applied" check passes even after REBASE reclaims the bytes)
2. REBASE r30_record_link 0x6940E → 0x6940B  
   tuple: `(0x6940E, 0x6940B, 0x69462, 0x6940B, None)`  
   (no clear_hi → clears+redecos entire body from 0x6940B)

### ui_loadout_menu_enter (finding 179 — REBASE)
- Currently at 0x683C5..0x6940B (after finding 178)
- Starts with `adc al` (bytes 14 68) — mid-instruction!
- Bytes 0x683C1..0x683C4 (26 FF 36 FA) are orphan (between ui_slot_record_init end and fn start)
- Full 5-byte instruction: 26 FF 36 FA 14 = `push word ptr es:[0x14FA]`  
  → real fn start = 0x683C1
- byte 0x683C5 is currently head of `adc al, 68h` (2 bytes: 14 68)

**Fix:**
REBASE ui_loadout_menu_enter 0x683C5 → 0x683C1  
tuple: `(0x683C5, 0x683C1, 0x6940B, 0x683C1, None, 0x683C6)`  
(clear_hi=0x683C6: clears 5 bytes 0x683C1..0x683C5 so create_insn can decode full push; 0x683C6 is after the 5th byte)

## Order
Finding 178: TRIM + REBASE r30_record_link  
Finding 179: REBASE ui_loadout_menu_enter  

Garbage fragments (r30_entry_partial_b etc.) have n_ext=0 and don't affect survey_mid.py → deferred.

## Finding numbers
178 = P5a (TRIM ui_loadout_menu_enter tail + REBASE r30_record_link)  
179 = P5b (REBASE ui_loadout_menu_enter to 0x683C1)
