import json
from pathlib import Path

# 1. Update enums.json
enums_path = Path('registry/enums.json')
with open(enums_path, 'r', encoding='utf-8') as f:
    enums = json.load(f)

existing_enum_names = {e['name'] for e in enums}

new_enums = [
    {
        "name": "TerrainTessellationMode",
        "type": "uint8_t",
        "description": "Polygon and tile mesh tessellation/subdivision modes extracted from opcode bits 9..11",
        "evidence": [
            {"functions": ["object_record_stream_step (0x267D0)", "line_record_flag_dispatch (0x287D0)", "record_span_build_and_dispatch (0x29917)"]}
        ],
        "values": [
            {"value": 0, "name": "TESSELLATION_NONE", "description": "Render original un-tessellated polygon", "evidence": "cs:state_byte_1f72e == 0"},
            {"value": 2, "name": "TESSELLATION_CURSOR", "description": "Cursor-aligned parameter append", "evidence": "param6_append_cursor_a (0x216F3)"},
            {"value": 4, "name": "TESSELLATION_MIDPOINT_QUAD", "description": "Quad midpoint edge subdivision", "evidence": "param6_append_avg_b / terrain_quad_subdivide_midpoint (0x21754)"},
            {"value": 6, "name": "TESSELLATION_TRIANGLE_SPLIT", "description": "Quad split diagonally into two triangles (V0,V1,V2) and (V2,V3,V0)", "evidence": "param6_append_3w_c / terrain_quad_split_triangles (0x217E1)"},
            {"value": 8, "name": "TESSELLATION_HIERARCHICAL_QUAD", "description": "Hierarchical fine quad subdivision", "evidence": "param6_append_scale_d / terrain_quad_subdivide_hierarchical (0x2185E)"}
        ]
    },
    {
        "name": "RasterShadingMode",
        "type": "uint8_t",
        "description": "Rasterizer span fill mode controlled by descriptor bit 15 (CL passed to vgraph_span_raster_dispatch)",
        "evidence": [
            {"functions": ["record_op_dispatch_220b0 (0x2061B)", "vgraph_slot_13 / vgraph_span_raster_dispatch (0x88229)"]}
        ],
        "values": [
            {"value": 0, "name": "SHADING_FLAT", "description": "Solid flat-color span fill via rep stosw", "evidence": "vgraph_span_raster_flat (loc_88247)"},
            {"value": 128, "name": "SHADING_PSEUDO_GOURAUD", "description": "8x8 screen-space ordered dither scanline shading", "evidence": "vgraph_span_raster_pseudo_gouraud (loc_882D3)"}
        ]
    },
    {
        "name": "TerrainFeatureAttr",
        "type": "uint16_t",
        "description": "ISLDAT feature category and scale attribute word at record offset +0x20",
        "evidence": [
            {"files": ["ISLDAT.*"], "disassembly": ["0x28A68..0x28A80", "pos_neighbor_norm_scan (0x14B17)"]}
        ],
        "values": [
            {"value": 20, "name": "FEATURE_COASTLINE", "description": "Coastline and open sea water mesh in Grid B (T1)", "evidence": "attr == 0x14"},
            {"value": 50, "name": "FEATURE_DEVELOPED_GROUND_PLATE", "description": "Developed ground surface plates / bases in Grid A (T2), rendered white in 3D", "evidence": "attr == 0x32"},
            {"value": 100, "name": "FEATURE_LAKE", "description": "Inland enclosed lake water bodies in Grid B (T1)", "evidence": "attr == 0x64"},
            {"value": 200, "name": "FEATURE_WIDE_WATER_BODY", "description": "Wide water bodies / gulfs in Grid B (T1)", "evidence": "attr == 0xC8"}
        ]
    }
]

for ne in new_enums:
    if ne['name'] not in existing_enum_names:
        enums.append(ne)

with open(enums_path, 'w', encoding='utf-8') as f:
    json.dump(enums, f, indent=2)
print("Updated enums.json.")

# 2. Update structs.json
structs_path = Path('registry/structs.json')
with open(structs_path, 'r', encoding='utf-8') as f:
    structs = json.load(f)

existing_struct_names = {s['name'] for s in structs}

new_structs = [
    {
        "name": "AltitudeBlock",
        "size": 256,
        "description": "Sparse 16x16 elevation height sample block from ALT.<theater> files",
        "evidence": "Every ALT.<theater> file size is a multiple of 256 bytes; sampled by slot3_tile_record_load (0x13870)",
        "fields": [
            {"offset": 0, "size": 256, "name": "height_samples", "type": "uint8_t[16][16]", "description": "Grid of 16x16 elevation samples for one regional sector"}
        ]
    },
    {
        "name": "StreamingTileRing",
        "size": 72,
        "description": "Active 3x3 tile streaming ring descriptors (9 tile slots around aircraft)",
        "evidence": "slot3_tile3x3_load (0x13755) loads slots 0..8 at offsets 150h, 162h",
        "fields": [
            {"offset": 0, "size": 18, "name": "slot_handles", "type": "uint16_t[9]", "description": "Memory/EMS handles or pointers for slots 0..8"},
            {"offset": 18, "size": 54, "name": "slot_metadata", "type": "uint8_t[9][6]", "description": "Tile coordinates and active streaming state flags"}
        ]
    }
]

