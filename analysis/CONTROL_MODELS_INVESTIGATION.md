# Control Models Investigation - Simple / Complex / Hi-Def

**Date:** November 11, 2026  
**Status:** INVESTIGATING 🔍

## Background

Falcon 3.0 has three control models selectable by the player:
1. **Simple** - Basic flight model
2. **Complex** - Intermediate flight model  
3. **Hi-Def** - High-fidelity model (based on complex sim, known to break down at low speeds)

## Question

How do these models integrate with the aerodynamic force calculation we documented @ `sub_38CF3`?

**Possibilities:**
1. Different coefficient values per model (same algorithm, different divisors)
2. Completely different code paths
3. Flags that enable/disable certain physics stages
4. Different force calculation functions selected via dispatch

## Evidence Gathered - UPDATE

### Configuration Bytes FOUND BUT NOT CONTROL MODEL

**DS:8994h** → cs:word_2E172+1 (world X coordinate offset)  
**DS:8995h** → cs:word_2E174 (world Y coordinate offset)  
**DS:8996h** → es:word_44D3D (unknown)  
**DS:899Ah** → mode_toggle_105f (mode toggle, not control model)

These bytes are multiplied by 0x3334 (13,108 = tile size) and used in `farobj_cfg_delta_apply` for world positioning, **NOT flight physics**.

**Conclusion:** Control model setting is stored elsewhere!

### New Search Target

Need to find where control model (0=simple, 1=complex, 2=hidef) is:
1. Stored in config/save file
2. Read during initialization  
3. Used to select physics behavior

**Likely patterns:**
```asm
cmp    byte_XXXX, 2        ; check if hidef
je     hidef_path
cmp    byte_XXXX, 1        ; check if complex
je     complex_path
; simple path (default)
```

### Aerodynamics Entry Point

**Function:** `sub_3E16B` @ 0x3E16B (865 bytes) - "farobj_cmd_accum_sweep"
- Only 1 caller: `sub_307A5`
- Does entity/command management, not direct physics
- May dispatch to different physics implementations

### Force Calculation Function

**Function:** `sub_38CF3` @ 0x38CF3 (2284 bytes)
- Contains the elevator/aileron force calculations we documented
- NO direct callers (may be called via function pointer or inline)
- Located in code region with other large functions

### No Obvious Branching Found

Search for "simple|complex|hi-def|hidef|control.*model|flight.*model" found no matches in function descriptions.

## Hypotheses

### Hypothesis 1: Coefficient-Based (MOST LIKELY)
The same algorithm runs for all models, but with different coefficient values:

```c
struct AircraftPhysics {
    int16_t speed_threshold;     // +0x60h
    int16_t force_divisor_1;     // +0x66h  ← Different per model?
    int16_t control_authority;   // +0x68h  ← Different per model?
    int16_t min_speed_effect;    // +0x6Ah
    int16_t force_divisor_2;     // +0x6Ch  ← Different per model?
    // ...
};
```

**Evidence:**
- Algorithm already has 5 stages of complexity
- Speed-dependent scaling provides realistic behavior
- Different divisors would create different handling
- Simple: large divisors = less responsive
- Complex: medium divisors = balanced
- Hi-Def: small divisors = very responsive (breaks down at low speed?)

**Why Hi-Def Breaks at Low Speed:**
With small divisors in the low-speed formula:
```c
force = (control_input × speed) / force_divisor;
```
At very low speeds with small divisor, force becomes tiny or unstable.

### Hypothesis 2: Code Path Selection

Different functions or branches based on config byte:
```c
if (control_model == HIDEF) {
    compute_hidef_aerodynamics();
} else if (control_model == COMPLEX) {
    compute_complex_aerodynamics();
} else {
    compute_simple_aerodynamics();
}
```

**Evidence Against:**
- No obvious branching found in aerodynamics functions
- sub_38CF3 has no callers (suggests single implementation)
- Would require finding 3 different force calculation functions

### Hypothesis 3: Stage Enable/Disable

