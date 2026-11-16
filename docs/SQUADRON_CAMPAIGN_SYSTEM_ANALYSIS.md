# Squadron & Campaign System Analysis
## Inferred from R45 Menu Strings and Code

Based on analysis of the R45 Squadron Management Menu, we can reverse-engineer the structure of Falcon 3.0's squadron and campaign systems.

---

## Squadron System

### Squadron Data Structure

**File References**:
- `sqdnames.str` - Squadron name strings
- Squadron data stored in campaign save files

**Squadron Properties** (from string evidence):

```
Squadron Record:
- Squadron Name (string)
- Squadron Commander (string - pilot name)
- Squadron Insignia (selectable graphic)
- Wing Assignment (1ST WING through 7TH WING)
- Number of Missions Flown (counter)
- Number of Pilots Active (counter)
- Number of Pilots Killed (counter)  
- Number of Pilots MIA (counter)
- Mission History/Records
```

**Squadron Operations**:
- SELECT SQUADRON - Choose squadron from list
- DELETE SQUADRON - Remove squadron
- SELECT INSIGNIA - Choose squadron emblem/patch
- SQUADRON RECORDS - View squadron statistics

### Wing Structure

Falcon 3.0 uses a **7-wing organization**:
```
1ST WING
2ND WING
3RD WING
4TH WING
5TH WING
6TH WING
7TH WING
```

This suggests a hierarchical structure: Theater → Wing → Squadron → Flight → Pilot

**Hypothesis**: Each wing may represent a different airbase or operational area within the theater.

---

## Pilot System

### Pilot Data Structure

**File References**:
- `NAMES.BIN` - Database of pilot names
- `CALLSIGN.BIN` - Database of callsigns

**Pilot Record Fields**:

```c
struct Pilot {
    char name[?];           // "NAME:"
    char callsign[?];       // "CALLSIGN:"
    
    // Status
    enum Status {
        ACTIVE,
        FATIGUED,
        INJURED,
        COURT_MARTIALED
    } current_status;       // "CURRENT STATUS:"
    
    // Rank
    enum Rank {
        LT,                 // Lieutenant
        CAPT,               // Captain
        MAJOR,
        LT_COL,             // Lieutenant Colonel
        COL                 // Colonel
    } rank;
    
    // Statistics
    uint16_t missions_flown;    // "MISSIONS:"
    uint16_t awards;            // "AWARDS:"
    uint16_t flight_hours;      // "FLIGHT HOURS:"
    uint16_t plane_kills;       // "PLANE KILLS:"
    uint16_t merits;            // "MERITS:"
    
    // Abilities (skill ratings)
    struct Abilities {
        uint8_t dogfighting;    // "PILOT ABILITIES: -DOGFIGHTING:"
        // Other skills likely exist (bombing, navigation, etc.)
    } abilities;
};
```

### Pilot Management Operations

- **ADD FLIGHT** - Create new flight (4-ship formation)
- **ASSIGN PILOTS** - Assign pilots to flights
- **DELETE FLIGHT** - Remove flight
- **PILOT TRANSFER** - Move pilots between squadrons
- **F-16 PILOTS** - List of available F-16 qualified pilots
- **PILOT INFORMATION** - View detailed pilot stats

### Pilot Status System

**ACTIVE** - Ready to fly
**FATIGUED** - Needs rest (possible mission limit per day?)
**INJURED** - Cannot fly (from combat damage/ejection?)
**COURT MARTIALED** - Removed from duty (discipline system?)

**Inference**: The game tracks pilot fatigue and injury, requiring squadron commanders to rotate pilots and manage roster availability. Court martial suggests consequences for poor performance or rule violations (friendly fire?).

---

## Mission System

### Mission Types

Found **20+ mission type strings**:

**Air-to-Air**:
- FIGHTER SCRAMBLE
- STRIKE SCRAMBLE
- BOMBER SCRAMBLE
- UMF SCRAMBLE
- AIR SUPERIORITY
- SCREEN (defensive screen)
- AREACAP (area combat air patrol)
- FRIENDLYINTERCEPT

**Escort**:
- ESCORTTRANSPORT
- ESCORTSTRIKEAIRCRAFT
- ESCORTBOMBERS
- ESCORTE3 (AWACS escort)

**Ground Attack**:
- CLOSEAIRSUPPORT (CAS)
- GROUNDSTRIKE
- BOMBMIS (bombing mission)

