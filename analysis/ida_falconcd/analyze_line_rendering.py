"""
Analyze line rendering functions for terrain vectors
"""

import idc
import idaapi
import idautils
import json

def analyze_line_draw_441e():
    """Analyze the main line drawing function (Bresenham)"""
    
    addr = 0x28B08
    func_end = idc.get_func_attr(addr, idc.FUNCATTR_END)
    
    print("=" * 80)
    print("LINE_DRAW_441E @ 0x28B08 - MAIN LINE RENDERER")
    print("=" * 80)
    print(f"Size: {func_end - addr} bytes (409 bytes)")
    print()
    
    # Full disassembly
    ea = addr
    line_num = 1
    while ea < func_end and line_num <= 100:  # First 100 lines
        disasm = idc.GetDisasm(ea)
        comment = idc.get_cmt(ea, 0)
        
        if comment:
            print(f"{line_num:3d}. {hex(ea):12s} {disasm:50s} ; {comment}")
        else:
            print(f"{line_num:3d}. {hex(ea):12s} {disasm}")
        
        line_num += 1
        ea = idc.next_head(ea)
    
    if ea < func_end:
        remaining = 0
        while ea < func_end:
            remaining += 1
            ea = idc.next_head(ea)
        print(f"... ({remaining} more lines, truncated)")
    
    print()

def analyze_line_record_draw_loop():
    """Analyze line_record_draw_loop - likely iterates through line segments"""
    
    addr = 0x28E50
    func_end = idc.get_func_attr(addr, idc.FUNCATTR_END)
    
    print("=" * 80)
    print("LINE_RECORD_DRAW_LOOP @ 0x28E50 - LINE LIST ITERATOR")
    print("=" * 80)
    print(f"Size: {func_end - addr} bytes (136 bytes)")
    print()
    
    # Full disassembly
    ea = addr
    line_num = 1
    while ea < func_end:
        disasm = idc.GetDisasm(ea)
        comment = idc.get_cmt(ea, 0)
        
        if comment:
            print(f"{line_num:3d}. {hex(ea):12s} {disasm:50s} ; {comment}")
        else:
            print(f"{line_num:3d}. {hex(ea):12s} {disasm}")
        
        line_num += 1
        ea = idc.next_head(ea)
    
    print()

def analyze_anim_line_object_draw():
    """Analyze anim_line_object_draw - might be for animated objects or vectors"""
    
    addr = 0x27A20
    func_end = idc.get_func_attr(addr, idc.FUNCATTR_END)
    
    print("=" * 80)
    print("ANIM_LINE_OBJECT_DRAW @ 0x27A20 - ANIMATED LINE RENDERER")
    print("=" * 80)
    print(f"Size: {func_end - addr} bytes (442 bytes)")
    print()
    
    # First 60 lines
    ea = addr
    line_num = 1
    while ea < func_end and line_num <= 60:
        disasm = idc.GetDisasm(ea)
        comment = idc.get_cmt(ea, 0)
        
        if comment:
            print(f"{line_num:3d}. {hex(ea):12s} {disasm:50s} ; {comment}")
        else:
            print(f"{line_num:3d}. {hex(ea):12s} {disasm}")
        
        line_num += 1
        ea = idc.next_head(ea)
    
    if ea < func_end:
        remaining = 0
        while ea < func_end:
            remaining += 1
            ea = idc.next_head(ea)
        print(f"... ({remaining} more lines, truncated)")
    
    print()

def analyze_box_edge_strip_draw():
    """Analyze box_edge_strip_draw - might be coastline edge rendering"""
    
    addr = 0x3A7DA
    func_end = idc.get_func_attr(addr, idc.FUNCATTR_END)
    
    print("=" * 80)
    print("BOX_EDGE_STRIP_DRAW @ 0x3A7DA - EDGE STRIP RENDERER")
    print("=" * 80)
    print(f"Size: {func_end - addr} bytes (109 bytes)")
    print()
    
    # Full disassembly
    ea = addr
    line_num = 1
    while ea < func_end:
        disasm = idc.GetDisasm(ea)
        comment = idc.get_cmt(ea, 0)
        
        if comment:
            print(f"{line_num:3d}. {hex(ea):12s} {disasm:50s} ; {comment}")
        else:
            print(f"{line_num:3d}. {hex(ea):12s} {disasm}")
        
        line_num += 1
        ea = idc.next_head(ea)
    
    print()

