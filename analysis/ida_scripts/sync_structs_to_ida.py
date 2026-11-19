"""
Sync all structures and enums from JSON registry to IDA database.
Follows docs/IDA_AUTOMATION_GUIDE.md:
- Module level code
- idaapi.auto_wait()
- idc.qexit(0)
- Reads registry/structs.json and registry/enums.json
"""

import json
from pathlib import Path
import traceback

import idc
import idaapi
import idautils

SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parent.parent
REGISTRY_DIR = PROJECT_ROOT / "registry"
LOG_FILE = SCRIPT_DIR / "sync_structs_report.json"

print("=" * 80)
print("SYNCING ALL STRUCTURES AND ENUMS TO IDA (FROM JSON)")
print("=" * 80)

print("Waiting for IDA auto-analysis...")
idaapi.auto_wait()
print("Auto-analysis complete.")

report = {
    "enums_created": 0,
    "enums_failed": 0,
    "structs_created": 0,
    "structs_failed": 0,
    "struct_details": {},
    "errors": []
}

try:
    # ---------------------------------------------------------
    # 1. Sync Enums
    # ---------------------------------------------------------
    enums_path = REGISTRY_DIR / "enums.json"
    if enums_path.exists():
        with open(enums_path, "r", encoding="utf-8") as f:
            enums_data = json.load(f)

        print(f"\nProcessing {len(enums_data)} enums from {enums_path}...")
        for enum_def in enums_data:
            ename = enum_def.get("name")
            if not ename:
                continue

            # Delete existing enum to recreate cleanly
            old_eid = idc.get_enum(ename)
            if old_eid != idc.BADADDR:
                idc.del_enum(old_eid)

            eid = idc.add_enum(idc.BADADDR, ename, 0)
            if eid == idc.BADADDR:
                print(f"  [!] Failed to create enum {ename}")
                report["enums_failed"] += 1
                report["errors"].append(f"Failed to create enum {ename}")
                continue

            desc = enum_def.get("description", "")
            if desc:
                idc.set_enum_cmt(eid, desc, 0)

            # Add members
            members = enum_def.get("values", [])
            if not members and "bitflags" in enum_def:
                members = enum_def.get("bitflags", [])

            for m in members:
                mname = m.get("name")
                val = m.get("value")
                if val is None and "bit" in m:
                    val = 1 << m["bit"]
                elif val is None and "mask" in m:
                    val = m["mask"]

                if mname and val is not None:
                    added_mname = mname
                    try:
                        err = idc.add_enum_member(eid, mname, val, idc.BADADDR)
                    except Exception:
                        # Collision: try prefixing with enum name
                        added_mname = f"{ename}_{mname}"
                        try:
                            err = idc.add_enum_member(eid, added_mname, val, idc.BADADDR)
                        except Exception as m_ex:
                            err = -1

                    if err == 0:
                        m_cmt = m.get("comment", "") or m.get("description", "")
                        if m_cmt:
                            m_id = idc.get_enum_member_by_name(added_mname)
                            if m_id != idc.BADADDR:
                                idc.set_enum_member_cmt(m_id, m_cmt, 0)

            report["enums_created"] += 1
            print(f"  [+] Enum {ename} synced")

    # ---------------------------------------------------------
    # 2. Sync Structs
    # ---------------------------------------------------------
    structs_path = REGISTRY_DIR / "structs.json"
    if structs_path.exists():
        with open(structs_path, "r", encoding="utf-8") as f:
            structs_data = json.load(f)

        print(f"\nProcessing {len(structs_data)} structs from {structs_path}...")
        for sdef in structs_data:
            sname = sdef.get("name")
            if not sname:
                continue

            # Recreate struct
            old_sid = idc.get_struc_id(sname)
            if old_sid != idc.BADADDR:
                idc.del_struc(old_sid)

            sid = idc.add_struc(idc.BADADDR, sname, 0)
            if sid == idc.BADADDR:
                print(f"  [!] Failed to create struct {sname}")
                report["structs_failed"] += 1
                report["errors"].append(f"Failed to create struct {sname}")
                continue

            notes = sdef.get("notes") or sdef.get("description") or ""
            if notes:
                idc.set_struc_cmt(sid, notes, 0)

            fields = sdef.get("fields", [])
            # Filter and sort by offset
            valid_fields = [f for f in fields if f.get("offset") is not None]
            valid_fields.sort(key=lambda x: x["offset"])

            added_count = 0
            for fld in valid_fields:
                fname = fld.get("name")
                offset = fld.get("offset")
                fsize = fld.get("size", 1)
                ftype = str(fld.get("type", "uint16")).lower()

                if not fname:
                    fname = f"field_{offset:X}"

                # Determine IDA flag and size
                if ftype in ["uint8", "int8", "flags8", "uint8_t", "char", "byte"]:
                    flag = idc.FF_BYTE | idc.FF_DATA
                    size = 1
                elif ftype in ["uint16", "int16", "flags16", "uint16_t", "short", "word", "seg16", "ptr16"]:
                    flag = idc.FF_WORD | idc.FF_DATA
                    size = 2
                elif ftype in ["uint32", "int32", "flags32", "uint32_t", "long", "dword", "far_ptr"]:
                    flag = idc.FF_DWORD | idc.FF_DATA
                    size = 4
                elif fsize > 1 or "bytes" in ftype or "[" in ftype:
                    flag = idc.FF_BYTE | idc.FF_DATA
                    size = fsize
                else:
                    flag = idc.FF_WORD | idc.FF_DATA
                    size = fsize if fsize > 0 else 2

                # If size is 0 (marker), skip adding member
                if size <= 0:
                    continue

                res = idc.add_struc_member(sid, fname, offset, flag, idc.BADADDR, size)
                if res == 0:
                    added_count += 1
                    fcmt = fld.get("comment") or fld.get("description") or ""
                    if fcmt:
                        try:
                            idc.set_member_cmt(sid, offset, fcmt, 0)
                        except Exception:
                            pass
                else:
                    # Retry with an offset-prefixed name in case of collision
                    alt_name = f"{fname}_{offset:X}"
                    res2 = idc.add_struc_member(sid, alt_name, offset, flag, idc.BADADDR, size)
                    if res2 == 0:
                        added_count += 1
                        fcmt = fld.get("comment") or fld.get("description") or ""
                        if fcmt:
                            try:
                                idc.set_member_cmt(sid, offset, fcmt, 0)
                            except Exception:
                                pass

            actual_size = idc.get_struc_size(sid)
            report["structs_created"] += 1
            report["struct_details"][sname] = {
                "sid": sid,
                "fields_added": added_count,
                "size": actual_size
            }
            print(f"  [+] Struct {sname}: {added_count} fields, size = {actual_size} bytes")

    report["status"] = "success"

except Exception as ex:
    err_msg = f"Exception: {ex}\n{traceback.format_exc()}"
    print(err_msg)
    report["errors"].append(err_msg)
    report["status"] = "failed"

with open(LOG_FILE, "w", encoding="utf-8") as f:
    json.dump(report, f, indent=2)

print(f"\nReport written to: {LOG_FILE}")
print("Exiting IDA...")
idc.qexit(0)
