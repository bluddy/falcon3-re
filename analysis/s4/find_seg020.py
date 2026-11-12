"""Find seg020 or equivalent in segment_map.json"""
import json

with open("segment_map.json") as f:
    data = json.load(f)

# Find segment containing 0x20BDB (view_projection)
target_addr = 0x20BDB
print(f"Looking for segment containing 0x{target_addr:X} (view_projection)...")

for seg in data['segments']:
    if seg['start_ea'] <= target_addr < seg['end_ea']:
        print(f"\nFound: {seg['name']}")
        print(f"  Range: 0x{seg['start_ea']:X} - 0x{seg['end_ea']:X}")
        print(f"  Size: {seg['end_ea'] - seg['start_ea']} bytes")
        print(f"  Selector: 0x{seg['selector']:X}")
        
        # Calculate offset
        offset = target_addr - seg['start_ea']
        print(f"\n  0x20BDB is at offset 0x{offset:X} within this segment")
        print(f"  Segment:offset = {seg['selector']:04X}:{offset:04X}")
        
        # Find more key addresses in this segment
        key_addrs = {
            0x248D1: "fixed_vec3_transform_es",
            0x256A3: "sub_256A3",
            0x21ECF: "abs helper (seg020:1A2F = 0x21ECF)",
        }
        
        print(f"\n  Other key addresses in {seg['name']}:")
        for addr, name in key_addrs.items():
            if seg['start_ea'] <= addr < seg['end_ea']:
                off = addr - seg['start_ea']
                print(f"    0x{addr:X} ({name}) = offset 0x{off:X}")

print(f"\nTotal segments in database: {len(data['segments'])}")
