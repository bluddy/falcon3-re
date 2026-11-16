"""
Dump raw bytes from the jump tables to understand their structure.
"""

import idc
import idaapi

def dump_bytes(addr, count, label):
    """Dump raw bytes from an address."""
    
    print(f"\n[*] {label} at 0x{addr:X}")
    print(f"    Dumping {count} bytes")
    print()
    
    # Dump as hex
    print("    Hex dump:")
    for offset in range(0, count, 16):
        line_addr = addr + offset
        print(f"    0x{line_addr:06X}:  ", end="")
        
        # Hex bytes
        hex_bytes = []
        for i in range(16):
            if offset + i < count:
                byte = idc.get_wide_byte(addr + offset + i)
                hex_bytes.append(f"{byte:02X}")
            else:
                hex_bytes.append("  ")
        print(" ".join(hex_bytes[:8]), " ", " ".join(hex_bytes[8:]), "  ", end="")
        
        # ASCII
        for i in range(16):
            if offset + i < count:
                byte = idc.get_wide_byte(addr + offset + i)
                if 32 <= byte <= 126:
                    print(chr(byte), end="")
                else:
                    print(".", end="")
        print()
    
    # Dump as words
    print("\n    Word dump:")
    for offset in range(0, count, 2):
        word_addr = addr + offset
        word = idc.get_wide_word(word_addr)
        print(f"    [+0x{offset:02X}] 0x{word_addr:06X}: 0x{word:04X}  ({word:5d})")
    
    # Try to interpret as code
    print("\n    Disassembly:")
    ea = addr
    for i in range(20):  # Show 20 instructions
        insn = idc.GetDisasm(ea)
        print(f"    0x{ea:06X}: {insn}")
        ea = idc.next_head(ea)
    
    return

def main():
    idaapi.auto_wait()
    
    print("=" * 80)
    print("DUMPING JUMP TABLE BYTES")
    print("=" * 80)
    
    # Table 1 address (from previous script)
    table1 = 0x12F9FC
    dump_bytes(table1, 64, "Table 1 (R29)")
    
    # Table 2 address
    table2 = 0x1852D5
    dump_bytes(table2, 64, "Table 2 (R53)")
    
    idc.qexit(0)

if __name__ == "__main__":
    main()
