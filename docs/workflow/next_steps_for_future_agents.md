# Next Steps for Future Agents
## Next Steps for Future Agents

1. ~~**Fix near/far**~~ ✅ Done: `/AL` + `int far` → `sub_16FDD` and `sub_2CB6E` both MATCH.
2. **Pick easy targets**: filter `functions.tsv` for size ≤ 10, `far=1`, `nretf=1`,
   no thunk — verify constants/globals getters next (IDB names via `function_bytes.json`).
3. **Classify hand-ASM vs C**: `prologues.json`/`epilogues.json` already extracted;
   C-compiled candidates are the ones with `ENTER` or consistent frames.
4. **Track C setup**: copy gunship's `extract_routines.py`/`replace_routines.py` into
   `scripts/`; write `tools/splice.py`; `mzdiff`/`mzmap` already available in WSL at
   `gunship_2000/tools/f19re/mzretools/debug/` — just run `mzmap FALCONCD.EXE falconcd.map` once.
5. **Extend `libscan.py`** with MSC 5.1 libraries from the `f19re` toolchain.
6. **Registry**: once routines verify, record them in `registry/FALCONCD.EXE.yaml`
   (name, ea, bytes hash, port status) per gunship's registry YAML format.

---