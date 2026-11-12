# Segment Export & Address Translation Guide

## Overview

This guide explains how to export segment information from IDA and use it to translate between linear addresses and IDA's segment:offset notation.

## Problem Statement

Our API exports use linear addresses (e.g., `0x10BDB`), but IDA uses segment:offset notation (e.g., `seg020:051B`). This mismatch made it impossible to:
- Navigate from our analysis to IDA locations
- Identify multi-entry functions systematically
- Understand which segment a function belongs to

## Solution

Three-part toolchain:
1. **export_segment_map.py** - IDA script that exports segment definitions and multi-entry points
2. **address_translator.py** - Python utility to translate addresses using the export
3. **run_segment_export.bat** - Batch file to automate the export

## Step 1: Run the Export

```bash
cd C:\Users\ybarnoy\projects\falcon3\tools
.\run_segment_export.bat
```

This will:
- Run IDA in batch mode
- Execute `export_segment_map.py`
- Generate `analysis/s4/segment_map.json`
- Exit IDA automatically

**Expected output:**
```
Enhanced Segment Export
============================================================
[1/3] Exporting segment map...
  Found XX segments
[2/3] Finding multi-entry functions...
  Found XX functions with secondary entry points
[3/3] Exporting enhanced function information...
  Exported 4127 functions

✓ Export complete: segment_map.json
```

## Step 2: Explore the Data

### View segment map:
```bash
cd C:\Users\ybarnoy\projects\falcon3\analysis\s4
python address_translator.py segment_map.json segments
```

### View multi-entry functions:
```bash
python address_translator.py segment_map.json multi
```

### Convert linear address to segment:offset:
```bash
python address_translator.py segment_map.json linear 0x10BDB
```

### Convert segment:offset to linear:
```bash
python address_translator.py segment_map.json segoff seg020:051B
```

### Find function containing an address:
```bash
python address_translator.py segment_map.json find 0x10BDB
python address_translator.py segment_map.json find seg020:051B
```

## What Gets Exported

### 1. Segments
```json
{
  "name": "seg020",
  "start_ea": 131766,
  "end_ea": 156892,
  "selector": 32,
  "class": "CODE",
  "type": 2,
  "bitness": 0
}
```

### 2. Multi-Entry Functions
```json
{
  "record_xform_apply": [
    {
      "address": 131867,
      "segoff": "seg020:051B",
      "offset_from_start": 159,
      "xref_count": 10222,
      "xrefs_from": [
        {"ea": 152739, "segoff": "seg020:5FED"}
      ]
    }
  ]
}
```

### 3. Enhanced Function Info
```json
{
  "name": "sub_256A3",
  "start_ea": 152739,
  "end_ea": 152751,
  "size": 12,
  "segoff": "seg020:5FED",
  "xrefs_to_entry": 10222
}
```

## Use Cases

### Finding the Real Location of "sub_10BDB"

Before the export, we thought `sub_10BDB` was at linear `0x10BDB`, but IDA couldn't find it there.

After export:
```bash
python address_translator.py segment_map.json find 0x10BDB
```

This would show if `0x10BDB` is actually a multi-entry point within another function, revealing it's at `seg020:051B` inside `record_xform_apply`.

### Navigating from Analysis to IDA

When analysis finds a hot function at `0x256A3`:
```bash
python address_translator.py segment_map.json linear 0x256A3
# Output: seg020:5FED
```

Now you can navigate directly in IDA to `seg020:5FED`.

### Understanding Overlay Structure

The segment map shows all overlay segments, their sizes, and address ranges. This helps understand which functions belong to which game mode overlay.

## Integration with Analysis Scripts

Future analysis scripts can load the segment map:

```python
from address_translator import AddressTranslator

translator = AddressTranslator('analysis/s4/segment_map.json')

# Translate addresses
segoff = translator.format_segoff(0x256A3)
linear = translator.parse_segoff('seg020:051B')

# Find functions
info = translator.find_function(0x10BDB)
if info['type'] == 'secondary_entry':
    print(f"This is entry {info['offset_from_start']} into {info['function']}")
```

## Expected Results

After running the export, we expect to find:
- ~4,127 functions
- Multiple segments (CODE, DATA, etc.)
- Dozens of multi-entry functions (functions with secondary entry points called from elsewhere)
- Clear mapping between linear addresses and segment:offset notation

The multi-entry function list will likely show `record_xform_apply` with a secondary entry at offset `+0x051B` that has ~10,222 xrefs - this is what we've been calling "sub_10BDB".

## Next Steps After Export

1. **Verify seg020:051B mapping** - Confirm our hypothesis about the multi-entry function
2. **Analyze DGROUP:0x4287** - Now that we know where the code is, understand what it accesses
3. **Systematically document multi-entry patterns** - Use the export to find all similar cases
4. **Update naming scripts** - Incorporate segment information into function naming decisions
5. **Fix boundary analysis** - Re-run with proper address translation

## Files Created

- `tools/export_segment_map.py` - IDA export script (436 lines)
- `tools/run_segment_export.bat` - Automation batch file
- `analysis/s4/address_translator.py` - Translation utility (295 lines)
- `docs/segment_export_guide.md` - This guide
