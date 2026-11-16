# Mission Briefing Strings - Complete Extraction

**Date**: 2026-11-16  
**Total Strings**: 1,330 in database  
**Mission-Related**: 272 strings  
**Menu Items**: 28 items  
**Primary Source**: R29 segment (708 strings)

---

## Executive Summary

Comprehensive extraction of all mission/briefing related strings from Falcon 3.0, revealing the complete UI structure for mission setup, briefing, execution, and debriefing.

**Key Finding**: Mission briefing system is highly detailed with 272 specialized strings covering:
- 53 navigation elements (waypoints, targets, bases)
- 49 pilot/aircraft management strings
- 40 mission type indicators
- 38 mission information strings
- 28 threat indicators
- 21 flight parameters

---

## String Categories

### 1. NAVIGATION (53 strings)

**Most Referenced**:
- `j4.`TARGET` (12 refs) - Target selection
- `Y/.`ALLIED WAYPOINTS` (5 refs) - Friendly navigation points

**Target Types**:
```
AIRBASE, AIRFIELD, NAVAL BASE, ARMY BASE
CHEMICAL WEAPONS PLANT, BIOLOGICAL WEAPONS PLANT
ANTISHIP, STRAFETARGET
```

**Target Classes** (A-D priority system):
```
-CLASS A TARGET: (Strategic - highest priority)
-CLASS B TARGET: (Infrastructure)
-CLASS C TARGET: (Military installations)
-CLASS D TARGET: (Tactical targets)
```

**Waypoint Management**:
```
..`ADD WAYPOINT
0.`DELETE WAYPOINT
1.`ENEMY WAYPOINTS
3.`SET WAYPOINTS
4.`WAYPOINT #
4.`ZOOM TO TARGET
```

**Flight Path Messages**:
```
COPY RETURNING TO BASE.
CLOSING ON GROUND TARGETS.
CLOSING ON PRIMARY TARGET.
CLOSING ON SHIP TARGET.
ATTACKING GROUND TARGETS!
ATTACKING PRIMARY TARGET.
```

---

### 2. PILOT & AIRCRAFT (49 strings)

**Most Referenced**:
- `e1.`ENEMY AIRCRAFT` (10 refs) - Enemy air display
- `.`ASSIGN PILOTS` (7 refs) - Pilot selection UI
- `;-.`STORES` (5 refs) - Weapons stores
- `E1.`EDIT FLIGHTS` (5 refs) - Flight configuration

**Flight Management**:
```
..`ADD AIRCRAFT
..`ADD FLIGHT
/.`AIRCRAFT #
0.`DELETE AIRCRAFT
0.`DELETE FLIGHT
1.`FLIGHT #
```

**Pilot Management**:
```
,.`PILOT
1.`F-16 PILOTS
2.`PILOT
2.`PILOT INFORMATION
3.`PILOT TRANSFER
NUMBER OF PILOTS ACTIVE:
NUMBER OF PILOTS KILLED:
NUMBER OF PILOTS MIA:
PILOT ABILITIES:
PILOT STATUS:
```

**Aircraft Status**:
```
AVAILABLE AIRCRAFT:
AVAILABLE PILOTS:
NUMBER OF AVAILABLE AIRCRAFT:
ALL FRIENDLY AIRCRAFT
ALL PLAYER AIRCRAFT
```

**Weapons/Stores**:
```
/.`CLEAR ALL WEAPONS
MISCELLANEOUS STORES REMAINING:
STORES.BIN
DUMPING AIR-TO-GROUND STORES!
FOR NEGLIGENT WEAPONS USAGE.
WEAPONS USAGE:
```

---

### 3. MISSION TYPES (40 strings)

**Most Referenced**:
- `G3.`RECON` (4 refs) - Reconnaissance mission

**Primary Mission Types**:
```
CAP           - Combat Air Patrol
CAS           - Close Air Support
ESCORT        - Escort mission
SEAD          - Suppression of Enemy Air Defenses
RECON         - Reconnaissance
GROUNDSTRIKE  - Ground attack
STRIKE        - Strategic strike
```

**Specialized Missions**:
```
AREACAP                  - Area Combat Air Patrol
ESCORTTRANSPORT          - Escort transport aircraft
ESCORTSTRIKEAIRCRAFT     - Escort strike aircraft
ESCORTBOMBERS            - Escort bomber formation
SEADSHIP                 - Anti-ship SEAD
RECONSHIP                - Naval reconnaissance
SEADGROUND               - Ground SEAD
FRIENDLYINTERCEPT        - Friendly intercept
ESCORTE3                 - Escort E-3 AWACS
HELOSUPPLYCAP            - Helicopter supply CAP
HAVCAP                   - High-altitude CAP
SUPPLY CAP               - Supply mission CAP
```

**Mission Menu Items**:
```
FLY MISSION
/.`BRIEFING
/.`CHOOSE MISSION
0.`DELETE MISSION
2.`NEXT MISSION
3.`SAVE MISSION
G2.`LOAD MISSION
0.`CLEAR MISSION
```

