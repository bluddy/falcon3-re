#!/usr/bin/env python3
"""Analyze supply data by looking at actual hex patterns."""

def main():
    with open('../game/SQUAD0.SQU', 'rb') as f:
        data = f.read()
    
    supply_data = data[0x7F8:0xA8F]
    print(f'Supply data: {len(supply_data)} bytes\n')
    
    # Show hex with markers for FF patterns
    print('Looking for 0xFF 0xFF patterns (potential record boundaries):')
    for i in range(len(supply_data) - 1):
        if supply_data[i] == 0xFF and supply_data[i+1] == 0xFF:
            print(f'  FF FF at 0x{0x7F8+i:04X} (offset {i} in supply block)')
    print()
    
    # Try interpreting as: each pilot has some status bytes, then repeats callsign/nickname
    # Main pilot record: 66 bytes at 0x3C + i*66
    # Extended record: ??? bytes at 0x7F8 + i*???
    
    # Let's manually parse first few records
    print('Manual parsing of first 3 extended records:')
    print()
    
    # Record 0 starts at 0x7F8
    print('Record 0 @ 0x7F8:')
    print(' ', ' '.join(f'{supply_data[i]:02X}' for i in range(0, 16)))
    print(' ', ' '.join(f'{supply_data[i+16]:02X}' for i in range(0, 16)))
    print(' ', ' '.join(f'{supply_data[i+32]:02X}' for i in range(0, 10)))
    print()
    
    # Decode: FF 1D 00 = header?
    # Then "GATTERA\x00..." = callsign (15 bytes)
    # Then "DAFFY\x00..." = nickname (15 bytes)
    # Then "RQPd\x00..." = ID? (looks like 4 bytes)
    # Then padding to next FF FF?
    
    rec0_callsign = supply_data[3:18].decode('ascii', errors='ignore').rstrip('\x00')
    rec0_nickname = supply_data[19:34].decode('ascii', errors='ignore').rstrip('\x00')
    rec0_id = supply_data[35:39].hex()
    print(f'  Callsign: "{rec0_callsign}"')
    print(f'  Nickname: "{rec0_nickname}"')
    print(f'  ID: {rec0_id}')
    print()
    
    # Find next FF FF to see record length
    next_ff = 39
    while next_ff < len(supply_data) - 1:
        if supply_data[next_ff] == 0xFF and supply_data[next_ff+1] == 0xFF:
            break
        next_ff += 1
    print(f'  Next FF FF at offset {next_ff} -> record 0 is {next_ff} bytes')
    print()
    
    # Record 1
    rec1_start = next_ff
    print(f'Record 1 @ 0x{0x7F8+rec1_start:04X} (offset {rec1_start}):')
    print(' ', ' '.join(f'{supply_data[rec1_start+i]:02X}' for i in range(min(16, len(supply_data)-rec1_start))))
    if rec1_start + 16 < len(supply_data):
        print(' ', ' '.join(f'{supply_data[rec1_start+16+i]:02X}' for i in range(min(16, len(supply_data)-rec1_start-16))))
    if rec1_start + 32 < len(supply_data):
        print(' ', ' '.join(f'{supply_data[rec1_start+32+i]:02X}' for i in range(min(16, len(supply_data)-rec1_start-32))))
    
    # Try same parsing
    if rec1_start + 39 < len(supply_data):
        rec1_callsign = supply_data[rec1_start+3:rec1_start+18].decode('ascii', errors='ignore').rstrip('\x00')
        rec1_nickname = supply_data[rec1_start+19:rec1_start+34].decode('ascii', errors='ignore').rstrip('\x00')
        rec1_id = supply_data[rec1_start+35:rec1_start+39].hex()
        print(f'  Callsign: "{rec1_callsign}"')
        print(f'  Nickname: "{rec1_nickname}"')
        print(f'  ID: {rec1_id}')

if __name__ == '__main__':
    main()
