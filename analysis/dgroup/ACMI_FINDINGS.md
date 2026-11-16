# ACMI Investigation Findings

## Key Discoveries

### 1. ACMI Files Found ✓
- **acmi.dat** - ACMI data file
- **acmi.idx** - ACMI index file  
- String: "K4.`ACMI" - Menu label

### 2. ACMI Menu Option Found ✓
**Location**: Menu dispatcher at 0x1909A0, case 8

```assembly
0x190A8B: ; jumptable case 8
0x190A8E: mov ax, 602Eh
0x190A91: mov es, ax
0x190A90: push word ptr es:aK4Acmi+2; ".`ACMI"
0x190A95: push word ptr es:aK4Acmi; "K4.`ACMI"
0x190A9A: push si
0x190A9B: call sub_11CC39  ; ACMI handler
```

### 3. View Mode Initialization ✓
**Function**: `view_mode_set` at 0x1086EC

**Key instruction** at 0x1087B2:
```assembly
mov cs:view_pipeline_mode, al  ; AL = 0 from earlier
```

This function initializes MANY flags to 0, including `view_pipeline_mode`.

**Observation**: The initialization sets mode to **0** by default!

## The Question

If `view_mode_set` always sets the mode to 0, how does ACMI mode set it to 1?

### Hypothesis 1: Parameter-Based
- `view_mode_set` might take a parameter
- Different callers pass 0 (sim) or 1 (ACMI)
- Need to find callers and check parameters

### Hypothesis 2: Separate ACMI Init
- There's a different initialization path for ACMI
- ACMI code directly writes to `view_pipeline_mode`
- The menu handler or ACMI loader sets it

### Hypothesis 3: Post-Init Modification
- `view_mode_set` runs first (sets everything to 0)
- Then ACMI-specific code modifies the flag
- Look for writes AFTER initialization

## What We Need

1. **Find all callers of `view_mode_set`** 
   - Check what parameters they pass
   - See if ACMI path is different

2. **Search for other writes to `view_pipeline_mode`**
   - We found only 1 write (at init)
   - But maybe there's a second write we missed
   - Or an indirect write via pointer

3. **Trace ACMI execution flow**
   - From menu selection → ACMI handler → mode setting
   - Find where the flag gets set to 1

## Next Steps

Priority 1: Find ALL callers of `view_mode_set` (0x1086EC)
- Check parameters
- See context of calls
- Identify ACMI vs normal sim paths

Priority 2: Double-check for other writes
- Search entire binary for 0x107762 (flag address)
- Look for byte writes, word writes, indirect writes
- Might have missed something

Priority 3: Trace ACMI flow
- Follow sub_11CC39 (ACMI handler)
- See what it calls
- Find path to mode setting

## Current Understanding

```
Normal Simulation:
  Startup → view_mode_set(?) → mode = 0 → Sim loop Path A

ACMI Playback:
  ACMI Menu → sub_11CC39 → ??? → mode = 1 → Sim loop Path B
                           ^
                           Missing link!
```

## Files Referenced

- **func_1909a0_disasm.txt** - Menu dispatcher with ACMI case
- **view_mode_setter_analysis.json** - Complete view_mode_set disassembly
- **acmi_analysis.json** - ACMI handler analysis
- **data_symbols.json** - ACMI file references

## Status

- ✓ Found ACMI menu option
- ✓ Found ACMI files
- ✓ Found initialization function
- ❌ Haven't found where mode gets set to 1 for ACMI
- ❌ Need to trace execution path

**Hypothesis remains unconfirmed**: Mode likely controls ACMI vs sim, but need to find the setting mechanism!
