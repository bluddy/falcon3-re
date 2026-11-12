"""
Decode the actual CALL target from relative addressing.
In x86: CALL instruction with relative offset = EA of next instruction + offset
"""

import idc
import idaapi
import json

def main():
    print("="*80)
    print("Decoding CALL targets from terrain_frame_update_driver")
    print("="*80)
    
    try:
        idaapi.auto_wait()
        
        # The three CALL instructions to sub_1570 from terrain analysis
        call_addresses = [0x153d7, 0x15405, 0x15410]
        
        results = []
        
        for call_addr in call_addresses:
            disasm = idc.GetDisasm(call_addr)
            
            # Get target using get_operand_value (returns relative offset for near calls)
            relative_offset = idc.get_operand_value(call_addr, 0)
            
            # Calculate absolute target
            # For near CALL: target = address_of_next_instruction + relative_offset
            next_insn = idc.next_head(call_addr, idc.BADADDR)
            absolute_target = next_insn + relative_offset - (1 << 16)  # Adjust for 16-bit signed
            
            # Try simpler: just look up the name from disasm
            target_name = disasm.split()[-1] if ' ' in disasm else "unknown"
            target_by_name = idc.get_name_ea_simple(target_name)
            
            info = {
                "call_address": hex(call_addr),
                "disasm": disasm,
                "relative_offset": hex(relative_offset),
                "next_instruction": hex(next_insn),
                "calculated_target": hex(absolute_target),
                "target_name": target_name,
                "target_by_name": hex(target_by_name) if target_by_name != idc.BADADDR else "not found"
            }
            
            # Check if function exists at target_by_name
            if target_by_name != idc.BADADDR:
                func = idaapi.get_func(target_by_name)
                if func:
                    info["function"] = {
                        "found": True,
                        "start": hex(func.start_ea),
                        "size": func.end_ea - func.start_ea
                    }
            
            results.append(info)
        
        # Write output
        output = r"C:\Users\ybarnoy\projects\falcon3\analysis\s4\decoded_calls.json"
        with open(output, "w") as f:
            json.dump(results, f, indent=2)
        
        print(f"Results written to: {output}")
        
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        idc.qexit(0)

if __name__ == "__main__":
    main()