---

### 4. MISSION INFO (38 strings)

**Most Referenced**:
- `G2.`LOAD MISSION` (4 refs)
- `.`MISSION.` (2 refs)
- `0.`CLEAR MISSION` (2 refs)
- `j0.`DEBRIEFING` (2 refs)

**Mission Setup**:
```
CHOOSE MISSION
LOAD MISSION
CLEAR MISSION
DELETE MISSION
SAVE MISSION
NEXT MISSION
FLY MISSION
```

**Mission Briefing**:
```
RECEIVING   THEATER   BRIEFING
CURRENT MISSION:
MISSIONS FLOWN:
MISSIONS ACCOMPLISHED:
NUMBER OF MISSIONS FLOWN:
----MISSION #
```

**Mission Status**:
```
YOUR MISSION IS OVER!
ENDED THE MISSION
MISSION SUCCESSFUL.
MISSION FAILURE.
MISSION EVALUATION:
nMISSION SUMMARY:
```

**Communications**:
```
TRANSMISSION BAD, REPEAT.
REQUEST PERMISSION TO ENGAGE.
REQUEST PERMISSION TO ATTACK.
FROM AWACS: PERMISSION GIVEN TO DESTROY ENEMY AIRCRAFT.
PERMISSION DENIED
```

**Debug/Dev**:
```
MISSION CONVERSION NOT IMPLEMENTED
mission.dmp
```

---

### 5. THREAT (28 strings)

**Most Referenced**:
- `x1.`ENEMY FORCES` (8 refs) - Enemy force display
- `THREAT` (1 ref)

**Air Threats**:
```
BANDIT! BANDIT!
BANDIT! BANDIT +NN O'CLOCK HIGH
ENEMY LOCK ON!
SCRATCH ONE BANDIT!
ENEMY MIGS
FROM AWACS: BE ADVISED - INCREASED ENEMY AIR ACTIVITY.
```

**Ground Threats**:
```
SAM SITE
SAM
AAA (Anti-Aircraft Artillery)
. POSSIBLE SAM THREATS.
. POSSIBLE AAA THREATS.
```

**Electronic Warfare**:
```
FROM AWACS: BE ADVISED - ENEMY ECM ACTIVITY DETECTED.
```

**Territory**:
```
PERCENT OCCUPIED BY ENEMY
ENEMY (RED AREA) OCCUPIES
DESTROY ENEMY
```

**Menu Items**:
```
..`AAA
1.`ENEMY SETUP
3.`SAMS
x1.`ENEMY FORCES
```

---

### 6. FLIGHT PARAMETERS (21 strings)

**Most Referenced**:
- `n/.`ALTITUDE` (17 refs) - Altitude setting

**Parameters**:
```
ALTITUDE =       FEET
SPEED =      KNOTS
HEADING =
n/.`ALTITUDE (menu item)
3.`SPEED (menu item)
```

**Fuel Warnings**:
```
NO FUEL--WAITING FOR RESUPPLY
BE ADVISED - FUEL IS LOW!
FUEL CRITICAL! FUEL CRITICAL!
TIME TO FEED THE WORMS, BUD!
POUNDS OF FUEL REMAINING:
FUEL300
FUEL370
```

**Time**:
```
CURRENT TIME:
RESUPPLY TIME:
REPLACEMENT TIME:
```

---

### 7. UI CONTROL (17 strings)

**Most Referenced**:
- `*0.`CONTINUE...` (3 refs) - Proceed to flight

**Navigation**:
```
*0.`CONTINUE...
q3.`RERUN
K4.`ACMI (replay)
F-.`SQDINFBK (squadron info back)
j0.`DEBRIEFING
```

**Generic**:
```
fmenu.def (menu definition file)
ESCAPE TO SKIP
DONE
OK
CANCEL
BACK
NEXT
```

---

### 8. RESULTS/STATISTICS (14 strings)

