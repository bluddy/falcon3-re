import json

data = json.load(open('ui_rendering_extraction.json'))

func = data['ui_element_render_complex_a']
print('ui_element_render_complex_a')
print('='*80)
print(f'Address: {func["address"]}')
print(f'Size: {func["size"]} bytes')
print(f'\nCalls {len(func["calls"])} functions:')
for call in func['calls']:
    print(f'  {call["name"]} at {call["address"]}')

print('\nCalled by:')
for xref in func['xrefs_to'][:15]:
    print(f'  {xref["name"]} at {xref["address"]}')

print('\n' + '='*80)
print('DISASSEMBLY:')
print('='*80)
for i, line in enumerate(func['disassembly']):
    print(f'{i:3d}: {line}')
