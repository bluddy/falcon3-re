#!/usr/bin/env python3
"""Check what segment these addresses are in"""
import idc
import ida_segment

targets = [0x407BF, 0x40DDB, 0x40C69, 0x40045, 0x3FD66, 0x404F1]

with open("C:/Users/ybarnoy/projects/falcon3/analysis/s1/segment_check.txt", "w") as f:
    for ea in targets:
        seg = ida_segment.getseg(ea)
        if seg:
            seg_name = idc.get_segm_name(ea)
            f.write(f"0x{ea:X}: segment {seg_name}, base=0x{seg.start_ea:X}, end=0x{seg.end_ea:X}\n")
            
            # Check what's at this address
            flags = idc.get_full_flags(ea)
            if idc.is_code(flags):
                disasm = idc.generate_disasm_line(ea, 0)
                f.write(f"  Code: {disasm}\n")
            elif idc.is_data(flags):
                f.write(f"  Data\n")
            else:
                f.write(f"  Unknown/Unexplored\n")
        else:
            f.write(f"0x{ea:X}: NOT IN ANY SEGMENT\n")

idc.qexit(0)
