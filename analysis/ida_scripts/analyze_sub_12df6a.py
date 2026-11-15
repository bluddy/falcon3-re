"""
Deep analysis of function 0x12DF6A (Rank #8, 120 callers, 6,799 bytes).

Extracts:
- All callees with addresses and names
- Code structure analysis (jumps, loops, switch tables)
- Data access patterns (globals, structures)
- Subsystem classification

Usage:
    idat.exe -A -S"analyze_sub_12df6a.py" FALCONCD.EXE.i64
"""

import idc
import idaapi
import idautils
import json
from pathlib import Path
from collections import defaultdict

TARGET_ADDR = 0x12DF6A

def get_function_callees(func_addr):
    """Get all functions called by this function."""
    callees = {}
    func = idaapi.get_func(func_addr)
    if not func:
        return []
    
    for head in idautils.Heads(func.start_ea, func.end_ea):
        for xref in idautils.XrefsFrom(head, 0):
            if xref.type in [idaapi.fl_CN, idaapi.fl_CF]:
                target = xref.to
                target_func = idaapi.get_func(target)
                if target_func:
                    callee_addr = target_func.start_ea
                    
                    if callee_addr == func_addr:
                        continue
                    
                    if callee_addr not in callees:
                        callee_name = idc.get_func_name(callee_addr)
                        callee_size = target_func.end_ea - target_func.start_ea
                        callees[callee_addr] = {
                            "address": f"{callee_addr:#08x}",
                            "name": callee_name,
                            "size": callee_size,
                            "call_sites": [f"{head:#08x}"]
                        }
                    else:
                        callees[callee_addr]["call_sites"].append(f"{head:#08x}")
    
    return list(callees.values())

def analyze_code_structure(func_addr):
    """Analyze code structure: jumps, switches, loops."""
    func = idaapi.get_func(func_addr)
    if not func:
        return {}
    
    structure = {
        "jumps": [],
        "loops": [],
        "switches": [],
        "basic_blocks": 0
    }
    
    # Count basic blocks
    flowchart = idaapi.FlowChart(func)
    structure["basic_blocks"] = flowchart.size
    
    # Analyze jumps
    for head in idautils.Heads(func.start_ea, func.end_ea):
        mnem = idc.print_insn_mnem(head)
        
        # Conditional/unconditional jumps
        if mnem in ["jmp", "jz", "jnz", "je", "jne", "jl", "jg", "jle", "jge", 
                    "ja", "jb", "jae", "jbe", "jo", "jno", "js", "jns", "jc", "jnc"]:
            target = idc.get_operand_value(head, 0)
            structure["jumps"].append({
                "from": f"{head:#08x}",
                "to": f"{target:#08x}",
                "type": mnem,
                "backward": target < head
            })
            
            # Detect loops (backward jumps)
            if target < head:
                structure["loops"].append({
                    "entry": f"{target:#08x}",
                    "back_edge": f"{head:#08x}"
                })
        
        # Switch/jump tables
        if mnem == "jmp" and idc.get_operand_type(head, 0) == idc.o_phrase:
            # Possible jump table
            si_info = idaapi.get_switch_info(head)
            if si_info:
                structure["switches"].append({
                    "location": f"{head:#08x}",
                    "cases": si_info.get_jtable_size()
                })
    
    return structure

def analyze_data_access(func_addr):
    """Analyze data access patterns."""
    func = idaapi.get_func(func_addr)
    if not func:
        return {}
    
    globals_accessed = {}
    segment_accesses = defaultdict(int)
    
    for head in idautils.Heads(func.start_ea, func.end_ea):
        for op_idx in range(2):  # Check up to 2 operands
            op_type = idc.get_operand_type(head, op_idx)
            
            # Memory references
            if op_type in [idc.o_mem, idc.o_displ]:
                addr = idc.get_operand_value(head, op_idx)
                
                # Get segment
                seg = idaapi.getseg(addr)
                if seg:
                    seg_name = idaapi.get_segm_name(seg)
                    segment_accesses[seg_name] += 1
                
                # Get name if available
                name = idc.get_name(addr)
                if name:
                    if addr not in globals_accessed:
                        globals_accessed[addr] = {
                            "address": f"{addr:#08x}",
                            "name": name,
                            "accesses": 0
                        }
                    globals_accessed[addr]["accesses"] += 1
    
    return {
        "globals": list(globals_accessed.values()),
        "segment_usage": dict(segment_accesses)
    }

