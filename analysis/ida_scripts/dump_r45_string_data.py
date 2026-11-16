"""
Dump the actual string data at the addresses we found:
- 0x1519B2: '.`SQUADRON'
- 0x151896: '.`PILOT INFORMATION'
- 0x1515BD: '.`COMMS.'
- 0x1516B0: '.`DONE'

And search nearby for more strings.
"""
import idaapi
import idautils
import idc

def dump_string_area(start_addr, length=100):
    """Dump bytes around an address to find strings."""
    data = idc.get_bytes(start_addr, length)
    if data:
        # Try to decode as ASCII
        try:
            decoded = data.decode('ascii', errors='replace')
            return decoded
        except:
            return None
    return None

def find_strings_in_range(start, end):
    """Find all printable strings in a range."""
    strings = []
    current_string = ""
    string_start = None
    
    for ea in range(start, end):
        byte_val = idc.get_wide_byte(ea)
        
        if byte_val == 0:
            # Null terminator
            if len(current_string) > 3:  # Min 4 chars
                strings.append({
                    "address": string_start,
                    "value": current_string,
                    "end": ea
                })
            current_string = ""
            string_start = None
        elif 32 <= byte_val < 127:  # Printable ASCII
            if string_start is None:
                string_start = ea
            current_string += chr(byte_val)
        else:
            # Non-printable
            if len(current_string) > 3:
                strings.append({
                    "address": string_start,
                    "value": current_string,
                    "end": ea - 1
                })
            current_string = ""
            string_start = None
    
    return strings

def main():
    # Known string addresses from dispatcher
    known_strings = [
        (0x1519B2, ".`SQUADRON"),
        (0x151896, ".`PILOT INFORMATION"),
        (0x1515BD, ".`COMMS."),
        (0x1516B0, ".`DONE")
    ]
    
    print("=== KNOWN STRINGS ===")
    for addr, expected in known_strings:
        # Dump 50 bytes at each location
        data = dump_string_area(addr, 50)
        if data:
            print(f"0x{addr:X}: {repr(data[:30])}")
            print(f"  Expected: {expected}")
        else:
            print(f"0x{addr:X}: FAILED TO READ")
        print()
    
    # Find the segment these strings are in
    seg = idaapi.getseg(0x1519B2)
    if seg:
        seg_name = idaapi.get_segm_name(seg)
        print(f"\n=== STRINGS SEGMENT: {seg_name} ===")
        print(f"Range: 0x{seg.start_ea:X} - 0x{seg.end_ea:X}")
        print(f"Size: {seg.size()} bytes")
        print()
        
        # Search for all strings in this segment
        print("Searching for all strings in segment...")
        all_strings = find_strings_in_range(seg.start_ea, seg.end_ea)
        
        print(f"\nFound {len(all_strings)} strings total")
        print("\nStrings containing menu-related words:")
        
        keywords = ["SQUADRON", "PILOT", "COMMS", "DONE", "SELECT", "ROSTER",
                    "CALLSIGN", "RANK", "STATUS", "READY", "MISSION", "KILL",
                    "NAME", "FLIGHT", "WING"]
        
        relevant = []
        for s in all_strings:
            for keyword in keywords:
                if keyword in s["value"].upper():
                    relevant.append(s)
                    print(f"  0x{s['address']:X}: '{s['value']}'")
                    break
        
        # Save all strings
        output_path = r"C:\Users\ybarnoy\projects\falcon3\analysis\ida_scripts\r45_all_strings.txt"
        with open(output_path, 'w') as f:
            f.write(f"=== ALL STRINGS IN SEGMENT {seg_name} ===\n\n")
            for s in all_strings:
                f.write(f"0x{s['address']:X}: {s['value']}\n")
        
        print(f"\nAll strings saved to {output_path}")
        
        # Save relevant strings
        rel_path = r"C:\Users\ybarnoy\projects\falcon3\analysis\ida_scripts\r45_relevant_strings.txt"
        with open(rel_path, 'w') as f:
            f.write("=== R45 MENU RELEVANT STRINGS ===\n\n")
            for s in relevant:
                f.write(f"0x{s['address']:X}: {s['value']}\n")
        
        print(f"Relevant strings saved to {rel_path}")

if __name__ == "__main__":
    main()
