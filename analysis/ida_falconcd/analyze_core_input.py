"""
Falcon 3.0 Core Input Analysis
Analyzes the main input handling functions
"""

import idc
import idaapi
import idautils
import json

def analyze_joystick_system():
    """Analyze the joystick subsystem"""
    
    print("=" * 80)
    print("JOYSTICK SUBSYSTEM ANALYSIS")
    print("=" * 80)
    
    joystick_functions = [
        ('int15_joystick_detect', 0x1117c),
        ('int15_joystick_read', 0x1119c),
        ('joystick_poll', 0x1122a),
        ('joystick_dispatch_6d', 0x11373),
        ('joystick_axis_read_clamp', 0x11450),
        ('joystick_gate_counter', 0x22b3a),
        ('joystick_detect_state_store', 0x10175d),
    ]
    
    results = {}
    
    for name, addr in joystick_functions:
        print(f"\n--- {name} @ {hex(addr)} ---")
        
        func_end = idc.get_func_attr(addr, idc.FUNCATTR_END)
        size = func_end - addr
        
        # Get first 20 instructions
        disasm = []
        ea = addr
        for i in range(min(20, size // 2)):
            if ea >= func_end:
                break
            line = idc.GetDisasm(ea)
            disasm.append(f"{hex(ea):12s} {line}")
            ea = idc.next_head(ea)
        
        # Look for INT 15h (BIOS joystick service)
        uses_int15 = False
        ea = addr
        while ea < func_end:
            if idc.print_insn_mnem(ea) == 'int':
                int_num = idc.get_operand_value(ea, 0)
                if int_num == 0x15:
                    uses_int15 = True
                    print(f"  Found INT 15h at {hex(ea)}")
            ea = idc.next_head(ea)
        
        # Look for port I/O (port 0x201 for joystick)
        uses_port_io = False
        ea = addr
        while ea < func_end:
            mnem = idc.print_insn_mnem(ea)
            if mnem in ['in', 'out']:
                port_operand = idc.print_operand(ea, 1)
                print(f"  Port I/O: {idc.GetDisasm(ea)}")
                if '201h' in port_operand:
                    uses_port_io = True
            ea = idc.next_head(ea)
        
        # Find cross-references
        xrefs_to = list(idautils.XrefsTo(addr))
        xref_count = len(xrefs_to)
        
        results[name] = {
            'address': hex(addr),
            'size': size,
            'uses_int15': uses_int15,
            'uses_port_io': uses_port_io,
            'xref_count': xref_count,
            'disasm_preview': disasm
        }
        
        print(f"\n  Size: {size} bytes")
        print(f"  INT 15h: {uses_int15}")
        print(f"  Port I/O: {uses_port_io}")
        print(f"  Called by: {xref_count} functions")
        
    return results

def analyze_keyboard_system():
    """Analyze keyboard input handling"""
    
    print("\n" + "=" * 80)
    print("KEYBOARD SUBSYSTEM ANALYSIS")
    print("=" * 80)
    
    # True keyboard functions (not false positives)
    keyboard_functions = [
        ('key_event_process', 0x181a7),
        ('key_code_resolve', 0x182c9),
        ('kb_record_key_event', 0x1914e),
        ('key_mapper', 0x197ea),
        ('key_action_execute', 0x18e1a),
        ('key_event_table_dispatch', 0x24ec4),
        ('kbd_scancode_xlat_shift', 0x253fc),
        ('kbd_state_clear_417', 0x10fd9),
        ('kbd_ctrl_wait_64', 0x11011),
        ('kbd_led_update_60h', 0x1101a),
        ('key_state_machine_tick', 0x3467d),
        ('key_code_pending_drain', 0x348ad),
        ('key_mode_switch_step', 0x33116),
        ('key_event_mode_gate', 0x3327a),
    ]
    
    results = {}
    
    for name, addr in keyboard_functions:
        print(f"\n--- {name} @ {hex(addr)} ---")
        
        func_end = idc.get_func_attr(addr, idc.FUNCATTR_END)
        size = func_end - addr
        
        # Look for INT 16h (BIOS keyboard service)
        uses_int16 = False
        ea = addr
        while ea < func_end:
            if idc.print_insn_mnem(ea) == 'int':
                int_num = idc.get_operand_value(ea, 0)
                if int_num == 0x16:
                    uses_int16 = True
                    print(f"  Found INT 16h at {hex(ea)}")
            ea = idc.next_head(ea)
        
        # Look for keyboard port I/O (0x60, 0x64)
        kbd_ports = []
        ea = addr
        while ea < func_end:
            mnem = idc.print_insn_mnem(ea)
            if mnem in ['in', 'out']:
                port_operand = idc.print_operand(ea, 1)
                if any(p in port_operand for p in ['60h', '64h']):
                    kbd_ports.append(idc.GetDisasm(ea))
                    print(f"  Keyboard port: {idc.GetDisasm(ea)}")
            ea = idc.next_head(ea)
        
        # Find calls
        calls_to = []
        ea = addr
        while ea < func_end:
            if idc.print_insn_mnem(ea) == 'call':
                target = idc.get_operand_value(ea, 0)
                if target != idc.BADADDR:
                    target_name = idc.get_func_name(target)
                    if target_name:
                        calls_to.append(target_name)
            ea = idc.next_head(ea)
        
        xrefs_to = list(idautils.XrefsTo(addr))
        
        results[name] = {
            'address': hex(addr),
            'size': size,
            'uses_int16': uses_int16,
            'kbd_ports': kbd_ports,
            'calls_to': calls_to[:10],  # First 10 only
            'xref_count': len(xrefs_to)
        }
        
        print(f"  Size: {size} bytes")
        print(f"  INT 16h: {uses_int16}")
        print(f"  Called by: {len(xrefs_to)} functions")
        if calls_to:
            print(f"  Calls to: {', '.join(calls_to[:5])}")
    
    return results

def analyze_control_mapping():
    """Analyze control axis mapping functions"""
    
    print("\n" + "=" * 80)
    print("CONTROL MAPPING ANALYSIS")
    print("=" * 80)
    
    control_functions = [
        ('control_axis_scale_store', 0x222aa),
        ('control_axis_value', 0x222d3),
        ('control_axis_store_step', 0x2fc79),
        ('control_axes_record_write', 0x307a5),
        ('control_axes_record_store', 0x3099c),
        ('control_axis_step_quantize', 0x344de),
        ('control_axes_read', 0x2234b),
    ]
    
    results = {}
    
    for name, addr in control_functions:
        print(f"\n--- {name} @ {hex(addr)} ---")
        
        func_end = idc.get_func_attr(addr, idc.FUNCATTR_END)
        size = func_end - addr
        
        # Get first 15 instructions to understand the logic
        disasm = []
        ea = addr
        for i in range(min(15, size // 2)):
            if ea >= func_end:
                break
            line = idc.GetDisasm(ea)
            disasm.append(line)
            print(f"  {hex(ea):12s} {line}")
            ea = idc.next_head(ea)
        
        xrefs_to = list(idautils.XrefsTo(addr))
        
        results[name] = {
            'address': hex(addr),
            'size': size,
            'xref_count': len(xrefs_to),
            'disasm': disasm
        }
    
    return results

def find_input_data_structures():
    """Find input-related data structures"""
    
    print("\n" + "=" * 80)
    print("INPUT DATA STRUCTURES")
    print("=" * 80)
    
    # Search data segment for input-related names
    data_segment = idc.get_segm_by_name('dseg')
    if data_segment == idc.BADADDR:
        print("Could not find data segment")
        return {}
    
    seg_start = idc.get_segm_start(data_segment)
    seg_end = idc.get_segm_end(data_segment)
    
    results = []
    
    for ea in range(seg_start, seg_end, 2):  # Step by 2 (word-aligned)
        name = idc.get_name(ea)
        if name and any(p in name.lower() for p in ['joy', 'key', 'button', 'axis', 'input', 'control']):
            size = idc.get_item_size(ea)
            value = idc.get_wide_word(ea)
            
            # Check cross-references
            xrefs = list(idautils.XrefsTo(ea))
            
            results.append({
                'address': hex(ea),
                'name': name,
                'size': size,
                'value': hex(value) if value else 'N/A',
                'xref_count': len(xrefs)
            })
            
            print(f"{hex(ea):12s} {name:40s} ({size:3d} bytes, value={hex(value) if value else 'N/A':6s}, {len(xrefs):3d} xrefs)")
    
    return results

if __name__ == '__main__':
    idaapi.auto_wait()
    
    results = {
        'joystick': analyze_joystick_system(),
        'keyboard': analyze_keyboard_system(),
        'control_mapping': analyze_control_mapping(),
        'data_structures': find_input_data_structures()
    }
    
    # Save results
    with open('core_input_analysis.json', 'w') as f:
        json.dump(results, f, indent=2)
    
    print("\n" + "=" * 80)
    print("CORE INPUT ANALYSIS COMPLETE")
    print("=" * 80)
    print(f"Results saved to core_input_analysis.json")
