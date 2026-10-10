"""Force analysis of overlay segments in IDA after fixups applied."""
import ida_bytes
import ida_funcs
import ida_segment
import idautils
import idaapi
import idc
import ida_auto

def analyze_overlay_segments():
    """Force analysis of all OVL_* segments."""
    for i in range(ida_segment.get_segm_qty()):
        s = ida_segment.getnseg(i)
        seg_name = idc.get_segm_name(s.start_ea)
        if seg_name.startswith("OVL_"):
            print(f"Analyzing segment {seg_name} [{hex(s.start_ea)}-{hex(s.end_ea)}] size={s.end_ea - s.start_ea}")
            
            # Make sure it's marked as code
            ida_segment.set_segm_class(s, "CODE")
            
            # Try to create functions at likely entry points
            ea = s.start_ea
            while ea < s.end_ea:
                b = ida_bytes.get_bytes(ea, 2)
                if b == b'\x55\x8b':  # push bp; mov bp, sp
                    if not ida_funcs.get_func(ea):
                        ida_funcs.add_func(ea)
                        print(f"  Created function at {hex(ea)}")
                elif b and b[0] == 0xC8:  # ENTER
                    if not ida_funcs.get_func(ea):
                        ida_funcs.add_func(ea)
                        print(f"  Created function at {hex(ea)} (ENTER)")
                elif b and b[0] == 0x55:
                    b2 = ida_bytes.get_bytes(ea+1, 1)
                    if b2 and b2[0] in (0x8b, 0x89):
                        if not ida_funcs.get_func(ea):
                            ida_funcs.add_func(ea)
                            print(f"  Created function at {hex(ea)} (push bp; mov)")
                ea += 1
            
            print(f"  Running autoanalysis on {seg_name}...")
            ida_auto.auto_mark_range(s.start_ea, s.end_ea, ida_auto.AU_CODE)
    
    idaapi.auto_wait()
    print("Done!")

analyze_overlay_segments()
idaapi.qexit(0)