**Score/Results**:
```
.`RESULT
Top 10 High Scores
GOOD KILL! GOOD KILL!
SCORE??.TMP
SCORENN.TMP
SCORE-1.TMP
SCORE00.TMP
```

**Kill Statistics**:
```
PLANE KILLS:
GOT A BVR KILL ON A
GOT HIT AND IS KILLED.
```

**Losses**:
```
ALLIED GROUND LOSSES:
ENEMY GROUND LOSSES:
ENEMY AIRCRAFT LOSSES:
ALLIED AIRCRAFT LOSSES:
```

---

### 9. WEATHER (8 strings)

```
WEATHER
FORECAST
OVERCAST
TOMORROW'S FORECAST:
WIND
VISIBILITY
CLOUD
CEILING
```

---

### 10. DISPLAY (4 strings)

```
VIEW =
ZOOM =
OMAPOBJ ID
-.`.MAP
```

---

## Menu Item Format

**Pattern**: `[Key][Code].`[Label]`

### Examples:

| String | Key | Code | Label | Purpose |
|--------|-----|------|-------|---------|
| `j4.`TARGET` | J | 4 | TARGET | Select target |
| `E1.`EDIT FLIGHTS` | E | 1 | EDIT FLIGHTS | Edit flight composition |
| `*0.`CONTINUE...` | * | 0 | CONTINUE | Start mission |
| `Y/.`ALLIED WAYPOINTS` | Y | / | ALLIED WAYPOINTS | View allied waypoints |
| `n/.`ALTITUDE` | N | / | ALTITUDE | Set altitude |

**Key Codes**:
- Numbers (0-9): Menu position or priority
- `-`: Back/cancel action
- `/`: Slash commands (special functions)
- Letters: Keyboard shortcuts

---

## Complete Menu Item List (28 items)

```
*0.`CONTINUE...          - Start mission
E1.`EDIT FLIGHTS         - Configure flights
F-.`SQDINFBK             - Squadron info back
G2.`LOAD MISSION         - Load saved mission
G3.`RECON                - Reconnaissance mission
J0.`                     - (Unknown/empty)
K4.`ACMI                 - Air Combat replay
P0.`DAY                  - Day setting
Q3.`RED FLAG CONTROL     - Red Flag training control
S-.`SQUAD                - Squadron menu
T4.`TAKEOFF              - Begin takeoff
V1.`EDIT NODES           - Edit nodes (multiplayer?)
X2.`MAX G.:              - Max G setting
Y0.`DEFAULT LOAD         - Default loadout
d6.`                     - (Unknown)
e1.`ENEMY AIRCRAFT       - Enemy aircraft display
e2.`MECH INF             - Mechanized infantry
f3.`REPORT               - Mission report
j-.`SUPINFBK             - Supply info back
j0.`DEBRIEFING           - Post-mission debriefing
j4.`TARGET               - Target selection
m6.`                     - (Unknown)
q3.`RERUN                - Retry mission
r2.`NAME                 - Name input
u4.`THEATER              - Theater selection
w-.`TEMP                 - Temporary (?)
x1.`ENEMY FORCES         - Enemy force display
y0.`DEFEAT               - Defeat condition
```

---

## Data Structure Implications

### MissionRecord Structure (Inferred):

```c
struct MissionRecord {
    uint8_t mission_type;           // CAP, STRIKE, CAS, SEAD, etc.
    uint8_t theater_id;             // Theater assignment
    uint16_t mission_day;           // Campaign day
    uint16_t mission_time;          // Time of day (0600, 1200, etc.)
    
    // Target information
    uint16_t target_type;           // AIRBASE, SAM_SITE, etc.
    uint8_t target_class;           // A, B, C, or D priority
    int16_t target_x;               // Grid coordinate
    int16_t target_y;               // Grid coordinate
    uint16_t target_altitude;       // Target altitude
    
    // Flight parameters
    uint16_t altitude;              // Mission altitude (feet)
    uint16_t speed;                 // Mission speed (knots)
    uint16_t heading;               // Initial heading
    
    // Waypoints
    uint8_t waypoint_count;         // Number of waypoints
    WaypointRecord waypoints[N];    // Waypoint array
    
    // Threats
    uint8_t sam_threat_level;       // SAM threat (0-10?)
    uint8_t aaa_threat_level;       // AAA threat (0-10?)
    uint8_t air_threat_level;       // Enemy aircraft threat
    
    // Script
    uint16_t script_offset;         // Pointer to mission script
    uint16_t script_length;         // Script size
    
    // Success criteria
    uint8_t primary_objective;      // What must be accomplished
    uint8_t secondary_objective;    // Optional objective
    uint16_t mission_timeout;       // Time limit
};
```

### WaypointRecord Structure:

