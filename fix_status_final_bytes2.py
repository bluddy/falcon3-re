with open('C:/Users/yotam/projects/falcon3/status.md', 'rb') as f:
    content = f.read()

# The exact old text as bytes
old = b"""## Immediate Next Steps (in order)

1. ~~Trace-driven boundary verification~~ **DONE (finding 33)**: 135 functions recovered (1,080 \xe2\x86\x92 1,215), EXACT 204\xe2\x86\x92340. Remaining: 87 UNKNOWN candidates in `boundary_report.json` (incl. `01F5:018F`, 132K calls, IDA refuses even with chunk conversion); MID cases are mostly dispatch-table labels \xe2\x80\x94 documented, not pursued. Re-check port-queue C candidates against new boundaries.
2. ~~Segment classification + thunk-state merge~~ **DONE (finding 34)**: `segment_classification.json` (multi-kind, DGROUP 27687 HYPOTHESIS, resident base PROVEN) + `thunk_states.json` (66/66 stable). Remaining: (a) **fresh traced run** to populate `SEG_HEAP_ALLOC` \xe2\x80\x94 the AH=48h/49h call-site hook postdates both committed traces; (b) confirm DGROUP via a dump-side pointer check (promote HYPOTHESIS \xe2\x86\x92 PROVEN); (c) **patch the static thunk table to the live targets** so agents see the true call graph; (d) memory-deref + indirect-target logging (advice.md \xc2\xa73.3 hooks 2-3) still unimplemented.
3. **Track C first splice test**: Export IDB assembly (`idat -A -Stools/ida_export.asm`), run `extract_routines.py` -> `splice.py` with keyboard unit verified routines -> reassemble -> `mzdiff.py` verification against function_bytes.json ground truth.
4. **Fix mzdiff fixup handling**: Apply RTLink fixups when extracting bytes from EXE for accurate comparison.
5. **10 straggler thunk entries** (user explicitly deferred; findings 19/26).
6. `libscan.py` with compiler libs (MSC 5.1 *and* BC 2.0) for library-function ID."""

new = b"""## Immediate Next Steps (in order)

1. **Patch static thunk table in IDA** (unblocks Track C): Run `tools/patch_thunks_ida.py` in IDA Pro to patch the static thunk table with the 66/66 live targets from `thunk_states.json`. This gives agents the true call graph.

2. **Fresh traced run** (populate SEG_HEAP_ALLOC): Run `tools/run_falcon_traced.ps1` with `FALCON_TRACE` env. The AH=48h/49h hooks will populate `SEG_HEAP_ALLOC` with call-site attribution.

3. **Memory-deref + indirect-target hooks** (advice.md \xc2\xa73.3 hooks 2-3): Implement memory-deref (`LES`, `LDS`, `MOV ES:[BX]`) and indirect `CALL/JMP [BX]` logging in `falcon_trace`. Currently unimplemented.

4. **Re-check port-queue C candidates** against new boundaries (post boundary repair). The 87 UNKNOWN candidates include many dispatch-table labels (same call counts) \u2014 not functions. Documented, not pursued."""

with open('C:/Users/yotam/projects/falcon3/status.md', 'rb') as f:
    content = f.read()

old = b"""## Immediate Next Steps (in order)

1. ~~Trace-driven boundary verification~~ **DONE (finding 33)**: 135 functions recovered (1,080 \xe2\x86\x92 1,215), EXACT 204\xe2\x86\x92340. Remaining: 87 UNKNOWN candidates in `boundary_report.json` (incl. `01F5:018F`, 132K calls, IDA refuses even with chunk conversion); MID cases are mostly dispatch-table labels \xe2\x80\x94 documented, not pursued. Re-check port-queue C candidates against new boundaries.
2. ~~Segment classification + thunk-state merge~~ **DONE (finding 34)**: `segment_classification.json` (multi-kind, DGROUP 27687 HYPOTHESIS, resident base PROVEN) + `thunk_states.json` (66/66 stable). Remaining: (a) **fresh traced run** to populate `SEG_HEAP_ALLOC` \xe2\x80\x94 the AH=48h/49h call-site hook postdates both committed traces; (b) confirm DGROUP via a dump-side pointer check (promote HYPOTHESIS \xe2\x86\x92 PROVEN); (c) **patch the static thunk table to the live targets** so agents see the true call graph; (d) memory-deref + indirect-target logging (advice.md \xc2\xa73.3 hooks 2-3) still unimplemented.
3. **Track C first splice test**: Export IDB assembly (`idat -A -Stools/ida_export.asm`), run `extract_routines.py` -> `splice.py` with keyboard unit verified routines -> reassemble -> `mzdiff.py` verification against function_bytes.json ground truth.
4. **Fix mzdiff fixup handling**: Apply RTLink fixups when extracting bytes from EXE for accurate comparison.
5. **10 straggler thunk entries** (user explicitly deferred; findings 19/26).
6. `libscan.py` with compiler libs (MSC 5.1 *and* BC 2.0) for library-function ID."""

