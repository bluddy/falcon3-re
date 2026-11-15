# Falcon 3.0 — Architecture Specification

*Last updated 2026-11-11. Findings 1–179 + S4 bottom-up analysis (Levels 0–18+) + **Top 100 Analysis COMPLETE (100%)**.*
*Certainty: **PROVEN** (byte-level) · **STRONG** (multi-signal) · **HYPOTHESIS** (single-signal) · **UNKNOWN***

This directory replaces `docs/architecture.md` with focused sub-documents.
See `docs/structures.md` for binary file format structs, `registry/functions.yaml` for
function signatures, `registry/structs.yaml` for data structure definitions.

**NEW**: Top 100 most-called functions systematically analyzed. See `analysis/TOP_100_COMPLETE.md` for full report.

---

## Sub-Documents

| File | Contents | Certainty |
|---|---|---|
| [binary.md](binary.md) | Toolchain, memory model, overlay system, calling conventions | PROVEN–STRONG |
| [game_loop.md](game_loop.md) | Main frame loop, mode state machine, per-frame update chains | STRONG |
| [farobj.md](farobj.md) | FarObj struct, type system, global tables, operation API | STRONG–HYPOTHESIS |
| [entity.md](entity.md) | 4-layer entity architecture, lifecycle, class codes | STRONG–HYPOTHESIS |
| [flight_physics.md](flight_physics.md) | Control axes, aircraft kinematics, slot arrays, motion | STRONG–HYPOTHESIS |
| [rendering.md](rendering.md) | 3D projection pipeline, terrain renderer, VGRAPH, math | STRONG |
| [terrain.md](terrain.md) | **COMPLETE**: Heightmap, ISLDAT+MAPOBJ vectors, rivers/roads | PROVEN |
| [audio.md](audio.md) | OPL/FM sound, channel system, device types | PROVEN–STRONG |
| [hardware_io.md](hardware_io.md) | IRQ0 timer, INT 33h mouse, joystick, keyboard, BDA | PROVEN |
| [resource.md](resource.md) | op_dispatch (16 DOS services), streaming file API | PROVEN |
| [globals.md](globals.md) | Key globals, runtime segments, subsystem map, unknowns | STRONG |
| [ui_menu_system.md](ui_menu_system.md) | **COMPLETE**: Input handling (K/M/J), rendering pipeline, menu state | STRONG–PROVEN |
| [ai.md](ai.md) | **80% COMPLETE**: AI contexts, behavior flags, data-driven system | STRONG–PROVEN |
| [mission_campaign.md](mission_campaign.md) | **30% COMPLETE**: Squadron/campaign/mission files, save system | STRONG–HYPOTHESIS |

---

## Quick Reference — Key Facts

| Fact | Value | Certainty |
|---|---|---|
| Compiler | Borland C++ 2.0 (`bcc -ml -1`) | PROVEN |
| Linker | RTLink/Plus | PROVEN |
| Memory model | DOS real mode, far/large | PROVEN |
| Binary | 118 KB resident + 1.2 MB overlays | PROVEN |
| DGROUP (DS=SS) | Paragraph 0x7A32 (linear 0x7A320) | PROVEN |
| OPL port | **0x388** (AdLib mode 2) | PROVEN |
| World tile size | **13,108** world units (0x3334) | STRONG |
| World grid | 512 × 512 tiles | STRONG |
| FarObj struct size | ≥ 210 bytes | STRONG |
| Flight axes range | ±2048 (0x800) | STRONG |
| view_projection | 282K calls/session (most-called 3D fn) | PROVEN |

## Quick Reference — Key Addresses

| Address | Name | Description |
|---|---|---|
| 0x2257B | `op_dispatch` | 16-slot DOS services shim (BX=byte offset) |
| 0x2703F | `farptr_table_get` | Load FarObj from main slot table (78 callers) |
| 0x20BDB | `view_projection` | Core 3D projection (282K calls, 1076B) |
| 0x31319 | `main_frame_update_loop` | Top-level game loop |
| 0x108BAC | `r15_simulation_loop` | **MAIN SIMULATION LOOP** (717B, 83 callers, dual-path: cockpit/external view) |
| 0x2FEF2 | `game_frame_update_chain` | Entity simulation chain |
| 0x2FD42 | `game_frame_pipeline_step` | Rendering pipeline entry |
| 0x13CB0 | `farobj_batch_build_project` | Terrain tile batch renderer |
| 0x1740D | `sound_device_init` | Sound hardware initialization |
| 0x3CE92 | `behavior_dispatcher` | AI master dispatch hub (2,580B) |
| 0x495DF | `entity_batch_processor` | AI context batch processor (40 entities) |
| 0x33443 | `master_state_machine` | Main menu/game state coordinator (2,688B) |
| 0x12FC43 | `input_poll_handler` | Input processing (K/M/J, 3,814B, 56 callers) |
| 0x130A2F | `input_sync_and_wait` | Universal input sync (42B, **194 callers**) |
| 0x128518 | `ui_text_render_engine` | Core text rendering (1,282B, 70 callers) |
| 0x128D5A | `ui_render_coordinator` | Rendering dispatcher (900B, 22 callers) |
| 0x1744B0 | `game_mode_r48_main_coordinator` | R48 game mode coordinator (9,061B, **360 callers**) |
| 0x1820B0 | `game_mode_r53_main_coordinator` | R53 game mode coordinator (12,693B, **342 callers**, largest function) |
| 0x1793C0 | `overlay_r4F_handler` | R4F game mode handler (7,661B, **262 callers**) |
| 0x18F610 | `overlay_r55_dispatcher` | R55 game mode dispatcher (4,935B, **212 callers**) |
| 0x166F80 | `r38_loadout_menu_dispatcher` | R38 loadout menu state machine (2,943B, **147 callers**) |
| 0x103C99 | `mission_session_init_coordinator` | Mission/game session initialization (945B, **144 callers**) |
| 0x12DF6A | `r29_tactical_screen_coordinator` | R29 tactical planning screen (6,799B, **120 callers**, hybrid pattern) |
| 0x101A12 | `input_device_calibration_init` | Input device calibration (1,719B, **104 callers**, 26 callees, joystick+mouse) |
| 0x17B437 | `squadron_mission_file_loader` | Squadron/mission file loader (4,516B, **104 callers**, 13 callees, .SQUAD/.MTV/.SHP/.TSK) |
| 0x15A8B0 | `theater_campaign_file_loader` | Theater/campaign file loader (2,553B, **102 callers**, 70 callees, .THEATER/.WAR/.NWS/.BIN/.SHP) |
| 0x138E6A | `int_to_string_converter` | Integer to ASCII string converter (106B, exclusive to squadron loader) |
| 0x138F9C | `string_concatenate` | Path string concatenator (84B, handles 0x00/0xFF terminators, exclusive to squadron loader) |
| 0x13B243 | `menu_dispatcher_19ops` | Master menu/overlay dispatcher (2,623B, 19-op jump table, **50 callers**) |
| R05_400C:0x34 | `farobj_main_table` | Main entity slot table |
| 0x65A7:0x000C | `ai_context_array` | 40 AI contexts × 24 bytes = 960 bytes |
| 0x7B0E:0x3868 | `trig_sin_table` | Sine lookup table |
| 0x7B0E:0x3052 | `farobj_typedesc_table` | Entity type descriptor table |
