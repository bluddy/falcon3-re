"""
Analyze video_mode function at 0x2D11A (111 bytes).

This function likely sets up the video mode and initializes the
function pointers we discovered are NULL in the static binary.
"""

import idc
import idaapi
import idautils
import json

def analyze_video_mode():
    """Analyze the video_mode function initialization."""
    
    func_addr = 0x2D11A
    func_name = idc.get_func_name(func_addr)
    func_end = idc.get_func_attr(func_addr, idc.FUNCATTR_END)
    func_size = func_end - func_addr
    
    print("=" * 80)
    print(f"ANALYZING: {func_name} at 0x{func_addr:05X} ({func_size} bytes)")
    print("=" * 80)
    
    # Get disassembly
    print("\nDISASSEMBLY:")
    print("-" * 80)
    
    ea = func_addr
    disasm_lines = []
    while ea < func_end:
        disasm = idc.generate_disasm_line(ea, 0)
        disasm_lines.append(f"0x{ea:05X}  {disasm}")
        print(f"0x{ea:05X}  {disasm}")
        ea = idc.next_head(ea)
    
    # Look for writes to our target addresses
    target_pointers = {
        0x35924: "dword_35924 (primary drawing)",
        0x35920: "dword_35920 (secondary drawing)",
        0x220A8: "dword_220A8 (pixel plotter)",
        0x220E0: "dword_220E0 (alt pixel plotter)",
    }
    
    print("\n" + "=" * 80)
    print("FUNCTION POINTER INITIALIZATIONS:")
    print("=" * 80)
    
    pointer_inits = []
    ea = func_addr
    while ea < func_end:
        # Check if this instruction references any of our targets
        for target_addr, target_name in target_pointers.items():
            for xref in idautils.XrefsFrom(ea):
                if xref.to == target_addr:
                    disasm = idc.generate_disasm_line(ea, 0)
                    
                    # Try to get the value being written
                    # Look for mov instructions
                    if "mov" in disasm.lower():
                        pointer_inits.append({
                            "address": ea,
                            "target": target_addr,
                            "target_name": target_name,
                            "disasm": disasm
                        })
                        print(f"\n0x{ea:05X}: {disasm}")
                        print(f"  -> Initializes {target_name}")
        
        ea = idc.next_head(ea)
    
    # Look for function calls (these might set up the pointers indirectly)
    print("\n" + "=" * 80)
    print("FUNCTION CALLS:")
    print("=" * 80)
    
    calls = []
    ea = func_addr
    while ea < func_end:
        if idc.print_insn_mnem(ea) == "call":
            # Get the target of the call
            for xref in idautils.XrefsFrom(ea):
                if xref.type == idaapi.fl_CN or xref.type == idaapi.fl_CF:
                    target_ea = xref.to
                    target_name = idc.get_func_name(target_ea) if target_ea else "unknown"
                    disasm = idc.generate_disasm_line(ea, 0)
                    
                    calls.append({
                        "address": ea,
                        "target": target_ea,
                        "target_name": target_name,
                        "disasm": disasm
                    })
                    
                    print(f"0x{ea:05X}: {disasm:50} -> {target_name} at 0x{target_ea:05X}")
        
        ea = idc.next_head(ea)
    
    # Check for INT 10h calls (video BIOS)
    print("\n" + "=" * 80)
    print("BIOS INT 10h CALLS (Video Services):")
    print("=" * 80)
    
    ea = func_addr
    while ea < func_end:
        if idc.print_insn_mnem(ea) == "int":
            # Get the interrupt number
            operand = idc.print_operand(ea, 0)
            if "10h" in operand:
                disasm = idc.generate_disasm_line(ea, 0)
                print(f"0x{ea:05X}: {disasm}")
        
        ea = idc.next_head(ea)
    
    # Save results
    results = {
        "function": {
            "address": func_addr,
            "name": func_name,
            "size": func_size,
            "disassembly": disasm_lines
        },
        "pointer_initializations": pointer_inits,
        "function_calls": calls
    }
    
    return results

def analyze_pointer_writes():
    """Find the specific instructions that write to our function pointers."""
    
    print("\n" + "=" * 80)
    print("ANALYZING ALL POINTER WRITES")
    print("=" * 80)
    
    targets = {
        0x35924: "dword_35924 (primary drawing)",
        0x35920: "dword_35920 (secondary drawing)",
    }
    
    for target_addr, target_name in targets.items():
        print(f"\n[*] {target_name} at 0x{target_addr:X}")
        print("-" * 40)
        
        # Find writes (xref_type == 2 means data write)
        for xref in idautils.XrefsTo(target_addr):
            disasm = idc.generate_disasm_line(xref.frm, 0)
            
            # Only show mov instructions (actual writes)
            if "mov" in disasm.lower() and "word ptr" in disasm.lower():
                # Extract the value being written
                func = idaapi.get_func(xref.frm)
                func_name = idc.get_func_name(func.start_ea) if func else "unknown"
                
                print(f"  0x{xref.frm:05X} in {func_name:40} : {disasm}")
                
                # Try to extract the immediate value
                if "," in disasm:
                    parts = disasm.split(",")
                    if len(parts) == 2:
                        value_str = parts[1].strip()
                        print(f"    -> Writing value: {value_str}")

def main():
    """Main analysis entry point."""
    
    print("\n" + "=" * 80)
    print("FALCON 3.0 - VIDEO MODE INITIALIZATION ANALYSIS")
    print("=" * 80)
    
    # Analyze video_mode function
    video_mode_results = analyze_video_mode()
    
    # Analyze pointer writes across all functions
    analyze_pointer_writes()
    
    # Save results
    output_path = "video_mode_analysis.json"
    with open(output_path, "w") as f:
        json.dump(video_mode_results, f, indent=2)
    
    print("\n" + "=" * 80)
    print(f"Results saved to: {output_path}")
    print("=" * 80)

if __name__ == "__main__":
    main()