```c
struct WaypointRecord {
    uint8_t waypoint_type;          // NAV, TARGET, INGRESS, EGRESS, BASE
    int16_t x;                      // Grid coordinate
    int16_t y;                      // Grid coordinate
    uint16_t altitude;              // Waypoint altitude (feet)
    uint16_t speed;                 // Target speed at waypoint (knots)
    uint8_t action;                 // Action at waypoint (fly-by, attack, etc.)
};
```

---

## Mission Flow (Inferred from Strings)

### 1. Mission Selection
```
CHOOSE MISSION → LOAD MISSION → RECEIVING THEATER BRIEFING
```

### 2. Mission Configuration
```
EDIT FLIGHTS → ASSIGN PILOTS → STORES (weapons) → ALTITUDE → TARGET
```

### 3. Briefing Display
```
Show waypoints, target, threats, weather, time
Allied waypoints, enemy forces, SAM/AAA positions
```

### 4. Pre-Flight
```
CONTINUE... → TAKEOFF → FLY MISSION
```

### 5. During Mission
```
AWACS communications
Threat warnings (BANDIT, SAM, FUEL warnings)
Target engagement permission requests
```

### 6. Post-Mission
```
DEBRIEFING → MISSION EVALUATION → RESULT
Score calculation, kills, losses, damage assessment
```

### 7. Options
```
RERUN (retry failed mission)
ACMI (replay mission)
```

---

## File References

**String Data Files**:
- `R29` segment(s) - Primary string storage (708 strings)

**Mission Files** (inferred):
- `mission.dmp` - Mission dump/save file
- `STORES.BIN` - Weapons stores data
- `fmenu.def` - Menu definition file

**Score Files**:
- `SCORE??.TMP` - Score template
- `SCORENN.TMP` - Score with number
- `SCORE-1.TMP` - Previous score
- `SCORE00.TMP` - Initial score

---

## Key Discoveries

### 1. Four-Tier Target Priority System
Targets classified as Class A (strategic), B (infrastructure), C (military), D (tactical).

### 2. Comprehensive Mission Types
16+ distinct mission types from basic CAP to specialized HAVCAP and ESCORTE3.

### 3. AWACS Integration
Extensive AWACS voice communications for waypoints, threats, and permissions.

### 4. Dynamic Permissions
Pilots must request permission to engage, suggesting rules of engagement system.

### 5. Red Flag Training Mode
`Q3.`RED FLAG CONTROL` suggests Red Flag training exercises (realistic combat training).

### 6. ACMI Replay System
Full mission replay capability (`K4.`ACMI`).

### 7. Multiplayer Support
References to player aircraft, node editing, connection status.

---

## Next Steps

### Immediate (2-3 hours):
1. **Find MissionRecord structure** - Search for mission type enum usage
2. **Locate mission file loader** - Find .MSN or mission.dmp loading code
3. **Analyze waypoint system** - Understand waypoint data structure

### Medium Term (4-6 hours):
4. **Map target types** - Create target type enum
5. **Decode AWACS system** - Understand voice message generation
6. **Trace permission system** - Rules of engagement implementation

### Long Term (8+ hours):
7. **Complete R53 state machine** - Full briefing menu flow
8. **Mission script system** - Opcode interpreter analysis
9. **ACMI replay system** - Recording and playback mechanism

---

## Files Generated

### Analysis Files:
- `briefing_strings_complete.json` - Structured JSON data (272 strings)
- `briefing_strings_complete.txt` - Human-readable list
- `r53_analysis_result.json` - R53 segment analysis
- `r5x_segments_result.json` - All R5X segments

### Documentation:
- `MISSION_BRIEFING_STRINGS_COMPLETE.md` - This file
- `R53_MISSION_BRIEFING_ANALYSIS.md` - R53 technical analysis

---

## Statistics Summary

| Category | Count | Top String (refs) |
|----------|-------|-------------------|
| Navigation | 53 | `j4.`TARGET` (12) |
| Pilot/Aircraft | 49 | `e1.`ENEMY AIRCRAFT` (10) |
| Mission Types | 40 | `G3.`RECON` (4) |
| Mission Info | 38 | `G2.`LOAD MISSION` (4) |
| Threats | 28 | `x1.`ENEMY FORCES` (8) |
| Flight Params | 21 | `n/.`ALTITUDE` (17) |
| UI Control | 17 | `*0.`CONTINUE...` (3) |
| Results | 14 | `.`RESULT` (1) |
| Weather | 8 | - |
| Display | 4 | - |
| **TOTAL** | **272** | - |

---

**Complete mission briefing string extraction finished!**  
**Ready for structure discovery and code analysis.**
