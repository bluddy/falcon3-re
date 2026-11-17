"""
Extract the far object dispatch table at cs:off_26426.
This table contains function pointers for drawing different entity types.
"""

import idc
import idaapi
import idautils
import json
from pathlib import Path

def main():
    print("Waiting for auto-analysis...")
    idaapi.auto_wait()
    print("Auto-analysis complete\n")
    
    # The dispatch table address from farobj_record_step
    table_addr = 0x26426
    
    print(f"=== Extracting Dispatch Table at 0x{table_addr:X} ===\n")
    
    # Read table entries (word-sized function pointers)
    table_entries = []
    addr = table_addr
    
    # Read up to 64 entries (or until we hit invalid data)
    for i in range(64):
        # Read word at this address
        value = idc.get_wide_word(addr)
        
        # Check if this looks like a valid code pointer
        # (should be in reasonable code range, not 0xFFFF, etc.)
        if value == 0xFFFF or value == 0:
            break
        
        # Get name of target if it's a function
        target_name = idc.get_func_name(value)
        if not target_name:
            target_name = f"sub_{value:X}"
        
        # Get any comment
        comment = idc.get_cmt(addr, 0) or idc.get_cmt(addr, 1)
        
        entry = {
            'index': i,
            'offset': i * 2,  # Word offsets
            'address': hex(addr),
            'target': hex(value),
            'target_name': target_name
        }
        
        if comment:
            entry['comment'] = comment
        
        table_entries.append(entry)
        
        print(f"[{i:2}] +0x{i*2:02X} @ 0x{addr:X} -> 0x{value:04X} {target_name}")
        
        addr += 2  # Next word
    
    print(f"\nFound {len(table_entries)} table entries\n")
    
    # Also check the bx calculation to understand indexing
    print("=== Analysis ===\n")
    print("From farobj_record_step line 132-137:")
    print("  mov     bx, es:[bx+6]      ; Get dispatch index")
    print("  test    bx, 3               ; Check if aligned?")
    print("  jnz     short skip")
    print("  cmp     bx, 34h             ; Max index = 0x34 (52 decimal)")
    print("  ja      short skip")
    print("  call    cs:off_26426[bx]    ; DISPATCH!")
    print()
    print(f"Max index: 0x34 (52 decimal) -> table entry 52/2 = 26")
    print(f"Table entries found: {len(table_entries)}")
    print()
    
    # Save results
    results = {
        'table_address': hex(table_addr),
        'entry_count': len(table_entries),
        'entries': table_entries,
        'notes': {
            'index_source': 'Loaded from entity record offset +6',
            'index_check': 'Must be word-aligned (test bx, 3)',
            'max_index': '0x34 (52 decimal)',
            'dispatch': 'call cs:off_26426[bx]'
        }
    }
    
    output_json = Path(__file__).parent / "farobj_dispatch_table.json"
    with open(output_json, 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"✓ JSON saved to: {output_json}\n")
    
    # Also save as text
    output_txt = Path(__file__).parent / "farobj_dispatch_table.txt"
    with open(output_txt, 'w') as f:
        f.write("=" * 80 + "\n")
        f.write("Far Object Dispatch Table\n")
        f.write("=" * 80 + "\n")
        f.write(f"Address: 0x{table_addr:X}\n")
        f.write(f"Entries: {len(table_entries)}\n")
        f.write("=" * 80 + "\n\n")
        
        f.write("Index | Offset | Address  | Target   | Function Name\n")
        f.write("------|--------|----------|----------|--------------------------------\n")
        
        for entry in table_entries:
            idx = entry['index']
            off = entry['offset']
            addr_str = entry['address']
            tgt = entry['target']
            name = entry['target_name']
            
            f.write(f"{idx:5} | 0x{off:04X} | {addr_str} | {tgt} | {name}\n")
            
            if 'comment' in entry:
                f.write(f"      |        |          |          | // {entry['comment']}\n")
        
        f.write("\n")
        f.write("=" * 80 + "\n")
        f.write("Usage (from farobj_record_step):\n")
        f.write("=" * 80 + "\n")
        f.write("  mov     bx, es:[bx+6]       ; Get dispatch index from entity+6\n")
        f.write("  test    bx, 3                ; Check word alignment\n")
        f.write("  jnz     short skip           ; Skip if not aligned\n")
        f.write("  cmp     bx, 34h              ; Check max index (52)\n")
        f.write("  ja      short skip           ; Skip if too large\n")
        f.write("  call    cs:off_26426[bx]     ; Call handler from table\n")
        f.write("\n")
        f.write(f"Max table index: 0x34 (52) = entry {52//2} if word-aligned\n")
        f.write(f"Table entries found: {len(table_entries)}\n")
    
    print(f"✓ Text saved to: {output_txt}\n")
    
    idc.qexit(0)

if __name__ == "__main__":
    main()
