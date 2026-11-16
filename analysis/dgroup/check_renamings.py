"""
Check if renamings were applied successfully.
"""

import idc
import idautils
import json

def main():
    print("Checking renamed functions...")
    
    targets = [
        (0x13DD40, "signed_mul_32bit"),
        (0x12805C, "mouse_input_sync_wait"),
        (0x13DD83, "signed_div_32bit"),
        (0x02C59F, "overlay_bridge_to_66e97"),
        (0x02C4FF, "overlay_bridge_to_r30_state_init"),
        (0x13DE3A, "table_dispatch_interpreter"),
        (0x088384, "dynamic_farcall_patcher"),
        (0x02C351, "overlay_bridge_to_66a05"),
    ]
    
    results = []
    for ea, expected_name in targets:
        actual_name = idc.get_func_name(ea)
        status = "✓" if actual_name == expected_name else "✗"
        results.append({
            'address': ea,
            'expected': expected_name,
            'actual': actual_name,
            'status': status
        })
        print(f"{status} 0x{ea:06X}: {actual_name}")
        if actual_name != expected_name:
            print(f"  Expected: {expected_name}")
    
    # Save results
    output_file = r'C:\Users\ybarnoy\projects\falcon3\analysis\renaming_check_results.json'
    with open(output_file, 'w') as f:
        json.dump(results, f, indent=2)
    
    success_count = sum(1 for r in results if r['status'] == '✓')
    print(f"\n✓ {success_count}/{len(results)} renamings confirmed")

if __name__ == '__main__':
    main()

idc.qexit(0)
