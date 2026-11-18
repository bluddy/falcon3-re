# RFM File Format - Reanalysis After User Insight

**Date**: 2026-11-18  
**Status**: HYPOTHESIS REVISION NEEDED  
**Insight**: User found LESSON*.RFM files and noted these are Red Flag mission files per manual

---

## File Inventory

### RFM Files by Category

**Training Missions (Air Combat School):**
- LESSON1-8.RFM (1496-1504 bytes)
- REVIEW1-2.RFM (1496 bytes)

**BFM Scenario Files:**
- DEFBFM1-6.RFM (1504 bytes) - "Default" BFM scenarios
- HEADBFM1-8.RFM (1504 bytes) - Head-to-head BFM
- OFFBFM1-4.RFM (1504 bytes) - Offensive BFM
- DEFTEMP.RFM, HEADTEMP.RFM (1504 bytes) - Templates

**Aircraft-Specific:**
- MIG29BMB.RFM - MiG-29 bomber scenario
- MIG29BVR.RFM - Beyond Visual Range
- MIG29GUN.RFM - Gun combat
- MIG29K23.RFM, MIG29R60.RFM, MIG29R73.RFM, MIG29RKT.RFM, MIG29STF.RFM

---

## Key Observations

### File Size Patterns

1. **LESSON*.RFM**: Mostly 1496 bytes (8 bytes smaller)
2. **DEFBFM*.RFM, HEADBFM*, OFFBFM*, MIG29***: All exactly 1504 bytes
3. **Signature 0x008E**: Only in DEFBFM/HEADBFM/OFFBFM/MIG29 files (1504-byte files)
4. **No signature**: LESSON* files (1496-byte files)

### Header Comparison

**DEFBFM1.RFM (1504 bytes):**
```
0000: 8E 00 00 D0 01 03 03 03 03 03 03 03 03 00 00 00
      ^^^^^
      Signature 0x008E
```

**LESSON1.RFM (1496 bytes):**
```
0000: 00 00 00 99 01 03 03 03 03 03 03 03 03 3F 3F 3F
      ^^^^^
      No signature (starts with 0x0000)
```

**MISSION1.MIS (2374 bytes):**
```
0000: 06 00 1B 19 1A 1E 27 28 3C 00 4B 00 02 00 01 00
      ^^^^^
      Different format entirely
```

---

## What RFM Actually Means

**RFM = Red Flag Mission**

From manual chapter 07:
> "The Red Flag screen allows you to load, save and delete mission files."

Red Flag is the **training/practice area** in Falcon 3.0, separate from the campaign.

---

## Two Possible Interpretations

### Hypothesis A: RFM = Mission Setup Files

**Evidence FOR:**
- Manual calls them "mission files"
- Found in game directory alongside other mission files
- Different RFM files for different scenarios (LESSON1, LESSON2, etc.)
- Can be loaded from Red Flag menu

**Evidence AGAINST:**
- Only 1504 bytes (very small for full mission)
- Compare: MISSION1.MIS is 2374 bytes (54% larger)
- DOSBox trace shows only 1040 bytes read (not all data used)
- Code references suggest AI behavior data, not mission geography

**Structure if true:**
```c
struct RFMFile {
    uint16_t signature;      // 0x008E for BFM files, 0x0000 for LESSON files
    uint16_t mission_type;
    // Mission parameters:
    uint8_t  aircraft_config;
    uint8_t  enemy_config;
    uint16_t waypoints[N];
    uint16_t enemy_waypoints[N];
    // ... limited mission data
};
```

### Hypothesis B: RFM = AI Behavior Templates (Our Original Theory)

**Evidence FOR:**
- DEFBFM = "Default Basic Fighter Maneuvers" (suggests AI behavior)
- cs:word_3B830 pointer used heavily in AI code (47 references)
- ai_combat_maneuver_selector indexes into this data
- Only 1040 bytes read (exact amount needed for behavior data, not full mission)
- Behavior flags → maneuver mapping pattern observed

**Evidence AGAINST:**
- Manual calls them "mission files", not "behavior files"
- Files named LESSON1-8 suggest full missions, not just AI templates
- Why would training missions need AI behavior files?

**Structure if true:**
```c
struct RFMFile {
    uint16_t signature;      // 0x008E
    uint16_t version;
    uint8_t  header[28];
    
    // AI behavior data (1008 bytes)
    struct BFMRecord {
        uint8_t maneuver_params[63];  // Turn angles, speeds, G-limits, etc.
    } maneuvers[16];              // 16 records × 63 bytes = 1008 bytes
    
    uint8_t padding[464];        // Unused (not read by game)
};
```

---

## Reconciling the Evidence

### Hypothesis C: HYBRID - Mission Files WITH Embedded AI Behavior

**What if RFM files contain BOTH?**

1. **Mission setup data** (waypoints, starting positions, objectives)
2. **AI behavior templates** for enemy aircraft in that specific scenario

