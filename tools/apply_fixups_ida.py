"""Apply RTLink fixups to IDA database for Falcon3 overlays.

This script loads the parsed fixup tables and applies segment relocations
to the overlay code in the IDA database.
"""
import json
import ida_bytes
import ida_segment
import ida_ida
import idaapi

FIXUP_JSON = r"C:\Users\yotam\projects\falcon3\analysis\ida_falconcd\fixup_tables_complete.json"

def apply_fixups():
    with open(FIXUP_JSON, 'r') as f:
        fixups = json.load(f)
    
    # Base paragraph from IDA's min_ea (0x10000 -> para 0x1000)
    base_para = ida_ida.inf_get_min_ea() >> 4
    print(f"Base paragraph: 0x{base_para:04x}")
    
    total_applied = 0
    total_failed = 0
    
    for rec_id_str, rec in fixups.items():
        rec_id = int(rec_id_str)
        seg = rec['seg']
        code_size = rec['code_size']
        fixups_by_type = rec['fixups_by_type']
        
        # Runtime segment paragraph for this overlay
        runtime_para = (ida_ida.inf_get_min_ea() >> 4) + seg
        runtime_base = runtime_para * 16
        code_start = runtime_base
        code_end = runtime_base + rec['code_size']
        
        print(f"\nProcessing id={rec['id']} seg=0x{seg:04x} runtime_para=0x{runtime_para:04x} "
              f"base=0x{runtime_base:08x} size={rec['code_size']}")
        
        # Verify segment exists
        seg_obj = ida_segment.getseg(runtime_base)
        if not seg_obj:
            print(f"  WARNING: Segment at 0x{runtime_base:08x} not found!")
            continue
        
        applied = 0
        failed = 0
        
        for typ, offsets in fixups_by_type.items():
            for offset in offsets:
                ea = runtime_base + offset
                if offset >= rec['code_size']:
                    failed += 1
                    continue
                
                # Read current word (unrelocated segment value)
                word = ida_bytes.get_word(ea)
                if word is None:
                    failed += 1
                    continue
                
                # Apply relocation: add runtime segment paragraph
                # The unrelocated value is a segment relative to 0
                # At runtime, it should be: unrelocated + runtime_para
                relocated = (word + runtime_para) & 0xFFFF
                
                # Write relocated value
                ida_bytes.patch_word(ea, relocated)
                total_applied += 1
                applied += 1
        
        print(f"  Applied: {applied}, Failed: {failed}")
        total_applied += applied
        total_failed += failed
    
    print(f"\nTotal applied: {total_applied}, Total failed: {total_failed}")
    
    # Re-analyze
    print("\nRe-running autoanalysis...")
    idaapi.auto_wait()
    print("Done!")

apply_fixups()
# EXPLICIT save (finding 40 audit): never rely on idat's implicit exit-save.
import ida_loader
print("saved idb: %s" % ida_loader.save_database(
    r"C:\Users\yotam\projects\falcon3\analysis\ida_falconcd\FALCONCD.EXE.i64", 0))
idaapi.qexit(0)