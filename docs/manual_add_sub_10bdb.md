# Manual Addition of sub_10BDB to IDA

**Finding 207:** sub_10BDB is called 10,222 times but missing from IDB  
**Location:** 0x10BDB in 149-byte gap  
**Estimated time:** 15 minutes

## Prerequisites

- IDA Professional 9.1 installed
- FALCONCD.EXE.i64 at: `analysis/ida_falconcd/FALCONCD.EXE.i64`
- Backup exists: Multiple .bak files in same directory

## Step-by-Step Instructions

### 1. Open IDA Database

```
File → Open → Navigate to analysis/ida_falconcd/FALCONCD.EXE.i64
```

**Wait for autoanalysis to complete** (check bottom status bar)

### 2. Navigate to Address 0x10BDB

```
Press 'G' (or Jump → Jump to Address)
Type: 10BDB
Press Enter
```

**Expected view:**
- You should see gray/undefined bytes
- Address 0x10BDB should be visible
- Previous function (sub_10B1C) ends above this address

### 3. Create Instructions

**At address 0x10BDB:**

```
Press 'C' (or Edit → Code)
```

This creates instructions from the bytes. IDA will disassemble forward until it hits a return or existing code.

**Expected result:**
```
.text:00010BDB        pop     ds
.text:00010BDC        mov     si, 43BAh
.text:00010BDF        mov     di, 43D2h
.text:00010BE2        mov     cx, [bx+18h]
...
```

**If it doesn't work:** The bytes might already be partially analyzed. Try selecting from 0x10BDB forward and press 'U' to undefine, then press 'C' again.

### 4. Create Function

**With cursor at 0x10BDB:**

```
Press 'P' (or Edit → Functions → Create Function)
```

IDA will analyze and create a function. It should automatically detect the function end (at the retf instruction).

**Expected result:**
- Function name appears (e.g., sub_10BDB)
- Function boundaries shown in disassembly
- Function added to Functions window (View → Open Subviews → Functions)

### 5. Verify Function

**Check function properties:**

```
Right-click on function name → Edit Function
```

**Verify:**
- Start: 0x10BDB
- End: Should be around 0x10C00-0x10C10 (find retf instruction)
- Type: Far (if checkbox available)

**Expected size:** ~30-40 bytes based on bytecode analysis

### 6. Verify Xrefs

**Check cross-references TO sub_10BDB:**

```
With cursor on sub_10BDB, press 'X' (or View → Open Subviews → Xrefs to)
```

**Expected xref:**
- **sub_256A3** at offset +10 (0x256AD) should call this function
- If you see this xref: ✓ SUCCESS

**If no xrefs shown:**
- Navigate to sub_256A3 (press 'G', type 256A3)
- Look for call instruction around offset +10
- The call should point to sub_10BDB
- If it doesn't, IDA may need reanalysis

### 7. Force Reanalysis of Caller (if needed)

**If sub_256A3 doesn't show xref:**

```
Navigate to sub_256A3 (address 0x256A3)
Select the entire function:
  - Press 'Home' to go to function start
  - Press 'Ctrl+E' or Edit → Functions → Edit Function
  - Note the end address
  - Press 'Esc'

Undefine and reanalyze:
  - Press 'U' (undefine)
  - Press 'C' (create code)
  - Press 'P' (create function)
```

Now check xrefs to sub_10BDB again - sub_256A3 should appear.

### 8. Save Database

```
File → Save (or Ctrl+S)
```

Wait for save to complete (watch status bar).

### 9. Export function_bytes.json

**Run export script:**

```
File → Script file... (or Alt+F7)
Navigate to: tools/extract_ida_bytes.py
Click 'Open'
```

**Or from command line after closing IDA:**
```powershell
cd analysis\ida_falconcd
idat.exe -A -Stools\extract_ida_bytes.py FALCONCD.EXE.i64
```

**Expected output:**
- New function_bytes.json created
- Should contain sub_10BDB entry
- Total functions should be 4,128 (was 4,127, +1)

### 10. Verify Success

**Run verification script:**

```powershell
cd analysis\s4
python check_10bdb_added.py
```

**Expected output:**
```
SUCCESS: sub_10BDB found in function_bytes.json!
  Address: 0x10BDB
  Size: XX bytes
  Bytecode matches extracted bytes
```

## Troubleshooting

### Problem: Can't create instructions at 0x10BDB

**Possible causes:**
1. Bytes already defined as data
2. Conflicting analysis

**Solution:**
- Select bytes from 0x10BDB to 0x10BE0
- Press 'U' to undefine
- Press 'C' to create code

### Problem: Function creation fails

**Possible causes:**
1. IDA can't find function end
2. Bytes contain data mixed with code

**Solution:**
- Manually find retf instruction (byte 0xCB)
- Note the address after retf
- Select from 0x10BDB to address after retf
- Press 'P' with explicit range

### Problem: No xrefs from sub_256A3

**Possible causes:**
1. sub_256A3 not reanalyzed
2. Call is indirect or obfuscated

**Solution:**
- Reanalyze sub_256A3 (step 7 above)
- Manually verify call at 0x256AD (should be E8 2B B5)

### Problem: Export script fails

**Fallback:**
- Close IDA
- Copy extract_ida_bytes.py content
- Open IDA Python console (File → Script command)
- Paste and run the export code manually

## After Success

**Next steps:**
1. Analyze sub_10BDB disassembly
2. Understand what it does with DGROUP:0x4287
3. Name the function appropriately
4. Complete Finding 207

**Estimated additional time:** 15 minutes for analysis + naming

