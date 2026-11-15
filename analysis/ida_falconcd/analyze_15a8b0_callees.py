"""
Deep analysis of theater_campaign_file_loader callees
Extract details about all 70 callees to understand what this function does
"""
import json

data = json.load(open('func_15a8b0.json'))

print('=== theater_campaign_file_loader Callee Analysis ===\n')

# Load all_functions_categorized for context
all_funcs_data = json.load(open('all_functions_categorized.json'))
all_funcs = {f['address'].lower(): f for f in all_funcs_data['all_functions']}

print(f'Total callees: {len(data["callees"])}\n')

# Categorize callees
categories = {
    'file_io': [],
    'menu': [],
    'input': [],
    'validation': [],
    'overlay': [],
    'unknown': []
}

for callee in data['callees']:
    name = callee['name'].lower()
    addr = callee['addr']
    
    # Get additional info
    func_info = all_funcs.get(addr.lower(), {})
    size = func_info.get('size', '?')
    calls = func_info.get('calls', '?')
    
    callee['size'] = size
    callee['calls'] = calls
    
    # Categorize
    if 'op_dispatch' in name or 'flag2224' in name:
        categories['file_io'].append(callee)
    elif 'menu' in name or 'selection' in name or 'config' in name:
        categories['menu'].append(callee)
    elif 'mouse' in name or 'input' in name:
        categories['input'].append(callee)
    elif 'validate' in name or 'check' in name:
        categories['validation'].append(callee)
    elif 'overlay' in name or 'r0' in name or 'r3' in name or 'r06' in name:
        categories['overlay'].append(callee)
    else:
        categories['unknown'].append(callee)

# Print categorized callees
for cat_name, callees in categories.items():
    if callees:
        print(f'\n=== {cat_name.upper()} ({len(callees)}) ===')
        for c in callees:
            print(f'  {c["addr"]}: {c["name"]:<40} ({c["size"]}B, {c["calls"]} callers)')

# Find interesting patterns in disassembly
print('\n\n=== INTERESTING PATTERNS ===\n')

# Global accesses
print('Globals accessed (segment 0x602E):')
globals_602e = set()
for line in data['disasm']:
    if 'es:' in line and '602Eh' in data['disasm'][max(0, data['disasm'].index(line)-3):data['disasm'].index(line)+1]:
        # Extract global name
        if 'es:byte_' in line or 'es:word_' in line or 'es:dword_' in line:
            parts = line.split('es:')
            if len(parts) > 1:
                global_name = parts[1].split(',')[0].split(']')[0].strip()
                if global_name and not global_name.startswith('['):
                    globals_602e.add(global_name)

for g in sorted(globals_602e):
    print(f'  0x602E:{g}')

# Segment 0x7894 accesses
print('\nGlobals accessed (segment 0x7894):')
globals_7894 = set()
for line in data['disasm']:
    if 'es:' in line and '7894h' in data['disasm'][max(0, data['disasm'].index(line)-3):data['disasm'].index(line)+1]:
        if 'es:byte_' in line or 'es:word_' in line or 'es:dword_' in line or 'es:graphics_mode_flag' in line:
            parts = line.split('es:')
            if len(parts) > 1:
                global_name = parts[1].split(',')[0].split(']')[0].strip()
                if global_name and not global_name.startswith('['):
                    globals_7894.add(global_name)

for g in sorted(globals_7894):
    print(f'  0x7894:{g}')

# File operations
print('\nFile operation patterns:')
file_ops = {}
for line in data['disasm']:
    if 'push' in line and any(op in data['disasm'][data['disasm'].index(line):data['disasm'].index(line)+5] for op in ['op_dispatch_far_entry', 'op_dispatch_far_wide']):
        # Look for operation code (last push before call)
        idx = data['disasm'].index(line)
        if idx + 4 < len(data['disasm']):
            next_lines = data['disasm'][idx:idx+5]
            if 'op_dispatch' in ''.join(next_lines):
                # Extract pushed values
                if 'push' in line and any(x in line for x in ['4', '6', '8', '0Ah', '0Ch', '0Eh']):
                    op = line.split('push')[-1].strip()
                    if op not in file_ops:
                        file_ops[op] = 0
                    file_ops[op] += 1

print('  Operation codes pushed:')
for op, count in sorted(file_ops.items()):
    print(f'    {op}: {count} times')

# Loop patterns
print('\nLoop patterns:')
loop_count = sum(1 for line in data['disasm'] if 'loop ' in line or ('jle short' in line and 'inc' in data['disasm'][max(0,data['disasm'].index(line)-2)]))
print(f'  Approximate loops: {loop_count}')

# Initialization patterns
print('\nInitialization patterns (mov xxx, 0):')
zero_inits = [line for line in data['disasm'] if ', 0' in line and ('mov' in line or 'and' in line) and 'es:' in line]
print(f'  Zero initializations: {len(zero_inits)}')
for line in zero_inits[:10]:
    print(f'    {line}')
if len(zero_inits) > 10:
    print(f'    ... and {len(zero_inits) - 10} more')
