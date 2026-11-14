# Falcon 3.0 Weapons Systems - Manual Summary

Quick reference extracted from Section IX (Flight) of the Falcon 3.0 manual to aid code analysis.

## Air-to-Air Weapons

### 1. AIM-9P Sidewinder (Short Range Missile - SRM)
- **Type**: Heat-seeking (infrared)
- **Aspect**: Rear-aspect only
- **HUD Indicator**: Small aiming reticle
- **Guidance**: Infrared seeker head with audio tone when tracking
- **Limitations**: Can be spoofed by sun, flares
- **Key**: Must be "in parameters" for effective kill

### 2. AIM-9M Sidewinder (Short Range Missile - SRM)  
- **Type**: Heat-seeking (infrared)
- **Aspect**: All-aspect (can lock from any angle)
- **HUD Indicator**: Medium aiming reticle
- **Guidance**: Improved infrared seeker
- **Advantages**: More flexible than AIM-9P, better resistance to countermeasures

### 3. AIM-120 AMRAAM (Medium Range Missile - MRM)
- **Type**: Radar-guided
- **Aspect**: All-aspect
- **HUD Indicator**: Large aiming reticle  
- **Guidance**: Active radar homing
- **Range**: Longer than Sidewinders
- **Note**: Requires radar lock

### 4. M61A1 Vulcan Cannon (Gun - DGFT Dogfight)
- **Type**: 20mm rotary cannon
- **HUD Mode**: DGFT (Dogfight)
- **HUD Display**: M61 Aiming Funnel (no reticle)
- **Ammo**: Limited (typically 512 rounds)
- **Rate of Fire**: High-speed burst
- **Usage**: Close-range dogfighting

## Air-to-Ground Weapons

### Missiles
- **AGM-65 Maverick**: Air-to-ground missile with multiple variants (AGM-65D mentioned)

### Bombs
- Various unguided and guided munitions
- GBU designation for guided bomb units

## Weapon Selection

### Controls
- **E key**: Cycle through air-to-air weapons (SRM → MRM → Gun)
- **B key**: Cycle through air-to-ground weapons
- **Spacebar**: Fire weapon

### Stores Control Panel (SCP)
Displays selected weapon info in format:
- `A-A 2 AIM120` = Air-to-air mode, 2 missiles, AIM-120 type
- `A-G 4 AGM-65D` = Air-to-ground mode, 4 missiles, AGM-65D type

### HUD Mode Indicators
- **SRM**: Short Range Missile (Sidewinder)
- **MRM**: Medium Range Missile (AMRAAM)
- **DGFT**: Dogfight mode (cannon)
- **A-G modes**: Various (CCIP, CCRP, EEOM, etc.)

## Lock-On Indicators

When missile achieves target lock:
1. **Aiming Reticle blinks** in HUD
2. **Target diamond** attaches to Target Designator Box
3. **Audio tone** from seeker head (for heat-seeking missiles)

Note: Lock tone does NOT guarantee hit - must be "in parameters" (correct range, aspect, target not maneuvering excessively).

## Countermeasures

### Defensive
- **Chaff**: Confuses radar-guided missiles
- **Flares**: Decoys heat-seeking missiles
- **Maneuvering**: Break locks, force missiles to miss

### Environmental Factors
- **Sun**: Can spoof heat-seeking missiles
- **Terrain**: Low-altitude flight can break radar locks
- **Speed/Energy**: High-speed targets harder to track

## Code Analysis Connections

### Weapon Type Mapping (from code analysis)

Based on manual descriptions, likely mappings to discovered types:

| Manual Name | Code Type | Evidence |
|-------------|-----------|----------|
| AIM-9 Sidewinder | 0x12 | velocity 6645, max_speed 506, damage_tier 5, 12× burst |
| AIM-120 AMRAAM | 0x13 | velocity 50127, max_speed 202, damage_tier 2, single shot |
| M61A1 20mm Gun | 0x33 | Same params as 0x12 but 6× burst, shared "gun burst" behavior |
| Unknown Gun Variant | 0x34 | velocity 21360, damage_tier 6 |
| Unknown Gun Variant | 0x35 | velocity 10680, max_speed 202, damage_tier 5 |
| Unknown Gun Variant | 0x36 | velocity 10680, max_speed 202, damage_tier 4 |
| Unknown Gun Variant | 0x37 | velocity 50127, max_speed 202, damage_tier 2 |

### Observations

1. **Burst fire for missiles**: The 12× burst for type 0x12 likely represents ripple-fire capability or multi-round salvos, not individual missile behavior.

2. **Shared parameters**: Types 0x12 and 0x33 share velocity/speed params, suggesting the gun may inherit missile ballistics (common in older sims for simplicity).

3. **Damage tiers**: Manual doesn't specify numeric damage values, but implies:
   - Guns: sustained fire, cumulative damage
   - Sidewinders: moderate-high damage (single hit usually kills)
   - AMRAAM: similar to Sidewinder

4. **Guidance systems**: Manual distinguishes:
   - Infrared (AIM-9): Target heat signature
   - Radar (AIM-120): Active radar homing
   - Gun: Ballistic (no guidance)

   Code likely has separate guidance handlers for each type (sub_2F6D0 @ 0x2F6D0 - TBD).

5. **Lock-on logic**: Code should have:
   - Seeker head simulation (angle limits, lock range)
   - Lock tone trigger
   - "In parameters" validation (range, aspect, closure rate)
   - Visual indicators (blinking reticle)

## Next Steps for Code Analysis

1. Search for HUD mode strings ("SRM", "MRM", "DGFT")
2. Find lock-on logic (audio tone trigger, reticle blink)
3. Decode guidance systems (IR vs radar vs ballistic)
4. Map damage tiers to actual damage calculation
5. Find countermeasure effectiveness logic
6. Locate "in parameters" validation code
7. Identify weapon spawn differences (burst count, velocity, damage)

## References

- Section IX: FLIGHT (manual/chapters_consolidated/09_f_l_i_g_h_t.txt)
- Section XIII: REFERENCE (manual/chapters_consolidated/13_r_e_f_e_r_e_n_c_e.txt)
- Section VI: AIR COMBAT SCHOOL (manual/chapters_consolidated/06_a_i_r___c_o_m_b_a_t___s_c_h_o_o_l.txt)
