"""
Find what the renderer callback pointers actually point to.

The far pointers we found:
- Cockpit primary: 2F64:6331
- Cockpit secondary: 1F6C:6396
- External primary: 1F6C:56F8
- External secondary: 1F6C:6D30

These might be:
1. Runtime overlay segments (loaded dynamically)
2. Code segment offsets that need translation
3. Function pointers within the main executable

Let's search for what these values actually represent.
"""

import idc
import idaapi
import idautils
import json

def search_for_address_as_data(value):
    """Search for an address value stored in the data segment."""
    
    print(f"\nSearching for value 0x{value:04X} in data segments...")
    
    results = []
    for seg_ea in idautils.Segments():
        seg_name = idc.get_segm_name(seg_ea)
        seg_end = idc.get_segm_end(seg_ea)
        
        # Search for this value as a word
        ea = seg_ea
        while ea < seg_end:
            word_val = idc.get_wide_word(ea)
            if word_val == value:
                # Found it!
                ref_name = idc.get_name(ea)
                if not ref_name:
                    ref_name = f"data_{ea:05X}"
                
                results.append({
                    "addr": ea,
                    "segment": seg_name,
                    "name": ref_name,
                    "value": word_val
                })
                
                print(f"  Found at 0x{ea:05X} in {seg_name}: {ref_name}")
            
            ea += 1
    
    return results

def find_function_near_offset(offset):
    """Try to find a function at or near this offset."""
    
    print(f"\nSearching for function at offset 0x{offset:04X}...")
    
    # Try the offset directly
    func = idaapi.get_func(offset)
    if func:
        func_name = idc.get_func_name(offset)
        print(f"  ✓ Found function: {func_name} at 0x{offset:05X}")
        return offset
    
    # Try nearby offsets (within 100 bytes)
    for delta in range(-100, 100):
        addr = offset + delta
        func = idaapi.get_func(addr)
        if func and func.start_ea == addr:
            func_name = idc.get_func_name(addr)
            print(f"  ✓ Found function nearby: {func_name} at 0x{addr:05X} (delta: {delta:+d})")
            return addr
    
    print(f"  ✗ No function found near 0x{offset:04X}")
    return None

def analyze_segment_value(seg_value):
    """Analyze what a segment value might represent."""
    
    print(f"\nAnalyzing segment value 0x{seg_value:04X}...")
    
    # Check if it's a paragraph address (segment * 16)
    linear_addr = seg_value << 4
    print(f"  As paragraph: 0x{linear_addr:05X}")
    
    # Check if there's a segment at this address
    seg = idaapi.getseg(linear_addr)
    if seg:
        seg_name = idc.get_segm_name(seg.start_ea)
        print(f"  ✓ Maps to segment: {seg_name} at 0x{seg.start_ea:05X}")
        return seg.start_ea
    
    # Check if it's an offset in the current code segment
    seg = idaapi.getseg(seg_value)
    if seg:
        seg_name = idc.get_segm_name(seg.start_ea)
        print(f"  ✓ Is an offset in segment: {seg_name}")
        return seg_value
    
    print(f"  ? Unknown segment value")
    return None

def main():
    """Main analysis entry point."""
    
    print("=" * 80)
    print("FALCON 3.0 - FINDING RENDERER TARGET FUNCTIONS")
    print("=" * 80)
    
    # The far pointer components we found
    renderers = [
        {"name": "Cockpit Primary", "seg": 0x2F64, "off": 0x6331},
        {"name": "Cockpit Secondary", "seg": 0x1F6C, "off": 0x6396},
        {"name": "External Primary", "seg": 0x1F6C, "off": 0x56F8},
        {"name": "External Secondary", "seg": 0x1F6C, "off": 0x6D30}
    ]
    
    results = {}
    
    for renderer in renderers:
        print("\n" + "=" * 80)
        print(f"ANALYZING: {renderer['name']}")
        print(f"Far pointer: {renderer['seg']:04X}:{renderer['off']:04X}")
        print("=" * 80)
        
        # Method 1: Try the offset directly as a function address
        func_addr = find_function_near_offset(renderer['off'])
        
        # Method 2: Analyze the segment value
        seg_base = analyze_segment_value(renderer['seg'])
        
        # Method 3: Compute linear address if segment is valid
        if seg_base is not None:
            linear_addr = seg_base + renderer['off']
            print(f"\nTrying linear address: 0x{linear_addr:05X}")
            func = idaapi.get_func(linear_addr)
            if func:
                func_name = idc.get_func_name(linear_addr)
                print(f"  ✓ Found function: {func_name} at 0x{linear_addr:05X}")
                func_addr = linear_addr
        
        # Method 4: Search for the offset value in data
        data_refs = search_for_address_as_data(renderer['off'])
        
        results[renderer['name']] = {
            "far_seg": renderer['seg'],
            "far_off": renderer['off'],
            "function_addr": func_addr,
            "data_references": data_refs
        }
    
    # Also check what functions are actually referenced via cs:dword_35924 and cs:dword_35920
    print("\n" + "=" * 80)
    print("CHECKING ACTUAL USAGE OF CALLBACK POINTERS")
    print("=" * 80)
    
    callback_ptrs = [
        (0x35924, "cs:dword_35924 (primary)"),
        (0x35920, "cs:dword_35920 (secondary)")
    ]
    
    for ptr_addr, ptr_name in callback_ptrs:
        print(f"\n[*] {ptr_name} at 0x{ptr_addr:05X}")
        print("-" * 40)
        
        # Who calls through this pointer?
        call_count = 0
        for xref in idautils.XrefsTo(ptr_addr):
            ea = xref.frm
            disasm = idc.generate_disasm_line(ea, 0)
            
            # Look for "call cs:dword_xxxxx"
            if "call" in disasm.lower():
                func = idaapi.get_func(ea)
                func_name = idc.get_func_name(func.start_ea) if func else "unknown"
                print(f"  0x{ea:05X} in {func_name:30} : {disasm}")
                call_count += 1
                
                if call_count >= 10:
                    break
        
        if call_count >= 10:
            print(f"  ... (showing first 10 calls)")
    
    # Save results
    output_path = "renderer_targets.json"
    with open(output_path, "w") as f:
        json.dump(results, f, indent=2)
    
    print("\n" + "=" * 80)
    print(f"Results saved to: {output_path}")
    print("=" * 80)

if __name__ == "__main__":
    main()