**Anti-Ship**:
- ANTISHIP
- SEADSHIP (SEAD + anti-ship)
- RECONSHIP (reconnaissance)

**SEAD** (Suppression of Enemy Air Defenses):
- SEADGROUND
- SEADSHIP

**Special Operations**:
- HELOSUPPLYCAP (helicopter supply CAP)
- Multiple "PG" (Playable Ground?) missions with specific objectives

### Mission Management

**Operations**:
- CHOOSE MISSION - Select from available missions
- CLEAR MISSION - Cancel selected mission
- DELETE MISSION - Remove mission
- LOAD MISSION - Load saved mission
- SAVE MISSION - Save mission configuration
- NEXT MISSION - Advance to next mission in campaign
- EDIT FLIGHTS - Configure flights for mission

**Mission Properties**:
- Mission Number ("----MISSION #")
- Mission Type (from list above)
- Target List ("DEFEND", "DESTROY ENEMY", "BOMB ANY OF [1] through [8]")
- Time of Day (0600 HRS, 1200 HRS, 1800 HRS, 2300 HRS)
- Weather conditions
- Assigned flights and pilots

### Mission Objectives

**Objective patterns found**:
```
"DEFEND [location] FROM [threat]"
"DESTROY ENEMY GROUND FORCES"
"DESTROY ENEMY MIGS"
"BOMB ANY OF [1] [2] [3] ... [8] AT [location]"
```

Supports **up to 8 simultaneous targets** per bombing mission.

**Playable Ground Missions** (unusual for a flight sim):
- PG1 BEACH DEFEND
- PG2 ATTACK
- PG3 NORTH PARADROP
- PG4 ATTACK / ANTISHIP / SEADSHIP
- PG5 WEST PARADROP
- PG6 WEST BEACHATTACK / ANTISHIP
- PG7 TRAIN ATTACK
- PG8 TRAIN DEFEND
- SAVE THE LUV BOAT

**Note**: These "PG" missions suggest either scripted campaign events or possibly a ground unit interface (unlikely but strings suggest it).

---

## Campaign System

### Theater Selection

**Available Theaters**:
```
Kuwait      (Gulf War 1991?)
Israel      (Middle East conflict)
Panama      (Operation Just Cause?)
Japan       (Defense scenario?)
Korea       (Korean Peninsula)
India       (South Asia)
```

**Multiplayer constraint**: "You must choose a squadron and theater before entering communications."

This suggests theater selection is permanent for a campaign session.

### Campaign Status Tracking

**Date/Time System**:
- Day counter ("CURRENT DATE: DAY [n]")
- Time of day ("CURRENT TIME: [time]")
- Mission scheduling at specific hours (0600, 1200, 1800, 2300)

**Territory Control**:
```
"CAMPAIGN ZONE UPDATE:"
" PERCENT OCCUPIED BY ENEMY"
" PERCENT OCCUPIED BY ALLIES"
```

**Inference**: Dynamic front line that shifts based on mission success/failure. Percentage-based territory tracking.

### Mission Statistics

**Mission-Level Stats**:
- CURRENT MISSION: [mission name]
- MISSIONS FLOWN: [count]
- MISSIONS ACCOMPLISHED: [count]
- SORTIES FLOWN: [count]

**Air Combat Stats**:
```
ALLIED AIRCRAFT SHOT DOWN: [count]
ENEMY AIRCRAFT SHOT DOWN: [count]
  -CLASS A FIGHTER: [count]
  -CLASS B FIGHTER: [count]
  -BOMBER/STRIKE: [count]
  -ATTACK/CLOSE AIR: [count]
  -HELICOPTER: [count]
  -TRANSPORT/AWACS: [count]
```

**Aircraft Classification**:
- **Class A Fighter**: High-end fighters (MiG-29, Su-27?)
- **Class B Fighter**: Lower-tier fighters (MiG-21, F-5?)
- **Bomber/Strike**: Strategic bombers and strike aircraft
- **Attack/Close Air**: A-10, Su-25 type
- **Helicopter**: All rotorcraft
- **Transport/AWACS**: Support aircraft

**Ground Target Stats**:
```
GROUND TARGETS DESTROYED: [count]
  -CLASS A TARGET: [count]
  -CLASS B TARGET: [count]
  -CLASS C TARGET: [count]
  -CLASS D TARGET: [count]
```

**Target Classification** (from separate strings):

**Class A** (Strategic):
- NUCLEAR PLANT
- CHEMICAL WEAPONS PLANT
- BIOLOGICAL WEAPONS PLANT
- COMMAND CENTER
- NUKE POWER STATION

