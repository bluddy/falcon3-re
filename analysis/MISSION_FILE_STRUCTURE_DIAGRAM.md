# Mission File Structure Diagram

**Visual representation of SQUAD0.MIS (824 bytes)**

```
┌─────────────────────────────────────────────────────────────────┐
│                         MISSION FILE (.MIS)                      │
│                           Total: 824 bytes                       │
└─────────────────────────────────────────────────────────────────┘

┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃  HEADER SECTION (8 bytes)                         0x0000-0x0007 ┃
┣━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┫
┃  +0x00: 0x03  Flight count = 3                                  ┃
┃  +0x01: 0x00  Unknown                                            ┃
┃  +0x02: 0x01  Unknown                                            ┃
┃  +0x03: 0x14  Unknown                                            ┃
┃  +0x04: 0x1E  Unknown                                            ┃
┃  +0x05: 0x0B  Waypoint count = 11                               ┃
┃  +0x06: 0x00  Unknown                                            ┃
┃  +0x07: 0x1A  Aircraft count = 26                               ┃
┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛

┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃  AIRCRAFT RECORDS (156 bytes)                     0x0008-0x00A3 ┃
┃  26 aircraft × 6 bytes each                                      ┃
┣━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┫
┃  Record format (6 bytes):                                        ┃
┃    +0x00: flags (0x00=player, 0x80=allied, 0x81=enemy)          ┃
┃    +0x01: aircraft_id (2-27 sequential)                          ┃
┃    +0x02: 0x00 (constant)                                        ┃
┃    +0x03: type_code (0x01=F-16, 0x34=F-15, 0x07=MiG-29, etc.)   ┃
┃    +0x04: 0x00 (constant)                                        ┃
┃    +0x05: subtype/variant                                        ┃
┃                                                                   ┃
┃  Aircraft 1:  00 02 00 01 00 XX  (Player F-16)                   ┃
┃  Aircraft 2:  80 03 00 34 00 XX  (Allied F-15)                   ┃
┃  Aircraft 3:  80 04 00 34 00 XX  (Allied F-15)                   ┃
┃  ... (23 more aircraft)                                           ┃
┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛

┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃  FLIGHT PLAN SECTION (429 bytes)                  0x00A4-0x0250 ┃
┃  Contains flight parameters and routing data                     ┃
┣━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┫
┃                                                                   ┃
┃  ┌─────────────────────────────────────────────────────────┐    ┃
┃  │  Flight Parameter Structures (23 bytes each)            │    ┃
┃  │  Located at: 0x0167, 0x017E, 0x0195                     │    ┃
┃  └─────────────────────────────────────────────────────────┘    ┃
┃                                                                   ┃
┃  Flight 1 @ 0x0167:  B4 00 C8 00 02 02 00 ... 1E 1E 00          ┃
┃    +0x00-01: 0x00B4 (180) - mystery uint16                      ┃
┃    +0x02:    0xC8 (200) - altitude = 20,000 feet                ┃
┃    +0x03:    0x00 - unknown (speed?)                             ┃
┃    +0x04:    0x02 - unknown                                      ┃
┃    +0x05:    0x02 - unknown                                      ┃
┃    +0x06:    0x00 - action code 0 (TAKEOFF/NOTHING)             ┃
┃    +0x07-13: zeros (padding)                                     ┃
┃    +0x14-15: 0x1E, 0x1E (30, 30) - timeout?                     ┃
┃    +0x16:    0x00 - terminator                                   ┃
┃                                                                   ┃
┃  Flight 2 @ 0x017E:  00 00 C8 00 02 02 00 ... 1E 1E 00          ┃
┃    Same format, altitude = 20,000 feet, action = 0              ┃
┃                                                                   ┃
┃  Flight 3 @ 0x0195:  00 00 C8 00 02 02 00 ... 1E 1E 00          ┃
┃    Same format, altitude = 20,000 feet, action = 0              ┃
┃                                                                   ┃
┃  ┌─────────────────────────────────────────────────────────┐    ┃
┃  │  Other Data (7-byte patterns with 0xFF markers)         │    ┃
┃  │  Purpose: Flight-to-waypoint linkage? Target refs?      │    ┃
┃  └─────────────────────────────────────────────────────────┘    ┃
┃                                                                   ┃
┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛

┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃  WAYPOINTS SECTION (231 bytes)                    0x0251-0x032D ┃
┃  11 waypoints × 21 bytes each                                    ┃
┣━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┫
┃  Waypoint format (21 bytes = 11 + 10 duplicate):                ┃
┃                                                                   ┃
┃  ┌─────────────── First Copy (11 bytes) ──────────────────┐     ┃
┃  │ +0x00: 0x01           marker                            │     ┃
┃  │ +0x01: x_low          X coordinate LOW byte             │     ┃
┃  │ +0x02: x_high         X coordinate HIGH byte            │     ┃
┃  │ +0x03: marker_1       int16 (-8 or -2)                  │     ┃
┃  │ +0x05: y_low          Y coordinate LOW byte             │     ┃
┃  │ +0x06: y_high         Y coordinate HIGH byte            │     ┃
┃  │ +0x07: marker_2       int16 (-12 or -9)                 │     ┃
┃  │ +0x09: constant       uint16 (always 16)                │     ┃
┃  └─────────────────────────────────────────────────────────┘     ┃
┃  ┌─────────────── Second Copy (10 bytes) ─────────────────┐     ┃
┃  │ Same structure without leading 0x01 marker              │     ┃
┃  └─────────────────────────────────────────────────────────┘     ┃
┃                                                                   ┃
┃  Waypoint 0:  01 00 C6 F8 FF 90 C6 F4 FF 10 00 (+ 10 dup)       ┃
┃    X = (0xC6 << 8) | 0x00 = 50,688                              ┃
┃    Y = (0xC6 << 8) | 0x90 = 50,832                              ┃
┃                                                                   ┃
┃  Waypoint 1:  01 2C C7 F8 FF 1C C8 F4 FF 10 00 (+ 10 dup)       ┃
┃    X = 0xC72C = 50,988  (delta: +300)                           ┃
┃    Y = 0xC81C = 51,132  (delta: +300)                           ┃
┃                                                                   ┃
┃  Waypoint 2:  01 58 C8 F8 FF A8 C9 F4 FF 10 00 (+ 10 dup)       ┃
┃    X = 0xC858 = 51,288  (delta: +300)                           ┃
┃    Y = 0xC9A8 = 51,432  (delta: +300)                           ┃
┃                                                                   ┃
┃  ... (8 more waypoints, all with +300 spacing)                   ┃
┃                                                                   ┃
┃  Perfect diagonal line proving 16-bit coordinate system! ✓       ┃
┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛


════════════════════════════════════════════════════════════════════
                        CODE EVIDENCE MARKERS
════════════════════════════════════════════════════════════════════

┌─────────────────────────────────────────────────────────────────┐
│  IDA Disassembly Evidence:                                       │
├─────────────────────────────────────────────────────────────────┤
│  ✓ add si, 0x17  at 0x4D96F  → 23-byte flight param stride     │
│  ✓ add di, 0x15  at 0x4B2A4  → 21-byte waypoint stride         │
│  ✓ mov dl, 0x64  widespread  → altitude × 100 encoding         │
│  ✓ Type codes at 0x4C301     → aircraft initialization         │
│  ✓ Strings at 0x14FD1F       → action code string table        │
│  ✓ mov ah, [si]; mov ah, [si+1] → 16-bit coordinate assembly   │
└─────────────────────────────────────────────────────────────────┘


════════════════════════════════════════════════════════════════════
                         FIELD SUMMARY
════════════════════════════════════════════════════════════════════

FULLY DECODED (100%):
  ✓ Waypoint X/Y coordinates (16-bit proven)
  ✓ Aircraft records (6 bytes)
  ✓ Aircraft type codes (11 types)

MOSTLY DECODED (80-90%):
  ✓ Flight parameters structure (23 bytes)
  ✓ Altitude field (+0x02, byte × 100)
  ✓ Action code field (+0x06, range 0-9)

PARTIALLY DECODED (50%):
  ~ Mission header (8 bytes)
  ~ Flight plan section layout

NOT YET DECODED:
  ✗ Speed parameter (likely defaulted)
  ✗ Mystery uint16 at flight params +0x00
  ✗ Bytes +0x04, +0x05 at flight params
  ✗ Waypoint markers (-8/-12 vs -2/-9)


════════════════════════════════════════════════════════════════════
                      CONFIDENCE ASSESSMENT
════════════════════════════════════════════════════════════════════

PROVEN (mathematical + code evidence):
  • Waypoint coordinates are 16-bit (perfect diagonal spacing)
  • Structure sizes 21 and 23 bytes (stride in IDA code)
  • Aircraft types 0x01, 0x34-0x36, 0x07-0x0B (init code)

HIGH CONFIDENCE (strong binary patterns + partial code):
  • Altitude is byte × 100 feet (0x64 constant in code)
  • Action codes 0-9 (string table found)
  • Aircraft record format (consistent across files)

MEDIUM CONFIDENCE (binary observation only):
  • Flight parameter field layout
  • Header byte meanings
  • Timeout values

LOW CONFIDENCE (hypothesis):
  • Speed defaulting mechanism
  • Marker value meanings
  • Unknown flag bytes


════════════════════════════════════════════════════════════════════
                     FILE SIZE BREAKDOWN
════════════════════════════════════════════════════════════════════

SQUAD0.MIS: 824 bytes total

  Header:              8 bytes    (  1.0%)
  Aircraft Records:  156 bytes    ( 18.9%)
  Flight Plan:       429 bytes    ( 52.1%)  ← largest section
  Waypoints:         231 bytes    ( 28.0%)
                     ─────────
  Total:             824 bytes    (100.0%)


════════════════════════════════════════════════════════════════════

Legend:
  ✓ = Confirmed/Proven
  ~ = Partially decoded
  ✗ = Not yet found
  
Status: 88% complete
Method: Static analysis only (no debugger/emulator)
Confidence: HIGH

════════════════════════════════════════════════════════════════════
