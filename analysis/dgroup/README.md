# View System Investigation - File Index

This directory contains the complete investigation of Falcon 3.0's view switching system.

## 📖 Start Here

**[FINAL_SUMMARY.md](FINAL_SUMMARY.md)** - Executive summary of findings and status

**[COMPLETE_VIEW_SYSTEM_DOCUMENTATION.md](COMPLETE_VIEW_SYSTEM_DOCUMENTATION.md)** - Master reference document with full architecture, code flow, and all addresses

## 📋 Key Documentation

- **[VIEW_SYSTEM_ARCHITECTURE.md](VIEW_SYSTEM_ARCHITECTURE.md)** - Detailed two-level architecture explanation
- **[VIEW_DISPATCH_FOUND.md](VIEW_DISPATCH_FOUND.md)** - How the dispatchers were discovered
- **[RENAMING_PLAN.md](RENAMING_PLAN.md)** - IDA renaming checklist and plan
- **[NEW_HYPOTHESIS.md](NEW_HYPOTHESIS.md)** - Session-static flag hypothesis

## 🔍 Investigation Process

- **[INVESTIGATION_SUMMARY.md](INVESTIGATION_SUMMARY.md)** - Initial investigation overview
- **[NEXT_ACTIONS.md](NEXT_ACTIONS.md)** - Original next steps (now complete)
- **[FINDINGS_SUMMARY.md](FINDINGS_SUMMARY.md)** - Mid-investigation findings
- **[VIEW_MODE_KEY_FINDING.md](VIEW_MODE_KEY_FINDING.md)** - Early discoveries
- **[VIEW_SWITCHING_NEXT_INVESTIGATION.md](VIEW_SWITCHING_NEXT_INVESTIGATION.md)** - Investigation continuation guide
- **[hypothesis_view_switching.md](hypothesis_view_switching.md)** - Initial hypothesis

## 📊 Data Files

### Key Findings
- **[view_jump_table.json](view_jump_table.json)** - 10-entry rendering jump table
- **[input_dispatch_patterns.json](input_dispatch_patterns.json)** - Complete dispatcher disassembly
- **[jump_table_addresses.json](jump_table_addresses.json)** - Input dispatcher table locations
- **[renaming_results.json](renaming_results.json)** - IDA renaming log

### Reference Data
- **[input_flag_refs.json](input_flag_refs.json)** - All 170+ refs to input_scan_code_queue
- **[r15_input_flag_refs.json](r15_input_flag_refs.json)** - R15 segment references
- **[view_flag_writes.json](view_flag_writes.json)** - All writes to view_pipeline_mode
- **[flag_readers_writers.json](flag_readers_writers.json)** - Read/write breakdown

## 🔧 Scripts

### Successfully Executed
- **[apply_renamings.py](apply_renamings.py)** - Renamed variables and functions in IDA ✓
- **[extract_view_jump_table.py](extract_view_jump_table.py)** - Extracted 10 view handlers ✓
- **[examine_input_dispatch_context.py](examine_input_dispatch_context.py)** - Found dispatchers ✓
- **[find_table_addresses.py](find_table_addresses.py)** - Located dispatch tables ✓

### Analysis Scripts
- analyze_view_handlers.py
- examine_handlers_simple.py
- examine_state_variable.py
- find_view_mode_to_flag_connection.py
- find_view_key_dispatch.py
- find_input_dispatcher.py
- analyze_input_dispatch_details.py
- search_for_view_scancodes.py
- rename_view_system_complete.py
- test_rename.py
- dump_table_bytes.py

## 🎯 Quick Reference

### Core Variables (Renamed in IDA)
```
0x79F16  : current_view_index       (view selector 0-9)
0x107762 : view_pipeline_mode       (sim vs ACMI?)
0x79B66  : input_scan_code_queue    (keyboard input)
```

### Key Functions (Renamed in IDA)
```
0x156945 : view_rendering_dispatcher   (10-case jump table)
0x12DB63 : tactical_screen_coordinator (input handler)
0x12FAC3 : input_poll_handler          (keyboard capture)
0x1087B2 : view_mode_set               (init function)
```

### Critical Addresses
```
0x130709 : Number key capture loop start
0x130749 : Scan code storage
0x12DFD6 : Input dispatcher 1
0x182476 : Input dispatcher 2  
0x156DC5 : View rendering dispatcher
0x156DD4 : Jump table (10 cases)
0x108BC5 : Pipeline mode check
```

## 📈 Investigation Flow

```
1. Started with: Find view switching code
2. Found: input_poll_handler captures keys
3. Found: input_scan_code_queue stores codes
4. Found: Dispatchers search tables
5. Found: Handlers set current_view_index
6. Found: Rendering dispatcher uses jump table
7. Realized: Pipeline mode is session-static
8. Hypothesis: Mode = ACMI vs simulation
9. Renamed: Everything in IDA
10. Documented: Complete system
```

## 🎓 Key Insights

1. **Two-level architecture**: Mode (static) + View index (dynamic)
2. **Session-static mode**: Set once, never changes during flight
3. **Dynamic view index**: THIS is what view keys change
4. **10 distinct views**: All indexed in jump table
5. **ACMI hypothesis**: Pipeline mode likely controls replay vs live

## ✅ Verification

All renamings confirmed in IDA:
- Variables: current_view_index, view_pipeline_mode, input_scan_code_queue
- Functions: view_rendering_dispatcher, tactical_screen_coordinator
- Comments: 7 key locations annotated

## 🔗 Related Files

- **IDA Database**: `analysis/ida_falconcd/FALCONCD.EXE.i64`
- **Manual**: `manual/extracted/f3keys.txt` (view key reference)
- **Archive**: `analysis/ida_falconcd/*.json` (various analysis data)

## 📝 Notes

- Investigation completed across multiple sessions
- 25+ scripts created during analysis
- All findings verified and cross-referenced
- Documentation synced with IDA renamings
- ACMI hypothesis needs game testing to confirm

## 🚀 Usage

For future reference or modification:
1. Read FINAL_SUMMARY.md for overview
2. Check COMPLETE_VIEW_SYSTEM_DOCUMENTATION.md for details
3. Open IDA and navigate to renamed functions/variables
4. Use quick reference addresses above
5. Consult JSON data files for raw information

---

**Status**: Investigation Complete ✅
**Last Updated**: 2024
**Confidence**: High (architecture), Medium (ACMI hypothesis)
**IDA**: All components renamed and commented
