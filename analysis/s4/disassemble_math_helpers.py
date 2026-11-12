"""
Manual disassembly of math helper functions.

Let's decode the key instructions to understand what each function does.
"""

import json

# Load extracted bytecode
with open('math_helper_bytecode.json') as f:
    helpers = json.load(f)

print("=" * 70)
print("Math Helper Manual Disassembly")
print("=" * 70)

def simple_disasm(bytecode_hex, addr):
    """Simple x86 16-bit disassembler for common instructions."""
    bytecode = bytes.fromhex(bytecode_hex)
    lines = []
    i = 0
    
    while i < len(bytecode):
        b = bytecode[i]
        line = f"  {addr+i:05X}: "
        
        # Single-byte instructions
        if b == 0xC3:
            lines.append(line + "C3           ret")
            i += 1
        elif b == 0xCB:
            lines.append(line + "CB           retf")
            i += 1
        elif b == 0x06:
            lines.append(line + "06           push es")
            i += 1
        elif b == 0x07:
            lines.append(line + "07           pop es")
            i += 1
        elif b == 0x1E:
            lines.append(line + "1E           push ds")
            i += 1
        elif b == 0x1F:
            lines.append(line + "1F           pop ds")
            i += 1
        elif b == 0x16:
            lines.append(line + "16           push ss")
            i += 1
        elif b == 0x9D:
            lines.append(line + "9D           popf")
            i += 1
        elif b == 0x50:
            lines.append(line + "50           push ax")
            i += 1
        elif b == 0x52:
            lines.append(line + "52           push dx")
            i += 1
        elif b == 0x59:
            lines.append(line + "59           pop cx")
            i += 1
        elif b == 0x5B:
            lines.append(line + "5B           pop bx")
            i += 1
        elif b == 0x5E:
            lines.append(line + "5E           pop si")
            i += 1
        elif b == 0x5F:
            lines.append(line + "5F           pop di")
            i += 1
        elif b == 0x40:
            lines.append(line + "40           inc ax")
            i += 1
        elif b == 0x99:
            lines.append(line + "99           cwd (sign extend ax to dx:ax)")
            i += 1
        elif b == 0xC9:
            lines.append(line + "C9           leave")
            i += 1
        
        # MOV immediate to register
        elif b >= 0xB0 and b <= 0xBF:
            reg = ['al','cl','dl','bl','ah','ch','dh','bh','ax','cx','dx','bx','sp','bp','si','di'][b-0xB0]
            if b < 0xB8:  # 8-bit
                if i + 1 < len(bytecode):
                    val = bytecode[i+1]
                    lines.append(line + f"{b:02X} {val:02X}        mov {reg}, 0x{val:02X}")
                    i += 2
                else:
                    i += 1
            else:  # 16-bit
                if i + 2 < len(bytecode):
                    val = bytecode[i+1] + (bytecode[i+2] << 8)
                    lines.append(line + f"{b:02X} {bytecode[i+1]:02X} {bytecode[i+2]:02X}     mov {reg}, 0x{val:04X}")
                    i += 3
                else:
                    i += 1
        
        # MOV r/m, r  or  MOV r, r/m (8B/89)
        elif b in [0x8B, 0x89]:
            if i + 1 < len(bytecode):
                modrm = bytecode[i+1]
                mod = (modrm >> 6) & 3
                reg = (modrm >> 3) & 7
                rm = modrm & 7
                
                regs = ['ax','cx','dx','bx','sp','bp','si','di']
                
                if mod == 0 and rm == 6:  # Direct address [xxxx]
                    if i + 3 < len(bytecode):
                        addr_val = bytecode[i+2] + (bytecode[i+3] << 8)
                        direction = "to" if b == 0x89 else "from"
                        lines.append(line + f"{b:02X} {modrm:02X} {bytecode[i+2]:02X} {bytecode[i+3]:02X}  mov [{direction}] {regs[reg]}, [0x{addr_val:04X}]")
                        i += 4
                    else:
                        i += 2
                elif mod == 1:  # [reg + disp8]
                    if i + 2 < len(bytecode):
                        disp = bytecode[i+2]
                        if disp >= 128:
                            disp = disp - 256
                        rm_str = ['bx+si','bx+di','bp+si','bp+di','si','di','bp','bx'][rm]
                        direction = "from" if b == 0x8B else "to"
                        lines.append(line + f"{b:02X} {modrm:02X} {bytecode[i+2]:02X}     mov {regs[reg]}, [{rm_str}{disp:+d}]  ; {direction}")
                        i += 3
                    else:
                        i += 2
                elif mod == 3:  # Register to register
                    direction = "from" if b == 0x8B else "to"
                    lines.append(line + f"{b:02X} {modrm:02X}        mov {regs[reg]}, {regs[rm]}  ; {direction}")
                    i += 2
                else:
                    lines.append(line + f"{b:02X} {modrm:02X}        mov (complex)")
                    i += 2
            else:
                i += 1
        
        # Segment override: ES: (26)
        elif b == 0x26:
            lines.append(line + "26           ES:")
            i += 1
        
        # Segment override: CS: (2E)
        elif b == 0x2E:
            lines.append(line + "2E           CS:")
            i += 1
        
        # CALL near rel16 (E8)
        elif b == 0xE8:
            if i + 2 < len(bytecode):
                offset = bytecode[i+1] + (bytecode[i+2] << 8)
                if offset >= 0x8000:
                    offset = offset - 0x10000
                target = addr + i + 3 + offset
                lines.append(line + f"E8 {bytecode[i+1]:02X} {bytecode[i+2]:02X}     call 0x{target:05X} (rel {offset:+d})")
                i += 3
            else:
                i += 1
        
        # JMP short (EB)
        elif b == 0xEB:
            if i + 1 < len(bytecode):
                offset = bytecode[i+1]
                if offset >= 128:
                    offset = offset - 256
                target = addr + i + 2 + offset
                lines.append(line + f"EB {bytecode[i+1]:02X}        jmp short 0x{target:05X} (rel {offset:+d})")
                i += 2
            else:
                i += 1
        
        # JMP near (E9)
        elif b == 0xE9:
            if i + 2 < len(bytecode):
                offset = bytecode[i+1] + (bytecode[i+2] << 8)
                if offset >= 0x8000:
                    offset = offset - 0x10000
                target = addr + i + 3 + offset
                lines.append(line + f"E9 {bytecode[i+1]:02X} {bytecode[i+2]:02X}     jmp 0x{target:05X} (rel {offset:+d})")
                i += 3
            else:
                i += 1
        
        # Conditional jumps (7x)
        elif b >= 0x70 and b <= 0x7F:
            if i + 1 < len(bytecode):
                offset = bytecode[i+1]
                if offset >= 128:
                    offset = offset - 256
                target = addr + i + 2 + offset
                conds = ['jo','jno','jb','jae','je','jne','jbe','ja',
                         'js','jns','jp','jnp','jl','jge','jle','jg']
                cond = conds[b - 0x70]
                lines.append(line + f"{b:02X} {bytecode[i+1]:02X}        {cond} 0x{target:05X} (rel {offset:+d})")
                i += 2
            else:
                i += 1
        
        # Shift operations (D1)
        elif b == 0xD1:
            if i + 1 < len(bytecode):
                modrm = bytecode[i+1]
                op = (modrm >> 3) & 7
                rm = modrm & 7
                ops = ['rol','ror','rcl','rcr','shl','shr','sal','sar']
                regs = ['ax','cx','dx','bx','sp','bp','si','di']
                if (modrm >> 6) == 3:  # Register
                    lines.append(line + f"D1 {modrm:02X}        {ops[op]} {regs[rm]}, 1")
                else:
                    lines.append(line + f"D1 {modrm:02X}        {ops[op]} (mem), 1")
                i += 2
            else:
                i += 1
        
        # ADD/OR/ADC/SBB/AND/SUB/XOR/CMP (03, 0B, 13, 1B, 23, 2B, 33, 3B)
        elif b in [0x03, 0x0B, 0x13, 0x1B, 0x23, 0x2B, 0x33, 0x3B]:
            ops = {0x03:'add', 0x0B:'or', 0x13:'adc', 0x1B:'sbb', 
                   0x23:'and', 0x2B:'sub', 0x33:'xor', 0x3B:'cmp'}
            if i + 1 < len(bytecode):
                modrm = bytecode[i+1]
                lines.append(line + f"{b:02X} {modrm:02X}        {ops[b]} ...")
                i += 2
            else:
                i += 1
        
        # Unknown - just show hex
        else:
            hex_str = ' '.join(f'{bytecode[j]:02X}' for j in range(i, min(i+4, len(bytecode))))
            lines.append(line + f"{hex_str:<12} ???")
            i += 1
        
        # Limit output
        if len(lines) >= 20:
            lines.append(f"  ... ({len(bytecode) - i} bytes remaining)")
            break
    
    return '\n'.join(lines)

