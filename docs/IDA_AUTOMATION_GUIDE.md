# IDA Pro Automation Guide - DEFINITIVE REFERENCE

**Last Updated**: 2026-11-14  
**Status**: VERIFIED WORKING  
**Purpose**: Single source of truth for IDA Pro automation in Falcon 3.0 project

---

## Executive Summary

**DO THIS**:
```batch
"C:\Program Files\IDA Professional 9.1\idat.exe" -A -S"your_script.py" "path\to\database.i64"
```

**DON'T DO THIS**:
- IDC scripts (unreliable, timeout issues)
- Complex multi-step scripts (timeouts)
- Scripts without `qexit(0)` at the end

---

## Core Principles

### 1. Always Use Python, Not IDC
✅ **GOOD** - Python scripts (`*.py`):
- Full IDAPython API
- Better error handling
- Can import external libraries
- Works reliably

❌ **BAD** - IDC scripts (`*.idc`):
- Limited functionality
- Timeout issues observed
- Harder to debug

### 2. Always Use Batch Mode (`idat.exe`)
```
idat.exe -A -S"script.py" "database.i64"
```

**Flags**:
- `-A`: Auto-analysis (wait for IDA to finish analysis)
- `-S"script.py"`: Run script and exit
- No GUI, runs in terminal

### 3. Always Exit Explicitly
```python
import idc
# ... your code ...
idc.qexit(0)  # CRITICAL - without this, script hangs!
```

### 4. Keep Scripts Simple
- One task per script
- Under 100 lines if possible
- Save results to JSON/text files
- Exit immediately after completion

---

## Working Script Template

```python
"""
Script description here.
"""

import idc
import idaapi
import idautils
import json
from pathlib import Path

def main():
    # Wait for auto-analysis
    print("Waiting for auto-analysis...")
    idaapi.auto_wait()
    print("Auto-analysis complete")
    
    # Your code here
    result = {
        "test": "success"
    }
    
    # Save results
    output_path = Path(__file__).parent / "output.json"
    with open(output_path, 'w') as f:
        json.dump(result, f, indent=2)
    
    print(f"Results saved to: {output_path}")
    
    # CRITICAL: Exit explicitly
    idc.qexit(0)

if __name__ == "__main__":
    main()
```

---

## File Paths

### IDA Installations (Windows)
```
C:\Program Files\IDA Professional 9.1\idat.exe  ← Use this
C:\Program Files\IDA Free 9.1\idat.exe
C:\Program Files\IDA Freeware 8.3\idat.exe
```

### Database Path
```
C:\Users\ybarnoy\projects\falcon3\analysis\ida_falconcd\FALCONCD.EXE.i64
```

### Script Locations
```
analysis/ida_scripts/          ← New scripts go here
analysis/s4/                   ← Working scripts (verified)
```

---

## Common Tasks

### Task 1: Rename Function and Export Disassembly

**File**: `analysis/ida_scripts/rename_and_export.py`

```python
import idc
import idaapi

def main():
    idaapi.auto_wait()
    
    # Rename function
    func_addr = 0x1297F0
    new_name = "idx_dat_loader"
    idc.set_name(func_addr, new_name, idc.SN_NOWARN)
    
    # Export disassembly
    func = idaapi.get_func(func_addr)
    if not func:
        print(f"ERROR: No function at {hex(func_addr)}")
        idc.qexit(1)
    
    with open("analysis/idx_dat_loader.asm", 'w') as f:
        ea = func.start_ea
        while ea < func.end_ea:
            disasm = idc.generate_disasm_line(ea, 0)
            f.write(f"{ea:08X}  {disasm}\n")
            ea = idc.next_head(ea, func.end_ea)
    
    print(f"Function renamed to {new_name}")
    print(f"Disassembly exported to analysis/idx_dat_loader.asm")
    idc.qexit(0)

if __name__ == "__main__":
    main()
```

**Run**:
```batch
cd C:\Users\ybarnoy\projects\falcon3
"C:\Program Files\IDA Professional 9.1\idat.exe" -A -S"analysis\ida_scripts\rename_and_export.py" "analysis\ida_falconcd\FALCONCD.EXE.i64"
```

### Task 2: Find String References

**File**: `analysis/ida_scripts/find_strings.py`

```python
import idc
import idaapi
import idautils
import json

def main():
    idaapi.auto_wait()
    
    search_terms = ["ARMS", "MENU", ".IDX", ".DAT"]
    results = {}
    
    for term in search_terms:
        results[term] = []
        
        # Search in strings
        for s in idautils.Strings():
            if term.upper() in str(s).upper():
                refs = []
                for xref in idautils.XrefsTo(s.ea):
                    refs.append({
                        'from': hex(xref.frm),
                        'func': idc.get_func_name(xref.frm)
                    })
                
                if refs:
                    results[term].append({
                        'addr': hex(s.ea),
                        'string': str(s),
                        'refs': refs
                    })
    
    with open("analysis/string_refs.json", 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"Found {sum(len(v) for v in results.values())} string references")
    idc.qexit(0)

if __name__ == "__main__":
    main()
```

### Task 3: Get Function Disassembly

