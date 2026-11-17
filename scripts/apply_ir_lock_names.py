import idc
import idautils
import idaapi

def apply_ir_lock_names():
    """Apply IR lock global names from registry to IDA"""
    
    # IR lock globals (data segment)
    globals_ds = [
        (0x44AA, "ir_lock_target_index", 2),
        (0x44DB, "ir_lock_cycle_index_mode0", 1),
        (0x44DC, "ir_lock_cycle_index_mode1", 1),
        (0x4890, "ir_lock_status_byte", 1),
        (0x48BA, "ir_lock_entity_base", 2),
        (0x487E, "ir_lock_slot_mapping", 16),
        (0x1075, "ir_lock_temp_byte_1075", 1),
        (0x44D4, "ir_lock_temp_byte_44d4", 1),
        (0x499E, "ir_lock_temp_byte_499e", 1),
    ]
    
    # Get data segment base
    data_seg = idaapi.get_segm_by_name(".data")
    if not data_seg:
        # Try alternative segment names
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
    
    # Apply data segment names
    for offset, name, size in globals_ds:
        addr = data_base + offset
        
        # Check if address is valid
        if addr < data_seg.start_ea or addr >= data_seg.end_ea:
            print(f"SKIP {name}: address {hex(addr)} outside data segment")
            continue
        
        # Set name
        if idc.set_name(addr, name, idaapi.SN_NOWARN):
            print(f"OK   {name} @ {hex(addr)} (offset {hex(offset)}, size {size})")
            renamed_count += 1
        else:
            old_name = idc.get_name(addr)
            print(f"FAIL {name} @ {hex(addr)} (current: {old_name})")
    
    print(f"\nRenamed {renamed_count} IR lock globals")
    
    # Note: Entity field heat_signature @ +0xAE will be set via struct member naming
    # when EntitySlotRecord struct is updated in IDA

print("Applying IR lock names from registry...")
apply_ir_lock_names()

idc.qexit(0)
