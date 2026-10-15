with open('C:/Users/yotam/projects/falcon3/status.md', 'rb') as f:
    content = f.read()

# Find the section
idx = content.find(b'## Immediate Next Steps (in order)')
if idx < 0:
    print('Section not found')
    exit(1)

# Find the end of the section (next ## header)
end_idx = content.find(b'\n## ', content.find(b'\n', content.find(b'## Immediate Next Steps (in order)') + 1))
if end_idx == -1:
    end_idx = len(content)

print(f'Section from {content.find(b"## Immediate Next Steps (in order)")} to {end_idx}')

# Extract the old section
old_section = content[content.find(b'## Immediate Next Steps (in order)'):end_idx]
print('Old section length:', len(old_section))

# New section
new_section = b"""## Immediate Next Steps (in order)

1. **Patch static thunk table in IDA** (unblocks Track C): Run `tools/patch_thunks_ida.py` in IDA Pro to patch the static thunk table with the 66/66 live targets from `thunk_states.json`. This gives agents the true call graph.

2. **Fresh traced run** (populate SEG_HEAP_ALLOC): Run `tools/run_falcon_traced.ps1` with `FALCON_TRACE` env. The AH=48h/49h hooks will populate `SEG_HEAP_ALLOC` with call-site attribution.

3. **Memory-deref + indirect-target hooks** (advice.md \xc2\xa73.3 hooks 2-3): Implement memory-deref (`LES`, `LDS`, `MOV ES:[BX]`) and indirect `CALL/JMP [BX]` logging in `falcon_trace`. Currently unimplemented.

4. **Re-check port-queue C candidates** against new boundaries (post boundary repair). The 87 UNKNOWN candidates include many dispatch-table labels (same call counts) \u2014 not functions. Documented, not pursued."""

# Replace
old_section = content[content.find(b'## Immediate Next Steps (in order)'):content.find(b'\n## ', content.find(b'## Immediate Next Steps (in order)') + 1)]
if old_section in content:
    content = content.replace(old_section, new_section)
    with open('C:/Users/yotam/projects/falcon3/status.md', 'wb') as f:
        f.write(content)
    print('Replaced successfully')
else:
    print('NOT FOUND')
    print('Expected:')
    print(repr(old_section[:200]))
    print('...')
    print('Looking for:')
    print(repr(b'## Immediate Next Steps (in order)'))