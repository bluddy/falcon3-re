import idc
import idaapi
import sys

output_file = open(r"C:\Users\ybarnoy\projects\falcon3\remaining_names_output.txt", "w")
sys.stdout = output_file
sys.stderr = output_file

print("Adding remaining entity field names and enums...")
idaapi.auto_wait()

# Update EntityFieldOffset enum with field +0x0A discovered in entity_slot_update_loop
print("=== Updating EntityFieldOffset Enum ===\n")

enum_id = idc.get_enum("EntityFieldOffset")
if enum_id != idc.BADADDR:
    # Add +0x0A field (tested for bit 1 in entity_slot_update_loop)
    new_fields = [
        (0x0A, "ENTITY_FLAGS_0A", "Entity flags at +0Ah, bit 1 tested by entity_slot_update_loop"),
    ]
    
    for val, name, comment in new_fields:
        member_id = idc.get_enum_member(enum_id, val, 0, 0)
        if member_id == idc.BADADDR:
            result = idc.add_enum_member(enum_id, name, val, idc.BADADDR)
            if result == 0:
                print(f"✓ Added 0x{val:02X} = {name}")
                idc.set_enum_cmt(idc.get_enum_member(enum_id, val, 0, 0), comment, 0)
            else:
                print(f"✗ Failed to add {name}")
        else:
            print(f"Field 0x{val:02X} already exists")

# Create ImpactState enum
print("\n=== Creating ImpactState Enum ===\n")

impact_enum = idc.get_enum("ImpactState")
if impact_enum != idc.BADADDR:
    idc.del_enum(impact_enum)
    print("Deleted existing ImpactState enum")

impact_enum = idc.add_enum(idc.BADADDR, "ImpactState", 0)
if impact_enum != idc.BADADDR:
    print(f"Created ImpactState enum")
    
    states = [
        (0xFF, "PRISTINE", "Never been hit, pristine state"),
        (0xA0, "IMPACTED", "Hit by weapon, damage applied"),
    ]
    
    for val, name, comment in states:
        result = idc.add_enum_member(impact_enum, name, val, idc.BADADDR)
        if result == 0:
            print(f"  ✓ Added 0x{val:02X} = {name}")
            idc.set_enum_cmt(idc.get_enum_member(impact_enum, val, 0, 0), comment, 0)

# Add comments to key entity functions
print("\n=== Adding Function Comments ===\n")

function_comments = [
    (0x3C1BD, "entity_slot_update_loop", """Main entity slot update coordinator.

Iterates through all 16 entity slots (stride 0x5C = 92 bytes) and performs
3-pass update processing:

Pass 1: Test [si+0Ah] bit 1, call update functions
Pass 2: Check ai_state_value_get, conditional processing  
Pass 3: Test [si+0Ah] bit 1 and cs:ai_heading_correction_calc bit 4,
        Load [si+0Ch] as table index for function dispatch

Base address: DS:ES = 0x54AF, SI = 0x386Fh
Stride: 0x5C (92 bytes)
Count: 0x10 (16 slots)
"""),
    
    (0x3D37F, "entity_physics_and_ai_update", """Main entity physics and AI update function.

Processes one entity per call, handling:
- Physics integration (gravity, drag, aerodynamics)
- Weapon guidance (HARM radiation seeking, IR tracking, radar)
- AI behavior (target following, evasion, combat)
- Collision detection preparation

Stats: 1319 bytes, 122 MOV, 37 CMP, 70 CALL, 103 JUMP

CRITICAL: Only ONE subtract to velocity in entire function:
  sub [si+2Eh], ax @ 0x3D3BD - applies gravity and drag

Checks weapon_type [si+75h] for weapon-specific behavior:
  - 0x19 (AGM88 HARM): radiation seeking
  - 0x33 (M61A1): gun projectile
  - 0x12-0x37: various weapon types
"""),
    
    (0x3CCB1, "farobj_field2e_zero_dispatch", """Zeros entity velocity field at +0x2E.

481-byte function that clears the velocity_component field,
likely called when entity becomes stationary or is destroyed.
"""),
]

for addr, name, comment in function_comments:
    idc.set_func_cmt(addr, comment, 1)
    print(f"✓ Added comment to {name} @ 0x{addr:X}")

# Add critical instruction comments
print("\n=== Adding Critical Instruction Comments ===\n")

critical_instructions = [
    (0x3C1EB, "Loop start: process entity at SI"),
    (0x3C1F2, "Test entity_flags_0a [si+0Ah] bit 1"),
    (0x3C20D, "Add stride 0x5C to move to next entity"),
    (0x3C1E9, "CX = 0x10 (16 entity slots)"),
    (0x3C1E7, "SI = 0x386F (entity array base)"),
    (0x3C244, "Test entity_flags_0a [si+0Ah] bit 1 (pass 2)"),
    (0x3C254, "Load entity field [si+0Ch] into DI (table index)"),
    (0x3C256, "Shift DI left (word index)"),
    (0x3C259, "Load function pointer from table"),
    (0x3C25B, "Call entity-specific function via BX"),
]

for addr, comment in critical_instructions:
    idc.set_cmt(addr, comment, 0)
    print(f"✓ 0x{addr:X}: {comment[:50]}...")

# Name the function table
print("\n=== Naming Entity Function Dispatch Table ===\n")

# funcs_3C261 is the function table used at 0x3C259
table_addr = 0x3C261
if idc.set_name(table_addr, "entity_type_function_table", idc.SN_CHECK):
    print(f"✓ Named function table @ 0x{table_addr:X}")
    idc.set_cmt(table_addr, "Entity type-specific function dispatch table. Indexed by [entity+0Ch] field.", 0)
else:
    print(f"✗ Failed to name table @ 0x{table_addr:X}")

print("\n\nRemaining names added.")
output_file.close()
idc.qexit(0)
