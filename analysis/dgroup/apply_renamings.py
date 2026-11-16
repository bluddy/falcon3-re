"""
Robust renaming script that handles errors and logs progress.
"""

import idc
import idaapi
import json

def safe_rename(addr, new_name, old_name_expected=None):
    """Safely rename, handling errors."""
    try:
        old_name = idc.get_name(addr)
        
        # Try rename
        flags = idc.SN_NOWARN | idc.SN_NOCHECK
        result = idc.set_name(addr, new_name, flags)
        
        return {
            'addr': f'0x{addr:X}',
            'old_name': old_name,
            'new_name': new_name,
            'success': result,
            'error': None
        }
    except Exception as e:
        return {
            'addr': f'0x{addr:X}',
            'old_name': old_name_expected or '?',
            'new_name': new_name,
            'success': False,
            'error': str(e)
        }

def safe_comment(addr, comment, repeatable=False):
    """Safely add comment."""
    try:
        idc.set_cmt(addr, comment, 1 if repeatable else 0)
        return {'addr': f'0x{addr:X}', 'success': True, 'comment': comment}
    except Exception as e:
        return {'addr': f'0x{addr:X}', 'success': False, 'error': str(e)}

def main():
    idaapi.auto_wait()
    
    print("Starting renamings...")
    
    results = {
        'variables': [],
        'functions': [],
        'comments': []
    }
    
    # Variables
    print("\nRenaming variables...")
    variables = [
        (0x79F16, "current_view_index"),
        (0x107762, "view_pipeline_mode"),
        (0x79B66, "input_scan_code_queue"),
    ]
    
    for addr, name in variables:
        result = safe_rename(addr, name)
        results['variables'].append(result)
        status = "✓" if result['success'] else "✗"
        print(f"  {status} 0x{addr:X}: {result['old_name']} -> {name}")
    
    # Functions
    print("\nRenaming functions...")
    functions = [
        (0x156945, "view_rendering_dispatcher"),
        (0x12DB63, "tactical_screen_coordinator"),
        (0x182390, "game_mode_r53_coordinator"),
    ]
    
    for addr, name in functions:
        result = safe_rename(addr, name)
        results['functions'].append(result)
        status = "✓" if result['success'] else "✗"
        print(f"  {status} 0x{addr:X}: {result['old_name']} -> {name}")
    
    # Key comments
    print("\nAdding comments...")
    comments = [
        (0x130709, "NUMBER KEY CAPTURE: Scan for keys 1-9,0 (scan 0x02-0x0B)", True),
        (0x130749, "Store scan code in input_scan_code_queue", False),
        (0x12DFD6, "INPUT DISPATCHER: Search table, dispatch via jmp [bx+8]", True),
        (0x182476, "INPUT DISPATCHER: Handle view keys (scan 0x03,0x04)", True),
        (0x156DC5, "VIEW DISPATCHER: Read current_view_index (0-9), jump table", True),
        (0x156DD4, "JUMP TABLE: 10 view handlers", True),
        (0x108BC5, "Read view_pipeline_mode (0=sim? 1=ACMI?)", True),
    ]
    
    for addr, comment, repeatable in comments:
        result = safe_comment(addr, comment, repeatable)
        results['comments'].append(result)
        status = "✓" if result['success'] else "✗"
        print(f"  {status} 0x{addr:X}: {comment[:50]}...")
    
    # Save results
    output_file = r"c:\Users\ybarnoy\projects\falcon3\analysis\dgroup\renaming_results.json"
    with open(output_file, 'w') as f:
        json.dump(results, f, indent=2)
    
    # Summary
    var_success = sum(1 for r in results['variables'] if r['success'])
    func_success = sum(1 for r in results['functions'] if r['success'])
    comm_success = sum(1 for r in results['comments'] if r['success'])
    
    print(f"\nSummary:")
    print(f"  Variables: {var_success}/{len(results['variables'])}")
    print(f"  Functions: {func_success}/{len(results['functions'])}")
    print(f"  Comments: {comm_success}/{len(results['comments'])}")
    print(f"\nResults saved to: {output_file}")
    
    idc.qexit(0)

if __name__ == "__main__":
    main()