new = b"""## Immediate Next Steps (in order)

1. **Patch static thunk table in IDA** (unblocks Track C): Run `tools/patch_thunks_ida.py` in IDA Pro to patch the static thunk table with the 66/66 live targets from `thunk_states.json`. This gives agents the true call graph.

2. **Fresh traced run** (populate SEG_HEAP_ALLOC): Run `tools/run_falcon_traced.ps1` with `FALCON_TRACE` env. The AH=48h/49h hooks will populate `SEG_HEAP_ALLOC` with call-site attribution.

3. **Memory-deref + indirect-target hooks** (advice.md \xc2\xa73.3 hooks 2-3): Implement memory-deref (`LES`, `LDS`, `MOV ES:[BX]`) and indirect `CALL/JMP [BX]` logging in `falcon_trace`. Currently unimplemented.

4. **Re-check port-queue C candidates** against new boundaries (post boundary repair). The 87 UNKNOWN candidates include many dispatch-table labels (same call counts) \u2014 not functions. Documented, not pursued."""

with open('C:/Users/yotam/projects/falcon3/status.md', 'rb') as f:
    content = f.read()

old = b"""## Immediate Next Steps (in order)

1. ~~Trace-driven boundary verification~~ **DONE (finding 33)**: 135 functions recovered (1,080 \xe2\x86\x92 1,215), EXACT 204\xe2\x86\x92340. Remaining: 87 UNKNOWN candidates in `boundary_report.json` (incl. `01F5:018F`, 132K calls, IDA refuses even with chunk conversion); MID cases are mostly dispatch-table labels \xe2\x80\x94 documented, not pursued. Re-check port-queue C candidates against new boundaries.
2. ~~Segment classification + thunk-state merge~~ **DONE (finding 34)**: `segment_classification.json` (multi-kind, DGROUP 27687 HYPOTHESIS, resident base PROVEN) + `thunk_states.json` (66/66 stable). Remaining: (a) **fresh traced run** to populate `SEG_HEAP_ALLOC` \xe2\x80\x94 the AH=48h/49h call-site hook postdates both committed traces; (b) confirm DGROUP via a dump-side pointer check (promote HYPOTHESIS \xe2\x86\x92 PROVEN); (c) **patch the static thunk table to the live targets** so agents see the true call graph; (d) memory-deref + indirect-target logging (advice.md \xc2\xa73.3 hooks 2-3) still unimplemented.
3. **Track C first splice test**: Export IDB assembly (`idat -A -Stools/ida_export.asm`), run `extract_routines.py` -> `splice.py` with keyboard unit verified routines -> reassemble -> `mzdiff.py` verification against function_bytes.json ground truth.
4. **Fix mzdiff fixup handling**: Apply RTLink fixups when extracting bytes from EXE for accurate comparison.
5. **10 straggler thunk entries** (user explicitly deferred; findings 19/26).
6. `libscan.py` with compiler libs (MSC 5.1 *and* BC 2.0) for library-function ID."""

new = b"""## Immediate Next Steps (in order)

1. **Patch static thunk table in IDA** (unblocks Track C): Run `tools/patch_thunks_ida.py` in IDA Pro to patch the static thunk table with the 66/66 live targets from `thunk_states.json`. This gives agents the true call graph.

2. **Fresh traced run** (populate SEG_HEAP_ALLOC): Run `tools/run_falcon_traced.ps1` with `FALCON_TRACE` env. The AH=48h/49h hooks will populate `SEG_HEAP_ALLOC` with call-site attribution.

3. **Memory-deref + indirect-target hooks** (advice.md \xc2\xa73.3 hooks 2-3): Implement memory-deref (`LES`, `LDS`, `MOV ES:[BX]`) and indirect `CALL/JMP [BX]` logging in `falcon_trace`. Currently unimplemented.

4. **Re-check port-queue C candidates** against new boundaries (post boundary repair). The 87 UNKNOWN candidates include many dispatch-table labels (same call counts) \u2014 not functions. Documented, not pursued."""

if old in content:
    content = content.replace(old, new)
    with open('C:/Users/yotam/projects/falcon3/status.md', 'wb') as f:
        f.write(content)
    print('Replaced successfully')
else:
    print('NOT FOUND')
    idx = content.find(b'## Immediate Next Steps (in order)')
    if idx >= 0:
        print('Found at', idx)
        # Show the actual bytes
        print(repr(content[idx:idx+500]))
    else:
        print('Section not found')