for ns in new_structs:
    if ns['name'] not in existing_struct_names:
        structs.append(ns)

with open(structs_path, 'w', encoding='utf-8') as f:
    json.dump(structs, f, indent=2)
print("Updated structs.json.")

# 3. Update globals.json
globals_path = Path('registry/globals.json')
with open(globals_path, 'r', encoding='utf-8') as f:
    globals_data = json.load(f)

existing_global_addrs = {g['address'] for g in globals_data}

new_globals = [
    {
        "address": 0x1F72E,
        "name": "terrain_tessellation_mode",
        "size": 1,
        "type": "uint8_t",
        "doc": "Terrain mesh tessellation mode (opcode bits 9..11). 0=none, 4=midpoint, 6=triangle split, 8=hierarchical.",
        "source": "FALCONCD.EXE analysis at 0x267FC, 0x28805, 0x29979"
    },
    {
        "address": 0x1F73B,
        "name": "raster_shading_mode_flag",
        "size": 1,
        "type": "uint8_t",
        "doc": "Rasterizer shading mode flag (opcode bit 15). 0x00=flat solid span fill (loc_88247), 0x80=pseudo-Gouraud 8x8 ordered dither scanline shading (loc_882D3).",
        "source": "FALCONCD.EXE analysis at 0x20623, 0x28A44, 0x88229"
    },
    {
        "address": 0x11BDA,
        "name": "slot3_alt_file_handle",
        "size": 2,
        "type": "uint16_t",
        "doc": "File or EMS handle for theater altitude block stream in slot3.",
        "source": "FALCONCD.EXE analysis at 0x1395B, 0x1396D"
    },
    {
        "address": 0x11BC4,
        "name": "streaming_tile_center_y",
        "size": 2,
        "type": "uint16_t",
        "doc": "Current center tile Y coordinate for 3x3 active tile streaming ring.",
        "source": "FALCONCD.EXE analysis at 0x13777"
    },
    {
        "address": 0x11BC2,
        "name": "streaming_tile_center_x",
        "size": 2,
        "type": "uint16_t",
        "doc": "Current center tile X coordinate for 3x3 active tile streaming ring.",
        "source": "FALCONCD.EXE analysis at 0x13780"
    }
]

for ng in new_globals:
    found = False
    for g in globals_data:
        if g['address'] == ng['address']:
            g.update(ng)
            found = True
            break
    if not found:
        globals_data.append(ng)

with open(globals_path, 'w', encoding='utf-8') as f:
    json.dump(globals_data, f, indent=2)
print("Updated globals.json.")

# 4. Update functions.json
funcs_path = Path('registry/functions.json')
with open(funcs_path, 'r', encoding='utf-8') as f:
    funcs_data = json.load(f)

func_updates = {
    0x88229: {
        "name": "vgraph_span_raster_dispatch",
        "system": "graphics",
        "doc": "Span rasterizer dispatch. Checks CL (opcode_index): if 0, calls flat span rasterizer loc_88247 (rep stosw); if non-zero (0x80), calls pseudo-Gouraud shaded rasterizer loc_882D3 (8x8 screen-space ordered dither scanline)."
    },
    0x217E1: {
        "name": "terrain_quad_split_triangles",
        "system": "terrain",
        "doc": "Quad-to-triangle mesh splitter (state_byte_1f72e == 6). Splits quad into diagonal triangles (V0,V1,V2) and (V2,V3,V0) for terrain elevation tessellation."
    },
    0x21754: {
        "name": "terrain_quad_subdivide_midpoint",
        "system": "terrain",
        "doc": "Quad midpoint subdivision (state_byte_1f72e == 4). Calculates opposite edge midpoints for adaptive terrain LOD."
    },
    0x2185E: {
        "name": "terrain_quad_subdivide_hierarchical",
        "system": "terrain",
        "doc": "Hierarchical fine quad subdivision (state_byte_1f72e == 8) for detailed near-camera terrain tessellation."
    },
    0x13870: {
        "name": "slot3_tile_record_load",
        "system": "slot3",
        "doc": "Loads sparse 16x16 elevation block from ALT file or EMS for a 32x32 terrain tile. If index is 0xFFFF (unpopulated sector), zeroes buffer for flat terrain/sea level."
    },
    0x13755: {
        "name": "slot3_tile3x3_load",
        "system": "slot3",
        "doc": "Maintains 3x3 active tile streaming ring (9 slots) centered on player coordinates (streaming_tile_center_x, streaming_tile_center_y)."
    }
}

for fn in funcs_data:
    addr = fn.get('address')
    if addr in func_updates:
        fn.update(func_updates[addr])

with open(funcs_path, 'w', encoding='utf-8') as f:
    json.dump(funcs_data, f, indent=2)
print("Updated functions.json.")