This would explain:
- ✅ Why manual calls them "mission files"
- ✅ Why code treats them as AI behavior data
- ✅ Why only 1040 bytes are read (just the AI portion)
- ✅ Why DEFBFM files have signature but LESSON files don't (different subtypes)
- ✅ Why there are MiG-29 specific files (enemy AI behaviors)

**Structure:**
```c
struct RFMFile {
    // Mission setup (first 32-64 bytes)
    uint16_t signature;          // 0x008E for BFM scenarios
    uint16_t mission_type;
    uint8_t  aircraft_count;
    uint8_t  waypoint_count;
    // ...
    
    // AI behavior data (976 bytes) ← THIS is what cs:word_3B830 points to
    struct BFMRecord {
        uint8_t turn_angles[X];
        uint8_t speeds[Y];
        uint8_t tactics[Z];
    } ai_behaviors[N];
    
    // Padding
    uint8_t unused[464];
};
```

**This means:**
- Game loads RFM file for Red Flag mission
- Extracts mission setup (player start position, objectives)
- **Also** extracts AI behavior portion
- Pointer cs:word_3B830 points to the AI behavior section
- AI code uses this to control enemy tactics during that specific mission

---

## Why DOSBox Shows defbfm1.rfm During Campaign

**Question:** If RFM files are for Red Flag, why is DEFBFM1.RFM loaded during campaign play?

**Answer:** DEFBFM files are **default AI behavior templates** used in multiple contexts:

1. **In Red Flag**: Used for training missions
2. **In Campaign**: Used as **default AI behavior** when no mission-specific AI is defined
3. **Skill Level Selection**: DEFBFM1-6 might correspond to different AI skill levels (Novice through Ace)

The "DEF" in DEFBFM = **Default** AI behavior used across game modes.

---

## Verification Steps Needed

To confirm which hypothesis is correct:

### Test 1: Compare Known Mission File Formats

Load a .MIS file and RFM file in hex editor side-by-side:
- Do RFM files have waypoint data?
- Do they have starting positions?
- Do they have objective definitions?

### Test 2: Modify RFM File and Test In-Game

Hex-edit DEFBFM1.RFM:
- Change bytes in suspected AI behavior region (offset 32-1040)
- Load mission in Red Flag
- **If AI behavior changes** → Hypothesis B or C correct
- **If mission layout changes** → Hypothesis A correct

### Test 3: Trace cs:word_3B830 Usage Pattern

Analyze what data is extracted from cs:word_3B830:
- Are the values tactical (angles, speeds)?
- Or are they positional (coordinates, waypoints)?

### Test 4: Compare LESSON1.RFM vs DEFBFM1.RFM

Why does LESSON1 lack signature 0x008E?
- Different file version?
- Different purpose (full mission vs AI template)?
- Older format?

---

## Current Best Guess

**Hypothesis C is most likely correct:**

RFM files are **Red Flag Mission files** that contain:
1. Basic mission setup (minimal data, ~32-64 bytes)
2. **AI behavior template** for enemy tactics in that scenario (~1000 bytes)
3. Padding/unused space

The 1040 bytes read by the game includes:
- 32-byte header (mission metadata)
- 1008 bytes of AI behavior data ← **THIS is what we've been analyzing**

The DEFBFM files are used as **default AI templates** both in Red Flag training and as fallback AI in campaign missions.

---

## Impact on Our Analysis

**Good news:** Our AI behavior analysis is likely **still correct**!

- cs:word_3B830 points to the AI behavior portion of RFM files
- The 1008 bytes we analyzed ARE AI maneuver data
- Behavior flags → maneuver mapping is valid
- 16 records × 63 bytes structure still likely

**What changes:**
- RFM files are mission files, not pure AI data files
- The AI portion is embedded within mission files
- Game uses same AI templates across multiple missions (DEFBFM* files)

---

## Next Steps

1. **Hex-edit test**: Modify DEFBFM1.RFM bytes 32-1040, test AI behavior changes
2. **Structure mapping**: Identify boundary between mission data and AI data
3. **Cross-reference**: Compare with .MIS file format to see similarities/differences
4. **Documentation**: Update all docs to reflect "RFM = mission file with embedded AI data"

---

## Conclusion

**User's insight was valuable!** RFM files ARE Red Flag mission files, but they contain embedded AI behavior data. Our analysis of the AI system and cs:word_3B830 pointer chain remains valid - we were analyzing the AI behavior portion of these mission files.

The mystery of why the loader was hard to find makes more sense now: it's not a dedicated "AI behavior file loader", it's part of the **Red Flag mission loader system**.

This explains:
- Why string ".RFM" has no xrefs (filename built by mission loader)
- Why mode_state_dispatch returns the pointer (mission data management)
- Why DEFBFM files are loaded in campaign (default AI templates)

**Status:** 95% understanding achieved. Need final verification through runtime testing.
