#!/usr/bin/env python3
"""IDA probe: disassemble top 5 MID-body boundary errors for manual inspection.

RUN IN IDA: File → Script File → probe_mid_top5.py
"""
import json
import idc
import idaapi
import idautils

# Top 5 MID targets by call frequency
TARGETS = [
    # (parent_fn_name, parent_ea, mid_offset, calls)
    ("segment_clip_test", 0x25F93, 0x106, 32576),
    ("fixed_vec3_read", 0x22C62, 0x027, 29328),
    ("control_axes_read", 0x2234B, 0x0D3, 7301),  # first of 3
    ("control_axes_read", 0x2234B, 0x0EB, 7301),  # second
    ("control_axes_read", 0x2234B, 0x0F0, 7301),  # third
    ("state_word_2223e_set", 0x22841, 0x00A, 7288),  # first of 3
    ("state_word_2223e_set", 0x22841, 0x005, 6547),  # second
    ("state_word_2223e_set", 0x22841, 0x00F, 5976),  # third
    ("dispatch_220d4_stub", 0x263F0, 0x006, 14099),
]

OUT = r"C:\Users\ybarnoy\projects\falcon3\analysis\s4\mid_top5_disasm.json"

def get_context_disasm(ea, before=10, after=10):
    """Get disassembly lines before/after an address."""
    lines = []
    
    # Find start address (walk back 'before' instructions)
    start_ea = ea
    for _ in range(before):
        prev = idc.prev_head(start_ea)
        if prev == idc.BADADDR or prev >= start_ea:
            break
        start_ea = prev
    
    # Collect lines
    cur_ea = start_ea
    for i in range(before + after + 1):
        if cur_ea == idc.BADADDR:
            break
        
        prefix = ">>> " if cur_ea == ea else "    "
        disasm = idc.GetDisasm(cur_ea)
        
        # Check if this is a terminator
        mnem = idc.print_insn_mnem(cur_ea)
        is_term = mnem in ["ret", "retf", "retn", "jmp"]
        term_mark = " <TERM>" if is_term else ""
        
        lines.append(f"{prefix}{cur_ea:05X}  {disasm}{term_mark}")
        cur_ea = idc.next_head(cur_ea)
    
    return lines

def check_if_after_terminator(ea):
    """Check if address immediately follows a terminator."""
    prev = idc.prev_head(ea)
    if prev == idc.BADADDR:
        return False
    mnem = idc.print_insn_mnem(prev)
    return mnem in ["ret", "retf", "retn", "jmp", "iret"]

def main():
    idaapi.auto_wait()
    
    result = {}
    print("=== Probing top 5 MID-body targets ===\n")
    
    seen = set()
    for parent_name, parent_ea, offset, calls in TARGETS:
        mid_ea = parent_ea + offset
        key = f"{parent_name}+0x{offset:03X}"
        
        if key in seen:
            continue
        seen.add(key)
        
        print(f"{key:50s} @ 0x{mid_ea:05X} ({calls:,} calls)")
        
        # Get parent function info
        parent_func = idaapi.get_func(parent_ea)
        if not parent_func:
            print(f"  ERROR: parent 0x{parent_ea:05X} is not a function\n")
            continue
        
        parent_size = parent_func.end_ea - parent_func.start_ea
        print(f"  Parent: 0x{parent_ea:05X}..0x{parent_func.end_ea:05X} ({parent_size}B)")
        
        # Check what's at MID target
        mid_func = idaapi.get_func(mid_ea)
        if mid_func:
            if mid_func.start_ea == mid_ea:
                print(f"  FIXED: MID target is now a function start")
            else:
                print(f"  MID: inside {idc.get_func_name(mid_func.start_ea)}")
        else:
            print(f"  ERROR: MID target not in any function")
        
        # Check if after terminator
        after_term = check_if_after_terminator(mid_ea)
        print(f"  After terminator: {after_term}")
        
        # Get disassembly context
        disasm = get_context_disasm(mid_ea, before=8, after=8)
        
        # Check xrefs to MID target
        xrefs_to_mid = []
        for xref in idautils.XrefsTo(mid_ea, 0):
            if xref.type in [idc.fl_CN, idc.fl_CF, idc.fl_JN, idc.fl_JF]:
                caller_func = idaapi.get_func(xref.frm)
                caller_name = idc.get_func_name(caller_func.start_ea) if caller_func else "?"
                xrefs_to_mid.append({
                    "from": hex(xref.frm),
                    "fn": caller_name,
                    "type": "call" if xref.type in [idc.fl_CN, idc.fl_CF] else "jmp",
                })
        
        result[key] = {
            "parent_name": parent_name,
            "parent_ea": hex(parent_ea),
            "parent_size": parent_size,
            "mid_offset": hex(offset),
            "mid_ea": hex(mid_ea),
            "calls": calls,
            "after_terminator": after_term,
            "xrefs_to_mid": xrefs_to_mid,
            "disasm": disasm,
        }
        
        print(f"  Xrefs to MID: {len(xrefs_to_mid)}")
        print()
    
    with open(OUT, "w") as f:
        json.dump(result, f, indent=2)
    
    print(f"\nWrote {OUT}")
    print("Ready for manual inspection")

if __name__ == "__main__":
    idaapi.auto_wait()
    main()
