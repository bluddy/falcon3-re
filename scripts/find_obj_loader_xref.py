with open('game/FALCONCD.EXE', 'rb') as f:
    exe = f.read()

# Let's search for references to offset of OBJECTS or FalcObj.Bin
# What is the offset in segment?
# Let's see the relocation table or search for 16-bit word matching the offset.
# Offset of b"OBJECTS\x00" is 0x26ac0.
# If DS is around 0x1000...
# Let's search for where 0x26ac0 appears or where strings around here appear.
for target_name, target_pos in [("OBJECTS", exe.find(b"OBJECTS\x00")), ("FalcObj", exe.find(b"FalcObj.Bin")), ("FSXObj", exe.find(b"FSXObj.Bin"))]:
    print(f"{target_name} at file offset {hex(target_pos)}")
    # In DOS exe, header is 0x200 (512 bytes) usually.
    # If file offset is 0x26ac0, image offset is 0x268c0.
    # Segment:offset might be e.g. 0x2000:0x68c0 or similar.
    # Let's search for the low 16 bits of target_pos - 0x200:
    for base_seg in range(0x1000, 0x3000, 0x100):
        img_off = target_pos - 0x200
        off = img_off - (base_seg << 4)
        if 0 <= off < 0x10000:
            off_bytes = off.to_bytes(2, 'little')
            # search for off_bytes in exe
            count = exe.count(off_bytes)
            # print if small count
            # but let's check xrefs specifically
