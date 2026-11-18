import idaapi
import idc
import idautils

idaapi.auto_wait()

output_path = r"C:\Users\ybarnoy\projects\falcon3\temp\campaign_writer_search.txt"

try:
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write("=== Campaign Writer Function Search ===\n\n")
        
        # Extract the mystery filename at DS:0A34Ah
        f.write("="*70 + "\n")
        f.write("Mystery Filename at DS:0A34Ah\n")
        f.write("="*70 + "\n\n")
        
        ds_seg = idc.get_sreg(0x6A73B, "ds")
        if ds_seg != idc.BADADDR:
            addr = (ds_seg << 4) + 0xA34A
            f.write(f"DS segment: {ds_seg:#x}\n")
            f.write(f"Calculated address: {addr:#x}\n")
            
            # Try to read as string
            str_type = idc.get_str_type(addr)
            if str_type is not None and str_type >= 0:
                string = idc.get_strlit_contents(addr)
                if string:
                    try:
                        decoded = string.decode('utf-8', errors='ignore')
                        f.write(f"String found: \"{decoded}\"\n")
                    except:
                        f.write(f"Raw bytes: {string.hex()}\n")
            else:
                # Read 32 bytes as hex
                bytes_data = idc.get_bytes(addr, 32)
                if bytes_data:
                    f.write(f"Raw bytes: {bytes_data.hex()}\n")
                    try:
                        decoded = bytes_data.decode('utf-8', errors='ignore')
                        f.write(f"Decoded: \"{decoded}\"\n")
                    except:
                        pass
        else:
            f.write("ERROR: Could not determine DS segment\n")
        
        f.write("\n\n")
        
        # Find functions that write .CAM files
        f.write("="*70 + "\n")
        f.write("Functions with .CAM String References (Potential Writers)\n")
        f.write("="*70 + "\n\n")
        
        cam_string_addr = None
        for seg in idautils.Segments():
            for head in idautils.Heads(seg, idc.get_segm_end(seg)):
                str_type = idc.get_str_type(head)
                if str_type is not None and str_type >= 0:
                    string = idc.get_strlit_contents(head)
                    if string:
                        try:
                            decoded = string.decode('utf-8', errors='ignore')
                            if '.CAM' in decoded.upper() or 'CAM' in decoded.upper():
                                cam_string_addr = head
                                f.write(f"Found .CAM string at {head:#x}: \"{decoded}\"\n")
                                
                                # Find xrefs to this string
                                xrefs = list(idautils.XrefsTo(head))
                                f.write(f"  Referenced by {len(xrefs)} locations:\n")
                                for xref in xrefs:
                                    func = idaapi.get_func(xref.frm)
                                    if func:
                                        func_name = idc.get_func_name(func.start_ea)
                                        func_size = func.end_ea - func.start_ea
                                        f.write(f"    {xref.frm:#x} in function {func_name} @ {func.start_ea:#x} ({func_size}B)\n")
                        except:
                            pass
        
        f.write("\n\n")
        
        # Search for file WRITE operations (op_dispatch with operation code for WRITE)
        # Based on squad_campaign_file_loader pattern:
        # - Operation 6 = OPEN
        # - Operation 8 = CLOSE  
        # - Operation 10 = READ
        # Likely: Operation 11 or 13 = WRITE
        
        f.write("="*70 + "\n")
        f.write("Functions Using File WRITE Operations\n")
        f.write("="*70 + "\n\n")
        
        f.write("Searching for op_dispatch_far_entry calls with write operations...\n\n")
        
        # Find all calls to op_dispatch_far_entry
        # Look for patterns where operation code might be WRITE (11, 13, etc.)
        
        for func_ea in idautils.Functions():
            func = idaapi.get_func(func_ea)
            if not func:
                continue
            
            func_name = idc.get_func_name(func_ea)
            
            # Look for patterns: push N; call op_dispatch_far_entry
            # where N might be a write operation
            write_operations_found = []
            
            for ea in idautils.FuncItems(func_ea):
                if idc.print_insn_mnem(ea) == 'push':
                    # Check if next instruction is call
                    next_ea = idc.next_head(ea)
                    if next_ea != idc.BADADDR and idc.print_insn_mnem(next_ea) == 'call':
                        target = idc.get_operand_value(next_ea, 0)
                        target_name = idc.get_func_name(target)
                        
                        if 'dispatch' in target_name.lower():
                            # Check the push value
                            push_value = idc.get_operand_value(ea, 0)
                            
                            # Look for operations other than 6 (OPEN), 8 (CLOSE), 10 (READ), 12 (READ variant)
                            # Likely write operations: 11, 13, 14
                            if push_value in [11, 13, 14, 15]:
                                write_operations_found.append((ea, push_value, target_name))
            
            if write_operations_found:
                func_size = func.end_ea - func.start_ea
                f.write(f"\nFunction: {func_name} @ {func_ea:#x} ({func_size}B)\n")
                f.write(f"  Found {len(write_operations_found)} potential write operations:\n")
                for ea, op_code, target in write_operations_found:
                    f.write(f"    {ea:#x}: push {op_code:#x} ({op_code}); call {target}\n")
        
        f.write("\n\n")
        
        # Look for xrefs to squad_campaign_file_loader to find caller
        f.write("="*70 + "\n")
        f.write("Functions Calling squad_campaign_file_loader\n")
        f.write("="*70 + "\n\n")
        
        loader_addr = 0x6A651
        xrefs_to_loader = list(idautils.XrefsTo(loader_addr))
        f.write(f"squad_campaign_file_loader @ {loader_addr:#x} called by {len(xrefs_to_loader)} locations:\n\n")
        
        for xref in xrefs_to_loader:
            func = idaapi.get_func(xref.frm)
            if func:
                func_name = idc.get_func_name(func.start_ea)
                func_size = func.end_ea - func.start_ea
                f.write(f"  {xref.frm:#x}: {func_name} @ {func.start_ea:#x} ({func_size}B)\n")
                
                # This caller might also call a writer function
                f.write(f"    Calls made by {func_name}:\n")
                call_count = 0
                for ea in idautils.FuncItems(func.start_ea):
                    if idc.print_insn_mnem(ea) == 'call':
                        target = idc.get_operand_value(ea, 0)
                        if target != idc.BADADDR:
                            target_name = idc.get_func_name(target)
                            target_func = idaapi.get_func(target)
                            if target_func:
                                target_size = target_func.end_ea - target_func.start_ea
                                # Look for large functions (likely complex writers)
                                if target_size > 500:  # Writers likely large like loader (2056B)
                                    f.write(f"      {ea:#x}: {target_name} @ {target:#x} ({target_size}B) <-- LARGE FUNCTION\n")
                                    call_count += 1
                            else:
                                f.write(f"      {ea:#x}: {target_name} @ {target:#x}\n")
                                call_count += 1
                        
                        if call_count > 20:  # Limit output
                            f.write(f"      ... ({call_count} total calls, truncated)\n")
                            break
                
                f.write("\n")
        
        f.write("\n=== Success ===\n")

except Exception as e:
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(f"ERROR: {str(e)}\n")
        import traceback
        f.write(traceback.format_exc())

idc.qexit(0)
