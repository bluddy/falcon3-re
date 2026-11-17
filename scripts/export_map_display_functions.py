"""
IDA Python script to export tactical map display functions.
Run with: idat64 -A -S"export_map_display_functions.py" FALCONCD.EXE.i64
"""

import idc
import idaapi
import idautils
import sys

# Target functions for map display analysis
FUNCTIONS = {
    'waypoint_coordinate_processor': 0x1A2441,
    'waypoint_display_processor': 0x1A0F10,
    'waypoint_display_helper': 0x1A163A,
    'tactical_screen_coordinator': 0x12DB6A,
}

OUTPUT_DIR = r'C:\Users\ybarnoy\projects\falcon3\analysis'

def export_function_disassembly(func_name, func_addr):
    """Export detailed disassembly of a function."""
    
    print(f"\n{'='*80}")
    print(f"Exporting: {func_name} @ 0x{func_addr:X}")
    print(f"{'='*80}")
    
    func = idaapi.get_func(func_addr)
    
    if not func:
        print(f"ERROR: No function at 0x{func_addr:X}")
        return False
    
    func_start = func.start_ea
    func_end = func.end_ea
    func_size = func_end - func_start
    
    print(f"Function bounds: 0x{func_start:X} - 0x{func_end:X} ({func_size} bytes)")
    
    output_file = f"{OUTPUT_DIR}\\{func_name}_disasm.txt"
    
    try:
        with open(output_file, 'w') as f:
            f.write(f"{'='*80}\n")
            f.write(f"Function: {func_name}\n")
            f.write(f"Address: 0x{func_start:X} - 0x{func_end:X}\n")
            f.write(f"Size: {func_size} bytes (0x{func_size:X})\n")
            f.write(f"{'='*80}\n\n")
            
            # Disassemble each instruction
            ea = func_start
            instr_count = 0
            
            while ea < func_end:
                # Get disassembly line
                disasm = idc.generate_disasm_line(ea, 0)
                
                # Get instruction bytes
                item_size = idc.get_item_size(ea)
                bytes_list = [idc.get_wide_byte(ea + i) for i in range(min(item_size, 10))]
                bytes_str = ' '.join([f'{b:02X}' for b in bytes_list])
                
                # Get any comments
                comment = idc.get_cmt(ea, 0)
                repeat_comment = idc.get_cmt(ea, 1)
                
                # Format output line
                f.write(f"0x{ea:08X}  {bytes_str:30s}  {disasm}")
                
                if comment:
                    f.write(f"  ; {comment}")
                if repeat_comment:
                    f.write(f"  ; {repeat_comment}")
                    
                f.write("\n")
                
                # Get cross-references FROM this address (calls, jumps)
                for xref in idautils.XrefsFrom(ea, 0):
                    if xref.type in [idc.fl_CN, idc.fl_CF]:  # Call or jump
                        target_name = idc.get_name(xref.to)
                        if target_name:
                            f.write(f"    {'':30s}      -> {target_name} @ 0x{xref.to:X}\n")
                
                ea = idc.next_head(ea, func_end)
                instr_count += 1
            
            # Data cross-references
            f.write(f"\n{'='*80}\n")
            f.write(f"DATA CROSS-REFERENCES ({instr_count} instructions analyzed)\n")
            f.write(f"{'='*80}\n\n")
            
            data_refs = set()
            ea = func_start
            while ea < func_end:
                for xref in idautils.XrefsFrom(ea, 0):
                    if xref.type == idc.dr_O:  # Data offset
                        data_refs.add(xref.to)
                ea = idc.next_head(ea, func_end)
            
            for data_ea in sorted(data_refs):
                data_name = idc.get_name(data_ea) or "(unnamed)"
                data_size = idc.get_item_size(data_ea)
                
                # Try to read value
                if data_size == 1:
                    data_value = idc.get_wide_byte(data_ea)
                    f.write(f"0x{data_ea:08X}  {data_name:40s}  = 0x{data_value:02X} (byte)\n")
                elif data_size == 2:
                    data_value = idc.get_wide_word(data_ea)
                    f.write(f"0x{data_ea:08X}  {data_name:40s}  = 0x{data_value:04X} (word)\n")
                elif data_size == 4:
                    data_value = idc.get_wide_dword(data_ea)
                    f.write(f"0x{data_ea:08X}  {data_name:40s}  = 0x{data_value:08X} (dword)\n")
                else:
                    f.write(f"0x{data_ea:08X}  {data_name:40s}  (size={data_size})\n")
            
            # Function calls analysis
            f.write(f"\n{'='*80}\n")
            f.write(f"FUNCTION CALLS\n")
            f.write(f"{'='*80}\n\n")
            
            callees = set()
            ea = func_start
            while ea < func_end:
                for xref in idautils.XrefsFrom(ea, 0):
                    if xref.type == idc.fl_CN:  # Near call
                        callees.add(xref.to)
                    elif xref.type == idc.fl_CF:  # Far call
                        callees.add(xref.to)
                ea = idc.next_head(ea, func_end)
            
            for callee_ea in sorted(callees):
                callee_name = idc.get_name(callee_ea) or f"sub_{callee_ea:X}"
                f.write(f"  {callee_name} @ 0x{callee_ea:X}\n")
        
        print(f"Exported to: {output_file}")
        return True
        
    except Exception as e:
        print(f"ERROR exporting {func_name}: {e}")
        return False

def main():
    print("="*80)
    print("TACTICAL MAP DISPLAY FUNCTIONS EXPORT")
    print("="*80)
    
    idaapi.auto_wait()
    
    success_count = 0
    
    for func_name, func_addr in FUNCTIONS.items():
        if export_function_disassembly(func_name, func_addr):
            success_count += 1
    
    print(f"\n{'='*80}")
    print(f"Export complete: {success_count}/{len(FUNCTIONS)} functions exported")
    print(f"{'='*80}")
    
    # Exit IDA
    idc.qexit(0)

if __name__ == '__main__':
    main()
