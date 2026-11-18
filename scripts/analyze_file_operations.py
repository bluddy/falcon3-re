import idaapi
import idc
import idautils

idaapi.auto_wait()

output_path = r"C:\Users\ybarnoy\projects\falcon3\temp\file_operations_analysis.txt"

try:
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write("=== File Operation Analysis ===\n\n")
        
        # Analyze squad_campaign_file_loader to extract all operation codes used
        f.write("="*70 + "\n")
        f.write("Operation Codes in squad_campaign_file_loader @ 0x6A651\n")
        f.write("="*70 + "\n\n")
        
        loader_addr = 0x6A651
        func = idaapi.get_func(loader_addr)
        
        if func:
            operations_found = {}
            
            ea = func.start_ea
            while ea < func.end_ea:
                if idc.print_insn_mnem(ea) == 'push':
                    push_val = idc.get_operand_value(ea, 0)
                    
                    # Look ahead for call to op_dispatch
                    next_ea = ea
                    for i in range(5):  # Check next 5 instructions
                        next_ea = idc.next_head(next_ea)
                        if next_ea == idc.BADADDR:
                            break
                        
                        if idc.print_insn_mnem(next_ea) == 'call':
                            target = idc.get_operand_value(next_ea, 0)
                            target_name = idc.get_func_name(target)
                            
                            if 'dispatch' in target_name.lower() or 'op_' in target_name.lower():
                                if push_val not in operations_found:
                                    operations_found[push_val] = []
                                operations_found[push_val].append((ea, next_ea, target_name))
                                break
                
                ea = idc.next_head(ea)
                if ea == idc.BADADDR:
                    break
            
            f.write(f"Found {len(operations_found)} unique operation codes:\n\n")
            for op_code in sorted(operations_found.keys()):
                locs = operations_found[op_code]
                f.write(f"Operation {op_code:#x} ({op_code}): Used {len(locs)} times\n")
                for push_ea, call_ea, target_name in locs[:3]:  # Show first 3
                    f.write(f"  {push_ea:#x}: push {op_code}; ... {call_ea:#x}: call {target_name}\n")
                if len(locs) > 3:
                    f.write(f"  ... ({len(locs) - 3} more)\n")
                f.write("\n")
        
        f.write("\n")
        
        # Find the mysterious DS:0A34Ah reference by checking the actual instruction
        f.write("="*70 + "\n")
        f.write("Extracting DS:0A34Ah String Reference\n")
        f.write("="*70 + "\n\n")
        
        # At 0x6A73B: push 0A34Ah
        ref_ea = 0x6A73B
        f.write(f"Instruction at {ref_ea:#x}:\n")
        f.write(f"  {idc.generate_disasm_line(ref_ea, 0)}\n\n")
        
        # The previous instruction should be: push ds
        prev_ea = idc.prev_head(ref_ea)
        f.write(f"Previous instruction at {prev_ea:#x}:\n")
        f.write(f"  {idc.generate_disasm_line(prev_ea, 0)}\n\n")
        
        # DS is the data segment - need to check what segment is loaded
        # In 16-bit DOS, DS usually points to the program's data segment
        # Let's find what's at the data segment offset 0xA34A
        
        f.write("Searching for string at offset 0xA34A in all segments...\n\n")
        
        for seg in idautils.Segments():
            seg_name = idc.get_segm_name(seg)
            seg_start = seg
            seg_end = idc.get_segm_end(seg)
            seg_size = seg_end - seg_start
            
            # Check if 0xA34A offset is within this segment
            if 0xA34A < seg_size:
                addr = seg_start + 0xA34A
                f.write(f"Segment {seg_name} @ {seg:#x}-{seg_end:#x} (size {seg_size:#x}):\n")
                f.write(f"  Offset 0xA34A would be at {addr:#x}\n")
                
                # Try to read as string
                str_type = idc.get_str_type(addr)
                if str_type is not None and str_type >= 0:
                    string = idc.get_strlit_contents(addr)
                    if string:
                        try:
                            decoded = string.decode('utf-8', errors='ignore')
                            f.write(f"  String found: \"{decoded}\"\n")
                        except:
                            f.write(f"  Raw bytes: {string.hex()}\n")
                else:
                    # Read 64 bytes as hex
                    bytes_data = idc.get_bytes(addr, 64)
                    if bytes_data:
                        f.write(f"  Raw bytes (64): {bytes_data.hex()}\n")
                        # Try to decode as ASCII
                        ascii_str = ""
                        for b in bytes_data:
                            if 32 <= b < 127:
                                ascii_str += chr(b)
                            else:
                                ascii_str += "."
                        f.write(f"  ASCII interpretation: {ascii_str}\n")
                
                f.write("\n")
        
        f.write("\n")
        
        # Find all functions with "save" or "write" in their names
        f.write("="*70 + "\n")
        f.write("Functions with 'save', 'write', 'store', 'update' in name\n")
        f.write("="*70 + "\n\n")
        
        save_funcs = []
        for func_ea in idautils.Functions():
            func_name = idc.get_func_name(func_ea)
            func_name_lower = func_name.lower()
            
            if any(keyword in func_name_lower for keyword in ['save', 'write', 'store', 'update', 'sync']):
                func = idaapi.get_func(func_ea)
                if func:
                    func_size = func.end_ea - func.start_ea
                    save_funcs.append((func_ea, func_name, func_size))
        
        f.write(f"Found {len(save_funcs)} functions:\n\n")
        for func_ea, func_name, func_size in sorted(save_funcs, key=lambda x: x[2], reverse=True):
            f.write(f"{func_ea:#x}: {func_name} ({func_size}B)\n")
            
            # Show if it references .CAM, .SQU, etc.
            refs_campaign_files = False
            for ea in idautils.FuncItems(func_ea):
                for xref in idautils.XrefsFrom(ea, 0):
                    str_type = idc.get_str_type(xref.to)
                    if str_type is not None and str_type >= 0:
                        string = idc.get_strlit_contents(xref.to)
                        if string:
                            try:
                                decoded = string.decode('utf-8', errors='ignore')
                                if any(ext in decoded.upper() for ext in ['.CAM', '.SQU', '.MIS', '.TRG', '.TSK', '.SHP', 'SQUAD']):
                                    f.write(f"  -> References: \"{decoded}\"\n")
                                    refs_campaign_files = True
                            except:
                                pass
            
            if not refs_campaign_files:
                f.write(f"  (no campaign file references found)\n")
            f.write("\n")
        
        f.write("\n")
        
        # Look for large functions (>1500 bytes) that might be the writer counterpart
        f.write("="*70 + "\n")
        f.write("Large Functions (>1500 bytes) - Potential Campaign Writers\n")
        f.write("="*70 + "\n\n")
        
        large_funcs = []
        for func_ea in idautils.Functions():
            func = idaapi.get_func(func_ea)
            if func:
                func_size = func.end_ea - func.start_ea
                if func_size > 1500:
                    func_name = idc.get_func_name(func_ea)
                    large_funcs.append((func_ea, func_name, func_size))
        
        f.write(f"Found {len(large_funcs)} large functions:\n\n")
        for func_ea, func_name, func_size in sorted(large_funcs, key=lambda x: x[2], reverse=True)[:20]:
            f.write(f"{func_ea:#x}: {func_name} ({func_size}B)\n")
            
            # Check for campaign file references
            refs = []
            for ea in idautils.FuncItems(func_ea):
                for xref in idautils.XrefsFrom(ea, 0):
                    str_type = idc.get_str_type(xref.to)
                    if str_type is not None and str_type >= 0:
                        string = idc.get_strlit_contents(xref.to)
                        if string:
                            try:
                                decoded = string.decode('utf-8', errors='ignore')
                                if any(ext in decoded.upper() for ext in ['.CAM', '.SQU', '.MIS', '.TRG', '.TSK', '.SHP', 'SQUAD']):
                                    refs.append(decoded)
                            except:
                                pass
            
            if refs:
                f.write(f"  Campaign file references: {len(refs)}\n")
                for ref in refs[:5]:
                    f.write(f"    \"{ref}\"\n")
                if len(refs) > 5:
                    f.write(f"    ... and {len(refs) - 5} more\n")
            f.write("\n")
        
        f.write("\n=== Success ===\n")

except Exception as e:
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(f"ERROR: {str(e)}\n")
        import traceback
        f.write(traceback.format_exc())

idc.qexit(0)
