import json

# 1. Update registry/structs.json
with open('registry/structs.json', 'r') as f:
    structs = json.load(f)

new_structs = [
    {
        "name": "Object3DLODHeader",
        "size": 10,
        "description": "LOD header for 3D objects in game/OBJECTS archive",
        "fields": [
            {"offset": 0, "name": "vertex_count", "type": "uint16_t", "size": 2, "description": "Number of vertices in this LOD"},
            {"offset": 2, "name": "vertex_table_offset", "type": "uint16_t", "size": 2, "description": "Byte offset to vertex array relative to chunk"},
            {"offset": 4, "name": "poly_table_offset", "type": "uint16_t", "size": 2, "description": "Byte offset to polygon pointer table (to)"},
            {"offset": 6, "name": "flags_word3", "type": "uint16_t", "size": 2, "description": "Unknown flags / bounding radius"},
            {"offset": 8, "name": "flags_word4", "type": "uint16_t", "size": 2, "description": "Unknown flags"}
        ]
    },
    {
        "name": "ObjectPolygon",
        "size": 8,
        "description": "Polygon record in Falcon 3.0 3D models (game/OBJECTS)",
        "fields": [
            {"offset": 0, "name": "normal_or_flags", "type": "uint16_t", "size": 2, "description": "Normal vector or visibility flags"},
            {"offset": 2, "name": "render_mode", "type": "uint16_t", "size": 2, "description": "Shading / rasterization mode"},
            {"offset": 4, "name": "color_index", "type": "uint16_t", "size": 2, "description": "Color index into VGA palette"},
            {"offset": 6, "name": "vertex_count", "type": "uint16_t", "size": 2, "description": "Vertex count N (followed by N+1 words, index*16)"}
        ]
    },
    {
        "name": "ObjectVisibilityNode",
        "size": 4,
        "description": "Visibility group / BSP node in game/OBJECTS (lists polygon offsets)",
        "fields": [
            {"offset": 0, "name": "marker", "type": "uint16_t", "size": 2, "description": "Node marker (0xFFFF for group)"},
            {"offset": 2, "name": "poly_offset_list", "type": "uint16_t[]", "size": 2, "description": "Array of 16-bit polygon offsets, terminated by 0xFFFF"}
        ]
    }
]

existing_struct_names = {s['name'] for s in structs}
added_s = 0
for ns in new_structs:
    if ns['name'] not in existing_struct_names:
        structs.append(ns)
        added_s += 1

with open('registry/structs.json', 'w') as f:
    json.dump(structs, f, indent=2)

print(f"Added {added_s} new structs to registry/structs.json")

# 2. Update registry/functions.json
with open('registry/functions.json', 'r') as f:
    funcs = json.load(f)

# Note: addresses in registry/functions.json are linear addresses
# In seg020 (base 0x1F6C0):
# 0x26B2E = 158510
# 0x2978E = 169870
# 0x28E50 = 167504
# 0x299D5 = 170453

new_funcs = [
    {
        "address": 0x26B2E,
        "name": "object_3d_project_and_draw",
        "system": "graphics_3d",
        "size": 0x94,
        "doc": "Main 3D object transformation and rendering dispatcher from game/OBJECTS archive",
        "source": "docs/architecture/graphics_3d.md"
    },
    {
        "address": 0x2978E,
        "name": "object_3d_poly_visibility_and_draw",
        "system": "graphics_3d",
        "size": 0x80,
        "doc": "Calculates face normal cross product, dot product with view vector, backface culls and dispatches",
        "source": "docs/architecture/graphics_3d.md"
    },
    {
        "address": 0x28E50,
        "name": "object_3d_poly_rasterize_dispatch",
        "system": "graphics_3d",
        "size": 0x75,
        "doc": "Prepares and dispatches polygon line / edge rasterizer queue",
        "source": "docs/architecture/graphics_3d.md"
    },
    {
        "address": 0x299D5,
        "name": "object_3d_record_span_mask_rebuild",
        "system": "graphics_3d",
        "size": 0x58,
        "doc": "Loads polygon transformed vertices (stride 16), builds edge masks and screen clipping flags",
        "source": "docs/architecture/graphics_3d.md"
    }
]

existing_func_addrs = {fn['address'] for fn in funcs}
added_f = 0
for nf in new_funcs:
    if nf['address'] not in existing_func_addrs:
        funcs.append(nf)
        added_f += 1
    else:
        # update existing
        for fn in funcs:
            if fn['address'] == nf['address']:
                fn.update(nf)
                print(f"Updated function at 0x{nf['address']:X}: {nf['name']}")

with open('registry/functions.json', 'w') as f:
    json.dump(funcs, f, indent=2)

print(f"Added {added_f} new functions to registry/functions.json")
