"""
Simple handler examination - just look at the dispatcher jump targets.
"""

import idc
import idaapi
import json

def main():
    idaapi.auto_wait()
    
    print("="*80)
    print("EXAMINING VIEW HANDLERS - SIMPLE")
    print("="*80)
    
    # Look at the dispatcher jump instruction
    dispatcher_addr = 0x182476
    
    print(f"\nDisassembling around dispatcher at 0x{dispatcher_addr:X}:")
    print()
    
    # Show 50 instructions from dispatcher
    ea = dispatcher_addr
    for i in range(50):
        insn = idc.GetDisasm(ea)
        print(f"  0x{ea:X}: {insn}")
        
        # Look for the jump table instruction
        if 'jmp' in insn and 'ptr' in insn and '[bx' in insn:
            print(f"    ^^^ THIS IS THE JUMP TABLE ACCESS")
            
            # The next few addresses might be the handler targets
            print(f"\n  Following 20 instructions after jump table:")
            next_ea = idc.next_head(ea)
            for j in range(20):
                next_insn = idc.GetDisasm(next_ea)
                print(f"    0x{next_ea:X}: {next_insn}")
                next_ea = idc.next_head(next_ea)
            break
        
        ea = idc.next_head(ea)
    
    # Also check what handlers we found in the table
    print("\n" + "="*80)
    print("HANDLERS FROM TABLE (from previous analysis):")
    print("="*80)
    print("\nScan 0x03 (ground view) -> check addresses around 0x1823E5")
    print("Scan 0x04 (cockpit view) -> check addresses around 0x182408")
    print()
    
    # Look at these potential handler locations
    for addr, name in [(0x1823E5, "ground_view"), (0x182408, "cockpit_view")]:
        if idc.is_mapped(addr):
            print(f"\n[*] Checking {name} at 0x{addr:X}:")
            ea = addr
            for i in range(15):
                insn = idc.GetDisasm(ea)
                print(f"    0x{ea:X}: {insn}")
                ea = idc.next_head(ea)
        else:
            print(f"\n[!] Address 0x{addr:X} not mapped")
    
    idc.qexit(0)

if __name__ == "__main__":
    main()
