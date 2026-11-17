#!/usr/bin/env python3
"""
Test 3D projection math using values captured from IDA.
Implements the fixed_vec3_accumulate_a algorithm.
"""

def fixed_vec3_accumulate(vec_x, vec_y, vec_z, scale_x, scale_y, scale_z, div_x, div_y, div_z):
    """
    Implement the fixed_vec3_accumulate_a algorithm.
    
    Formula: Result = (X*ScaleX/DivX) + (Y*ScaleY/DivY) + (Z*ScaleZ/DivZ)
    """
    
    # X component
    product_x = vec_x * scale_x
    quotient_x = product_x // div_x
    remainder_x = product_x % div_x
    result = remainder_x
    
    print(f"X: {vec_x} * {scale_x} = {product_x}")
    print(f"   {product_x} / {div_x} = {quotient_x} remainder {remainder_x}")
    print(f"   Contribution: {remainder_x}")
    
    # Y component
    product_y = vec_y * scale_y
    quotient_y = product_y // div_y
    remainder_y = product_y % div_y
    result += remainder_y
    
    print(f"Y: {vec_y} * {scale_y} = {product_y}")
    print(f"   {product_y} / {div_y} = {quotient_y} remainder {remainder_y}")
    print(f"   Contribution: {remainder_y}")
    
    # Z component
    product_z = vec_z * scale_z
    quotient_z = product_z // div_z
    remainder_z = product_z % div_z
    result += remainder_z
    
    print(f"Z: {vec_z} * {scale_z} = {product_z}")
    print(f"   {product_z} / {div_z} = {quotient_z} remainder {remainder_z}")
    print(f"   Contribution: {remainder_z}")
    
    print(f"\nTotal Result: {result} (0x{result:04X})")
    
    # Check if result needs to be interpreted as signed 16-bit
    if result > 32767:
        signed_result = result - 65536
        print(f"Signed 16-bit: {signed_result}")
    else:
        signed_result = result
    
    return signed_result

def main():
    print("="*80)
    print("3D PROJECTION MATH TEST")
    print("="*80)
    print()
    
    # Values captured from IDA (idle state)
    print("Test Case 1: Idle State Values")
    print("-"*80)
    
    vec_x = 7397
    vec_y = 29447
    vec_z = 802
    
    scale_x = 179
    scale_y = 183
    scale_z = 182
    
    div_x = 32771
    div_y = 32779
    div_z = 32783
    
    print(f"Vector: ({vec_x}, {vec_y}, {vec_z})")
    print(f"Scale:  ({scale_x}, {scale_y}, {scale_z})")
    print(f"Divisor: ({div_x}, {div_y}, {div_z})")
    print()
    
    result = fixed_vec3_accumulate(vec_x, vec_y, vec_z, 
                                   scale_x, scale_y, scale_z,
                                   div_x, div_y, div_z)
    
    print()
    print("="*80)
    print("ANALYSIS")
    print("="*80)
    print()
    
    # Analyze divisors
    print("Divisor Analysis:")
    print(f"  Average: {(div_x + div_y + div_z) / 3:.1f}")
    print(f"  Close to 32768 (0x8000) = 2^15")
    print(f"  Variance: X={div_x-32768:+d}, Y={div_y-32768:+d}, Z={div_z-32768:+d}")
    print()
    print("This suggests a custom 15-bit normalization scheme,")
    print("possibly with slight adjustments per axis for lens distortion")
    print("or aspect ratio correction.")
    print()
    
    # Analyze scale factors
    print("Scale Factor Analysis:")
    print(f"  Average: {(scale_x + scale_y + scale_z) / 3:.1f}")
    print(f"  Small values (< 200) suggest:")
    print(f"    - Narrow field of view")
    print(f"    - Or world coordinates in large units")
    print()
    
    # Test with simple values
    print("="*80)
    print("Test Case 2: Simple Values")
    print("-"*80)
    print()
    print("Testing with vector (100, 100, 100) and scale (1000, 1000, 1000):")
    print()
    
    result2 = fixed_vec3_accumulate(100, 100, 100,
                                    1000, 1000, 1000,
                                    32768, 32768, 32768)
    
    print()
    print(f"Expected for typical fixed-point: {100*1000//32768} per component × 3 = {(100*1000//32768)*3}")
    print(f"Actual result: {result2}")
    
    # Test perspective projection
    print()
    print("="*80)
    print("Test Case 3: Perspective Projection Simulation")
    print("-"*80)
    print()
    
    # Simulated waypoint at (1000, 2000, 500)
    # Camera at (500, 1500, 0)
    # Relative position: (500, 500, 500)
    
    cam_x = 500
    cam_y = 500  
    cam_z = 500
    
    # Projection matrix for screen_x (M11, M12, M13)
    m11 = 1000  # Focal length / aspect
    m12 = 0
    m13 = 0
    
    print(f"Camera-relative position: ({cam_x}, {cam_y}, {cam_z})")
    print(f"Projection matrix row 1: ({m11}, {m12}, {m13})")
    print()
    
    screen_x = fixed_vec3_accumulate(cam_x, cam_y, cam_z,
                                     m11, m12, m13,
                                     32768, 32768, 32768)
    
    print()
    print(f"Projected screen_x: {screen_x}")
    print(f"After centering (+160): {screen_x + 160}")
    print()
    
    if 0 <= screen_x + 160 <= 319:
        print("✓ Within screen bounds (0-319)")
    else:
        print("✗ Outside screen bounds")

if __name__ == '__main__':
    main()
