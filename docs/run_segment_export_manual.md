# Manual Segment Export Instructions

The batch mode IDA automation isn't working, so here's how to run the export manually through IDA's UI.

## Steps

1. **Open IDA with the FALCONCD.EXE.i64 database:**
   ```
   "C:\Program Files\IDA Professional 9.1\idat.exe" "C:\Users\ybarnoy\projects\falcon3\analysis\ida_falconcd\FALCONCD.EXE.i64"
   ```

2. **Wait for IDA to finish loading** (status bar shows "Idle")

3. **Run the export script:**
   - Menu: `File` → `Script file...`
   - Navigate to: `C:\Users\ybarnoy\projects\falcon3\tools\export_segments_simple.py`
   - Click `Open`

4. **Watch the Output window** (View → Open subviews → Output window if not visible)
   - You should see progress messages:
     ```
     Starting segment export...
     Output: C:\Users\ybarnoy\projects\falcon3\analysis\ida_falconcd\segment_map.json
     Found XX segments
     Found 4127 functions
     Finding multi-entry points...
     Found XX multi-entry functions
     ✓ Export complete: ...
     ```

5. **The export takes ~30-60 seconds** to scan all 4,127 functions for multi-entry points

6. **Output file location:**
   ```
   C:\Users\ybarnoy\projects\falcon3\analysis\ida_falconcd\segment_map.json
   ```

7. **After export completes, move the file:**
   ```powershell
   Move-Item C:\Users\ybarnoy\projects\falcon3\analysis\ida_falconcd\segment_map.json C:\Users\ybarnoy\projects\falcon3\analysis\s4\segment_map.json
   ```

## Alternative: Use IDA Python Console

If the script file dialog doesn't work:

1. Open IDA Python console: `File` → `Python command`
2. Paste and run:
   ```python
   exec(open(r'C:\Users\ybarnoy\projects\falcon3\tools\export_segments_simple.py').read())
   ```

## What to Expect

The export will create a JSON file with:
- **Segments**: All memory segments (seg002, seg020, DGROUP, etc.) with start/end addresses
- **Functions**: All 4,127 functions with segment:offset notation
- **Multi-entry functions**: Functions with secondary entry points (like seg020:051B)

## After Export

Once you have the file at `analysis/s4/segment_map.json`, run:
```powershell
cd C:\Users\ybarnoy\projects\falcon3\analysis\s4
python verify_10bdb_mapping.py
```

This will confirm whether seg020:051B is the mysterious "sub_10BDB" with ~10,222 calls.

## Troubleshooting

**If the script errors:**
- Check the Output window for error messages
- Make sure IDA finished loading (status bar = "Idle")
- Try the Python console method instead

**If no output:**
- The script prints to IDA's Output window, not the console
- View → Open subviews → Output window

**If file not created:**
- Check file permissions in the ida_falconcd directory
- Try running IDA as administrator
