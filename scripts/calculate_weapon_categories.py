"""
Calculate weapon categories using the hash formula.
Based on fixed_vec3_accumulate_a function analysis.

From vec3_setup_trace.txt we have weapon parameters:
- Weapon BX=5: field_06=0x380, field_08=0x1D78, field_0A=0x08
- Weapon BX=6: field_06=0x380, field_08=0x2710, field_0A=0x10
- Weapon BX=9: field_06=0x318, field_08=0x1004, field_0A=0x18

From fixed_vec3_accumulate_a disassembly:
- Divisors: X=32771 (0x8003), Y=32779 (0x800B), Z=32783 (0x800F)
- Need to extract scale factors from IDA manually
"""

import json

# Weapon parameters from trace
weapons = {
    5: {"field_06": 0x380, "field_08": 0x1D78, "field_0A": 0x08},
    6: {"field_06": 0x380, "field_08": 0x2710, "field_0A": 0x10},
    9: {"field_06": 0x318, "field_08": 0x1004, "field_0A": 0x18},
}

# Divisors and scale factors (extracted from IDA)
div_x = 32771  # 0x8003
div_y = 32779  # 0x800B
div_z = 32783  # 0x800F

scale_x = 179  # 0xB3
scale_y = 183  # 0xB7
scale_z = 182  # 0xB6

def calculate_category(field_06, field_08, field_0A, scale_x, scale_y, scale_z):
    """
    Calculate weapon category using the hash formula.
    Uses 16-bit x86 MUL/DIV semantics (DX:AX intermediate).
    
    x86 MUL: AX * operand -> DX:AX (32-bit result)
    x86 DIV: DX:AX / operand -> quotient in AX, remainder in DX
    
    The code does: MOV CX, DX after each DIV, so it's using the HIGH word
    of the division result (quotient >> 16 essentially).
    """
    # X component: field_06 * scale_x / div_x
    # MUL produces 32-bit result in DX:AX
    product_x = field_06 * scale_x
    # DIV: divide 32-bit DX:AX by div_x
    quotient_x = product_x // div_x
    remainder_x = product_x % div_x
    # Code stores DX, but what is DX after DIV?
    # After DIV of 32-bit by 16-bit: AX = quotient (16 bits), DX = remainder (16 bits)
    # Then MOV CS:[vec3_x], DX - stores the remainder
    # Then MOV CX, DX - adds remainder to result
    result_x = remainder_x
    
    # Same for Y and Z
    product_y = field_08 * scale_y
    quotient_y = product_y // div_y
    remainder_y = product_y % div_y
    result_y = remainder_y
    
    product_z = field_0A * scale_z
    quotient_z = product_z // div_z
    remainder_z = product_z % div_z
    result_z = remainder_z
    
    # Sum them (CX = DX + DX + DX)
    category = (result_x + result_y + result_z) & 0xFFFF
    
    # Mask to 10 bits
    category_masked = category & 0x3FF
    
    # Extract base category (bits 0-4) and subcategory (bits 5-9)
    base_category = category_masked & 0x1F
    sub_category = (category_masked >> 5) & 0x1F
    
    return {
        "result_x": result_x,
        "result_y": result_y,
        "result_z": result_z,
        "category_raw": category,
        "category_masked": category_masked,
        "base_category": base_category,
        "sub_category": sub_category
    }

print("=" * 70)
print("WEAPON CATEGORY CALCULATION")
print("=" * 70)
print()

print("Known divisors:")
print(f"  div_x = {div_x} (0x{div_x:04X})")
print(f"  div_y = {div_y} (0x{div_y:04X})")
print(f"  div_z = {div_z} (0x{div_z:04X})")
print()

print("Actual scale factors (from IDA):")
print(f"  scale_x = {scale_x} (0x{scale_x:04X})")
print(f"  scale_y = {scale_y} (0x{scale_y:04X})")
print(f"  scale_z = {scale_z} (0x{scale_z:04X})")
print()

print("Calculating categories...")
print("-" * 70)

for weapon_id, params in weapons.items():
    result = calculate_category(
        params["field_06"],
        params["field_08"],
        params["field_0A"],
        scale_x, scale_y, scale_z
    )
    
    print(f"\nWeapon {weapon_id}:")
    print(f"  Parameters: field_06=0x{params['field_06']:04X} ({params['field_06']}), "
          f"field_08=0x{params['field_08']:04X} ({params['field_08']}), "
          f"field_0A=0x{params['field_0A']:04X} ({params['field_0A']})")
    print(f"  Products: X={params['field_06']}*{scale_x}={params['field_06']*scale_x}, "
          f"Y={params['field_08']}*{scale_y}={params['field_08']*scale_y}, "
          f"Z={params['field_0A']}*{scale_z}={params['field_0A']*scale_z}")
    print(f"  Remainders: X={result['result_x']}, Y={result['result_y']}, Z={result['result_z']}")
    print(f"  Raw sum: {result['category_raw']} (0x{result['category_raw']:04X})")
    print(f"  Masked (0x3FF): {result['category_masked']} (0x{result['category_masked']:03X})")
    print(f"  Base category: {result['base_category']}")
    print(f"  Sub-category: {result['sub_category']}")


print()
print("=" * 70)

# Save results
output_path = "C:\\Users\\ybarnoy\\projects\\falcon3\\temp\\weapon_categories_calculated.json"
with open(output_path, 'w') as f:
    output = {}
    for weapon_id, params in weapons.items():
        result = calculate_category(
            params["field_06"],
            params["field_08"],
            params["field_0A"],
            scale_x, scale_y, scale_z
        )
        output[f"weapon_{weapon_id}"] = result
    json.dump(output, f, indent=2)

print(f"\nResults saved to: {output_path}")
