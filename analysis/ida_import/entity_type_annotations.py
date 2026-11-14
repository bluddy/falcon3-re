"""
IDA Python Script: Entity Type System Annotations
Falcon 3.0 Reverse Engineering Project

Purpose: Annotate entity type system discoveries in IDA database
Date: November 11, 2026
Session: AI System Analysis - Session 2

Usage:
1. Open FALCON.EXE in IDA Pro
2. File → Script file → Select this file
3. Script will rename fields and add comments
"""

import idaapi
import idc
import idautils

# ============================================================================
# Entity Type Enum
# ============================================================================

def create_entity_type_enum():
    """Create EntityType enum in IDA"""
    
    enum_id = idc.add_enum(-1, "EntityType", idaapi.hex_flag())
    
    if enum_id == idc.BADADDR:
        print("[!] EntityType enum already exists, retrieving...")
        enum_id = idc.get_enum("EntityType")
    
    # Add known type values
    types = [
        (0x10, "TYPE_GUIDED_MISSILE", "Guided missiles - skip AI state machine, always tracking"),
        (0x16, "TYPE_FRIENDLY_AIRCRAFT", "Friendly aircraft/wingmen - full AI, friendly fire protection"),
        (0x33, "TYPE_PLAYER_AIRCRAFT", "Player aircraft - special handling, enhanced physics"),
        (0xFF, "TYPE_INVALID", "Dead/destroyed entity marker"),
        
        # Likely types (ground/special)
        (0x03, "TYPE_GROUND_UNIT", "Ground units/vehicles (likely)"),
        (0x0B, "TYPE_SPECIAL_0B", "Special entity type 0x0B"),
        (0x0C, "TYPE_SPECIAL_0C", "Special entity type 0x0C"),
        (0x0D, "TYPE_SPECIAL_0D", "Special entity type 0x0D (SAM/AAA?)"),
        (0x0F, "TYPE_SPECIAL_0F", "Special entity type 0x0F"),
        (0x2B, "TYPE_SPECIAL_2B", "Special entity type 0x2B"),
        (0x2C, "TYPE_SPECIAL_2C", "Special entity type 0x2C"),
    ]
    
    for value, name, comment in types:
        idc.add_enum_member(enum_id, name, value, -1)
        print(f"[+] Added enum member: {name} = 0x{value:02X} - {comment}")
    
    return enum_id

# ============================================================================
# Function Annotations
# ============================================================================

def annotate_functions():
    """Add comments to key functions"""
    
    annotations = [
        # Entity initialization
        (0x3BB8F, "entity_init_from_data", "Initialize entity from data table"),
        (0x3BD6E, None, "Load entity data from table"),
        (0x3BD7E, None, "LOAD entity_type from data[+0x26], mask 0x3F"),
        (0x3BD82, None, "Mask type bits 0-5 only (bits 6-7 for flags?)"),
        (0x3BD8F, None, "Check game mode: 0=single player, 1+=multiplayer"),
        (0x3BD96, None, "Check if entity is player wingman (BP == ds:1360h)"),
        (0x3BD9C, None, "OVERRIDE: Force type = 0x16 (friendly) for player wingmen"),
        (0x3BD9E, None, "SET entity_type field [di+0x75]"),
        
        # Entity destruction
        (0x3BDB9, None, "Set entity_type = 0xFF (invalid/destroyed)"),
        
        # Behavior dispatcher - Type 0x33 (Player)
        (0x3CFA0, None, "Check entity_type == 0x33 (player aircraft)"),
        (0x3CFA6, None, "Type 0x33 special handler (player)"),
        (0x3D470, None, "Type 0x33 check (player) - skip certain logic"),
        (0x3D67D, None, "Type 0x33 check (player) - special path"),
        (0x3D830, None, "Type 0x33 check - use physics constant 0x0C00 (vs 0x0800)"),
        
        # Behavior dispatcher - Type 0x10 (Missiles)
        (0x3D042, None, "Check entity_type == 0x10 (guided missiles)"),
        (0x3D087, None, "Type 0x10 → skip AI state machine, go to tracking"),
        (0x3C269, None, "Type 0x10 check (missile dispatch)"),
        
        # Friendly fire - Type 0x16
        (0x3DEE6, None, "Get shooter entity_type"),
        (0x3DEE9, None, "Check entity_type == 0x16 (friendly) for fire restrictions"),
        (0x4D4B7, None, "Type 0x16 check - set friendly flag"),
        
        # Ground unit checks - Types 0x0B-0x0F, 0x2B-0x2C
        (0x39218, None, "Type 0x0B check - group with other special types"),
        (0x3921E, None, "Type 0x0C check - group with 0x0B"),
        (0x39224, None, "Type 0x2C check - special entity"),
        (0x3922A, None, "Type 0x2B check - special entity"),
        (0x39230, None, "Type 0x0D check - special entity (SAM/AAA?)"),
        (0x39236, None, "Type 0x0F check - special entity"),
        (0x3C892, None, "Type 0x0D check"),
        (0x3C898, None, "Type 0x0F check"),
        (0x42537, None, "Type 0x0D check"),
        
        # Other type checks
        (0x40EED, None, "Type >= 0x20 check - high-value entities?"),
    ]
    
    for addr, func_name, comment in annotations:
        if func_name:
            idc.set_name(addr, func_name, idc.SN_NOWARN)
            print(f"[+] Renamed function at 0x{addr:X}: {func_name}")
        
        if comment:
            idc.set_cmt(addr, comment, 0)  # 0 = regular comment
            print(f"[+] Added comment at 0x{addr:X}: {comment}")