# Disassemble each helper
for helper in helpers:
    print(f"\n{'=' * 70}")
    print(f"{helper['segoff']} - {helper['analysis']}")
    print(f"Parent: {helper['parent']} +0x{helper['offset']:04X}")
    print(f"Size: {helper['size']} bytes")
    print('=' * 70)
    
    disasm = simple_disasm(helper['bytecode_hex'], helper['address'])
    print(disasm)

print("\n" + "=" * 70)
print("Analysis Summary")
print("=" * 70)

print("""
Based on the disassembly:

seg015:0C65 (21 bytes):
  - push ss; pop cx
  - mov ax, 0x7772
  - mov es, ax (setup segment)
  - Likely: setup helper or segment switcher

seg015:0C7A (97 bytes):
  - Large function with ES: overrides
  - Multiple jumps
  - Likely: complex computation or dispatcher

seg015:0CDB (21 bytes):
  - mov bh, 0; push ax; mov ax, bx; push dx
  - cwd (sign extend)
  - pop bx; pop cx
  - add cx, cx; adc dx, dx
  - Likely: 32-bit shift or multiply setup

seg015:0CF0 (97 bytes):
  - push [bp-4]
  - far call to 0x19940D94
  - pop cx; pop cx
  - Complex with multiple operations
  - Likely: composite math operation

seg015:0D51 (21 bytes):
  - call 0x1CBA7 (rel -2462)
  - add sp, 6 (cleanup)
  - jmp (large offset)
  - Likely: wrapper that calls another function

seg015:0D66 (64 bytes):
  - Multiple ES: overrides
  - Tests and conditional jumps
  - Likely: conditional math operation

seg017:01FE (30 bytes):
  - push es
  - shl bx, 2 (multiply by 4)
  - mov ax, 0x7772
  - mov es, ax
  - mov ax, [es:bx+0x0F36]
  - mov dx, [es:bx+0x0F34]
  - Likely: table lookup (4-byte entries)

seg017:021C (64 bytes):
  - Has IMUL instruction
  - Has LOOP instruction
  - Multiple segment accesses
  - Likely: multiply with accumulation (loop)

seg017:01E3 (19 bytes):
  - Very short
  - Compare and conditional jump
  - popf; pop di; pop si
  - leave; retf
  - Likely: epilogue/return path

seg020:1A2F (64 bytes):
  - cmp dx, cx; jae ...
  - xchg dx, cx
  - Multiple comparisons and conditionals
  - Likely: min/max or abs value calculation
""")
