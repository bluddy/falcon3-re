"""
Falcon 3.0 Input Main Loop Analysis
Traces the main input processing pipeline
"""

import idc
import idaapi
import idautils
import json

def analyze_control_axes_read():
    """Deep dive into control_axes_read - the main entry point"""
    
    addr = 0x2234B
    func_end = idc.get_func_attr(addr, idc.FUNCATTR_END)
    
    print("=" * 80)
    print("CONTROL_AXES_READ @ 0x2234B - MAIN INPUT ENTRY POINT")
    print("=" * 80)
    print(f"Size: {func_end - addr} bytes")
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

def analyze_joystick_axis_read_clamp():
    """Analyze joystick_axis_read_clamp - hardware reader"""
    
    addr = 0x11450
    func_end = idc.get_func_attr(addr, idc.FUNCATTR_END)
    
    print("=" * 80)
    print("JOYSTICK_AXIS_READ_CLAMP @ 0x11450 - HARDWARE READER")
    print("=" * 80)
    print(f"Size: {func_end - addr} bytes")
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

def analyze_key_event_process():
    """Analyze key_event_process - keyboard coordinator"""
    
    addr = 0x181A7
    func_end = idc.get_func_attr(addr, idc.FUNCATTR_END)
    
    print("=" * 80)
    print("KEY_EVENT_PROCESS @ 0x181A7 - KEYBOARD COORDINATOR")
    print("=" * 80)
    print(f"Size: {func_end - addr} bytes")
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
        print(f"... ({line_num} more lines, truncated)")
    
    print()

def find_input_frame_coordinator():
    """Find the function that calls control_axes_read each frame"""
    
    print("=" * 80)
    print("FINDING FRAME COORDINATOR")
    print("=" * 80)
    
    control_axes_read = 0x2234B
    
    xrefs = list(idautils.XrefsTo(control_axes_read))
    
    print(f"\ncontrol_axes_read @ {hex(control_axes_read)} called by:")
    
    for xref in xrefs:
        caller_addr = xref.frm
        func_start = idc.get_func_attr(caller_addr, idc.FUNCATTR_START)
        func_name = idc.get_func_name(func_start)
        
        print(f"\n  {hex(caller_addr):12s} in {func_name}")
        
        # Show context around the call
        print(f"  Context:")
        start_ea = max(func_start, caller_addr - 10)
        end_ea = min(idc.get_func_attr(func_start, idc.FUNCATTR_END), caller_addr + 10)
        
        ea = start_ea
        while ea <= end_ea:
            disasm = idc.GetDisasm(ea)
            marker = " >>> " if ea == caller_addr else "     "
            print(f"  {marker}{hex(ea):12s} {disasm}")
            ea = idc.next_head(ea)
    
    print()

def analyze_input_data_storage():
    """Find where input axes are stored"""
    
    print("=" * 80)
    print("INPUT DATA STORAGE ANALYSIS")
    print("=" * 80)
    
    # Known data locations from disassembly
    storage_locations = [
        ('cs:byte_22232', 0x22232, 'Axis storage array'),
        ('cs:word_2222C', 0x2222C, 'X scale factor'),
        ('cs:word_2222E', 0x2222E, 'Y scale factor'),
        ('cs:word_22230', 0x22230, 'Scale backup'),
        ('cs:word_2223A', 0x2223A, 'Alternate axis value'),
        ('cs:word_22244', 0x22244, 'Keyboard input value'),
    ]
    
    print("\nKnown input storage locations:")
    for name, addr, description in storage_locations:
        # Try to get actual name from IDA
        ida_name = idc.get_name(addr)
        if ida_name:
            name = ida_name
        
        # Get cross-references
        xrefs = list(idautils.XrefsTo(addr))
        
        print(f"\n{name:30s} @ {hex(addr)}")
        print(f"  Purpose: {description}")
        print(f"  References: {len(xrefs)}")
        
        if len(xrefs) <= 5:
            for xref in xrefs:
                func_name = idc.get_func_name(idc.get_func_attr(xref.frm, idc.FUNCATTR_START))
                xref_type = "read" if xref.type == idc.dr_R else "write"
                print(f"    {hex(xref.frm):12s} {xref_type:6s} in {func_name}")
    
    print()

def analyze_input_state_machine():
    """Analyze key_state_machine_tick"""
    
    addr = 0x3467D
    func_end = idc.get_func_attr(addr, idc.FUNCATTR_END)
    
    print("=" * 80)
    print("KEY_STATE_MACHINE_TICK @ 0x3467D - STATE MACHINE")
    print("=" * 80)
    print(f"Size: {func_end - addr} bytes")
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
    
    analyze_control_axes_read()
    analyze_joystick_axis_read_clamp()
    find_input_frame_coordinator()
    analyze_input_data_storage()
    analyze_key_event_process()
    analyze_input_state_machine()
    
    print("=" * 80)
    print("INPUT MAIN LOOP ANALYSIS COMPLETE")
    print("=" * 80)
