# Aircraft Type Code Mapping

## Overview

Mission files use single-byte type codes (byte 3 of aircraft records) to identify aircraft types. These codes reference aircraft initialization routines that set performance characteristics.

## Type Code Mapping

### Confirmed from IDA Analysis

Based on aircraft initialization code at addresses 0x4C301-0x4C546 in level19_batch4.txt:

| Type Code | Hex  | Aircraft (Hypothesis) | Evidence | Role |
|-----------|------|----------------------|----------|------|
| 0x01      | 0x01 | F-16 (Player)        | Type 1 used for 5-aircraft player flight | Fighter |
| 0x34      | 0x34 | F-15 Eagle           | Allied fighter, byte[si+1Ah]=6 | Air Superiority |
| 0x35      | 0x35 | F-111 Aardvark       | Allied strike, byte[si+1Ah]=5 | Strike/Bomber |
| 0x36      | 0x36 | F-4 Phantom II       | Allied fighter, byte[si+1Ah]=4 | Fighter/Strike |
| 0x05      | 0x05 | Support Aircraft     | Different structure, support role | AWACS/Tanker? |
| 0x06      | 0x06 | Support Aircraft     | Different structure, support role | AWACS/Tanker? |
| 0x07      | 0x07 | MiG-29 Fulcrum       | Enemy fighter, byte[si+2]=0x6C | Fighter |
| 0x08      | 0x08 | MiG-23 Flogger       | Enemy fighter/bomber, byte[si+2]=0x6C | Fighter/Strike |
| 0x09      | 0x09 | MiG-21 Fishbed       | Enemy fighter, byte[si+2]=0x0A | Fighter |
| 0x0A      | 0x0A | Su-25 Frogfoot       | Enemy ground attack | Attack |
| 0x0B      | 0x0B | Su-27 Flanker        | Enemy air superiority | Fighter |

### Performance Characteristics Set by Type

Each type code initializes a structure with specific values:

**Type 0x34 (F-15):**
```
[si+2]  = 0x0C06
[si+4]  = 0x5370
[si+6]  = 0x78
[si+8]  = 0x0000
[si+0Ah] = 0x37A0
[si+0Ch] = 0x2515
[si+0Eh] = 0x67
[si+1Ah] = 6
```

**Type 0x35 (F-111):**
```
[si+2]  = 0x0C16
[si+4]  = 0x29B8
[si+6]  = 0x50
[si+8]  = 0x0000
[si+0Ah] = 0x1BD0
[si+0Ch] = 0x128A
[si+0Eh] = 0x67
[si+14h] = 0xCA
[si+1Ah] = 5
```

**Type 0x36 (F-4):**
```
[si+2]  = 0x0416
[si+4]  = 0x29B8
[si+6]  = 0x50
[si+8]  = 0x0000
[si+0Ah] = 0x1BD0
[si+0Ch] = 0x0F04
[si+0Eh] = 0x400
[si+14h] = 0xCA
[si+1Ah] = 4
```

**Type 0x07 (MiG-29):**
```
[si+2]  = 0x6C
[si+3]  = 0xFF
[si+6]  = 0x100
[si+8]  = 0x4812
[si+0Ah] = 0x20
[si+0Eh] = 0x3674
[si+10h] = 0x34CC
[si+12h] = 0x200
[si+1Fh] = 0x24D6
[si+21h] = 0x06
[si+23h] = 0xF0
```

## Structure Field Interpretation (Hypothesis)

Based on the values and typical flight sim data:

| Offset | Size | Purpose (Hypothesis) |
|--------|------|---------------------|
| +0x00  | 2    | Base position/ID |
| +0x02  | 2    | Speed/thrust parameter |
| +0x04  | 2    | Turn rate or agility |
| +0x06  | 2    | Climb rate |
| +0x08  | 2    | Max speed or ceiling |
| +0x0A  | 2    | Acceleration |
| +0x0C  | 2    | Maneuverability |
| +0x0E  | 2    | Weapon capacity or radar range |
| +0x1A  | 1    | AI skill level or aggression |

## SQUAD0.MIS Aircraft Distribution

Applying this mapping to SQUAD0.MIS's 26 aircraft:

**Allied Forces (15 aircraft):**
- 5× Type 0x01 (F-16) - Player flight
- 3× Type 0x34 (F-15) - Air superiority escort
- 3× Type 0x35 (F-111) - Strike package
- 4× Type 0x36 (F-4) - Additional fighters

**Enemy Forces (11 aircraft):**
- 2× Type 0x09 (MiG-21) - Interceptors
- 3× Type 0x0A (Su-25) - Ground attack
- 3× Type 0x08 (MiG-23) - Fighter/bombers
- 1× Type 0x07 (MiG-29) - Air superiority
- 2× Type 0x0B (Su-27) - Advanced fighters

## Notes

1. **Type 0x01 Special:** Always used for player flight, has unique handling

2. **Allied Types (0x34-0x36):**
   - Set different byte[si+1Ah] values (6, 5, 4)
   - This may indicate AI skill levels
   - Higher numbers = better performance?

3. **Enemy Types (0x07-0x0B):**
   - All set byte[si+2] = 0x6C (most types)
   - May share common AI behavior
   - Type 0x09 uses byte[si+2] = 0x0A (different behavior)

4. **Support Types (0x05-0x06):**
   - Completely different structure
   - Likely AWACS, tankers, or transports
   - Not combat aircraft

## Verification Needed

1. Confirm aircraft names by:
   - Finding string tables in IDA
   - Checking .LOD file relationships
   - Analyzing mission file patterns across theaters

2. Decode structure fields:
   - Performance parameters (speed, turn rate, etc.)
   - AI behavior flags
   - Weapon loadout references

3. Map remaining type codes:
   - Types 0x02-0x04 (not seen in SQUAD0.MIS)
   - Types 0x0C-0x33 (if they exist)
   - Types 0x37+ (if they exist)
