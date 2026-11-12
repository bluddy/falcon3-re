# Game Loop & Mode State Machine

---

## Top-Level Loop: `main_frame_update_loop` (0x31319, 257B, R05_1F64)

```
while True:
    if word_54D2B <= 14 or == 26:   → MENU PATH
    elif word_54EFA == 0x0D:        → EXIT
    else:                           → FLIGHT PATH
```

### MENU PATH (each iteration)
1. `bda_kb_flag_get` → read BDA keyboard flags, store to byte_54F6D
2. `flag_bits_dispatch(BX=0x135, DI=0x141)` → dispatch input events
3. Loop if `byte_54F0C` ≠ 0; else `retn` (exit loop)

### FLIGHT PATH (each flight frame)
```
1.  game_frame_update_chain        ← entity simulation + AI + HUD  [see below]
2.  game_frame_pipeline_step       ← rendering + terrain + projection  [see below]
3.  viewport_rect_state_store      ← save viewport bounds
4.  tick_rate_compute              ← frame timing → cs:word_2F677/2F679
5.  flag22220_clear                ← reset tick_counter (cs:word_22220 = 0)
6.  view_terrain_frame_step        ← terrain step
7.  hud_data_panel_draw            ← HUD data panel
8.  vga_dac_palette_upload         ← upload palette to VGA DAC
9.  bda_kb_flag_get (second)       ← re-read keyboard state
10. flag_bits_dispatch(BX=0x148, DI=0x176) ← second input dispatch pass
11. → loop
```

### Key Globals

| Global | Type | Meaning |
|---|---|---|
| `word_54D2B` | uint16 | **Game mode**: ≤14 or =26 = menus; else = in-flight |
| `word_54EFA` | uint16 | Quit trigger: 13 (0x0D) = exit loop |
| `byte_54F0C` | uint8 | Loop continue: nonzero = keep looping (menu mode) |

---

## Entity Update Chain: `game_frame_update_chain` (0x2FEF2, 300B, R05_1F64)

Callers: `game_config_apply_init` (startup) and `sub_30D5F`.

```
farobj_slot_update_driver              → 16 entity slot records (0x54AF:0x386F)
farobj_move_accumulate_step(CX=82)     → entity motion accumulation
entity_timer_row_scan(CX=82, DI=0x4677) → countdown timers
aircraft_slot_cycle_step               → 40 aircraft/AI slots (0x49AB:[0xC])
mode_strip_frame_step
tile_object_interpreter
farobj_tile_key_cache
farobj_slot_step_spawn                 → spawn queue processing
farobj_sweep_all                       → slot+cmd+accum sweeps
range_cb_dispatch_loop
hud_state_rowtable_step  }
hud_panel_transform_step }   HUD
hud_readout_timer_render }
entity_timer2e_dec_14
sprite_project_gate_c5
entity_proj_depth_class                → depth classification (DS:48BAh entity)
angle_matrix_far_invoke(DS:48BAh+0xC)  → build rotation matrix from aircraft heading
fixed_matrix_load_7b0e(0x430C)         → load matrix into trig segment
```

**Aircraft state globals** (set/used in this chain):
- `DS:0x48BAh` = `current_aircraft_ptr` — current aircraft entity offset
- `DS:0x44AAh` = `aircraft_index` — 0-based aircraft index (0-2 for multiplayer)
- `DS:0x44DDh` = `entity_array_base` — entity array start offset (stride 0x52)
- `CS:word_2F679` = tick rate (computed by `tick_rate_compute`)

---

## Rendering Pipeline: `game_frame_pipeline_step` (0x2FD42, 387B, R05_1F64)

Called once per FLIGHT frame by `main_frame_update_loop`. Level-18 in callgraph.

```
fn_table_dispatch(SI=0x2C, DI=0x20) → select view mode, get projection constants
                                       stores BX→DS:0x30, CX→DS:0x2E, DX→DS:0x2C
near_fnptr_invoke                   → invoke registered near callback
farobj_pos_wrap_update(SI=0x2C, BX=0x2C) → set tile position update flag
pos_clamp_40(SI=0x20, DI=0x14)     → clamp aircraft position
entity_update_batch(SI=0x20)        → terrain map window update
view_pos_cache_update               → position cache (gated: cs:byte_2F6BA==0)
terrain_vm_flag_gate(SI=0x20, BX=0x2C, AX=DS:0x24Dh) → terrain VM mode flags
flag_gate_zero_abc                  → flag gating → stores to DS:0x4EAh
[DS:4EAh & 1] viewmode3_vector_project → mode 3 cockpit vectors
entity_state_load(BX=0x2C, SI=0x14) → terrain/entity state computation
[DS:4EAh & ~2] terrain_frame_update_driver(BX=0x2C) → terrain scripts
viewlist_project_flagged            → project flagged view objects
state_word_11cc8_get + r39_farptr_gate_big → entity state gate
farobj_scan_74_timer_c              → animation timers (mod 8)
farobj_scan_74_gate_a               → scan visibility gates
farobj_sort_and_step (3× per mode?) → depth sort + step farobj instances
```

**View mode flag `DS:4EAh`**:
- bit 0 = use `viewmode3_vector_project`
- bit 1 = skip `terrain_frame_update_driver`

---

## Mode Frame Step Core: `mode_frame_step_core` (0x3A3D6, 508B, R05_1F64)

Per-entity simulation step, called each frame for each active entity.

**Entry condition check** (gate):
```
IF ds:0x44C != 0 OR [si+0xCAh] & 0x100: set ds:0x4AC4=0, return
```

**On entry**: stores state: `cs:byte_39AA8=AH`, `ds:0x49A3=AH`, `ds:0x49A2=AL`, `ds:0x706=SI` (entity ptr), `ds:0x49A0=cs:word_2F679` (tick rate).

**Main operations**:
1. `cs_word_store(AL=ds:0x4A7Eh)` — store mode byte
2. `dispatch_220d8_via_24bba` — render callback
3. `far_cb_2`, `sub_263F6` (farobj render vtable) — rendering dispatch
4. `view_limits_load(SI=0x49C0)` — load view limits
5. Mode phase check: `ds:0x4AC2 >= 4` → alternate path
6. `ds:0x4A83` gate: determines if `steerpoint_scan_update` runs
7. `ds:0x4A89` counter: compared to tick rate → gates `entity_table_walk_49a3`
8. Farobj active gate: checks `ES:[bx+0x74] & 1` from scan list

**Key globals**:

| Global | Description |
|---|---|
| `DS:0x706h` | simulation entity ptr (SI on entry) |
| `DS:0x4AC2h` | mode phase counter; ≥ 4 = alternate rendering path |
| `DS:0x4AC4h` | gate: 0 = paused/skipped |
| `DS:0x4A7Eh` | current mode byte (passed to dispatch) |

---

## Input Event System: `flag_bits_dispatch` (0x24FB9, 97B, Level-18)

Runs TWICE per FLIGHT frame (different BX/DI selectors each pass, 21K total dynamic calls).

```
CS:0x5762   flag_block_merge_zero_5c63 → merges/clears flag bytes
            ↓
Loop i=0..10, bit 7..0:
  if CS:0x5762[i] bit set:
    cs:byte_24E21 = 0xFF       ← event dispatched flag
    key_event_table_dispatch   ← dispatch to handler
    bit >>= 1
  al += 1                       ← event ID counter
Return: CF=0 if any event, CF=1 if none
```

**Event layout**: 11 bytes × 8 bits = 88 input event slots at `CS:0x5762`.
Each bit = one keyboard/button event mapped to a handler in `key_event_table`.
