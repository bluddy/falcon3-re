---
inclusion: auto
name: ida-automation-best-practices
description: Best practices for IDA Pro automation and scripting
---

# IDA Pro Automation Best Practices

## Critical Rules for IDA Python Scripts

### 1. Always Use Absolute Paths

**Problem**: IDA runs from the IDB directory, not your script directory.

```python
# ❌ WRONG - creates file in wrong directory
output_file = "results.json"
with open(output_file, "w") as f:
    json.dump(data, f)

# ✅ RIGHT - absolute path
output_file = r"C:\Users\ybarnoy\projects\falcon3\analysis\s4\results.json"
with open(output_file, "w") as f:
    json.dump(data, f)
```

**Why**: IDA's working directory is where the .i64 file is located, NOT where your script is.

### 2. Wait for Auto-Analysis

```python
import idaapi

# ALWAYS start your script with this
idaapi.auto_wait()
```

**Why**: IDA needs to finish analyzing the binary before your script can access functions, xrefs, etc.

### 3. Exit Immediately When Done

```python
import idc

# ALWAYS end your script with this
idc.qexit(0)
```

**Why**: Prevents IDA from hanging. Exit code 0 = success, 1 = error.

### 4. Use Correct IDA API Functions

**Segment Access**:
```python
# ❌ WRONG - doesn't exist
dgroup_base = idc.get_segm_by_name("DGROUP")

# ✅ RIGHT - two-step process
dgroup_sel = idc.selector_by_name("DGROUP")
if dgroup_sel != idc.BADADDR:
    dgroup_base = idc.get_segm_by_sel(dgroup_sel)
```

**Function Finding**:
```python
# By name
addr = idc.get_name_ea_simple("function_name")

# By address
func = idaapi.get_func(addr)
if func:
    size = func.end_ea - func.start_ea
```

**XRef Analysis**:
```python
import idautils

# Get all cross-references TO an address
xrefs = list(idautils.XrefsTo(addr, 0))

for xref in xrefs:
    caller_addr = xref.frm
    caller_name = idc.get_func_name(caller_addr)
```

### 5. Handle Errors Gracefully

```python
try:
    # Your analysis code
    result = analyze_something()
    
    # Save results
    with open(output_file, "w") as f:
        json.dump(result, f)
    
except Exception as e:
    # Save error info
    with open(error_file, "w") as f:
        json.dump({"error": str(e)}, f)
    
finally:
    # Always exit
    idc.qexit(0)
```

### 6. Limit Operations to Avoid Timeouts

```python
# ❌ WRONG - process all xrefs (could be thousands)
for xref in xrefs:
    # Process every single one...

# ✅ RIGHT - sample first N
for xref in xrefs[:100]:  # First 100 only
    # Process sample
```

**Why**: Large datasets can cause timeouts. Sample for initial analysis, then drill down.

---

## Complete Script Template

```python
"""
Purpose: Describe what this script does
Output: Where results are saved
"""

import idc
import idaapi
import idautils
import json
from pathlib import Path

def analyze_something():
    """Your analysis function."""
    try:
        # Wait for auto-analysis
        idaapi.auto_wait()
        
        # Your analysis code here
        addr = idc.get_name_ea_simple("function_name")
        if addr == idc.BADADDR:
            return {"error": "Function not found"}
        
        func = idaapi.get_func(addr)
        if not func:
            return {"error": "No function at address"}
        
        # Collect data
        result = {
            "address": hex(addr),
            "size": func.end_ea - func.start_ea,
            "name": idc.get_func_name(addr)
        }
        
        return result
        
    except Exception as e:
        return {"error": str(e)}

def main():
    print("="*80)
    print("SCRIPT NAME - What it does")
    print("="*80)
    
    try:
        # Run analysis
        result = analyze_something()
        
        # Save with ABSOLUTE path
        output_file = r"C:\full\path\to\output.json"
        with open(output_file, "w") as f:
            json.dump(result, f, indent=2)
        
        print(f"✓ Results saved to: {output_file}")
        
    except Exception as e:
        print(f"✗ Fatal error: {e}")
        # Save error
        error_file = r"C:\full\path\to\error.json"
        with open(error_file, "w") as f:
            json.dump({"error": str(e)}, f)
    
    finally:
        # ALWAYS exit
        print("Exiting IDA...")
        idc.qexit(0)

if __name__ == "__main__":
    main()
```

---

## Running Scripts

### Command Line
```bash
# Windows
idat.exe -A -S"C:\path\to\script.py" database.i64

# Measure timing
Measure-Command { idat.exe -A -S"script.py" db.i64 }
```

### Best Practices
1. **Test with minimal script first** (1-2 operations)
2. **Time your scripts** - should be < 5 seconds for simple analysis
3. **Check output files exist** before assuming success
4. **Exit code 0 = success**, 1 = error (but check output anyway)

---

## Common Pitfalls

### Pitfall 1: Runtime vs Static Data

**Problem**: Some segment names (like "DGROUP") are runtime concepts.

```python
# This might fail if DGROUP is runtime-only
dgroup_sel = idc.selector_by_name("DGROUP")
if dgroup_sel == idc.BADADDR:
    # DGROUP doesn't exist as named segment
    # Need alternative approach
```

