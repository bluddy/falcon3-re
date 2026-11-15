"""
Test RLE decompression on MONITOR.DAT to see if it works better than MADFONT.
"""
import struct
from pathlib import Path
from rle_decompress import parse_idx_dat, extract_dat_record, rle_decompress

def test_monitor_rle():
    """Test RLE on MONITOR.DAT."""
    
    print("Testing RLE decompression on MONITOR.DAT")
    print("=" * 80)
    
    records = parse_idx_dat('../game/MONITOR.IDX', '../game/MONITOR.DAT')
    
    print(f"Found {len(records)} records\n")
    
    # Test each record
    for i, rec in enumerate(records):
        extracted = extract_dat_record(rec['data'])
        
        if not extracted:
            print(f"Record {i:2}: Failed to extract")
            continue
        
        magic = extracted['magic']
        w, h = extracted['width'], extracted['height']
        comp_size = extracted['compressed_size']
        decomp_size = extracted['decompressed_size']
        
        expected_pixels = w * h
        
        print(f"Record {i:2}: magic=0x{magic:04X}, header=({w:3},{h:3}), "
              f"compressed={comp_size:4}B, decompressed={decomp_size:4}B", end='')
        
        if magic != 0x0400:
            print(f" - WRONG MAGIC")
            continue
        
        if decomp_size == 0:
            # Check first byte of compressed data
            if comp_size > 0:
                first_byte = extracted['compressed_data'][0]
                print(f" - decomp=0 (first byte: 0x{first_byte:02X})")
            else:
                print(f" - decomp=0 (no data)")
        else:
            ratio = decomp_size / expected_pixels if expected_pixels > 0 else 0
            print(f" - expected={expected_pixels}, ratio={ratio:.4f}")
            
            # Check for planar format possibility
            planar_bytes = ((expected_pixels) + 7) // 8 * 4
            if decomp_size == planar_bytes:
                print(f"      -> Could be planar! ({decomp_size} bytes = {w}x{h} planar)")

if __name__ == '__main__':
    test_monitor_rle()
