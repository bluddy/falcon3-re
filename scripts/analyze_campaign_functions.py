import idaapi
import idc
import idautils

idaapi.auto_wait()

output_path = r"C:\Users\ybarnoy\projects\falcon3\temp\campaign_functions_detail.txt"

# Functions of interest
functions_to_analyze = [
    (0x136133, "campaign_save_temp_file_write", "Likely campaign file writer"),
    (0x17B437, "squadron_mission_file_loader", "Another large campaign loader"),
    (0x1793C0, "overlay_r4F_handler", "16 campaign file references"),
]

try:
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write("=== Detailed Campaign Function Analysis ===\n\n")
        
        for addr, expected_name, description in functions_to_analyze:
            f.write(f"\n{'='*70}\n")
            f.write(f"Function: {expected_name} @ {addr:#x}\n")
            f.write(f"Description: {description}\n")
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
            if len(xrefs_to) > 0 and len(xrefs_to) <= 10:
                for xref in xrefs_to:
                    caller_func = idaapi.get_func(xref.frm)
                    if caller_func:
                        caller_name = idc.get_func_name(caller_func.start_ea)
                        f.write(f"  {xref.frm:#x}: {caller_name}\n")
            
            # Count calls
            calls_count = 0
            for ea in idautils.FuncItems(func.start_ea):
                if idc.print_insn_mnem(ea) == 'call':
                    calls_count += 1
            
            if calls_count == 0:
                f.write(f"\nLEAF FUNCTION (no calls)\n\n")
            else:
                f.write(f"\nMakes {calls_count} calls\n\n")
            
            # String references
            f.write("String references:\n")
            str_refs = []
            for ea in idautils.FuncItems(func.start_ea):
                for xref in idautils.XrefsFrom(ea, 0):
                    str_type = idc.get_str_type(xref.to)
                    if str_type is not None and str_type >= 0:
                        string = idc.get_strlit_contents(xref.to)
                        if string:
                            try:
                                decoded = string.decode('utf-8', errors='ignore')
                                if decoded and len(decoded) > 0:
                                    str_refs.append((ea, decoded))
                            except:
                                pass
            
            if str_refs:
                for ea, string in str_refs:
                    f.write(f"  {ea:#x}: \"{string}\"\n")
            else:
                f.write("  (none found)\n")
            
            f.write(f"\nTotal strings: {len(str_refs)}\n\n")
            
            # Disassembly (first 200 instructions for analysis)
            f.write("Disassembly (first 200 instructions):\n")
            f.write("-" * 70 + "\n")
            
            ea = func.start_ea
            instr_count = 0
            max_instructions = 200
            
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
                remaining_bytes = func.end_ea - ea
                remaining_instrs = 0
                temp_ea = ea
                while temp_ea < func.end_ea:
                    temp_ea = idc.next_head(temp_ea)
                    if temp_ea == idc.BADADDR:
                        break
                    remaining_instrs += 1
                
                f.write(f"\n... (truncated, ~{remaining_instrs} more instructions, {remaining_bytes} bytes)\n")
            
            f.write("\n")
        
        f.write("\n=== Success ===\n")
        
except Exception as e:
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(f"ERROR: {str(e)}\n")
        import traceback
        f.write(traceback.format_exc())

idc.qexit(0)
