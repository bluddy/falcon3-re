# Troubleshooting
## Troubleshooting

| Error | Cause | Fix |
|-------|-------|-----|
| `Could not extract bytes for X` | `.COD` not found or function name mismatch | Check `dos_compilers\msc5.1\X*.COD` exists; C function must be `X` (8-char truncated) |
| `error C2054: expected '(' to follow '__far'` | MSC 5.1 has no `__far` | Use `int far func(void)` |
| `error C2062: type 'int' unexpected` | Wrong qualifier order (`far int`) | `int far func(void)` |
| portcheck MISMATCH expected=raw-exe bytes | Compared pre-relocation file bytes | Use `function_bytes.json` (auto-loaded; regen via `extract_ida_bytes.py`) |
| portcheck `ret` vs `retf` mismatch | Compiled near, original far | Fixed: compile line now uses `/AL`, declare `int far func(void)` |
| MISMATCH on small `sub_*` | Function is hand-written ASM, not C | Check bytes for `55 8b ec` / `ENTER` prologue vs ad-hoc; port as asm instead |
| DOSBox compile fails, empty log | Config path escaping | Paths in config need `\\` doubled; run with `cwd=repo root` |
| IDA hangs / conflicts | Interactive IDA holds another DB | Only run `idat.exe` headless; never open falcon in MCP IDA |
| `fixup` mismatches in survey bytes | Survey era vs fixup-era IDB | Always extract fresh `function_bytes.json` after re-running fixups |
| Routine has far call (`9a xx xx seg off`), bytes never match | IDA bytes have load-base `+0x1000` in relocated words (finding 15) | Normalize: allow ±0x1000 on words at MZ reloc positions, or compare vs raw-EXE+relocs |
| Splicing bytes from `function_bytes.json` breaks relocations | Those are *relocated* (runtime) bytes | Splice **unrelocated** file bytes — DOS re-applies relocs at load |
| Overlay function bytes decode as garbage | Overlay fixups possibly mis-applied (finding 16) | Don't trust overlay function bytes until re-audited; resident 815 proven good |

---