**Class B** (Major Infrastructure):
- AIRBASE / AIRPORT / AIRFIELD
- NAVAL BASE
- RADAR SITE
- BRIDGE
- MISSILE SITE
- POWER STATION

**Class C** (Military):
- ARMY BASE
- SAM SITE
- RAIL YARD
- BUNKER
- AMMODUMP
- MISSILE LAUNCHER

**Class D** (Tactical):
- BUILDING
- HANGAR
- RUNWAY
- REFINERY
- STORAGE TANK
- TOWER
- FACTORY
- WAREHOUSE
- OIL WELL
- LOCK
- TRESTLE

### Campaign Rating System

```
ORDNANCE EFFICIENCY RATING: [value]
OVERALL CAMPAIGN RATING: [value]
```

**Ordnance Efficiency**: Measures bombs/missiles used vs targets destroyed (effectiveness metric)
**Overall Campaign Rating**: Combined score of mission success, losses, efficiency

---

## Supply System

### Supply Status Menu

**String**: "SUPPLY STATUS"

**Inference**: Tracks available aircraft, weapons, and supplies.

### Ground Forces

**Unit Types Tracked**:
```
TANKS
MECH. INFANTRY (Mechanized Infantry)
TRANSPORTS
INFANTRY
ARTILLERY
RADAR
```

Suggests the campaign simulates ground warfare alongside air operations, with missions affecting ground unit availability and advancement.

### Weapons Loadout System

**Available Weapons** (from strings):

**Air-to-Air**:
- AIM9P - Sidewinder (Rear aspect IR)
- AIM9M - Advanced Sidewinder (All aspect IR)
- AIM9R - Sidewinder variant
- AIM120 - AMRAAM (Radar missile)
- AIM120E - Extended range AMRAAM

**Air-to-Ground**:
- MK82 - 500lb bomb
- MK82HD - High-drag variant
- MK83 - 1000lb bomb
- MK84 - 2000lb bomb
- DURANDAL - Anti-runway bomb
- PAVEWAY - Laser-guided bomb

**Air-to-Ground Missiles**:
- AGM65B - Maverick (TV-guided)
- AGM65D - Maverick (IR-guided)
- AGM88A - HARM (anti-radiation)
- AGM45A - Shrike (anti-radiation)
- HARPOON - Anti-ship missile

**Pods/Tanks**:
- ALQ131 - ECM pod
- FUEL300 - 300 gallon fuel tank
- FUEL370 - 370 gallon fuel tank
- LANTIRN - Targeting pod

**Weapon Categories** (pilot skills):
- GUNS
- REAR ASPECT IR
- ALL ASPECT IR
- RADAR MISSILES
- CAS ORDNANCE (Close Air Support)
- HEAVY ORDNANCE

---

## Naval System

### Ship Types

**Soviet/Russian**:
- KUZNETSOV (KUZNETSV) - Aircraft carrier
- KIROV - Battle cruiser
- ROGOV - Landing ship
- UDALOY - Destroyer
- BEREZINA - Replenishment ship

**US**:
- SUMNER - Destroyer

**Targets**:
- TANKER - Commercial tanker
- PATRIOT - Patriot missile battery (ground-based)

**Naval Operations**:
- NAVAL TASK FORCE (target type)
- ANTISHIP missions
- SEADSHIP missions
- RECONSHIP missions

---

## Weather System

**Weather Conditions**:
```
CLEAR
PARTLY CLOUDY
CLOUDY
MOSTLY CLOUDY
OVERCAST
```

**Ceiling Heights**:
```
CEILING: VERY LOW
CEILING: LOW
CEILING: MEDIUM
CEILING: HIGH
```

**Inference**: Weather affects mission planning and difficulty. Low ceilings may restrict air operations or require instrument flying.

---

## Multiplayer/Communications System

### Multiplayer Features

**Network Operations**:
- "Sending theater name to other players."
- "Waiting to transfer pilot info to squadron leader."
- "Sending pilot info to squadron leader."
- "Receiving pilot info from [player]"
- "Sending squadron info to other pilots"
- "Receiving squadron info"
- "Waiting to receive squadron info"
- "Waiting to receive campaign data"
- "Sending campaign data"
- "Receiving campaign data"

**Squadron Hierarchy**:
- Squadron Leader role exists
- Leader manages squadron configuration
- Other players transfer pilot info to leader
- Synchronized campaign state across players

