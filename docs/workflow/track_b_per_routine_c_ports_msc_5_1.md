# Track B: Per-Routine C Ports (MSC 5.1)
## Track B: Per-Routine C Ports (MSC 5.1)

### Prerequisites
- DOSBox-X at `C:\dosbox-x\dosbox-x.exe`
- MSC 5.1 at `dos_compilers\msc5.1\` (mounted as `C:\` in DOSBox; compiler in `RBIN\CL.EXE`)
- `analysis/ida_falconcd/function_bytes.json` (regenerate if IDB changes — Step A4)

### DOSBox-X Config (generated on the fly by `portcheck_falcon.py`)

```ini
[autoexec]
mount c C:\Users\yotam\projects\falcon3\dos_compilers\msc5.1
c:
path c:\rbin;c:\rbinb
set INCLUDE=c:\include
set LIB=c:\lib
rbin\cl /c /Gs /Fc<NAME8> /Ic:\include <file.c> > compile.log
exit
```

- `/c` compile only, `/Gs` no stack probes, `/Fc` generate `.cod` listing
- Output: `<NAME8>.OBJ` + `<NAME8>.COD` **in the MSC root (C:\)** — not in the source dir

### Single-Routine Verify

```bash
venv\Scripts\python tools\portcheck_falcon.py <routine> --source src\<name>.c --segment 0x<seg> --offset 0x<ofs>
```

Internal flow:
1. Copy source into MSC dir under 8.3 name (first 8 chars of routine name!)
2. Run DOSBox-X compile
3. Parse `.cod` listing for `_routine` PROC…ENDP block → code bytes
4. Load reference bytes from `function_bytes.json` (fallback: raw EXE)
5. Byte-compare → `OK` / `FAIL` with hex dumps

### Naming Rules (CRITICAL — all tripped over these)

| Rule | Example |
|------|---------|
| C filename = routine name truncated to 8 chars | `sub_16FDD` → `sub_16FD.c`, `.cod` = `SUB_16FD.COD` |
| C **function name** must match routine name parsed from `.cod` (`_name PROC`) | declare `int sub_16FD(void)`, NOT `sub_16FDD` |
| Leading underscore is MSC's C decoration — don't write it | `.cod` shows `_sub_16FD` |
| One function per file | Multiple routines in one `.cod` confuse extraction |
| arg `--segment`/`--offset` from `survey.json`: `seg = ea>>4`, `ofs = ea&0xF` | `ea=0x16FDD` → `0x16FD` / `0xD` |

### MSC 5.1 C Syntax Rules

| Issue | Fix |
|-------|-----|
| `__far` rejected (`error C2054`) | MSC 5.1 has no `__far`; qualifier is `far` after return type: `int far func(void)` |
| `far int func(void)` rejected (`C2062`) | Order matters: `int far func(void)` |
| Default model gives near calls (`RET C3`) but original is far (`RETF CB`) | Declare routine `far` and/or compile with `/AL` (large model) |
| No `byte` / `uint` types | `unsigned char` / `unsigned int` |
| No standard CRT linked in original | Don't include `<stdio.h>`; keep routines freestanding |

### Smoke Tests (verified ✅)

| Source | Output bytes | Result |
|--------|-------------|--------|
| `hello.c` (`main(){return 0;}` w/ constant folded to 42) | `b8 2a 00 c3` | ✅ compile+extract works |
| `getans.c` (`int getans(){return 42;}`) | `b8 2a 00 c3` | ✅ compile+extract works |

### Verified Game Routines

| Routine | Original (IDA) | C source | Result |
|---------|----------------|----------|--------|
| `sub_16FDD` | `b8 01 00 cb` (mov ax,1; retf) | `int far sub_16FDD(void){return 1;}` | ✅ MATCH |
| `sub_2CB6E` | `b8 ff ff cb` (mov ax,-1; retf) | `int far sub_2CB6E(void){return -1;}` | ✅ MATCH |

**Key insight**: compile with `/AL` (large model) so returns are `RETF`, and declare
`int far func(void)` (qualifier *after* return type). Without this, near `RET` never matches.

### Attempted Game Routines (diagnostics)

| Routine | Original (IDA) | Diagnosis |
|---------|----------------|-----------|
| `sub_10340` | `d1 e3 2e 89 87 25 00 cb` (hand-ASM: `sal bx,1; mov cs:[bx+25h],ax; retf`) | **Hand-written ASM, not C** — skip or port as `.asm` |

---