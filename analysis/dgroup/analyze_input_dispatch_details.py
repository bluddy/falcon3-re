"""
Analyze the detailed JSON files for functions that read input_flag_pending_2.
Look for comparisons with view key scan codes right after the read.
"""

import json
import os
import glob

# View key scan codes
VIEW_KEYS = list(range(0x02, 0x0C))  # 0x02-0x0B

# Candidates with their read addresses
candidates = {
    'game_mode_r53_main_coordinator': ['0x182476', '0x183834', '0x183FA6', '0x184B10', '0x185068'],
    'r29_tactical_screen_coordinator': ['0x12DFD6', '0x12EEDC', '0x12F512'],
    'overlay_r45_logic': ['0x156D7E'],
    'overlay_r48_processor': ['0x16DBF4'],
    'overlay_r49_handler': ['0x17089E'],
}

def load_function_json(func_name):
    """Try to find and load the detailed JSON for a function."""
    pattern = f"c:/Users/ybarnoy/projects/falcon3/analysis/ida_falconcd/func_*_full.json"
    
    for filepath in glob.glob(pattern):
        try:
            with open(filepath, 'r') as f:
                data = json.load(f)
                if data.get('name') == func_name:
                    return data, filepath
        except:
            continue
    
    return None, None

def analyze_after_read(disasm, read_addr_str):
    """Analyze instructions after a read of input_flag_pending_2."""
    
    # Find the read instruction index
    read_idx = None
    for i, insn in enumerate(disasm):
        if insn.get('address') == read_addr_str:
            read_idx = i
            break
    
    if read_idx is None:
        return None
    
    print(f"\n  Found read at {read_addr_str} (index {read_idx})")
    print(f"  {disasm[read_idx]['disasm']}")
    
    # Look at next 30 instructions
    results = []
    for i in range(read_idx + 1, min(read_idx + 31, len(disasm))):
        insn = disasm[i]
        disasm_text = insn.get('disasm', '')
        addr = insn.get('address', '')
        
        # Look for comparisons
        if 'cmp' in disasm_text.lower():
            # Check if comparing with our scan codes
            for key in VIEW_KEYS:
                if f'{key}' in disasm_text or f'0{key:X}h' in disasm_text or f'{key:X}h' in disasm_text:
                    print(f"  >>> {addr}: {disasm_text} [VIEW KEY CANDIDATE!]")
                    results.append({'addr': addr, 'insn': disasm_text, 'scan_code': key})
                    break
            else:
                # Just show any comparison
                print(f"      {addr}: {disasm_text}")
        
        # Look for switch/jump tables
        elif 'jmp' in disasm_text.lower() and '[' in disasm_text:
            print(f"  >>> {addr}: {disasm_text} [POSSIBLE JUMP TABLE!]")
            results.append({'addr': addr, 'insn': disasm_text, 'type': 'jump_table'})
        
        # Look for conditional jumps
        elif any(x in disasm_text.lower() for x in ['jz', 'jnz', 'je', 'jne', 'ja', 'jb', 'jl', 'jg']):
            pass  # Too many to show, only show after cmp
        
        # Look for calls to view-related functions
        elif 'call' in disasm_text.lower() and any(x in disasm_text.lower() for x in ['view', 'external', 'cockpit']):
            print(f"  >>> {addr}: {disasm_text} [VIEW FUNCTION CALL!]")
            results.append({'addr': addr, 'insn': disasm_text, 'type': 'view_call'})
    
    return results

def main():
    print("=" * 80)
    print("ANALYZING INPUT DISPATCH IN DETAIL")
    print("=" * 80)
    print(f"View key scan codes: {[hex(x) for x in VIEW_KEYS]}")
    print()
    
    all_findings = {}
    
    for func_name, read_addrs in candidates.items():
        print(f"\n{'=' * 80}")
        print(f"Function: {func_name}")
        print('=' * 80)
        
        # Load the JSON
        data, filepath = load_function_json(func_name)
        
        if data is None:
            print(f"  WARNING: Could not find detailed JSON for {func_name}")
            continue
        
        print(f"  Loaded from: {os.path.basename(filepath)}")
        disasm = data.get('disassembly', [])
        print(f"  Function has {len(disasm)} instructions")
        
        # Analyze each read location
        func_findings = []
        for read_addr in read_addrs:
            findings = analyze_after_read(disasm, read_addr)
            if findings:
                func_findings.extend(findings)
        
        if func_findings:
            all_findings[func_name] = func_findings
    
    # Summary
    print("\n" + "=" * 80)
    print("SUMMARY OF FINDINGS")
    print("=" * 80)
    
    if not all_findings:
        print("\nNo view key dispatch patterns found in analyzed functions.")
        print("The dispatch may be:")
        print("1. In a function we haven't analyzed yet")
        print("2. Using an indirect mechanism (function pointers, callbacks)")
        print("3. Happening via a different input mechanism")
    else:
        for func_name, findings in all_findings.items():
            print(f"\n{func_name}:")
            for finding in findings:
                print(f"  {finding}")
    
    # Save results
    output_file = r"c:\Users\ybarnoy\projects\falcon3\analysis\dgroup\view_dispatch_findings.json"
    with open(output_file, 'w') as f:
        json.dump(all_findings, f, indent=2)
    
    print(f"\n\nResults saved to: {output_file}")

if __name__ == "__main__":
    main()
