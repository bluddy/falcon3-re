# Falcon 3.0 — Runtime Architecture

*This file is superseded by the `docs/architecture/` directory.*
*Last full revision: 2026-11-12 (findings 1–179 + S4 Level-0 through Level-18+).*

See [docs/architecture/index.md](architecture/index.md) for the full specification.

## Quick Navigation

| Sub-document | Contents |
|---|---|
| [index.md](architecture/index.md) | Overview, quick-reference tables, key addresses |
| [binary.md](architecture/binary.md) | Toolchain, memory model, overlay system, calling conventions |
| [game_loop.md](architecture/game_loop.md) | Main frame loop, mode state machine, per-frame chains |
| [farobj.md](architecture/farobj.md) | FarObj struct (≥210B), type system, global tables, operation API |
| [entity.md](architecture/entity.md) | 4-layer entity architecture, lifecycle, class codes |
| [flight_physics.md](architecture/flight_physics.md) | Control axes, kinematics, aircraft slots, motion |
| [rendering.md](architecture/rendering.md) | 3D pipeline, terrain renderer, view_projection algorithm |
| [terrain.md](architecture/terrain.md) | Tile system (512×512 @ 13,108 units), coordinate conversion |
| [audio.md](architecture/audio.md) | OPL/FM (port 0x388 PROVEN), channel system, device types |
| [hardware_io.md](architecture/hardware_io.md) | IRQ0 timer, INT 33h mouse, joystick, BDA keyboard |
| [resource.md](architecture/resource.md) | op_dispatch (16 DOS services), streaming file API |
| [globals.md](architecture/globals.md) | Key globals, runtime segments, subsystem map, unknowns |

## What Changed

The original monolithic `architecture.md` (20 sections) is now split into focused
sub-documents with deeper detail in each area. The sub-documents add:
- Complete FarObj struct with dual-purpose field notes
- Full op_dispatch table with linear addresses and certainty levels
- Aircraft kinematics block (13-word flight state block)
- Terrain coordinate conversion formula
- Complete audio channel system (handle convention, volume table)
- Mode_frame_step_core detailed flow
- Entity motion table (27B per entry)
- BDA keyboard flags bit layout (PROVEN)
