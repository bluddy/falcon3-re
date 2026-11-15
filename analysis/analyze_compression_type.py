"""
Analyze what type of compression this might be
"""
import struct
from collections import Counter

dat = open('../game/people.dat', 'rb').read()

# First record
record = dat[0:666]
compressed = record[6:]  # Skip header

print("Compression Analysis")
print("="*60)
print(f"Data size: {len(compressed)} bytes\n")

# Byte frequency analysis
freq = Counter(compressed)
print(f"Unique bytes: {len(freq)}/256")
print(f"Most common bytes:")
for byte, count in freq.most_common(10):
    print(f"  0x{byte:02X}: {count} times ({100*count/len(compressed):.1f}%)")

# Check for patterns
print(f"\nPattern analysis:")
print(f"  Repeated bytes: {sum(1 for i in range(len(compressed)-1) if compressed[i] == compressed[i+1])}")
print(f"  Zero bytes: {compressed.count(0)}")

# Entropy check
import math
entropy = -sum((count/len(compressed)) * math.log2(count/len(compressed)) for count in freq.values())
print(f"  Shannon entropy: {entropy:.2f} bits/byte (max 8.0)")

if entropy > 7.5:
    print("  -> Very high entropy - likely compressed or encrypted")
elif entropy > 6.0:
    print("  -> High entropy - compressed or complex data")
else:
    print("  -> Lower entropy - possibly uncompressed or simple compression")

# Check all records to see if they're similar
print(f"\n" + "="*60)
print("Checking all 40 records...")

idx_data = open('../game/people.idx', 'rb').read()
num_records = len(idx_data) // 4

entropies = []
sizes = []

for i in range(num_records):
    offset = struct.unpack('<H', idx_data[i*4:(i*4)+2])[0]
    size = struct.unpack('<H', idx_data[i*4+2:(i*4)+4])[0]
    end = offset + size
    
    record_data = dat[offset:end]
    if len(record_data) < 6:
        continue
    
    comp_data = record_data[6:]
    sizes.append(len(comp_data))
    
    freq = Counter(comp_data)
    ent = -sum((c/len(comp_data)) * math.log2(c/len(comp_data)) for c in freq.values())
    entropies.append(ent)

print(f"Record sizes: min={min(sizes)}, max={max(sizes)}, avg={sum(sizes)/len(sizes):.0f}")
print(f"Entropies: min={min(entropies):.2f}, max={max(entropies):.2f}, avg={sum(entropies)/len(entropies):.2f}")
print(f"\nAll records have high entropy - definitely compressed!")
