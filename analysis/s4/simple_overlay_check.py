"""Simple check of overlay_tail_bridge"""

import idc
import idaapi
import idautils
import json

def main():
    print("Checking overlay_tail_bridge...")
    
    addr = idc.get_name_ea_simple("overlay_tail_bridge")
    if addr == idc.BADADDR:
        addr = 0x166F
    
    func = idaapi.get_func(addr)
    if not func:
        print(f"No function at {hex(addr)}")
        idc.qexit(1)
        return
    
    print(f"Address: {hex(addr)}")
    print(f"Size: {func.end_ea - func.start_ea} bytes")
    
    # Get segment
    seg = idaapi.getseg(addr)
    if seg:
        seg_name = idaapi.get_segm_name(seg)
        print(f"Segment: {seg_name}")
    
    # Count calls
    ea = func.start_ea
    call_count = 0
    while ea < func.end_ea:
        if idc.print_insn_mnem(ea) == "call":
            call_count += 1
        ea = idc.next_head(ea, func.end_ea)
    
    print(f"Calls: {call_count}")
    
    # Get callers
    xrefs = list(idautils.XrefsTo(func.start_ea, 0))
    print(f"Called by: {len(xrefs)} call sites")
    
    for xref in xrefs[:5]:
        caller = idc.get_func_name(xref.frm)
        print(f"  - {caller} at {hex(xref.frm)}")
    
    result = {
        "address": hex(addr),
        "size": func.end_ea - func.start_ea,
        "segment": seg_name if seg else None,
        "calls": call_count,
        "callers": len(xrefs)
    }
    
    with open(r"C:\Users\ybarnoy\projects\falcon3\analysis\s4\overlay_bridge_info.json", "w") as f:
        json.dump(result, f, indent=2)
    
    print("Done")
    idc.qexit(0)

if __name__ == "__main__":
    idaapi.auto_wait()
    main()
