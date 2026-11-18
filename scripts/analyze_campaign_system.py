import idaapi
import idc
import idautils

idaapi.auto_wait()

output_path = r"C:\Users\ybarnoy\projects\falcon3\temp\campaign_analysis.txt"

# Campaign system functions to analyze
functions_to_analyze = [
    (0x6A651, "squad_campaign_file_loader"),  # Main loader (2056 bytes)
    (0x6A9A2, "squad_campaign_file_loader_2"),  # Alt loader (1207 bytes)
    (0x6AD84, "squad_campaign_file_loader_3"),  # Alt loader (213 bytes)
    (0x6AE59, "ui_slot_list_mode_enter"),  # UI entry (1393 bytes)
]

try:
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write("=== Campaign System Analysis ===\n\n")
        
        for addr, expected_name in functions_to_analyze:
            f.write(f"\n{'='*70}\n")
            f.write(f"Function: {expected_name} @ {addr:#x}\n")
            f.write(f"{'='*70}\n\n")
            
            func = idaapi.get_func(addr)
            if not func:
                f.write(f"ERROR: No function at {addr:#x}\n")
                continue
            
            actual_name = idc.get_func_name(addr)
            size = func.end_ea - func.start_ea
            
            f.write(f"Actual name: {actual_name}\n")
            f.write(f"Size: {size} bytes\n")
            f.write(f"Range: {func.start_ea:#x} - {func.end_ea:#x}\n\n")
            
            # Count xrefs
            xrefs_to = list(idautils.XrefsTo(func.start_ea))
            f.write(f"Called by: {len(xrefs_to)} locations\n")
            
            # Count calls
            calls_count = 0
            for ea in idautils.FuncItems(func.start_ea):
                if idc.print_insn_mnem(ea) == 'call':
                    calls_count += 1
            
            if calls_count == 0:
                f.write(f"LEAF FUNCTION (no calls)\n\n")
            else:
                f.write(f"Makes {calls_count} calls\n\n")
            
            # String references
            f.write("String references:\n")
            str_count = 0
            for ea in idautils.FuncItems(func.start_ea):
                for xref in idautils.XrefsFrom(ea, 0):
                    str_type = idc.get_str_type(xref.to)
                    if str_type is not None and str_type >= 0:
                        string = idc.get_strlit_contents(xref.to)
                        if string:
                            try:
                                decoded = string.decode('utf-8', errors='ignore')
                                if decoded and len(decoded) > 2:
                                    f.write(f"  {ea:#x}: \"{decoded}\"\n")
                                    str_count += 1
                            except:
                                pass
            
            if str_count == 0:
                f.write("  (none found)\n")
            f.write(f"\nTotal strings: {str_count}\n\n")
            
            # Disassembly (first 100 instructions for large functions)
            f.write("Disassembly:\n")
            f.write("-" * 70 + "\n")
            
            max_instructions = 150 if size > 1000 else 200
            ea = func.start_ea
            instr_count = 0
            while ea < func.end_ea and instr_count < max_instructions:
                disasm = idc.generate_disasm_line(ea, 0)
                comment = idc.get_cmt(ea, 0) or idc.get_cmt(ea, 1)
                
                if comment:
                    f.write(f"{ea:#x}: {disasm:50s} ; {comment}\n")
                else:
                    f.write(f"{ea:#x}: {disasm}\n")
                
                ea = idc.next_head(ea)
                instr_count += 1
                if ea == idc.BADADDR:
                    break
            
            if ea < func.end_ea:
                remaining = func.end_ea - ea
                f.write(f"\n... (truncated, {remaining} more bytes)\n")
            
            f.write("\n")
        
        f.write("\n=== Success ===\n")
        
except Exception as e:
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(f"ERROR: {str(e)}\n")
        import traceback
        f.write(traceback.format_exc())

idc.qexit(0)
