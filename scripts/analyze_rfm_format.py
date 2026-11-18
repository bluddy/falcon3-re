"""
Analyze .RFM file format (likely AI maneuver/behavior data).
Files are named DEFBFM*.RFM (Default Basic Fighter Maneuvers).
"""

from pathlib import Path
import struct

def analyze_rfm_file(file_path):
    """Analyze structure of an RFM file."""
    with open(file_path, 'rb') as f:
        data = f.read()
    
    print(f"\n{'='*70}")
    print(f"FILE: {file_path.name}")
    print(f"{'='*70}")
    print(f"Size: {len(data)} bytes")
    print()
    
    # Header analysis
    print("HEADER ANALYSIS (first 32 bytes):")
    print("-" * 70)
    
    header = data[:32]
    for i in range(0, 32, 4):
        bytes_chunk = header[i:i+4]
        as_u32 = struct.unpack('<I', bytes_chunk)[0] if len(bytes_chunk) == 4 else 0
        as_i32 = struct.unpack('<i', bytes_chunk)[0] if len(bytes_chunk) == 4 else 0
        as_u16s = struct.unpack('<HH', bytes_chunk) if len(bytes_chunk) == 4 else (0, 0)
        hex_str = ' '.join(f'{b:02X}' for b in bytes_chunk)
        
        print(f"  +0x{i:02X}: {hex_str:11s} = u32:{as_u32:10d} i32:{as_i32:11d} u16:({as_u16s[0]}, {as_u16s[1]})")
    
    # The first word might be a signature/version
    first_word = struct.unpack('<H', data[0:2])[0]
    print(f"\nFirst word: 0x{first_word:04X} ({first_word})")
    
    # Count byte value frequencies
    print("\nBYTE VALUE FREQUENCY (top 20):")
    print("-" * 70)
    
    freq = {}
    for b in data:
        freq[b] = freq.get(b, 0) + 1
    
    sorted_freq = sorted(freq.items(), key=lambda x: x[1], reverse=True)[:20]
    for value, count in sorted_freq:
        pct = count * 100.0 / len(data)
        ascii_char = chr(value) if 32 <= value < 127 else '.'
        print(f"  0x{value:02X} ({value:3d} '{ascii_char}'):  {count:4d} times ({pct:5.1f}%)")
    
    # Look for patterns
    print("\nPATTERN ANALYSIS:")
    print("-" * 70)
    
    # Check if it's a table of fixed-size records
    if len(data) % 2 == 0:
        print(f"  File size is even: {len(data)} bytes")
        print(f"  Possible record counts:")
        for record_size in [2, 4, 8, 16, 32, 47, 94, 188, 376, 752]:
            if len(data) % record_size == 0:
                count = len(data) // record_size
                print(f"    {record_size:3d} bytes/record -> {count:3d} records")
    
    # Detect repeated patterns
    print("\nREPEATED SEQUENCES (4+ bytes):")
    print("-" * 70)
    
    sequences = {}
    for length in [4, 8]:
        for i in range(len(data) - length):
            seq = data[i:i+length]
            if seq in sequences:
                sequences[seq].append(i)
            else:
                sequences[seq] = [i]
    
    repeated = {k: v for k, v in sequences.items() if len(v) >= 2}
    for seq, positions in sorted(repeated.items(), key=lambda x: len(x[1]), reverse=True)[:5]:
        hex_seq = ' '.join(f'{b:02X}' for b in seq)
        print(f"  {hex_seq}: appears {len(positions)} times at offsets {positions[:5]}")
    
    return data

def main():
    game_dir = Path(r"C:\Users\ybarnoy\projects\falcon3\game")
    
    print("=" * 70)
    print("ANALYZING .RFM FILES (Basic Fighter Maneuvers)")
    print("=" * 70)
    
    rfm_files = sorted(game_dir.glob("*.RFM"))[:5]  # Analyze first 5
    
    for rfm_file in rfm_files:
        analyze_rfm_file(rfm_file)
    
    print("\n" + "=" * 70)
    print("COMPARISON SUMMARY")
    print("=" * 70)
    
    # Compare file sizes
    all_rfm = sorted(game_dir.glob("*.RFM"))
    sizes = {}
    for f in all_rfm:
        size = f.stat().st_size
        sizes[size] = sizes.get(size, 0) + 1
    
    print(f"\nTotal .RFM files: {len(all_rfm)}")
    print("\nFile size distribution:")
    for size, count in sorted(sizes.items()):
        print(f"  {size:5d} bytes: {count:2d} files")

if __name__ == "__main__":
    main()
