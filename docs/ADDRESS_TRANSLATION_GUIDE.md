# Address Translation Guide - CRITICAL REFERENCE

**READ THIS BEFORE ANY ADDRESS-RELATED WORK**

## The Problem

Falcon 3.0 uses **segment:offset addressing** in IDA, but our analysis tools and exports use **linear addresses**. This mismatch has caused confusion and wasted hours (see Finding 207).

## The Solution

**ALWAYS use `segment_map.json` to translate addresses.**

## Quick Reference

### File Location
```
C:\Users\ybarnoy\projects\falcon3\analysis\s4\segment_map.json
```

### Key Segments

| Segment | Start (Linear) | End (Linear) | Size | Description |
|---------|---------------|--------------|------|-------------|
| seg002  | 0x10840      | 0x11081      | 2,241 | Resident code |
| seg020  | 0x1F6C0      | 0x2AA30      | 45,936 | Large overlay (graphics?) |
| DGROUP  | varies       | varies       | varies | Data segment |

### Verified Mappings

**Always double-check against these known-good mappings:**

| Function | Linear | Segment:Offset | IDA Name |
|----------|--------|----------------|----------|
| sub_256A3 | 0x256A3 | seg020:5FE3 | sub_256A3 |
| sub_20BDB | 0x20BDB | seg020:151B | view_projection |
| sub_10B1C | 0x10B1C | seg002:02DC | sub_10B1C |
| record_xform_apply | 0x1FB3C | seg020:047C | record_xform_apply |

## Translation Commands

### Setup
```powershell
cd C:\Users\ybarnoy\projects\falcon3\analysis\s4
```

### Linear → Segment:Offset
```powershell
python address_translator.py segment_map.json linear 0x256A3
# Output: seg020:5FE3
```

### Segment:Offset → Linear
```powershell
python address_translator.py segment_map.json segoff seg020:5FE3
# Output: 0x256A3
```

### Find Function at Address
```powershell
python address_translator.py segment_map.json find 0x20BDB
# Shows function name, type (main/secondary entry), offset info
```

### List All Segments
```powershell
python address_translator.py segment_map.json segments
```

### List Multi-Entry Functions
```powershell
python address_translator.py segment_map.json multi 20
```

## Manual Calculation (Emergency Fallback)

If tools unavailable, calculate manually:

### Segment:Offset → Linear
```
Linear = Segment_Base + Offset
```

Example: seg020:5FE3 → ?
1. Find seg020 base in segment_map.json: 0x1F6C0
2. Add offset: 0x1F6C0 + 0x5FE3 = 0x256A3

### Linear → Segment:Offset
```
1. Find which segment contains the linear address
2. Offset = Linear - Segment_Base
```

Example: 0x256A3 → ?
1. Check segments: 0x1F6C0 ≤ 0x256A3 < 0x2AA30 → seg020
2. Calculate offset: 0x256A3 - 0x1F6C0 = 0x5FE3
3. Result: seg020:5FE3

## Common Pitfalls

### ❌ DON'T: Trust Linear Address Math Blindly
```python
# WRONG - This assumes linear layout
target = 0x10BDB  # Typo or miscalculation
```

### ✅ DO: Verify Every Address
```python
# RIGHT - Verify against segment map
with open('segment_map.json') as f:
    data = json.load(f)
    # Find function by linear address
    func = [f for f in data['functions'] if f['start_ea'] == target]
    if not func:
        print(f"WARNING: 0x{target:X} not a function start!")
```

### ❌ DON'T: Assume seg020:XXXX = 0x20XXX
The segment base is **NOT** the segment number * 0x1000!
- seg020 base = 0x1F6C0 (NOT 0x20000)
- seg002 base = 0x10840 (NOT 0x02000)

### ✅ DO: Use Verified Mappings
Always check against known-good addresses (see table above).

## When You See an Address...

### 1. Identify the Source Format

**In IDA disassembly:**
```assembly
seg020:5FE3    ; This is segment:offset
call view_projection  ; IDA shows both name and segoff
```

**In function_bytes.json:**
```json
"sub_256A3": {
  "ea": 153251,  // This is LINEAR (0x256A3)
  ...
}
```

**In analysis output:**
```python
target = 0x20BDB  # Usually linear, but VERIFY!
```

### 2. Translate to Both Formats

**Example workflow:**
```powershell
# Given linear 0x20BDB from analysis
python address_translator.py segment_map.json linear 0x20BDB
# Output: seg020:151B

# Now search IDA for "seg020:151B"
# Or use IDA "G" (goto) command: G seg020:151B
```

### 3. Verify Function Exists

```powershell
python address_translator.py segment_map.json find 0x20BDB
# Output shows:
#   type: main_entry or secondary_entry or mid_function
#   function: view_projection
#   segoff: seg020:151B
```

## Multi-Entry Functions (57% of codebase!)

**Critical:** 2,385 out of 4,170 functions have secondary entry points.

