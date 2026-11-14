p = r"C:\Users\ybarnoy\projects\falcon3\status.md"
s = open(p, newline="", encoding="utf-8").read()
crlf = "\r\n" in s
s = s.replace("\r\n", "\n")
a = s.index("     - Left open (findings 126-136):")
b = s.index("   - **Now:**")
new = """     - Left open (findings 126-136): 0x167449 (inside 166F80), 0x22C8B, no-xref runs, and the R30 menu state machine
       0x66E62..0x6940E (read-only probes, nothing applied).  It is one giant `[bp+6]` / `[bp-0Eh]` switch function now
       split into ~25 named pieces (ui_menu_panel_init, menu_event_dispatch, ui_menu_transition_step, r30_entry_partial_b/c/d,
       farobj_record_clear_fields, ui_loadout_menu_enter ...), all reached by jumps; the 67F58..683C5 stretch redecodes as one
       body once the pieces and their names are cleared (ui_loadout_menu_enter at 0x683C5 is a bogus start inside the
       `push es:[14FAh]` at 0x683C1).  The 15-word switch table at 0x69209 (offsets from segment base 0x669F0, `jmp
       cs:jpt_674CF[bx]` at 0x674CF) has only 6 cases decoded; the other bodies (0x68A18, 0x68A5E, 0x68AE2, 0x68C02,
       0x68CC0, 0x68E49, 0x68F20, 0x69123) are undecoded and unreferenced.  0x6940B (`enter 6,0`, far-called from 0x675BA)
       is the real start of r30_record_link; 0x69227 is a real far entry.  Fixing this means merging ~25 named pieces
       (ledger entries lost) and needs a decision on the owning function; deferred.
"""
s = s[:a] + new + s[b:]
open(p, "w", newline="", encoding="utf-8").write(s.replace("\n", "\r\n") if crlf else s)
print("ok")