**Theater Constraint**:
- "You must choose a squadron and theater before entering communications."
- "You must choose a squadron to go into Red Flag."

**Red Flag Reference**:
- Red Flag is the US Air Force training exercise
- Suggests a training/practice mode separate from campaigns

### Multiplayer Architecture

**Inference**: 
1. One player acts as Squadron Leader
2. Other players join as squadron members
3. Leader selects theater and squadron
4. Campaign state is synchronized (missions, territory, etc.)
5. Each player likely controls their own flight in cooperative missions

---

## Flight Structure

### Flight Organization

**Operations**:
- ADD FLIGHT
- DELETE FLIGHT
- EDIT FLIGHTS
- ASSIGN PILOTS

**Flight Parameters** (from R57 Weapons Loadout analysis):
- Flight size: Up to 4 aircraft (standard USAF flight)
- Loadout per aircraft
- Pilot assignments

**Formations** (from strings):
```
V STACK     (Vertical stack)
H STACK     (Horizontal stack)
C STACK     (Combat stack?)
LADDER      (Ladder formation)
WEDGE       (Wedge formation)
ECHELON     (Echelon formation)
```

**Flight Roles**:
```
LEADER      (Flight leader - player or AI)
1ST WING through 7TH WING
```

### Tactical Settings

**AI Aggressiveness**:
```
DUMB
PASSIVE
AGGRESSIVE
```

**Tactical Modes**:
```
TACT 1, TACT 2, TACT 3     (Tactical modes)
STRAT 1, STRAT 2, STRAT 3  (Strategic modes)
```

**Route Planning**:
```
ROUTE: ONE  (Single route)
ROUTE: ALL  (All waypoints)
```

**Engagement Settings**:
```
AIR: OFF / AIR: ON      (Air-to-air engagement)
GRND: OFF / GRND: ON    (Air-to-ground engagement)
```

**Loiter Modes**:
```
LOITER      (Hold position)
TAKEOFF     (Departure)
INTRCEPT    (Intercept enemy)
ESCORT      (Escort mode)
```

---

## Data File Structure

### Discovered Data Files

**Pilot Database**:
- `NAMES.BIN` - Pilot name pool
- `CALLSIGN.BIN` - Callsign pool

**Squadron Data**:
- `sqdnames.str` - Squadron name strings

**Mission Data**:
- `MISSION.` - Mission definition files

**Campaign Data**:
- `CDATA.CCT` - Campaign data container?
- `RESULT` - Mission result storage?

**Graphics/UI**:
- `PICFONT.IDX/.DAT` - UI font sprites

### Campaign Save Structure (Inferred)

```
Campaign Save File:
  - Theater selection
  - Current day/time
  - Territory control percentages
  - Squadron data:
    - Squadron name
    - Wing assignment
    - Squadron commander
    - Insignia selection
    - Mission history
    - Statistics (missions flown, pilots lost, etc.)
  - Pilot roster:
    - For each pilot:
      - Name, callsign, rank
      - Status (active/fatigued/injured/court-martialed)
      - Statistics (missions, kills, hours)
      - Skill ratings
  - Available missions
  - Supply status
  - Campaign statistics (aircraft shot down, targets destroyed)
  - Current mission configuration
  - Weather state
```

---

## UI/Menu Flow (Inferred)

### Main Menu Flow

```
Campaign Selection
    ↓
Squadron Management (R45) ←→ Communications
    ↓
    ├─→ SELECT SQUADRON
    ├─→ PILOT INFORMATION
    │     ├─→ View pilot stats
    │     └─→ PILOT TRANSFER
    ├─→ ASSIGN PILOTS
    │     └─→ ADD/DELETE FLIGHT
    ├─→ EDIT FLIGHTS (R57 Weapons Loadout)
    │     └─→ Configure loadouts
    ├─→ CHOOSE MISSION
    │     ├─→ LOAD/SAVE MISSION
    │     ├─→ CLEAR/DELETE MISSION
    │     └─→ Mission briefing (R52/R56?)
    ├─→ CAMPAIGN STATUS
    │     └─→ View statistics
    ├─→ SUPPLY STATUS
    │     └─→ View available equipment
    ├─→ COMMS.
    │     └─→ Multiplayer lobby
    └─→ DONE
         └─→ Launch mission or return to main menu
```

---

## Campaign Progression System

### How Campaigns Progress (Inferred)

