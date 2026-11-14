# Migration to YAML-Based Registry

**Date**: 2026-11-11  
**Purpose**: Move from Python-only to YAML registry for better structure and integration with old Track E data

## Current State

### What We Have Now (Informal)
- `analysis/ida_scripts/apply_known_names.py` - 71 functions in Python dict
- Functions documented in markdown files
- Global variables as Python comments
- **Working well** for our needs

### What Exists (Track E Legacy)
- `registry/naming.yaml` - **2,116 functions** with metadata!
- `registry/structs.yaml` - Data structure definitions (MZHeader, RTLinkDirEntry, etc.)
- `registry/functions.yaml` - Function metadata
- `registry/routines.yaml` - Routine classifications
- `registry/game_knowledge.yaml` - Game system knowledge

## The Opportunity

We have **2,116 named functions** sitting in the old registry that we're not using!

**Format is excellent:**
```yaml
- ida: sub_16FDD
  name: always_true
  kind: function
  notes: returns constant 1 (finding 08/22)
```

## Proposed Architecture

### Structure

```
registry/
├── functions.yaml          # Master function registry (YAML)
├── globals.yaml            # Global variables (NEW)
├── structs.yaml            # Data structures (EXISTS)
├── game_knowledge.yaml     # Game systems (EXISTS)
└── README.md               # Documentation

analysis/ida_scripts/
├── apply_known_names.py    # IDA sync script (reads YAML)
├── export_to_yaml.py       # Export current Python → YAML
└── validate_registry.py    # Validate YAML consistency
```

### YAML Format

**functions.yaml:**
```yaml
schema: 1
functions:
  - address: 0x11450
    ida_name: sub_11450
    name: flight_control_axes_read_normalize
    system: flight_physics
    size: 114
    level: 2
    doc: |
      Reads 4 flight control axes and normalizes to ±2048 range.
      Clamps to prevent overflow.
    params:
      - {name: axis, type: int, desc: "Axis number 0-3"}
    returns: {type: int16, desc: "Normalized value ±2048"}
    callers: 8
    callees: 3
```

**globals.yaml (NEW):**
```yaml
schema: 1
globals:
  - address: 0x3840
    segment: DS
    name: terrain_heightmap_31x31
    size: 1922
    type: array[31][31]
    system: terrain
    doc: |
      31×31 height samples for terrain rendering.
      Bilinearly interpolated by tile_quad_sample.
```

## Migration Plan

### Phase 1: Extract & Merge (1-2 hours)
1. ✅ Keep current `apply_known_names.py` working
2. Create `export_to_yaml.py` to export our 71 functions to YAML
3. Analyze old `naming.yaml` for useful additions
4. Merge intelligently (our 71 are better documented)
5. Create `globals.yaml` from our current KNOWN_GLOBALS

### Phase 2: Update Scripts (1 hour)
1. Modify `apply_known_names.py` to read from YAML
2. Keep backward compatibility (can read Python dict OR YAML)
3. Add validation: `validate_registry.py`
4. Test that IDA synchronization still works

### Phase 3: Documentation (30 min)
1. Update `WORKFLOW.md` to reference YAML
2. Create `registry/README.md` explaining structure
3. Document YAML schema

### Phase 4: Expand (ongoing)
1. Add more functions from old registry (2,116 available!)
2. Add data structures from `structs.yaml`
3. Cross-reference with `game_knowledge.yaml`

## Benefits

### Why YAML?
✅ **Human-readable** - Easy to edit in any editor  
✅ **Structured** - Proper schema with validation  
✅ **Extensible** - Can add fields without breaking code  
✅ **Tool-friendly** - Python, IDA, and other tools can read it  
✅ **Version control friendly** - Git diffs are meaningful  
✅ **Integration** - Can merge with old Track E data  

### Why Keep Python Script?
✅ **IDA integration** - Script runs inside IDA  
✅ **Flexibility** - Can do complex logic  
✅ **Backward compatibility** - Existing workflow continues  

### Best of Both
- YAML is the **source of truth** (data)
- Python is the **tool** (logic)
- Markdown is the **documentation** (narrative)

## Risks & Mitigations

| Risk | Mitigation |
|------|------------|
| Break current workflow | Keep Python script working, add YAML reader |
| YAML merge conflicts | Use schema validation, document merge strategy |
| Complexity increase | Start simple, add features incrementally |
| Old registry has wrong data | Our 71 functions override, validate before merging |

## Decision Points

### What to Merge from Old Registry?

**2,116 functions is a LOT**. We need to:
1. ✅ Check quality (are they accurate?)
2. ✅ Check overlap (do they conflict with our 71?)
3. ✅ Prioritize (which systems are complete?)
4. ✅ Validate (can we trust the addresses?)

**Strategy**: Start with **non-overlapping systems** we haven't documented yet:
- Input system (keyboard, joystick)
- Mission file loaders
- Save/load system
- Campaign management

### Schema Version

Use `schema: 1` for now, allows evolution:
- `schema: 2` could add new fields
- Tools check schema version for compatibility

## Implementation

### Step 1: Create functions.yaml

```bash
cd registry
python ../analysis/ida_scripts/export_to_yaml.py
# Creates functions_v2.yaml with our 71 functions
```

### Step 2: Validate

```bash
python ../analysis/ida_scripts/validate_registry.py
# Checks: no duplicate addresses, all fields present, etc.
```

### Step 3: Update apply_known_names.py

```python
import yaml

# Try YAML first, fall back to embedded dict
try:
    with open('../../../registry/functions.yaml') as f:
        data = yaml.safe_load(f)
        KNOWN_FUNCTIONS = {f['address']: f['name'] for f in data['functions']}
except:
    # Fall back to embedded dict
    KNOWN_FUNCTIONS = { ... }
```

### Step 4: Test

```bash
cd analysis
# Run IDA sync - should work exactly as before
idat.exe -A -S"ida_scripts/apply_known_names.py" "ida_falconcd/FALCONCD.EXE.i64"
```

## Timeline

**Phase 1**: 1-2 hours (export, analyze, merge)  
**Phase 2**: 1 hour (update scripts)  
**Phase 3**: 30 min (documentation)  
**Total**: 2.5-3.5 hours for basic migration

**Phase 4** is ongoing - can add functions incrementally.

## Success Criteria

✅ IDA synchronization continues to work  
✅ Registry is in YAML format  
✅ Our 71 functions are preserved  
✅ Validation catches errors  
✅ Documentation is updated  
✅ Path to merge old registry is clear  

## Next Steps

1. **Review this plan** - Does it make sense?
2. **Decide**: Migrate now or later?
3. **If now**: Start with Phase 1 (export current functions)
4. **If later**: Keep current Python approach, revisit when we have 100+ functions

## Recommendation

**Start migration now** because:
- We have 71 functions (good foundation)
- Old registry has 2,116 functions (huge value)
- YAML is better long-term architecture
- Can do it incrementally without breaking current workflow

**Or wait** if:
- Current Python approach is working fine
- Don't want to add complexity yet
- Want to reach 100 functions first

**My vote**: Migrate now, but keep it simple - just functions.yaml and globals.yaml to start.

---

*Plan created: 2026-11-11*