**Solution**: 
- Find data by address range analysis
- Look for known references (e.g., code that loads selector 0x7B0E)
- Use runtime tracing as fallback

### Pitfall 2: Assuming Function Exists

```python
# ❌ WRONG - crashes if not found
func = idaapi.get_func(addr)
size = func.end_ea - func.start_ea  # Crashes if func is None

# ✅ RIGHT - check first
func = idaapi.get_func(addr)
if func:
    size = func.end_ea - func.start_ea
else:
    print(f"No function at {hex(addr)}")
```

### Pitfall 3: String Concatenation in Paths

```python
# ❌ WRONG - fragile, escaping issues
output = "C:\\Users\\" + username + "\\file.json"

# ✅ RIGHT - raw string or Path
output = r"C:\Users\username\file.json"
# or
from pathlib import Path
output = Path("C:/Users/username/file.json")
```

### Pitfall 4: Not Limiting XRef Loops

```python
# Get all xrefs
xrefs = list(idautils.XrefsTo(popular_function, 0))

# ❌ WRONG - could be 10,000+ xrefs
for xref in xrefs:
    # Process all...  takes forever

# ✅ RIGHT - sample or limit
for xref in xrefs[:100]:
    # Process first 100
    
# Or count without processing
print(f"Total xrefs: {len(xrefs)}")
```

---

## Performance Guidelines

### Fast Operations (< 1 second)
- Get function by name
- Get function size
- Count xrefs
- Access segment info
- Read a few instructions

### Medium Operations (1-5 seconds)
- Analyze 10-20 functions
- Process 100 xrefs
- Scan a segment
- Build small call graph

### Slow Operations (> 5 seconds)
- Process all xrefs to popular function
- Scan entire database
- Complex pattern matching
- Deep recursive analysis

**Strategy**: Start with fast operations, drill down incrementally.

---

## Debugging Tips

### Problem: Script Hangs

1. **Check for missing qexit()** - script never exits
2. **Check for infinite loops** - limit iterations
3. **Check xref count** - popular functions have thousands

### Problem: No Output File

1. **Check path** - use absolute path
2. **Check exception** - wrapped in try/except?
3. **Check working directory** - use absolute, not relative

### Problem: Wrong Results

1. **Check auto_wait()** - analysis might not be complete
2. **Check BADADDR** - function/segment not found
3. **Check None returns** - get_func() can return None

---

## Verification Checklist

Before running analysis script:

- [ ] Uses `idaapi.auto_wait()`
- [ ] Uses absolute paths for output
- [ ] Has try/except error handling
- [ ] Always calls `idc.qexit(0)`
- [ ] Limits large loops (xrefs, etc.)
- [ ] Checks for BADADDR and None
- [ ] Saves results even on error
- [ ] Has timeout estimate (< 5s ideal)

---

## Common IDA API Reference

### Finding Things
```python
# By name
addr = idc.get_name_ea_simple("name")

# Segment
seg_sel = idc.selector_by_name("seg020")
seg_base = idc.get_segm_by_sel(seg_sel)

# Function at address
func = idaapi.get_func(addr)
```

### Analyzing Functions
```python
# Function info
func = idaapi.get_func(addr)
size = func.end_ea - func.start_ea
name = idc.get_func_name(addr)

# Instructions
ea = func.start_ea
while ea < func.end_ea:
    mnem = idc.print_insn_mnem(ea)
    disasm = idc.GetDisasm(ea)
    ea = idc.next_head(ea, func.end_ea)
```

### Cross-References
```python
# XRefs TO address
xrefs_to = list(idautils.XrefsTo(addr, 0))

# XRefs FROM address  
xrefs_from = list(idautils.XrefsFrom(addr, 0))

# Caller info
for xref in xrefs_to:
    caller = idc.get_func_name(xref.frm)
```

### Segments
```python
# Iterate all segments
for seg_ea in idautils.Segments():
    seg = idaapi.getseg(seg_ea)
    name = idaapi.get_segm_name(seg)
    print(f"{name}: {hex(seg.start_ea)} - {hex(seg.end_ea)}")
```

---

## Typical Execution Times (Falcon 3.0 IDB)

- **Minimal test**: 1.3 seconds
- **Get function info**: 1.3 seconds
- **Count xrefs (100)**: 1-2 seconds
- **List all segments**: 1.3 seconds
- **Analyze 10 functions**: 2-3 seconds
- **Deep call graph**: 5-10 seconds

**Target**: Keep scripts under 5 seconds for rapid iteration.

---

## When to Use Manual IDA vs Automation

### Use Automation When:
- ✅ Need to process multiple items
- ✅ Need reproducible results
- ✅ Need to export data
- ✅ Analysis is well-defined
- ✅ Can verify results programmatically

### Use Manual IDA When:
- ✅ Exploring unknown code
- ✅ Need visual context
- ✅ Renaming/restructuring
- ✅ One-time inspection
- ✅ Automation keeps failing

---

## Summary

**Golden Rules**:
1. Absolute paths
2. auto_wait() first
3. qexit() last
4. Check for BADADDR/None
5. Limit large loops
6. Handle errors

**Result**: Fast (< 5s), reliable, reproducible analysis.
