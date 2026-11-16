"""
Verify that structures and enums were created in IDA.
"""
import idc
import idaapi
import json

def main():
    print("=== VERIFYING STRUCTURES AND ENUMS ===\n")
    
    idaapi.auto_wait()
    
    results = {
        "enums": {},
        "structs": {}
    }
    
    # Check enums
    enum_names = ["PilotRank", "PilotStatus", "WingID", "TheaterID", "MissionType", 
                  "R45MenuState", "R57MenuState", "TimeOfDay", "WeatherCondition"]
    
    print("Checking Enums:")
    print("-" * 60)
    for enum_name in enum_names:
        enum_id = idc.get_enum(enum_name)
        if enum_id != idc.BADADDR:
            # Get member count
            count = idc.get_enum_size(enum_id)
            results["enums"][enum_name] = {
                "found": True,
                "id": enum_id,
                "size": count
            }
            print(f"✓ {enum_name}: Found (ID={enum_id}, {count} members)")
        else:
            results["enums"][enum_name] = {"found": False}
            print(f"✗ {enum_name}: NOT FOUND")
    
    # Check structs
    struct_names = ["PilotRecord", "ExtendedPilotRecord", "SquadronFile", "SquadronHeader",
                    "MenuElement", "FlightRecord", "LoadoutRecord"]
    
    print("\nChecking Structures:")
    print("-" * 60)
    for struct_name in struct_names:
        sid = idc.get_struc_id(struct_name)
        if sid != idc.BADADDR:
            # Get struct size
            size = idc.get_struc_size(sid)
            results["structs"][struct_name] = {
                "found": True,
                "id": sid,
                "size": size
            }
            print(f"✓ {struct_name}: Found (ID={sid}, size={size} bytes, 0x{size:X})")
        else:
            results["structs"][struct_name] = {"found": False}
            print(f"✗ {struct_name}: NOT FOUND")
    
    # Detailed check on PilotRecord
    print("\nDetailed PilotRecord Check:")
    print("-" * 60)
    sid = idc.get_struc_id("PilotRecord")
    if sid != idc.BADADDR:
        # Check specific fields
        fields = ["status_flags", "rank", "callsign", "nickname", "id_code",
                  "dogfighting_skill", "bombing_skill", "flying_skill", "fatigue_level"]
        
        for field_name in fields:
            offset = idc.get_member_offset(sid, field_name)
            if offset != -1:
                print(f"  ✓ {field_name} at offset 0x{offset:X}")
            else:
                print(f"  ✗ {field_name} NOT FOUND")
    
    # Summary
    enum_found = sum(1 for e in results["enums"].values() if e.get("found"))
    struct_found = sum(1 for s in results["structs"].values() if s.get("found"))
    
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    print(f"Enums: {enum_found}/{len(enum_names)} found")
    print(f"Structs: {struct_found}/{len(struct_names)} found")
    
    # Save results
    output_path = r"C:\Users\ybarnoy\projects\falcon3\analysis\structure_verification.json"
    with open(output_path, 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"\nResults saved to: {output_path}")
    
    idc.qexit(0)

if __name__ == "__main__":
    main()