def categorize_callees(callees):
    """Categorize callees by subsystem based on naming."""
    categories = defaultdict(list)
    
    for callee in callees:
        name = callee["name"]
        
        # UI/Menu
        if any(x in name for x in ["ui_", "menu_", "draw_", "render_", "text_", "cursor_"]):
            categories["ui"].append(name)
        # Input
        elif any(x in name for x in ["input_", "mouse_", "key", "joystick_"]):
            categories["input"].append(name)
        # Entity/AI
        elif any(x in name for x in ["entity_", "ai_", "farobj_", "aircraft_"]):
            categories["entity"].append(name)
        # Graphics/Rendering
        elif any(x in name for x in ["vga_", "pixel_", "sprite_", "line_", "poly_"]):
            categories["graphics"].append(name)
        # Mission/Campaign
        elif any(x in name for x in ["mission_", "campaign_", "loadout_", "waypoint_"]):
            categories["mission"].append(name)
        # Resource/Data
        elif any(x in name for x in ["load_", "alloc_", "file_", "resource_", "dat_"]):
            categories["resource"].append(name)
        # Terrain
        elif any(x in name for x in ["terrain_", "heightmap_", "tile_"]):
            categories["terrain"].append(name)
        # Audio
        elif any(x in name for x in ["sbi_", "sound_", "audio_"]):
            categories["audio"].append(name)
        # Overlay
        elif any(x in name for x in ["overlay_", "r48_", "r53_", "r55_"]):
            categories["overlay"].append(name)
        else:
            categories["uncategorized"].append(name)
    
    return dict(categories)

def main():
    print("="*80)
    print(f"DEEP ANALYSIS: Function 0x12DF6A")
    print("="*80)
    
    print("\nWaiting for auto-analysis...")
    idaapi.auto_wait()
    
    func = idaapi.get_func(TARGET_ADDR)
    if not func:
        print(f"ERROR: {TARGET_ADDR:#08x} is not a function!")
        idc.qexit(1)
        return
    
    func_name = idc.get_func_name(TARGET_ADDR)
    func_size = func.end_ea - func.start_ea
    
    print(f"\nFunction: {func_name}")
    print(f"Address:  {TARGET_ADDR:#08x}")
    print(f"Size:     {func_size} bytes")
    
    # Get callees
    print("\n" + "="*80)
    print("EXTRACTING CALLEES")
    print("="*80)
    callees = get_function_callees(TARGET_ADDR)
    print(f"Found {len(callees)} unique callees")
    
    # Categorize
    categories = categorize_callees(callees)
    print("\nCallees by subsystem:")
    for cat, names in sorted(categories.items()):
        print(f"  {cat:20}: {len(names):3} functions")
    
    # Code structure
    print("\n" + "="*80)
    print("CODE STRUCTURE ANALYSIS")
    print("="*80)
    structure = analyze_code_structure(TARGET_ADDR)
    print(f"Basic blocks: {structure['basic_blocks']}")
    print(f"Jumps:        {len(structure['jumps'])}")
    print(f"Loops:        {len(structure['loops'])}")
    print(f"Switches:     {len(structure['switches'])}")
    
    # Data access
    print("\n" + "="*80)
    print("DATA ACCESS PATTERNS")
    print("="*80)
    data_access = analyze_data_access(TARGET_ADDR)
    print(f"Global variables accessed: {len(data_access['globals'])}")
    print("\nTop 10 most accessed globals:")
    for global_var in sorted(data_access["globals"], 
                            key=lambda x: x["accesses"], 
                            reverse=True)[:10]:
        print(f"  {global_var['name']:30} @ {global_var['address']:10} "
              f"({global_var['accesses']:3} accesses)")
    
    print("\nSegment access counts:")
    for seg, count in sorted(data_access["segment_usage"].items()):
        print(f"  {seg:20}: {count:4} accesses")
    
    # Save report
    report = {
        "function": {
            "name": func_name,
            "address": f"{TARGET_ADDR:#08x}",
            "size": func_size
        },
        "callees": {
            "total": len(callees),
            "list": callees,
            "by_category": categories
        },
        "structure": structure,
        "data_access": data_access
    }
    
    output_path = Path(__file__).parent.parent / "sub_12df6a_analysis.json"
    with open(output_path, "w") as f:
        json.dump(report, f, indent=2)
    
    print("\n" + "="*80)
    print(f"Report saved to: {output_path}")
    print("="*80)
    
    # Generate disassembly
    print("\nGenerating disassembly...")
    disasm_lines = []
    for head in idautils.Heads(func.start_ea, func.end_ea):
        line = idc.generate_disasm_line(head, 0)
        disasm_lines.append(f"{head:#08x}: {line}")
    
    disasm_path = Path(__file__).parent.parent / "sub_12df6a_disasm.txt"
    with open(disasm_path, "w") as f:
        f.write("\n".join(disasm_lines))
    
    print(f"Disassembly saved to: {disasm_path}")
    print("="*80)
    
    idc.qexit(0)

if __name__ == "__main__":
    main()