# ============================================================================
# Structure Field Renaming
# ============================================================================

def create_entity_struct():
    """Create or update FarObjEntity structure"""
    
    # Note: This is a template - actual struct may already exist
    # Check if struct exists first
    sid = idc.get_struc_id("FarObjEntity")
    
    if sid == idc.BADADDR:
        print("[!] FarObjEntity struct not found")
        print("[!] Please create struct manually or locate existing struct")
        print("[!] Then add these fields:")
        print("    +0x74: entity_status (byte) - Bit 0=active, bits 3/4/5=invalid")
        print("    +0x75: entity_type (byte) - Type dispatch (EntityType enum)")
        return
    
    # Try to rename fields if struct exists
    idc.set_member_name(sid, 0x74, "entity_status")
    idc.set_member_name(sid, 0x75, "entity_type")
    
    # Set member types
    idc.set_member_type(sid, 0x74, idc.FF_BYTE, -1, 1)
    idc.set_member_type(sid, 0x75, idc.FF_BYTE, -1, 1)
    
    # Add comments
    idc.set_member_cmt(sid, 0x74, "Entity status flags: bit 0=active/targetable, bits 3/4/5=invalid/dying", 0)
    idc.set_member_cmt(sid, 0x75, "Entity behavioral type - see EntityType enum", 0)
    
    print("[+] Updated FarObjEntity struct fields")

# ============================================================================
# Data References
# ============================================================================

def annotate_data_refs():
    """Annotate important data references"""
    
    data_refs = [
        (0x15B3, "game_mode", "Game mode: 0=single player, 1+=multiplayer"),
        (0x1360, "player_entity_slot", "Player entity slot ID for wingman check"),
        (0x15B4, "friendly_fire_permission_flags", "Permission flags for type 0x16 firing"),
    ]
    
    for addr, name, comment in data_refs:
        # Note: Adjust segment based on actual data segment
        # These addresses are in data segment (ds:)
        idc.set_name(addr, name, idc.SN_NOWARN)
        idc.set_cmt(addr, comment, 0)
        print(f"[+] Annotated data at 0x{addr:X}: {name}")

# ============================================================================
# Main Execution
# ============================================================================

def main():
    """Run all annotation tasks"""
    
    print("=" * 70)
    print("Falcon 3.0 - Entity Type System Annotations")
    print("=" * 70)
    print()
    
    print("[*] Creating EntityType enum...")
    create_entity_type_enum()
    print()
    
    print("[*] Annotating functions...")
    annotate_functions()
    print()
    
    print("[*] Updating entity struct...")
    create_entity_struct()
    print()
    
    print("[*] Annotating data references...")
    annotate_data_refs()
    print()
    
    print("=" * 70)
    print("[+] Annotation complete!")
    print("=" * 70)
    print()
    print("Summary:")
    print("  - EntityType enum created with 11 known types")
    print("  - 25+ function addresses annotated")
    print("  - Entity struct fields renamed")
    print("  - Data references documented")
    print()
    print("Next steps:")
    print("  1. Review annotations in IDA")
    print("  2. Continue analysis to find enemy AI type")
    print("  3. Extract data tables to identify remaining types")

if __name__ == "__main__":
    main()
