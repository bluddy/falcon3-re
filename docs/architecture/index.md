# Falcon 3.0 — Architecture Specification

*Last updated 2026-11-12. Findings 1–179 + S4 bottom-up analysis (Levels 0–18+).*
*Certainty: **PROVEN** (byte-level) · **STRONG** (multi-signal) · **HYPOTHESIS** (single-signal) · **UNKNOWN***

This directory replaces `docs/architecture.md` with focused sub-documents.
See `docs/structures.md` for binary file format structs, `registry/functions.yaml` for
function signatures, `registry/structs.yaml` for data structure definitions.

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
| [terrain.md](terrain.md) | Tile world (512×512, 13,108 units/tile), terrain scripts | STRONG |
| [audio.md](audio.md) | OPL/FM sound, channel system, device types | PROVEN–STRONG |
| [hardware_io.md](hardware_io.md) | IRQ0 timer, INT 33h mouse, joystick, keyboard, BDA | PROVEN |
| [resource.md](resource.md) | op_dispatch (16 DOS services), streaming file API | PROVEN |
| [globals.md](globals.md) | Key globals, runtime segments, subsystem map, unknowns | STRONG |

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
| 0x2FEF2 | `game_frame_update_chain` | Entity simulation chain |
| 0x2FD42 | `game_frame_pipeline_step` | Rendering pipeline entry |
| 0x13CB0 | `farobj_batch_build_project` | Terrain tile batch renderer |
| 0x1740D | `sound_device_init` | Sound hardware initialization |
| R05_400C:0x34 | `farobj_main_table` | Main entity slot table |
| 0x7B0E:0x3868 | `trig_sin_table` | Sine lookup table |
| 0x7B0E:0x3052 | `farobj_typedesc_table` | Entity type descriptor table |
