# Prior Art: Existing Falcon3 IDA Databases & Dumps

## C:\Users\yotam\Downloads\ida\falcon\

### IDA Databases
| File | Size | Date | Notes |
|------|------|------|-------|
| `FALCONCD.EXE.i64` | 2.1 MB | 2026-02-11 | IDA Free 8.x, DOSBox memory dump |
| `FALCONCD2.i64` | 7.1 MB | ? | Larger, possibly with more analysis |
| `FALCONCD.EXE.idb` | ? | 2022 | IDA 7.x format |
| `Falcon_mem.EXE.i64` | ? | ? | Memory dump of running game |

### Memory Dumps (DOSBox)
| File | Size | Description |
|------|------|-------------|
| `cockpit_*.BIN` | 65,536 each | Video/cockpit memory regions |
| `26_2_13/MEMDUMP_map_screen.BIN` | 1,048,576 | Map screen state |
| `26_2_13/MEMDUMP_menu.BIN` | 1,048,576 | Menu state |
| `26_2_13/MEMDUMP_mission.BIN` | 1,048,576 | Mission state |
| `26_2_13/MEMDUMP_sim.BIN` | 1,048,576 | Simulation state |
| `26_2_13/*.i64` | various | IDA databases on above dumps |
| `26_3_1/cs_*.bin` | 65,535 each | Code segment dumps? |
| `26_3_1/falcon_menu.BIN` | 1,048,576 | Menu memory |
| `26_3_1/falcon_mission.BIN` | 1,048,576 | Mission memory |
| `26_3_1/falcon_sim.BIN` | 1,048,576 | Sim memory |

**Limitations**: These were created with IDA Free from DOSBox memory dumps (not the raw EXE). They capture data structures at specific runtime moments but lack:
- Full code coverage (only snapshot of loaded overlays)
- Cross-references between overlays
- Relocation/original file structure
- Static analysis of all code paths

## Key Findings from Prior Work

### Data Structures Identified (from memory dumps)
- `SimState` / `MissionState` / `MenuState` structs
- Entity/vehicle tables
- Terrain/map data structures
- Cockpit instrument layouts
- Joystick calibration data

### Overlay Knowledge
- RTLink overlay manager confirmed
- Segment usage map (which segment holds which subsystem)
- Some overlay entry points identified

### Gaps / Why Stuck
1. **Overlay file format**: RTLink record structure not fully decoded (headers, fixups, grouping)
2. **Asset containers**: `DISPLAY.DAT` and `ARMSDATA\*.DAT` packed with PKWARE DCL — extraction incomplete
3. **EMS/XMS handling**: Dynamic memory views not captured in static dumps
4. **CS/DS aliasing**: Same linear memory accessed via different segment:offset pairs
5. **Tooling**: IDA Free lacked FLIRT for 16-bit, no decompiler, limited scripting

## Our Current Snapshot (2026-10-10)

Fresh headless IDA Pro 9.1 on raw `FALCONCD.EXE`:
- **817 functions** identified (resident + 9 overlay groups)
- **82 KB** of code analyzed (out of ~1.3 MB total image+tail)
- **9 overlay segments** mapped at correct runtime paragraphs with 16-bit base paragraphs
- Overlapping segments supported via distinct base paragraphs (CS/DS aliasing modeled)
- RTLink 18-byte directory parsed, 70 records placed
- 4-byte tail directory parsed (51 entries)
- No FLIRT matches (16-bit sigs unavailable)
- No standard CRT detected

This snapshot provides a static, cross-referenceable foundation that the prior dynamic dumps could not.