import idc
import idautils
import idaapi
import yaml

def sync_weapon_globals_to_ida():
    """Sync all weapon globals from registry to IDA"""
    
    # Read registry
    with open('registry/globals.yaml', 'r') as f:
        registry = yaml.safe_load(f)
    
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
    
    renamed_count = 0
    skipped_count = 0
    
    # Process globals
    for var in registry['data_segment_0x54AF']['globals']:
        name = var.get('name')
        address = var.get('address')
        segment = var.get('segment')
        
        if not name or not address:
            continue
        
        # Skip if segment specified and not 'data' or None
        if segment and segment not in ['data', None]:
            continue
        
        # Skip menu/UI globals (different segment)
        if segment and segment != 'data':
            skipped_count += 1
            continue
        
        # Parse address (could be int or hex string)
        if isinstance(address, str):
            addr_val = int(address, 16) if address.startswith('0x') else int(address)
        else:
            addr_val = address
        
        # Calculate absolute address
        abs_addr = data_base + addr_val
        
        # Check if in data segment
        if abs_addr < data_seg.start_ea or abs_addr >= data_seg.end_ea:
            skipped_count += 1
            continue
        
        # Only rename if related to weapons
        if not any(kw in name.lower() for kw in ['weapon', 'ir_lock', 'loadout', 'ammo']):
            continue
        
        # Set name
        if idc.set_name(abs_addr, name, idaapi.SN_NOWARN):
            print(f"OK   {name} @ {hex(abs_addr)} (offset {hex(addr_val)})")
            renamed_count += 1
        else:
            old_name = idc.get_name(abs_addr)
            print(f"SKIP {name} @ {hex(abs_addr)} (current: {old_name})")
            skipped_count += 1
    
    print(f"\nRenamed: {renamed_count}, Skipped: {skipped_count}")
    
    # Also check if IR lock globals are properly named
    print("\nVerifying IR lock globals:")
    ir_lock_addrs = [
        (0x44AA, "ir_lock_target_index"),
        (0x44DB, "ir_lock_cycle_index_mode0"),
        (0x44DC, "ir_lock_cycle_index_mode1"),
        (0x4890, "ir_lock_status_byte"),
        (0x48BA, "ir_lock_entity_base"),
        (0x487E, "ir_lock_slot_mapping"),
    ]
    
    for offset, expected_name in ir_lock_addrs:
        addr = data_base + offset
        current_name = idc.get_name(addr)
        if current_name == expected_name:
            print(f"  ✓ {expected_name} @ {hex(addr)}")
        else:
            print(f"  ✗ {expected_name} @ {hex(addr)} - current: {current_name}")

print("Syncing weapon globals from registry to IDA...")
sync_weapon_globals_to_ida()

idc.qexit(0)
