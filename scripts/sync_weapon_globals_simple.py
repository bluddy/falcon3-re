import idc
import idautils
import idaapi

def sync_weapon_globals():
    """Sync weapon globals to IDA (hardcoded from registry)"""
    
    # Get data segment
    data_seg = None
    for seg_ea in idautils.Segments():
        seg = idaapi.getseg(seg_ea)
        if seg and seg.type == idaapi.SEG_DATA:
            data_seg = seg
            break
    
    if not data_seg:
        print("ERROR: Could not find data segment")
        return
    
    data_base = data_seg.start_ea
    print(f"Data segment base: {hex(data_base)}")
    
    # Weapon globals from registry (offset, name, size)
    weapon_globals = [
        # IR lock system
        (0x44AA, "ir_lock_target_index", 2),
        (0x44DB, "ir_lock_cycle_index_mode0", 1),
        (0x44DC, "ir_lock_cycle_index_mode1", 1),
        (0x4890, "ir_lock_status_byte", 1),
        (0x48BA, "ir_lock_entity_base", 2),
        (0x487E, "ir_lock_slot_mapping", 16),
        (0x1075, "ir_lock_temp_byte_1075", 1),
        (0x44D4, "ir_lock_temp_byte_44d4", 1),
        (0x499E, "ir_lock_temp_byte_499e", 1),
        
        # Weapon system
        (0x15B3, "weapon_game_mode", 1),
        (0x15B4, "weapon_friendly_fire_flags", 2),
        
        # Loadout system
        (0x5000, "loadout_total_weight", 4),
        (0x5004, "loadout_fuel_capacity", 2),
        (0x5006, "loadout_drag_coefficient", 2),
        (0x5010, "loadout_hardpoint_config", 18),
        (0x5030, "loadout_weapon_supply", 32),
    ]
    
    renamed_count = 0
    
    for offset, name, size in weapon_globals:
        addr = data_base + offset
        
        # Check if in segment
        if addr < data_seg.start_ea or addr >= data_seg.end_ea:
            print(f"SKIP {name} @ {hex(addr)} - outside data segment")
            continue
        
        # Set name
        if idc.set_name(addr, name, idaapi.SN_NOWARN):
            print(f"OK   {name} @ {hex(addr)} (offset {hex(offset)}, size {size})")
            renamed_count += 1
        else:
            current = idc.get_name(addr)
            if current == name:
                print(f"SAME {name} @ {hex(addr)} (already set)")
                renamed_count += 1
            else:
                print(f"FAIL {name} @ {hex(addr)} (current: {current})")
    
    print(f"\nTotal weapon globals synced: {renamed_count}/{len(weapon_globals)}")
    
    # Check radar globals are still named (should be from previous work)
    print("\nVerifying radar globals (from previous session):")
    radar_check = [
        (0x595B2, "radar_mode_state"),
        (0x59573, "radar_type_selector"),
        (0x5959B, "radar_selected_target_index"),
    ]
    
    for offset, expected_name in radar_check:
        addr = data_base + offset
        current = idc.get_name(addr)
        if current == expected_name:
            print(f"  ✓ {expected_name}")
        else:
            print(f"  ✗ Expected {expected_name}, got {current}")

print("Syncing weapon globals to IDA...")
sync_weapon_globals()

idc.qexit(0)
