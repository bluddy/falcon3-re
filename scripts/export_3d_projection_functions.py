"""
Export the critical 3D projection functions that power the tactical map.
"""

import idc
import idaapi
import idautils

FUNCTIONS = {
    'farobj_vec3_accum_b_ret': 0x022C89,
    'fixed_vec3_accumulate_a': 0x022C91,
}

OUTPUT_DIR = r'C:\Users\ybarnoy\projects\falcon3\analysis'

def export_function_disassembly(func_name, func_addr):
    """Export detailed disassembly."""
    
    print(f"\n{'='*80}")
    print(f"Exporting: {func_name} @ 0x{func_addr:X}")
    print(f"{'='*80}")
    
    func = idaapi.get_func(func_addr)
    
    if not func:
        # Try to create function
        print(f"No function found, attempting to create...")
        if not idc.add_func(func_addr):
            print(f"ERROR: Could not create function at 0x{func_addr:X}")
            return False
        func = idaapi.get_func(func_addr)
    
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
            
            f.write(f"DISASSEMBLY\n")
            f.write(f"{'='*80}\n\n")
            
            ea = func_start
            while ea < func_end:
                disasm = idc.generate_disasm_line(ea, 0)
                item_size = idc.get_item_size(ea)
                bytes_list = [idc.get_wide_byte(ea + i) for i in range(min(item_size, 10))]
                bytes_str = ' '.join([f'{b:02X}' for b in bytes_list])
                
                comment = idc.get_cmt(ea, 0)
                repeat_comment = idc.get_cmt(ea, 1)
                
                f.write(f"0x{ea:08X}  {bytes_str:30s}  {disasm}")
                
                if comment:
                    f.write(f"  ; {comment}")
                if repeat_comment:
                    f.write(f"  ; {repeat_comment}")
                    
                f.write("\n")
                
                # Cross-references
                for xref in idautils.XrefsFrom(ea, 0):
                    if xref.type in [idc.fl_CN, idc.fl_CF]:
                        target_name = idc.get_name(xref.to)
                        if target_name:
                            f.write(f"    {'':30s}      -> {target_name} @ 0x{xref.to:X}\n")
                
                ea = idc.next_head(ea, func_end)
            
            # Data references
            f.write(f"\n{'='*80}\n")
            f.write(f"DATA REFERENCES\n")
            f.write(f"{'='*80}\n\n")
            
            data_refs = set()
            ea = func_start
            while ea < func_end:
                for xref in idautils.XrefsFrom(ea, 0):
                    if xref.type == idc.dr_O:
                        data_refs.add(xref.to)
                ea = idc.next_head(ea, func_end)
            
            for data_ea in sorted(data_refs):
                data_name = idc.get_name(data_ea) or "(unnamed)"
                data_size = idc.get_item_size(data_ea)
                
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
            
            # Callers
            f.write(f"\n{'='*80}\n")
            f.write(f"CALLERS (functions that call this one)\n")
            f.write(f"{'='*80}\n\n")
            
            callers = set()
            for xref in idautils.XrefsTo(func_start, 0):
                if xref.type in [idc.fl_CN, idc.fl_CF]:
                    caller_func = idaapi.get_func(xref.frm)
                    if caller_func:
                        callers.add(caller_func.start_ea)
            
            for caller_ea in sorted(callers):
                caller_name = idc.get_name(caller_ea) or f"sub_{caller_ea:X}"
                f.write(f"  {caller_name} @ 0x{caller_ea:X}\n")
            
            f.write(f"\nTotal callers: {len(callers)}\n")
        
        print(f"Exported to: {output_file}")
        return True
        
    except Exception as e:
        print(f"ERROR: {e}")
        return False

def main():
    print("="*80)
    print("3D PROJECTION FUNCTIONS EXPORT")
    print("="*80)
    
    idaapi.auto_wait()
    
    for func_name, func_addr in FUNCTIONS.items():
        export_function_disassembly(func_name, func_addr)
    
    print(f"\n{'='*80}")
    print(f"Export complete")
    print(f"{'='*80}")
    
    idc.qexit(0)

if __name__ == '__main__':
    main()
