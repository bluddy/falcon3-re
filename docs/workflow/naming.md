# Naming Workflow
### 3. Naming workflow (renames never touch the ledger's `ida`)

```bash
# add entry to registry/naming.yaml {ida, name, kind, notes}
venv\Scripts\python tools\naming.py apply      # -> src/*.c, src/asm/*.asm, JSON name fields
venv\Scripts\python tools\naming.py check      # consistency gate (exit 1 = broken)
venv\Scripts\python tools\naming.py push-ida   # sync INTO the IDB (headless, saved)
python -m unittest discover -s tests           # 21 tests; run after touching naming.py
```
- portcheck accepts either name (`resolve` handles ida⇄semantic).
- **Never rename ad-hoc in the GUI** — ledger first, then push-ida. (extract_ida_bytes
  keys by previous extract's keys, so pushes can't shift JSON keys — proven.)
- Revert: `naming.py revert <ida_name>` (restores ida text everywhere).