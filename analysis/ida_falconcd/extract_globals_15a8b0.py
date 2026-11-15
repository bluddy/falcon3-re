"""
Extract and categorize all globals accessed by theater_campaign_file_loader
This will help us understand data structures and rename globals
"""
import json
import re

data = json.load(open('func_15a8b0.json'))

# Extract all global references
globals_found = {}

for line in data['disasm']:
    # Look for segment:global patterns
    # Pattern 1: es:byte_XXXXX, es:word_XXXXX, es:dword_XXXXX
    matches = re.findall(r'es:(byte_[0-9A-F]+|word_[0-9A-F]+|dword_[0-9A-F]+)', line)
    for match in matches:
        # Find which segment was loaded into ES in previous lines
        idx = data['disasm'].index(line)
        seg = None
        for i in range(max(0, idx-5), idx):
            prev_line = data['disasm'][i]
            if 'mov' in prev_line and 'es' in prev_line and 'ax' in prev_line:
                # Extract segment value
                seg_matches = re.findall(r'(602Eh|7894h|709Fh|7A32h|4FC2h)', prev_line)
                if seg_matches:
                    seg = seg_matches[0]
        
        if seg:
            key = f'{seg}:{match}'
            if key not in globals_found:
                globals_found[key] = []
            globals_found[key].append(line.strip())
    
    # Pattern 2: Named globals
    named_matches = re.findall(r'es:([a-zA-Z_][a-zA-Z0-9_]+)', line)
    for match in matches:
        if match not in ['es']:  # Skip register names
            idx = data['disasm'].index(line)
            seg = None
            for i in range(max(0, idx-5), idx):
                prev_line = data['disasm'][i]
                if 'mov' in prev_line and 'es' in prev_line:
                    seg_matches = re.findall(r'(602Eh|7894h|709Fh|7A32h|4FC2h)', prev_line)
                    if seg_matches:
                        seg = seg_matches[0]
            
            if seg:
                key = f'{seg}:{match}'
                if key not in globals_found:
                    globals_found[key] = []
                globals_found[key].append(line.strip())

# Categorize by segment
segments = {
    '602Eh': 'Main Data Segment',
    '7894h': 'Mission Data Segment',
    '709Fh': 'Graphics Configuration',
    '7A32h': 'DGROUP (Configuration)',
    '4FC2h': 'Unknown Segment'
}

print('=== GLOBALS ACCESSED BY theater_campaign_file_loader ===\n')

for seg, desc in segments.items():
    seg_globals = {k: v for k, v in globals_found.items() if k.startswith(seg)}
    if seg_globals:
        print(f'\n=== {desc} ({seg}) - {len(seg_globals)} globals ===')
        for global_name, usages in sorted(seg_globals.items()):
            print(f'\n{global_name}')
            # Show first 3 usages
            for usage in usages[:3]:
                print(f'  {usage}')
            if len(usages) > 3:
                print(f'  ... and {len(usages) - 3} more usages')

# Count operations by type
print('\n\n=== OPERATION SUMMARY ===')
read_count = sum(1 for line in data['disasm'] if 'mov' in line and ', es:' in line)
write_count = sum(1 for line in data['disasm'] if 'mov' in line and 'es:' in line and ', ' in line and line.index('es:') < line.index(', '))
cmp_count = sum(1 for line in data['disasm'] if 'cmp' in line and 'es:' in line)

print(f'Reads from globals (mov reg, es:global): {read_count}')
print(f'Writes to globals (mov es:global, value): {write_count}')
print(f'Comparisons with globals: {cmp_count}')

# Look for arrays/loops
print('\n=== ARRAY ACCESS PATTERNS ===')
array_accesses = [line for line in data['disasm'] if 'es:[' in line and '+' in line]
print(f'Array index expressions: {len(array_accesses)}')
for line in array_accesses[:10]:
    print(f'  {line.strip()}')
if len(array_accesses) > 10:
    print(f'  ... and {len(array_accesses) - 10} more')
