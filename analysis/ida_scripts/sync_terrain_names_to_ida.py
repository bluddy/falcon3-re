import json
from pathlib import Path
import idc
import idaapi
import ida_name

print("=" * 80)
print("SYNCING TERRAIN FUNCTIONS AND GLOBALS TO IDA")
print("=" * 80)

idaapi.auto_wait()

SCRIPT_DIR = Path(r"C:\Users\yotam\projects\falcon3\analysis\ida_scripts")
PROJECT_ROOT = SCRIPT_DIR.parent.parent
REGISTRY_DIR = PROJECT_ROOT / "registry"

# 1. Sync Functions
func_updates = {
    0x88229: "vgraph_span_raster_dispatch",
    0x88247: "vgraph_span_raster_flat",
    0x882D3: "vgraph_span_raster_pseudo_gouraud",
    0x217E1: "terrain_quad_split_triangles",
    0x21754: "terrain_quad_subdivide_midpoint",
    0x2185E: "terrain_quad_subdivide_hierarchical",
    0x13870: "slot3_tile_record_load",
    0x13755: "slot3_tile3x3_load"
}

for ea, name in func_updates.items():
    res = ida_name.set_name(ea, name, ida_name.SN_NOWARN)
    print(f"Set func name 0x{ea:X} -> {name}: {res}")

# 2. Sync Globals
global_updates = {
    0x1F72E: "terrain_tessellation_mode",
    0x1F73B: "raster_shading_mode_flag",
    0x11BDA: "slot3_alt_file_handle",
    0x11BC4: "streaming_tile_center_y",
    0x11BC2: "streaming_tile_center_x"
}

for ea, name in global_updates.items():
    res = ida_name.set_name(ea, name, ida_name.SN_NOWARN)
    print(f"Set global name 0x{ea:X} -> {name}: {res}")

print("Syncing structs and enums...")
# Also run struct sync logic
enums_path = REGISTRY_DIR / "enums.json"
if enums_path.exists():
    with open(enums_path, "r", encoding="utf-8") as f:
        enums_data = json.load(f)
    for enum_def in enums_data:
        enum_name = enum_def["name"]
        enum_id = idc.get_enum(enum_name)
        if enum_id == idc.BADADDR:
            enum_id = idc.add_enum(idc.BADADDR, enum_name, 0)
        if enum_id != idc.BADADDR:
            for val in enum_def.get("values", []):
                idc.add_enum_member(enum_id, val["name"], val["value"], idc.BADADDR)

print("Finished successfully.")
idc.qexit(0)
