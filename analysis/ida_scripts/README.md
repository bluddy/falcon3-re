# IDA Scripts Directory

**Last Updated**: 2026-11-14  
**Status**: CLEAN - Only verified working scripts

---

## Quick Start

**Read First**: `../../docs/IDA_AUTOMATION_GUIDE.md` - Complete guide to IDA automation

**Run a Script**:
```batch
cd C:\Users\ybarnoy\projects\falcon3
"C:\Program Files\IDA Professional 9.1\idat.exe" -A -S"analysis\ida_scripts\SCRIPT_NAME.py" "analysis\ida_falconcd\FALCONCD.EXE.i64"
```

---

## Available Scripts

### extract_idx_dat_loader.py ✅ VERIFIED WORKING
**Purpose**: Extract and rename the .IDX/.DAT file loader function  
**Target**: sub_1297F0 → idx_dat_loader  
**Output**: `analysis/idx_dat_loader.asm`

**What it does**:
- Renames function to idx_dat_loader
- Finds PICFONT.IDX and PICFONT.DAT string references
- Exports complete disassembly (187 bytes, 62 instructions)

**Run**:
```batch
idat.exe -A -S"analysis\ida_scripts\extract_idx_dat_loader.py" "analysis\ida_falconcd\FALCONCD.EXE.i64"
```

---

### extract_menu_strings.py ✅ PREVIOUSLY SUCCESSFUL
**Purpose**: Find all menu-related strings and file I/O operations  
**Output**: `analysis/ida_falconcd/FALCONCD.EXE_extracted.json`

**What it found**:
- 6 string references (PICFONT, SQUAD, HARPOON, madfont)
- 139 INT 21h DOS calls cataloged
- Complete file I/O wrapper inventory

**Note**: This was run successfully before, output already exists

---

### quick_extract.py (UNTESTED)
**Purpose**: Quick extraction of basic info  
**Status**: Not yet verified, use extract_idx_dat_loader.py instead

---

## Guidelines

### ✅ DO:
- Use Python scripts (not IDC)
- Call `idaapi.auto_wait()` at start
- Call `idc.qexit(0)` at end
- Keep scripts under 100 lines
- Save output to files
- Test with `-A -S` flags

### ❌ DON'T:
- Use IDC scripts (removed for unreliability)
- Create complex multi-step scripts
- Forget `qexit()` call
- Use segment:offset addresses (use linear)

---

## Script Template

Copy this for new scripts:

```python
"""
Script description.
"""
import idc
import idaapi
from pathlib import Path

def main():
    # Wait for analysis
    idaapi.auto_wait()
    
    # Your code here
    result = {"test": "success"}
    
    # Save output
    output = Path(__file__).parent.parent / "output.txt"
    with open(output, 'w') as f:
        f.write(str(result))
    
    print(f"Saved to: {output}")
    
    # REQUIRED: Exit cleanly
    idc.qexit(0)

if __name__ == "__main__":
    main()
```

---

## Troubleshooting

**Script hangs**: Missing `qexit(0)` call  
**No output**: Check file paths  
**Function not found**: Verify address with `analysis/s4/address_translator.py`

**Full guide**: See `docs/IDA_AUTOMATION_GUIDE.md`

---

## More Examples

See `analysis/s4/` for many verified working scripts:
- `test_ida_minimal.py` - Basic connectivity test
- `verify_graphics_pipeline.py` - Complex extraction
- All `*_probe.py` files - Data collection patterns

---

## Next Tasks

Suggested scripts to create:

1. **extract_file_io_wrappers.py**
   - Target: file_open (0x226BD), file_read (0x226F5), file_lseek (0x2274D)
   - Extract all DOS file I/O wrapper functions

2. **find_rle_decompressor.py**
   - Search for functions that process 6-byte headers (00 04 width height)
   - Find RLE decompression algorithm

3. **extract_menu_loaders.py**
   - Find COMMMENU, SYSMENU, DIFFMENU string references
   - Extract menu initialization code

4. **extract_squad_handler.py**
   - Target: sub_6A651 (46 references!)
   - May contain AI behavior table loading

---

**Remember**: Simple, focused scripts = Success

