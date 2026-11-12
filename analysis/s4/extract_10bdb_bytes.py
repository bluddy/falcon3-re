"""
Extract bytecode at 0x10BDB from the executable.
IDA address 0x10BDB = file offset calculation needed.

IDA load base = 0x10000
File header size = 0x2C00 (from FALCONCD.EXE.yaml)
So: file_offset = ida_addr - 0x10000 + 0x2C00 = ida_addr + 0x1C00
"""
from pathlib import Path

ida_addr = 0x10BDB
file_offset = ida_addr + 0x1C00  # 0x10BDB + 0x1C00 = 0x127DB

# Read from the executable
exe_path = Path('../../game/FALCONCD.EXE')
if not exe_path.exists():
    exe_path = Path('../../analysis/ida_falconcd/FALCONCD.EXE')

if exe_path.exists():
    with open(exe_path, 'rb') as f:
        f.seek(file_offset)
        bytecode = f.read(64)  # Read 64 bytes
    
    print(f"Bytecode at IDA 0x{ida_addr:05X} (file offset 0x{file_offset:05X}):")
    print(f"\nHex dump:")
    for i in range(0, min(64, len(bytecode)), 16):
        hex_str = ' '.join(f"{bytecode[i+j]:02X}" for j in range(min(16, len(bytecode)-i)))
        ascii_str = ''.join(chr(bytecode[i+j]) if 32 <= bytecode[i+j] < 127 else '.' for j in range(min(16, len(bytecode)-i)))
        print(f"  {i:04X}: {hex_str:<48} {ascii_str}")
    
    # Try to identify patterns
    print(f"\nPattern analysis:")
    
    # Check for function prologue
    if bytecode[0:2] == b'\x55\x8b':  # push bp; mov bp, sp
        print("  ✓ Standard function prologue (push bp; mov bp,sp)")
    elif bytecode[0:1] == b'\xc8':  # enter
        print("  ✓ ENTER instruction prologue")
    elif bytecode[0:3] == b'\x1e\x56\x8b' or bytecode[0:2] == b'\x1e\x57':
        print("  ✓ Manual prologue (push ds/es; push si/di)")
    
    # Check for retf
    if b'\xcb' in bytecode[:32]:
        retf_pos = bytecode[:32].find(b'\xcb')
        print(f"  ✓ RETF found at offset +0x{retf_pos:X}")
        print(f"    Likely function size: {retf_pos + 1} bytes")
    elif b'\xc3' in bytecode[:32]:
        ret_pos = bytecode[:32].find(b'\xc3')
        print(f"  ✓ RET (near) found at offset +0x{ret_pos:X}")
    
    # Manual disassembly of first few instructions
    print(f"\nManual disassembly (first ~20 bytes):")
    
    i = 0
    while i < min(20, len(bytecode)):
        b = bytecode[i]
        
        # Common single-byte opcodes
        if b == 0x1E:
            print(f"    {i:04X}: 1E              push ds")
            i += 1
        elif b == 0x1F:
            print(f"    {i:04X}: 1F              pop ds")
            i += 1
        elif b == 0x50:
            print(f"    {i:04X}: 50              push ax")
            i += 1
        elif b == 0x51:
            print(f"    {i:04X}: 51              push cx")
            i += 1
        elif b == 0x52:
            print(f"    {i:04X}: 52              push dx")
            i += 1
        elif b == 0x53:
            print(f"    {i:04X}: 53              push bx")
            i += 1
        elif b == 0x56:
            print(f"    {i:04X}: 56              push si")
            i += 1
        elif b == 0x57:
            print(f"    {i:04X}: 57              push di")
            i += 1
        elif b == 0x58:
            print(f"    {i:04X}: 58              pop ax")
            i += 1
        elif b == 0x59:
            print(f"    {i:04X}: 59              pop cx")
            i += 1
        elif b == 0x5E:
            print(f"    {i:04X}: 5E              pop si")
            i += 1
        elif b == 0x5F:
            print(f"    {i:04X}: 5F              pop di")
            i += 1
        elif b == 0x8B and i+1 < len(bytecode):
            # mov reg, r/m
            modrm = bytecode[i+1]
            print(f"    {i:04X}: 8B {modrm:02X}            mov ...")
            i += 2
        elif b == 0x89 and i+1 < len(bytecode):
            # mov r/m, reg
            modrm = bytecode[i+1]
            print(f"    {i:04X}: 89 {modrm:02X}            mov ...")
            i += 2
        elif b == 0xA1 and i+2 < len(bytecode):
            # mov ax, [addr]
            addr = int.from_bytes(bytecode[i+1:i+3], 'little')
            print(f"    {i:04X}: A1 {addr:04X}        mov ax, [0x{addr:04X}]")
            i += 3
        elif b == 0xA3 and i+2 < len(bytecode):
            # mov [addr], ax
            addr = int.from_bytes(bytecode[i+1:i+3], 'little')
            print(f"    {i:04X}: A3 {addr:04X}        mov [0x{addr:04X}], ax")
            i += 3
        elif b == 0xC3:
            print(f"    {i:04X}: C3              ret (near)")
            i += 1
        elif b == 0xCB:
            print(f"    {i:04X}: CB              retf")
            i += 1
            break
        else:
            print(f"    {i:04X}: {b:02X}              (skipping)")
            i += 1
    
    # Save to file for further analysis
    output_path = Path('sub_10BDB_bytecode.bin')
    with open(output_path, 'wb') as f:
        f.write(bytecode)
    
    print(f"\nSaved {len(bytecode)} bytes to {output_path}")
    
else:
    print(f"ERROR: FALCONCD.EXE not found at {exe_path}")
