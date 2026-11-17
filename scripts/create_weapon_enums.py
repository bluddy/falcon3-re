import idc
import idaapi

def create_weapon_enums():
    """Create weapon-related enums in IDA"""
    
    print("Creating weapon enums in IDA...")
    
    # ========== WeaponType enum ==========
    enum_id = idc.add_enum(-1, "WeaponType", 0)
    if enum_id == idc.BADADDR:
        enum_id = idc.get_enum("WeaponType")
    
    # A-A Weapons (missiles)
    idc.add_enum_member(enum_id, "WEAPON_AIM9_SIDEWINDER", 0x12, -1)
    idc.add_enum_member(enum_id, "WEAPON_AIM120_AMRAAM", 0x13, -1)
    
    # A-G Weapons (bombs, AGMs) - gap 0x14-0x32
    idc.add_enum_member(enum_id, "WEAPON_AG_START", 0x14, -1)
    idc.add_enum_member(enum_id, "WEAPON_AGM88_HARM", 0x19, -1)  # Confirmed from code
    idc.add_enum_member(enum_id, "WEAPON_AG_END", 0x32, -1)
    
    # Guns
    idc.add_enum_member(enum_id, "WEAPON_M61A1_VULCAN", 0x33, -1)
    idc.add_enum_member(enum_id, "WEAPON_GUN_VARIANT_1", 0x34, -1)
    idc.add_enum_member(enum_id, "WEAPON_GUN_VARIANT_2", 0x35, -1)
    idc.add_enum_member(enum_id, "WEAPON_GUN_VARIANT_3", 0x36, -1)
    idc.add_enum_member(enum_id, "WEAPON_GUN_VARIANT_4", 0x37, -1)
    
    print(f"  Created WeaponType enum: {11} members")
    
    # ========== IRLockSearchMode enum ==========
    enum_id = idc.add_enum(-1, "IRLockSearchMode", 0)
    if enum_id == idc.BADADDR:
        enum_id = idc.get_enum("IRLockSearchMode")
    
    idc.add_enum_member(enum_id, "IR_LOCK_MODE_SIMPLE", 0, -1)      # 4 targets (0-3)
    idc.add_enum_member(enum_id, "IR_LOCK_MODE_EXTENDED", 1, -1)    # 13 targets (4-16)
    
    print(f"  Created IRLockSearchMode enum: 2 members")
    
    # ========== WeaponKeyCode enum ==========
    enum_id = idc.add_enum(-1, "WeaponKeyCode", 0)
    if enum_id == idc.BADADDR:
        enum_id = idc.get_enum("WeaponKeyCode")
    
    idc.add_enum_member(enum_id, "KEY_BACKSPACE_AG_SELECT", 0x0E, -1)
    idc.add_enum_member(enum_id, "KEY_ENTER_AA_SELECT", 0x1C, -1)
    idc.add_enum_member(enum_id, "KEY_Z_RADAR_LOCK", 0x2C, -1)
    idc.add_enum_member(enum_id, "KEY_APOSTROPHE_RIPPLE_PLUS", 0x28, -1)
    idc.add_enum_member(enum_id, "KEY_SEMICOLON_RIPPLE_MINUS", 0x27, -1)
    idc.add_enum_member(enum_id, "KEY_SPACE_FIRE", 0x39, -1)
    
    print(f"  Created WeaponKeyCode enum: 6 members")
    
    # ========== DetectionModeState enum (already exists from radar, verify) ==========
    enum_id = idc.get_enum("DetectionModeState")
    if enum_id == idc.BADADDR:
        enum_id = idc.add_enum(-1, "DetectionModeState", 0)
        idc.add_enum_member(enum_id, "DETECTION_INACTIVE", 0, -1)
        idc.add_enum_member(enum_id, "DETECTION_MODE_1", 1, -1)
        idc.add_enum_member(enum_id, "DETECTION_MODE_2", 2, -1)
        idc.add_enum_member(enum_id, "DETECTION_MODE_3", 3, -1)
        idc.add_enum_member(enum_id, "DETECTION_MODE_4", 4, -1)
        idc.add_enum_member(enum_id, "DETECTION_ACTIVE_LOCK", 5, -1)  # IR lock tone triggers at 5
        print(f"  Created DetectionModeState enum: 6 members")
    else:
        print(f"  DetectionModeState enum already exists")
    
    print("\nAll weapon enums created successfully!")
    return True

# Execute
create_weapon_enums()

idc.qexit(0)