Same code, but certain stages skipped based on flags:
```c
if (model >= COMPLEX) {
    // Apply minimum threshold
}
if (model == HIDEF) {
    // Apply quadratic high-speed dampening
} else {
    // Always use linear
}
```

**Evidence:** 
- Could explain why Hi-Def has issues (more complex math)
- Would show as conditional gates in assembly
- Haven't found such gates yet

## Investigation Plan

### Step 1: Find Configuration Bytes
- Read addresses DS:8994h, 8995h, 8996h, 899Ah
- Determine which byte is control model setting
- Check where these bytes are read during physics

### Step 2: Search for Conditional Physics
Look for assembly patterns like:
```asm
mov    al, ds:8994h           ; load control model
cmp    al, 2                  ; check if HI-DEF
jne    simple_path
; hi-def specific code
```

### Step 3: Extract All Aircraft Coefficients
- Get Simple model coefficients for F-16
- Get Complex model coefficients for F-16
- Get Hi-Def model coefficients for F-16
- Compare the differences

### Step 4: Test Low-Speed Behavior
If we find the coefficients, calculate what happens at low speed:
```
speed = 50 (low)
control_input = 2048 (full)

Simple:   force = (2048 × 50) / large_divisor  → small force (sluggish)
Complex:  force = (2048 × 50) / medium_divisor → medium force
Hi-Def:   force = (2048 × 50) / small_divisor  → large force

But if divisor is TOO small and speed approaches 0:
force = (2048 × 5) / 10 = 1024      ; still reasonable
force = (2048 × 1) / 10 = 204.8     ; getting twitchy
force = (2048 × 0) / 10 = 0         ; DEAD STICK!
```

This could explain the low-speed breakdown!

## Data Structures to Find

### Config Structure (DS:8994h area)
```c
struct GameConfig {
    uint8_t byte_8994;           // Unknown
    uint8_t byte_8995;           // Unknown
    uint8_t byte_8996;           // Unknown
    // ...
    uint8_t byte_899A;           // Unknown
    // One of these is likely control_model (0=simple, 1=complex, 2=hidef)
};
```

### Aircraft Template per Model
```c
struct AircraftData {
    // ... standard fields ...
    
    // Physics coefficients @ +0x60-0x70
    struct {
        int16_t speed_threshold;
        int16_t field_62;
        int16_t field_64;
        int16_t force_divisor_1;      // Elevator
        int16_t control_authority;
        int16_t min_speed_effect;
        int16_t force_divisor_2;      // Aileron
        int16_t control_mult_2;
        int16_t speed_threshold_2;
    } physics[3];  // [0]=simple, [1]=complex, [2]=hidef?
};
```

Or separate template copies per model?

## Questions to Answer

1. **Where is control model stored?**
   - DS:8994h-899Ah config bytes?
   - Entity structure?
   - Global variable?

2. **How are coefficients selected?**
   - Table lookup: `coefficients[aircraft_type][control_model]`?
   - Single set of coefficients (model doesn't affect physics)?
   - Completely different code paths?

3. **What breaks in Hi-Def at low speed?**
   - Division by near-zero speed?
   - Overflow in force calculation?
   - Instability in accumulation?
   - Missing stall model?

4. **Is it per-aircraft or global?**
   - Does player aircraft use player setting?
   - Do AI aircraft always use same model?
   - Mixed models in same mission?

## Next Steps

1. Search for DS:8994h, 8995h, 8996h, 899Ah usage in physics code
2. Look for table lookups with 3 entries (3 models)
3. Extract coefficient values from game data files
4. Compare F-16 coefficients across potential model variants
5. Trace from config load to physics application

## Status

**Current Understanding:** 95% of single model documented  
**Model Selection:** 0% understood  
**Model Differences:** 0% understood

This is a **critical missing piece** that could explain:
- Player experience differences
- Hi-Def low-speed issues
- Why certain players prefer certain models
- Aircraft handling variations

---

*Investigation: November 11, 2026*  
*Analyst: Kiro*  
*Status: OPEN*
