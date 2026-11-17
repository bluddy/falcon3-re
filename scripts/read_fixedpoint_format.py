"""
Read the fixed-point divisor values to determine the format.
"""

import idc
import idaapi

def main():
    print("="*80)
    print("FIXED-POINT FORMAT DETECTION")
    print("="*80)
    
    idaapi.auto_wait()
    
    # Read divisor values
    div_x = idc.get_wide_word(0x22C83)
    div_y = idc.get_wide_word(0x22C85)
    div_z = idc.get_wide_word(0x22C87)
    
    print(f"\nDivisor Values:")
    print(f"  X: {div_x:5d} (0x{div_x:04X})")
    print(f"  Y: {div_y:5d} (0x{div_y:04X})")
    print(f"  Z: {div_z:5d} (0x{div_z:04X})")
    
    # Determine format
    if div_x == 256 and div_y == 256 and div_z == 256:
        fmt = "8.8 fixed-point (8 bits integer, 8 bits fractional)"
        precision = 1.0 / 256
        int_range = (-128, 127)
        print(f"\n✓ Format: {fmt}")
        print(f"  Precision: 1/{256} = {precision:.6f}")
        print(f"  Integer range: {int_range[0]} to {int_range[1]}")
        print(f"  Total range: {int_range[0]} to {int_range[1] + precision:.2f}")
        
    elif div_x == 4096:
        fmt = "12.4 fixed-point (12 bits integer, 4 bits fractional)"
        precision = 1.0 / 16
        int_range = (-2048, 2047)
        print(f"\n✓ Format: {fmt}")
        print(f"  Precision: 1/16 = {precision:.6f}")
        print(f"  Integer range: {int_range[0]} to {int_range[1]}")
        
    elif div_x == 65536:
        fmt = "16.16 fixed-point (16 bits integer, 16 bits fractional)"
        precision = 1.0 / 65536
        int_range = (-32768, 32767)
        print(f"\n✓ Format: {fmt}")
        print(f"  Precision: 1/65536 = {precision:.8f}")
        print(f"  Integer range: {int_range[0]} to {int_range[1]}")
        
    else:
        fmt = f"Custom format (divisor = {div_x})"
        print(f"\n? Format: {fmt}")
        print(f"  Divisors vary: X={div_x}, Y={div_y}, Z={div_z}")
    
    # Read matrix scale values
    print(f"\n{'='*80}")
    print("TRANSFORM MATRIX SCALE FACTORS")
    print(f"{'='*80}")
    
    scale_x = idc.get_wide_word(0x22C7D)
    scale_y = idc.get_wide_word(0x22C7F)
    scale_z = idc.get_wide_word(0x22C81)
    
    print(f"\nCurrent Matrix Values:")
    print(f"  Scale X (M11): {scale_x:5d} (0x{scale_x:04X})")
    print(f"  Scale Y (M12): {scale_y:5d} (0x{scale_y:04X})")
    print(f"  Scale Z (M13): {scale_z:5d} (0x{scale_z:04X})")
    
    # Read vector components
    print(f"\n{'='*80}")
    print("CURRENT VECTOR STATE")
    print(f"{'='*80}")
    
    vec_x = idc.get_wide_word(0x22C71)
    vec_y = idc.get_wide_word(0x22C73)
    vec_z = idc.get_wide_word(0x22C75)
    
    # Interpret as signed
    vec_x = vec_x if vec_x < 32768 else vec_x - 65536
    vec_y = vec_y if vec_y < 32768 else vec_y - 65536
    vec_z = vec_z if vec_z < 32768 else vec_z - 65536
    
    print(f"\nVector Components:")
    print(f"  X: {vec_x:6d} (0x{vec_x & 0xFFFF:04X})")
    print(f"  Y: {vec_y:6d} (0x{vec_y & 0xFFFF:04X})")
    print(f"  Z: {vec_z:6d} (0x{vec_z & 0xFFFF:04X})")
    
    # Output to file
    with open(r'C:\Users\ybarnoy\projects\falcon3\analysis\fixedpoint_format.txt', 'w') as f:
        f.write("FIXED-POINT FORMAT DETECTION\n")
        f.write("="*80 + "\n\n")
        f.write(f"Divisors:\n")
        f.write(f"  X: {div_x:5d} (0x{div_x:04X})\n")
        f.write(f"  Y: {div_y:5d} (0x{div_y:04X})\n")
        f.write(f"  Z: {div_z:5d} (0x{div_z:04X})\n\n")
        f.write(f"Format: {fmt}\n\n")
        f.write(f"Matrix Scale Factors:\n")
        f.write(f"  X: {scale_x:5d} (0x{scale_x:04X})\n")
        f.write(f"  Y: {scale_y:5d} (0x{scale_y:04X})\n")
        f.write(f"  Z: {scale_z:5d} (0x{scale_z:04X})\n\n")
        f.write(f"Vector State:\n")
        f.write(f"  X: {vec_x:6d}\n")
        f.write(f"  Y: {vec_y:6d}\n")
        f.write(f"  Z: {vec_z:6d}\n")
    
    print(f"\n✓ Saved to: analysis/fixedpoint_format.txt")
    
    idc.qexit(0)

if __name__ == '__main__':
    main()
