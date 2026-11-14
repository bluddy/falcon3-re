p = r"C:\Users\ybarnoy\projects\falcon3\status.md"
s = open(p, newline="", encoding="utf-8").read()
crlf = "\r\n" in s
s = s.replace("\r\n", "\n")
a = "     - Left open (findings 126-136): 0x167449 (inside 166F80), 0x22C8B, 0x67F77, no-xref runs."
b = ("     - Left open (findings 126-136): 0x167449 (inside 166F80), 0x22C8B, no-xref runs, and 0x67F58..0x683C5: not a pair of\n"
     "       fragments but one 628-instruction body (a repeated `les bx,[79E6C]; mov byte ptr es:[bx+N],0` stamp, entered by the\n"
     "       `jmp loc_67E29` back-edge and fall-through) that continues ui_menu_transition_step (0x67BAF) over 14 named fragments\n"
     "       (r30_entry_partial_b/c/d, r30_hlt_stub, farobj_record_clear_fields ...); ui_loadout_menu_enter at 0x683C5 starts\n"
     "       inside the `push es:[14FAh]` at 0x683C1.  Needs a function-merge path in the apply tool (read-only probe, nothing applied).")
assert s.count(a) == 1
s = s.replace(a, b)
open(p, "w", newline="", encoding="utf-8").write(s.replace("\n", "\r\n") if crlf else s)
print("ok")
