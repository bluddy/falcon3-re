import json

data = json.load(open('func_15a8b0.json'))

print('=== overlay_r46_processor Analysis ===\n')
print(f'Address: {data["address"]}')
print(f'Size: {data["size"]} bytes')
print(f'Disassembly lines: {data["disasm_line_count"]}')
print(f'Callees: {data["callee_count"]}')
print(f'String refs: {len(data["string_refs"])}')

print('\n=== String References ===')
for ref in data['string_refs']:
    print(f'  {ref["addr"]}: "{ref["value"]}"')

print(f'\n=== Top 20 Callees (of {data["callee_count"]}) ===')
for callee in data['callees'][:20]:
    print(f'  {callee["addr"]}: {callee["name"]}')

print('\n=== File I/O Pattern Analysis ===')
# Count op_dispatch calls
op_dispatch_count = sum(1 for line in data['disasm'] if 'op_dispatch_far_entry' in line)
op_dispatch_wide_count = sum(1 for line in data['disasm'] if 'op_dispatch_far_wide' in line)
string_concat_count = sum(1 for line in data['disasm'] if 'string_concatenate' in line)
int_to_str_count = sum(1 for line in data['disasm'] if 'int_to_string_converter' in line)

print(f'  op_dispatch_far_entry calls: {op_dispatch_count}')
print(f'  op_dispatch_far_wide calls: {op_dispatch_wide_count}')
print(f'  string_concatenate calls: {string_concat_count}')
print(f'  int_to_string_converter calls: {int_to_str_count}')

print('\n=== File Types Detected ===')
files = set()
for ref in data['string_refs']:
    val = ref['value']
    if '.' in val:
        # Extract extension
        parts = val.split('.')
        if len(parts) >= 2:
            ext = parts[-1].rstrip('`')
            files.add(f'.{ext}')

for file_type in sorted(files):
    print(f'  {file_type}')