1. **Theater Selection** - Choose operational theater (Kuwait, Korea, etc.)
2. **Squadron Assignment** - Select or create squadron, assign to wing
3. **Mission Selection** - Choose from available missions (dynamic based on campaign state)
4. **Mission Planning**:
   - Configure flights (add/delete)
   - Assign pilots to flights
   - Edit loadouts per aircraft (R57 menu)
   - Review briefing (R52/R56 menu)
5. **Mission Execution** - Fly the mission (main game)
6. **Mission Result** - Statistics recorded, campaign state updated
7. **Campaign Update**:
   - Territory percentages change
   - New missions become available
   - Pilot status updated (fatigue, injury, promotion?)
   - Squadron statistics updated
   - Time advances
8. **Repeat** - Continue campaign or exit

### Dynamic Campaign Elements

**Evidence for Dynamic Campaign**:
- Territory percentage tracking suggests front line movement
- Mission availability likely depends on campaign state
- Pilot fatigue system requires rotation and time management
- Supply tracking suggests resource limits
- Multiple mission types imply varied objectives based on strategic needs

**Hypothesis**: Falcon 3.0 implements an early **dynamic campaign** where:
- Player mission outcomes affect territorial control
- Enemy responds to player actions
- Mission types vary based on strategic situation
- Resource management (pilots, supplies) matters
- Campaign can be won or lost based on territorial control

---

## Unique/Notable Features

### Court Martial System
- Pilots can be "COURT MARTIALED"
- Possible causes: Friendly fire? Mission failure? Ejecting unnecessarily?
- Consequence: Pilot removed from roster

### Fatigue Management
- Pilots become FATIGUED from too many missions
- Requires squadron commander to rotate pilots
- Adds resource management layer to campaign

### Wing Organization
- 7-wing structure unusual for flight sims of the era
- Suggests large-scale campaign with multiple bases/operational areas
- May allow player to command entire wing operations?

### Multiplayer Campaign
- Cooperative campaign mode
- Squadron leader manages mission for all players
- Synchronized campaign state
- Rare feature for 1991 flight sim

### Mission Result Tracking
- Detailed statistics per mission
- Aircraft classification system
- Target classification system
- Efficiency ratings
- Suggests replay value through score optimization

---

## Questions/Unknowns

1. **Ground Unit System**: How do TANKS, INFANTRY, etc. factor into gameplay? Are they simulated or just statistics?

2. **"PG" Missions**: What are these "Playable Ground" missions? Ground unit control? Scripted events?

3. **Court Martial Triggers**: What actions cause a pilot to be court martialed?

4. **Wing Significance**: Do different wings have different capabilities, aircraft, or bases?

5. **Territory Calculation**: How are territory percentages calculated? Per mission? Per day?

6. **Supply Limits**: Are there hard limits on aircraft/weapons, or infinite respawns?

7. **AI Squadron**: Are other squadrons simulated in the campaign, or just the player's?

8. **Campaign Victory**: What are the win/loss conditions? Capture all territory? Time limit?

9. **Red Flag Mode**: Is this a separate training mode? Multiplayer arena?

10. **Rank Progression**: Do pilots gain ranks based on performance? Does it affect abilities?

---

## Comparison to Contemporary Flight Sims

### Falcon 3.0 (1991) vs Others

**F-15 Strike Eagle II (1989)**:
- Simple mission selection
- No persistent campaign
- No pilot management
- **Falcon 3.0 more advanced**

**F-19 Stealth Fighter (1988)**:
- Campaign with promotion system
- Mission variety
- No squadron management
- **Falcon 3.0 similar scope, more detailed**

**Aces of the Pacific (1992)**:
- Career mode with pilot progression
- Squadron assignment
- Limited management
- **Falcon 3.0 more complex squadron system**

**Conclusion**: Falcon 3.0's squadron and campaign system was **highly advanced for 1991**, with:
- Persistent pilot roster with skill progression
- Squadron-level management
- Dynamic campaign with territorial control
- Multiplayer cooperative campaign
- Resource management (fatigue, supplies)

This level of campaign complexity wouldn't become standard until late 1990s sims like **Falcon 4.0 (1998)** and **Jane's USAF (1999)**.

---

## Files Referenced

- Source: `docs/R45_MENU_ANALYSIS.md`
- String database: `analysis/ida_scripts/r45_all_strings.txt`
- Relevant strings: `analysis/ida_scripts/r45_relevant_strings.txt`
- Related: `docs/R57_WEAPONS_LOADOUT_MENU_ANALYSIS.md`
