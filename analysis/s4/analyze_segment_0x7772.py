"""
Analyze data from segment 0x7772 to identify table types.

Run this after extracting data from IDA.
"""

import struct
import math

def analyze_table_pattern(data, offset, entry_size=4, count=64):
    """
    Analyze a table to guess its purpose.
    
    Args:
        data: bytes object with table data
        offset: starting offset in data
        entry_size: bytes per entry (4 = dword)
        count: number of entries to analyze
    """
    print(f"\nAnalyzing table at offset 0x{offset:04X}")
    print(f"Entry size: {entry_size} bytes, Count: {count}")
    print("=" * 70)
    
    entries = []
    for i in range(count):
        pos = offset + (i * entry_size)
        if pos + entry_size > len(data):
            break
        
        if entry_size == 2:
            val = struct.unpack('<H', data[pos:pos+2])[0]
            # Treat as signed
            if val >= 0x8000:
                signed_val = val - 0x10000
            else:
                signed_val = val
        elif entry_size == 4:
            val = struct.unpack('<I', data[pos:pos+4])[0]
            # Try as 32-bit signed
            if val >= 0x80000000:
                signed_val = val - 0x100000000
            else:
                signed_val = val
        else:
            continue
        
        entries.append((val, signed_val))
    
    # Show first 16 entries
    print(f"\nFirst 16 entries:")
    print(f"{'Index':<6} {'Hex':<12} {'Unsigned':<12} {'Signed':<12} {'FixedPt':<12}")
    print("-" * 70)
    
    for i, (val, signed_val) in enumerate(entries[:16]):
        # Interpret as fixed-point with various scales
        fp_16 = signed_val / 65536.0  # 16.16 fixed point
        fp_8 = signed_val / 256.0      # 24.8 fixed point
        
        if entry_size == 4:
            print(f"{i:<6} 0x{val:08X}  {val:<12} {signed_val:<12} {fp_16:+.4f}")
        else:
            print(f"{i:<6} 0x{val:04X}      {val:<12} {signed_val:<12} {fp_8:+.4f}")
    
    # Pattern analysis
    print(f"\nPattern Analysis:")
    
    # Check if values are monotonic
    signed_vals = [s for _, s in entries]
    is_increasing = all(signed_vals[i] <= signed_vals[i+1] for i in range(len(signed_vals)-1))
    is_decreasing = all(signed_vals[i] >= signed_vals[i+1] for i in range(len(signed_vals)-1))
    
    if is_increasing:
        print("  [✓] Monotonically increasing (linear or power table)")
    elif is_decreasing:
        print("  [✓] Monotonically decreasing (reciprocal table?)")
    else:
        print("  [✓] Non-monotonic (trig table or complex function)")
    
    # Check for oscillating pattern (sin/cos)
    changes = 0
    for i in range(1, len(signed_vals)):
        if (signed_vals[i] - signed_vals[i-1]) * (signed_vals[i-1] - signed_vals[i-2] if i > 1 else 1) < 0:
            changes += 1
    
    if changes > len(signed_vals) / 4:
        print("  [✓] Oscillating pattern detected (sin/cos likely)")
    
    # Check value range for fixed-point identification
    max_val = max(abs(s) for s in signed_vals)
    
    if max_val <= 0x10000:  # Fits in 16.16 fixed [-1, 1]
        print(f"  [✓] Values fit in 16.16 fixed point [-1, 1] range")
        print(f"      Max absolute value: {max_val / 65536.0:.4f}")
        
        # Check if it looks like sin/cos (values near -1 to 1)
        fp_vals = [s / 65536.0 for s in signed_vals]
        if -1.1 <= min(fp_vals) <= -0.9 and 0.9 <= max(fp_vals) <= 1.1:
            print(f"  [✓✓] LIKELY SIN/COS TABLE (values span [-1, 1])")
    
    elif max_val <= 0x1000000:  # 24.8 fixed point
        print(f"  [✓] Values fit in 24.8 fixed point range")
        print(f"      Max absolute value: {max_val / 256.0:.4f}")
    
    else:
        print(f"  [✓] Large values (not normalized fixed-point)")
        print(f"      Max absolute value: {max_val}")
    
    # Try to match sin/cos pattern if non-monotonic
    if not is_increasing and not is_decreasing and len(entries) >= 32:
        print(f"\n  Testing sin/cos hypothesis:")
        
        # Generate expected sin values for comparison
        fp_vals = [s / 65536.0 for s in signed_vals[:32]]
        
        # Try different periods
        for period in [256, 360, 512, 1024]:
            angle_step = 2 * math.pi / period
            expected = [math.sin(i * angle_step) for i in range(32)]
            
            # Calculate RMS error
            errors = [(fp_vals[i] - expected[i]) ** 2 for i in range(len(fp_vals))]
            rms = math.sqrt(sum(errors) / len(errors))
            
            if rms < 0.1:
                print(f"    [✓✓] MATCH: SIN table with {period} entries per cycle (RMS error: {rms:.4f})")
            
            # Try cosine
            expected_cos = [math.cos(i * angle_step) for i in range(32)]
            errors_cos = [(fp_vals[i] - expected_cos[i]) ** 2 for i in range(len(fp_vals))]
            rms_cos = math.sqrt(sum(errors_cos) / len(errors_cos))
            
            if rms_cos < 0.1:
                print(f"    [✓✓] MATCH: COS table with {period} entries per cycle (RMS error: {rms_cos:.4f})")
    
    # Check for square root pattern
    if is_increasing and len(entries) >= 16:
        print(f"\n  Testing square root hypothesis:")
        
        # Expected sqrt pattern
        actual = [s for _, s in entries[:16]]
        expected = [int(math.sqrt(i) * 256) for i in range(16)]  # Assuming 8.8 fixed
        
        errors = [(actual[i] - expected[i]) ** 2 for i in range(len(actual))]
        rms = math.sqrt(sum(errors) / len(errors)) if errors else 0
        
        if rms < 100:
            print(f"    [✓✓] MATCH: SQRT table (RMS error: {rms:.2f})")
    
    # Check for reciprocal (1/x) pattern
    if is_decreasing and len(entries) >= 16:
        print(f"\n  Testing reciprocal (1/x) hypothesis:")
        
        actual = [s for _, s in entries[:16] if s != 0]
        expected = [int(65536.0 / (i+1)) for i in range(len(actual))]  # 16.16 fixed
        
        errors = [(actual[i] - expected[i]) ** 2 for i in range(len(actual))]
        rms = math.sqrt(sum(errors) / len(errors)) if errors else 0
        
        if rms < 1000:
            print(f"    [✓✓] MATCH: Reciprocal (1/x) table (RMS error: {rms:.2f})")