```python
import idc
import idaapi

def get_function_disasm(func_addr):
    """Get complete disassembly of a function."""
    func = idaapi.get_func(func_addr)
    if not func:
        return None
    
    lines = []
    ea = func.start_ea
    while ea < func.end_ea:
        disasm = idc.generate_disasm_line(ea, 0)
        lines.append(f"{ea:08X}  {disasm}")
        ea = idc.next_head(ea, func.end_ea)
    
    return {
        'name': idc.get_func_name(func_addr),
        'start': hex(func.start_ea),
        'end': hex(func.end_ea),
        'size': func.end_ea - func.start_ea,
        'disasm': lines
    }

def main():
    idaapi.auto_wait()
    
    # Example: Get sub_1297F0
    result = get_function_disasm(0x1297F0)
    
    if result:
        with open("analysis/function_disasm.txt", 'w') as f:
            f.write(f"; {result['name']}\n")
            f.write(f"; Address: {result['start']} - {result['end']}\n")
            f.write(f"; Size: {result['size']} bytes\n\n")
            for line in result['disasm']:
                f.write(line + "\n")
        print(f"Exported {result['name']}: {result['size']} bytes")
    
    idc.qexit(0)

if __name__ == "__main__":
    main()
```

---

## Address Translation

**ALWAYS** translate addresses before using them in IDA scripts!

### Use This Tool First:
```bash
cd analysis/s4
python address_translator.py segment_map.json linear 0x1297F0
```

Output:
```
Linear: 0x1297F0
SegOff: R29_29FEs:1549
Function: {'type': 'main_entry', 'function': 'sub_1297F0', ...}
```

### In Your Script:
```python
# Use the LINEAR address (not segment:offset)
func_addr = 0x1297F0  # This works
# IDA converts internally
```

**See**: `docs/ADDRESS_TRANSLATION_GUIDE.md` for complete details

---

## Troubleshooting

### Problem: Script Hangs/Timeout

**Cause**: No `qexit()` call or infinite loop

**Fix**:
```python
# Add at end of main()
idc.qexit(0)
```

### Problem: "Function not found"

**Cause**: Wrong address or database not analyzed

**Fix**:
1. Verify address with `address_translator.py`
2. Check `idaapi.auto_wait()` is called
3. Use `idc.get_name_ea_simple("func_name")` to find by name

### Problem: Script Exits But No Output

**Cause**: File path issues or exceptions swallowed

**Fix**:
```python
try:
    # your code
except Exception as e:
    print(f"ERROR: {e}")
    import traceback
    traceback.print_exc()
finally:
    idc.qexit(1)  # Exit with error code
```

### Problem: Can't Find IDA Installation

**Check**:
```powershell
Get-ChildItem "C:\Program Files" -Filter "IDA*" -Directory
```

---

## Verified Working Scripts

These scripts have been tested and work reliably:

### In `analysis/s4/`:
- `test_ida_minimal.py` - Basic connectivity test
- `verify_graphics_pipeline.py` - Full pipeline verification
- `level0_disasm_probe.py` - Function extraction
- All `*_probe.py` files - Data extraction

### Success Pattern:
1. Simple, focused task
2. Saves results to JSON
3. Calls `idaapi.auto_wait()`
4. Calls `idc.qexit(0)` at end
5. Run with `-A -S` flags

---

## Quick Reference Commands

### Run Script:
```batch
"C:\Program Files\IDA Professional 9.1\idat.exe" -A -S"script.py" "database.i64"
```

### Test IDA Access:
```batch
cd analysis\s4
"..\..\..\Program Files\IDA Professional 9.1\idat.exe" -A -S"test_ida_minimal.py" "..\ida_falconcd\FALCONCD.EXE.i64"
```

### Check Results:
```powershell
Get-Content analysis\s4\ida_test_result.json | ConvertFrom-Json
```

---

## Integration with Git Workflow

### Before Committing IDA Changes:

1. **Export function** with script
2. **Save output** to `analysis/` directory
3. **Commit both** script and output
4. **Document** in commit message what was renamed

### Example:
```bash
# Run extraction
idat.exe -A -S"rename_idx_loader.py" "database.i64"

# Commit
git add analysis/ida_scripts/rename_idx_loader.py
git add analysis/idx_dat_loader.asm
git commit -m "IDA: Renamed sub_1297F0 to idx_dat_loader, extracted disassembly"
```

---

## Historical Issues (AVOID THESE)

### ❌ Issue 1: IDC Scripts Timing Out
**What**: Used `.idc` files, they hung indefinitely
**Fix**: Switch to Python scripts

### ❌ Issue 2: Complex Multi-Step Scripts
**What**: Scripts that tried to do too much
**Fix**: Break into smaller, focused scripts

### ❌ Issue 3: No Exit Call
**What**: Scripts finished but IDA didn't exit
**Fix**: Always call `idc.qexit(0)`

### ❌ Issue 4: Wrong Address Format
**What**: Used segment:offset in script
**Fix**: Use linear addresses, IDA converts automatically

---

## Success Criteria

A good IDA automation script:
- ✅ Runs in under 2 minutes
- ✅ Saves results to file
- ✅ Exits cleanly with `qexit()`
- ✅ Handles errors gracefully
- ✅ Uses linear addresses
- ✅ Can be run multiple times safely

---

## Examples from This Project

### Previously Successful Extraction
The file `FALCONCD.EXE_extracted.json` (270KB, created 11/14/2026) was successfully generated using the pattern described here.

**Script Used**: `analysis/ida_scripts/extract_menu_strings.py` (139 INT 21h calls cataloged!)

**Key Success Factors**:
1. Python script
2. Simple data collection
3. JSON output
4. Called `qexit(0)`
5. Used `-A -S` flags

---

## Next Steps for Any Agent

1. **Read this guide** completely
2. **Copy a working script** from `analysis/s4/`
3. **Modify for your task** (keep it simple!)
4. **Test with** `-A -S` flags
5. **Verify output** file is created
6. **Commit** script and results

---

**Remember**: Simple scripts that exit cleanly = Success

**If it's not working**: Check you have `idaapi.auto_wait()` and `idc.qexit(0)`