### Example: record_xform_apply
```
Main entry:    seg020:047C (0x1FB3C)
Secondary +8:  seg020:0484 (0x1FB44) - 1 xref
Secondary +32: seg020:049C (0x1FB5C) - 1 xref
Secondary +311: seg020:05B3 (0x1FC93) - 4 xrefs
```

**If analysis shows many calls to an address that's "not a function":**
1. Check if it's a secondary entry point
2. Use `address_translator.py find <addr>` to check
3. Look in segment_map.json → multi_entry_functions

## Debugging Address Issues

### Symptom: "Function not found at 0xXXXXX"

**Checklist:**
1. ✓ Double-check the address value (typo? 0x10BDB vs 0x20BDB?)
2. ✓ Verify with `address_translator.py find 0xXXXXX`
3. ✓ Check if it's a secondary entry point
4. ✓ Recalculate from disassembly if needed
5. ✓ Search IDA for the bytecode pattern as fallback

### Symptom: "IDA shows different address than analysis"

**Resolution:**
1. IDA shows segment:offset → use translator to get linear
2. Analysis shows linear → use translator to get segment:offset
3. Verify both point to same function name
4. Update analysis to use correct address

### Symptom: "Calling into middle of function?"

**Likely:** Multi-entry function (57% of codebase!)
1. Check segment_map.json → multi_entry_functions
2. Find parent function name
3. Check offset_from_start
4. This is NORMAL in Falcon 3.0 architecture

## Integration into Scripts

```python
import json
from pathlib import Path

class AddressHelper:
    def __init__(self):
        seg_map_path = Path('analysis/s4/segment_map.json')
        with open(seg_map_path) as f:
            self.seg_map = json.load(f)
        
        # Build lookup
        self.segments = {s['name']: s for s in self.seg_map['segments']}
        self.functions = {f['start_ea']: f for f in self.seg_map['functions']}
    
    def linear_to_segoff(self, linear):
        """Convert linear address to segment:offset string."""
        for seg in self.seg_map['segments']:
            if seg['start_ea'] <= linear < seg['end_ea']:
                offset = linear - seg['start_ea']
                return f"{seg['name']}:{offset:04X}"
        return f"0x{linear:X}"
    
    def find_function(self, addr):
        """Find function at address (main or secondary entry)."""
        # Check main entries
        if addr in self.functions:
            return self.functions[addr]
        
        # Check secondary entries
        for fname, entries in self.seg_map.get('multi_entry_functions', {}).items():
            for entry in entries:
                if entry['address'] == addr:
                    return {
                        'name': fname,
                        'type': 'secondary_entry',
                        'offset_from_start': entry['offset_from_start']
                    }
        
        # Check if inside function
        for func in self.seg_map['functions']:
            if func['start_ea'] <= addr < func['end_ea']:
                return {
                    'name': func['name'],
                    'type': 'mid_function',
                    'offset': addr - func['start_ea']
                }
        
        return None

# Usage in analysis scripts
helper = AddressHelper()
segoff = helper.linear_to_segoff(0x256A3)
func = helper.find_function(0x20BDB)
print(f"0x256A3 is at {segoff}")
print(f"Function: {func['name']}")
```

## Before Opening an Issue...

**If you think there's a missing function or addressing error:**

1. ✓ Translate the address with `address_translator.py`
2. ✓ Check segment_map.json directly
3. ✓ Verify against known-good mappings (see table above)
4. ✓ Search IDA manually for the segment:offset
5. ✓ Check for typos (0x10BDB vs 0x20BDB cost us 8 hours!)

**Only after these checks:** Document as a finding.

## Lessons from Finding 207

**What happened:**
- Misread 0x20BDB as 0x10BDB (simple typo)
- Spent 8 hours investigating "missing function"
- Built segment export tooling to resolve it
- Discovered function existed as `view_projection` at 0x20BDB

**What we learned:**
1. Always double-check address values
2. Build verification tools early
3. Cross-reference between IDA and exports
4. Even "wasted" time can yield valuable infrastructure

**The silver lining:**
- Now have segment_map.json (4,170 functions mapped)
- Discovered multi-entry architecture prevalence (57%!)
- Built reusable address translation tools

---

## Quick Command Reference Card

**Copy-paste these commands as needed:**

```powershell
# Navigate to tools directory
cd C:\Users\ybarnoy\projects\falcon3\analysis\s4

# Linear to segment:offset
python address_translator.py segment_map.json linear 0x256A3

# Segment:offset to linear  
python address_translator.py segment_map.json segoff seg020:5FE3

# Find function at address
python address_translator.py segment_map.json find 0x20BDB

# List segments
python address_translator.py segment_map.json segments

# List multi-entry functions (top 20)
python address_translator.py segment_map.json multi 20

# View full segment map in JSON
Get-Content segment_map.json | ConvertFrom-Json | ConvertTo-Json -Depth 5
```

---

**This document saved you from wasting hours. You're welcome. 😊**

**Last Updated:** 2026-11-12 (Session 56)  
**Maintainer:** Keep this updated as we discover more address mappings!