def find_who_calls_line_draw():
    """Find all functions that call line_draw_441e"""
    
    print("=" * 80)
    print("WHO CALLS LINE_DRAW_441E?")
    print("=" * 80)
    
    line_draw = 0x28B08
    
    xrefs = list(idautils.XrefsTo(line_draw))
    
    print(f"\nline_draw_441e @ {hex(line_draw)} called by {len(xrefs)} locations:\n")
    
    for xref in xrefs:
        caller_addr = xref.frm
        func_start = idc.get_func_attr(caller_addr, idc.FUNCATTR_START)
        func_name = idc.get_func_name(func_start)
        
        print(f"  {hex(caller_addr):12s} in {func_name}")
        
        # Show context (3 lines before, call, 3 lines after)
        context_start = caller_addr
        for _ in range(3):
            prev = idc.prev_head(context_start)
            if prev != idc.BADADDR:
                context_start = prev
        
        ea = context_start
        for _ in range(7):
            if ea == idc.BADADDR:
                break
            disasm = idc.GetDisasm(ea)
            marker = " >>> " if ea == caller_addr else "     "
            print(f"  {marker}{hex(ea):12s} {disasm}")
            ea = idc.next_head(ea)
        print()
    
    print()

def analyze_line_from_points():
    """Analyze line_from_points - converts point pairs to lines"""
    
    addr = 0x29F20
    func_end = idc.get_func_attr(addr, idc.FUNCATTR_END)
    
    print("=" * 80)
    print("LINE_FROM_POINTS @ 0x29F20 - POINT PAIR TO LINE CONVERTER")
    print("=" * 80)
    print(f"Size: {func_end - addr} bytes (405 bytes)")
    print()
    
    # First 50 lines
    ea = addr
    line_num = 1
    while ea < func_end and line_num <= 50:
        disasm = idc.GetDisasm(ea)
        comment = idc.get_cmt(ea, 0)
        
        if comment:
            print(f"{line_num:3d}. {hex(ea):12s} {disasm:50s} ; {comment}")
        else:
            print(f"{line_num:3d}. {hex(ea):12s} {disasm}")
        
        line_num += 1
        ea = idc.next_head(ea)
    
    if ea < func_end:
        remaining = 0
        while ea < func_end:
            remaining += 1
            ea = idc.next_head(ea)
        print(f"... ({remaining} more lines, truncated)")
    
    print()

def analyze_viewmode3_vector_project():
    """Analyze viewmode3_vector_project - 3D projection for vectors"""
    
    addr = 0x2F535
    func_end = idc.get_func_attr(addr, idc.FUNCATTR_END)
    
    print("=" * 80)
    print("VIEWMODE3_VECTOR_PROJECT @ 0x2F535 - VECTOR 3D PROJECTION")
    print("=" * 80)
    print(f"Size: {func_end - addr} bytes (91 bytes)")
    print()
    
    # Full disassembly
    ea = addr
    line_num = 1
    while ea < func_end:
        disasm = idc.GetDisasm(ea)
        comment = idc.get_cmt(ea, 0)
        
        if comment:
            print(f"{line_num:3d}. {hex(ea):12s} {disasm:50s} ; {comment}")
        else:
            print(f"{line_num:3d}. {hex(ea):12s} {disasm}")
        
        line_num += 1
        ea = idc.next_head(ea)
    
    print()

if __name__ == '__main__':
    idaapi.auto_wait()
    
    analyze_line_draw_441e()
    analyze_line_record_draw_loop()
    find_who_calls_line_draw()
    analyze_anim_line_object_draw()
    analyze_box_edge_strip_draw()
    analyze_line_from_points()
    analyze_viewmode3_vector_project()
    
    print("=" * 80)
    print("LINE RENDERING ANALYSIS COMPLETE")
    print("=" * 80)
