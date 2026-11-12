#!/usr/bin/env python3
"""IDA script: Push Level-0 Batch 1 (10 functions) names to IDB.

Reads function_bytes.json and applies names for the 10 Level-0 batch 1 functions.

RUN: ida64 -A -S"_push_level0_batch1.py" FALCONCD.EXE.i64
"""
import json
import idc
import idaapi

ROOT = r"C:\Users\ybarnoy\projects\falcon3"
FB = ROOT + r"\analysis\ida_falconcd\function_bytes.json"
OUT = ROOT + r"\analysis\s4\push_level0_batch1.log"

# The 10 functions we just named
BATCH1 = [
    "sub_263F6",   # farobj_dispatch_table
    "sub_12890",   # cs_byte_00e8_get
    "sub_2295C",   # zero_ax
    "sub_22436",   # cs_word_2b76_get
    "sub_2243B",   # cs_word_2b78_get
    "sub_2284B",   # cs_word_2b82_set
    "sub_230D8",   # trig_lookup_sin
    "sub_22846",   # cs_word_2b80_set
    "sub_23134",   # trig_lookup_cos
    "sub_22850",   # cs_word_2b84_set
]

def main():
    idaapi.auto_wait()
    
    fb = json.loads(open(FB).read())
    
    log_lines = []
    renamed = 0
    already_ok = 0
    not_found = 0
    
    for key in BATCH1:
        entry = fb.get(key)
        if not entry:
            log_lines.append("ERROR: {} not in function_bytes.json".format(key))
            not_found += 1
            continue
        
        ea = entry["ea"]
        new_name = entry.get("name")
        if not new_name:
            log_lines.append("SKIP: {} has no name in function_bytes.json".format(key))
            continue
        
        current_name = idc.get_func_name(ea)
        if current_name == new_name:
            log_lines.append("OK: {:05X} already named {}".format(ea, new_name))
            already_ok += 1
            continue
        
        # Apply the name
        success = idc.set_name(ea, new_name, idc.SN_NOWARN | idc.SN_NOCHECK)
        if success:
            log_lines.append("RENAMED: {:05X} {} -> {}".format(ea, current_name, new_name))
            renamed += 1
        else:
            log_lines.append("FAILED: {:05X} could not rename to {}".format(ea, new_name))
    
    # Write log
    with open(OUT, "w") as f:
        f.write("\n".join(log_lines))
        f.write("\n\n=== SUMMARY ===\n")
        f.write("Renamed: {}\n".format(renamed))
        f.write("Already OK: {}\n".format(already_ok))
        f.write("Not found: {}\n".format(not_found))
        f.write("Total batch: {}\n".format(len(BATCH1)))
    
    print("\n=== Level-0 Batch 1 Naming ===")
    print("Renamed: {}".format(renamed))
    print("Already OK: {}".format(already_ok))
    print("Not found: {}".format(not_found))
    print("\nWrote {}".format(OUT))
    
    idc.qexit(0)

if __name__ == "__main__":
    main()