def main():
    """
    Main analysis function.
    
    To use:
    1. Extract data from IDA segment 0x7772
    2. Save as binary file: segment_0x7772.bin
    3. Run this script
    """
    import sys
    from pathlib import Path
    
    # Check for input file
    data_file = Path('segment_0x7772.bin')
    
    if not data_file.exists():
        print("=" * 70)
        print("Segment 0x7772 Data Analyzer")
        print("=" * 70)
        print(f"\nERROR: {data_file} not found!")
        print("\nTo use this tool:")
        print("1. In IDA, navigate to segment 0x7772")
        print("2. Select the data range (e.g., 0x0000 to 0x2000)")
        print("3. Edit → Export data → Binary file")
        print("4. Save as: segment_0x7772.bin")
        print("5. Run this script again")
        print("\nAlternatively, provide test data as command line argument.")
        return
    
    # Load data
    with open(data_file, 'rb') as f:
        data = f.read()
    
    print("=" * 70)
    print("Segment 0x7772 Data Analyzer")
    print("=" * 70)
    print(f"\nLoaded {len(data)} bytes from {data_file}")
    
    # Analyze table at 0x0F34 (the one we know about)
    if len(data) >= 0x0F34 + 256:
        analyze_table_pattern(data, 0x0F34, entry_size=4, count=64)
    
    # Look for other interesting tables
    print("\n" + "=" * 70)
    print("Scanning for other tables...")
    print("=" * 70)
    
    # Scan for table-like patterns
    # (blocks of monotonic or periodic data)
    
    # Check every 64-byte boundary for potential tables
    for offset in range(0, min(len(data) - 256, 0x2000), 64):
        if offset == 0x0F34:  # Skip the one we already analyzed
            continue
        
        # Quick check: are values reasonably table-like?
        try:
            values = [struct.unpack('<I', data[offset+i:offset+i+4])[0] 
                     for i in range(0, min(64, len(data)-offset-4), 4)]
            
            # Check if it looks like a table (not all zeros, not all 0xFFFFFFFF)
            non_zero = sum(1 for v in values if v != 0)
            non_ff = sum(1 for v in values if v != 0xFFFFFFFF)
            
            if non_zero > len(values) * 0.8 and non_ff > len(values) * 0.8:
                # Looks interesting, analyze it
                print(f"\nPotential table found at offset 0x{offset:04X}")
                analyze_table_pattern(data, offset, entry_size=4, count=16)
        except:
            continue

if __name__ == '__main__':
    main()
