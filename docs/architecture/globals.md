# Globals, Segments & Subsystem Map

---

## Key Runtime Segments

| Segment | Paragraph | Description | Evidence |
|---|---|---|---|
| **DGROUP** | **0x7A32** | Main data/stack; DS=SS=DGROUP throughout | PROVEN (finding 121) |
| 0x71C1 | 0x61C1 | Terrain/map data; entity positions relative to tile grid | STRONG |
| 0x7772 | 0x6772 | Event/sound/hardware state: sound card mode, event counters, IRQ state | STRONG |
| 0x7894 | 0x6894 | Game entity state: slot index table, entity counters | HYPOTHESIS |
| 0x7B0E | 0x6B0E | Trig/projection math: sine table, view matrix, farobj sort arrays | STRONG |
| 0x49AB | 0x39AB | Aircraft/AI slot data (aircraft_slot_cycle_step DS) | STRONG |
| 0x54AF | 0x44AF | Main farobj scan list, entity slot records, entity accum table | STRONG |
| 0x65A7 | — | Secondary entity data (aircraft_slot_cycle_step second DS) | HYPOTHESIS |
| 0x62D4 | — | Mode 3 cockpit vector data (viewmode3_vector_project) | HYPOTHESIS |
| 0x69FF | — | Entity motion table (farobj_move_accumulate_step) | STRONG |
| 0x6B58 | — | Spawn queue data (farobj_slot_step_spawn) | HYPOTHESIS |
| 0x834A | — | Frame callback ES segment (preset in far_cb_with_args) | HYPOTHESIS |
| 0x5982 | — | Entity sweep / game-state table area | HYPOTHESIS |
| 0x7075 | — | ISLDAT/entity file data (entity_slot_create) | HYPOTHESIS |

---

## DGROUP Key Globals (DS=0x7A32 = linear 0x7A320)

### Timer / Synchronization

| CS/DS offset | Name | Type | Description |
|---|---|---|---|
| `cs:byte_2224B` | `timer_gate_flag` | uint8 | 1 = suppress tick_counter in IRQ0 |
| `cs:word_22220` | `tick_counter` | uint16 | Gated IRQ0 counter (gate=0 → increments) |
| `cs:word_22222` | `timer_divider` | uint16 | Always increments; AND 3 == 0 → BIOS chain |
| `cs:byte_22246` | `joystick_timer_flag` | uint8 | Enables joystick polling via IRQ0 chain |
| `cs:word_2F677/2F679` | `tick_rate` | uint16×2 | Frame timing (computed by tick_rate_compute) |

### FarObj / 3D Context

| CS/DS offset | Name | Type | Description |
|---|---|---|---|
| `cs:word_22210` | `active_farptr_offset` | uint16 | Current 3D context pointer — offset |
| `cs:word_22212` | `active_farptr_seg` | uint16 | Current 3D context pointer — segment |
| `cs:word_22214` | `saved_farptr_offset` | uint16 | Saved 3D context pointer — offset |
| `cs:word_22216` | `saved_farptr_seg` | uint16 | Saved 3D context pointer — segment |
| `cs:word_1F6E6` | — | uint16 | Secondary projection scale factor (view_projection CX) |

### Rendering Batch

| CS/DS offset | Name | Type | Description |
|---|---|---|---|
| `cs:byte_1F734` | `batch_active_flag` | uint8 | Render batch active (flag_set_lowbit/flag_clear) |
| `cs:byte_1F733` | `batch_mode_bits` | uint8 | Bit 0 drives batch_active_flag |
| `cs:byte_1F743` | `render_batch_flag` | uint8 | Read by flag_byte_get; checked by pipeline stages |
| `cs:word_1F71C` | — | uint16 | Saved ES (view origin segment, set by view_projection) |
| `cs:word_1F71E` | — | uint16 | Saved BX (view origin offset, set by view_projection) |

### Render Dispatch Pointers (cs:0x2200x family)

| CS address | Name | Description |
|---|---|---|
| `cs:dword_220A0` | — | dispatch_220a0_stub callback |
| `cs:dword_220C8` | `clip_handler` | Clip/skip path (AX < 0 → skip draw) |
| `cs:opcode_handler_1` | — | far_cb_0 target |
| `cs:opcode_handler_2` | — | far_cb_1 target |
| `cs:opcode_handler_5` | `draw_handler` | Draw path (AX ≥ 0 → draw) |
| `cs:dword_220D0` | — | dispatch_220d0_stub (terrain strip) |
| `cs:dword_220D4` | — | dispatch_220d4_stub (HUD draw) |
| `cs:dword_220E0` | `frame_cb_ptr` | Main frame callback (ES=0x834A set) |
| `cs:dword_220E4` | `view_limits_cb_ptr` | View frustum limits callback |
| `cs:dword_220EC` | — | dispatch_220ec_invoke target |

### Viewport / Clipping

| CS/DS offset | Name | Type | Description |
|---|---|---|---|
| `cs:word_2547C` | `viewport_xmin` | int16 | Left clip bound for segment_clip_test |
| `cs:word_25480` | `viewport_xmax` | int16 | Right clip bound |
| `cs:word_2547E` | `viewport_ymin` | int16 | Top clip bound |
| `cs:word_25482` | `viewport_ymax` | int16 | Bottom clip bound |
| `cs:byte_25484` | `op_flags` | flags8 | far_op_execute dispatch control (bit 3 = bypass) |
| `cs:byte_2548B` | — | uint8 | Clip pending flag (set by clip_pending_atomic_apply) |
| `cs:byte_2549D` | — | uint8 | Gate: nonzero → skip clip_pending_apply_record |

### Game Mode / Loop

| DS offset | Name | Type | Description |
|---|---|---|---|
| `word_54D2B` | `game_mode` | uint16 | ≤14 or =26 = menus; else = in-flight simulation |
| `word_54EFA` | `quit_flag` | uint16 | 13 (0x0D) = exit game loop |
| `byte_54F0C` | `loop_continue` | uint8 | Nonzero = continue main loop iteration |
| `byte_54F6D` | `bda_kb_state` | uint8 | Last read BDA keyboard flags |

### Input

| CS address | Name | Type | Description |
|---|---|---|---|
| `cs:0x5762` | `input_flag_bytes` | flags8[11] | 88-bit event flag bitmap (flag_bits_dispatch) |
| `cs:byte_22232+0` | `axis_aileron` | int16 | Aileron/roll axis ±2048 |
| `cs:byte_22232+2` | `axis_elevator` | int16 | Elevator/pitch axis ±2048 |
| `cs:byte_22232+4` | `axis_throttle` | int16 | Throttle axis ±2048 |
| `cs:byte_22232+6` | `axis_rudder` | int16 | Rudder/yaw axis ±2048 |
| `cs:word_2222C` | `axis_sensitivity` | uint16 | Axis normalization divisor |
| `cs:word_11102` | `joy_btn_latch` | uint16 | Joystick/mouse button latch (input_status_pack) |

### File I/O / Streaming

| CS address | Name | Type | Description |
|---|---|---|---|
| `cs:word_22248` | `op_status` | flags8 | op_dispatch status (bit 7 = mode preserve) |
| `cs:byte_2224A` | `op_error_flag` | uint8 | Set on op_dispatch error; triggers terminate |
| `cs:byte_2224B` | `timer_gate_flag` | uint8 | Set during file_read to gate IRQ0 counter |
| `cs:word_27476` | `file_handle` | uint16 | Current streaming file handle |
| `cs:word_2747A` | `stream_budget` | uint16 | Bytes remaining in streaming budget |
| `cs:word_27480/27482` | `stream_src_ptr` | far_ptr | Source copy pointer for streaming |

---

## 0x7B0E Trig/Matrix Segment

| Offset | Name | Type | Description |
|---|---|---|---|
| `0x3052` | `farobj_typedesc_table` | far_ptr[N] | FarObj type descriptor table (indexed by object_kind×4) |
| `0x3868` | `trig_sin_table` | int16[N] | Sine lookup table (trig_table_lookup reads here) |
| `0x379E` | — | uint8[11] | draw_from_struct temporary draw parameters |
| `0x43BA` | `flight_state_trig` | int16[13] | Copy of aircraft kinematics for matrix computation |
| `0x430C` | — | — | View matrix load target (fixed_matrix_load_7b0e) |
| `0x7E948` | `view_matrix` | int16[4] | 2×2 view rotation matrix (from fn_table_dispatch) |
| `0x7E966` | `proj_z_scale` | int16 | Projection Z scale factor |
| `0x7E968` | `proj_z_offset` | int16 | Projection Z offset |
| `0x7E94C` | — | int16[N] | Projection constant block |
| `0x7BFEC+0x68` | — | uint16 | First farobj sort array pointer count |
| `0x7BFEC+0x10D6` | — | uint16 | Second farobj sort array pointer count |
| `0x2DF8` | — | ptr[N] | First farobj sort array (sorted by [+1FE8h]) |
| `0x1D8A` | — | ptr[N] | Second farobj sort array (sorted by [+0F7Ah]) |

---

## 0x7772 Event/Sound Segment

| Offset | Name | Description |
|---|---|---|
| `0x77B1F+0x27` | `event_state` | Current event state code (drives 17-case dispatch in event_state_machine) |
| `0x77B1F+0x17` | — | Entity AI state word |
| `0x77B1F+0x19` | — | Entity activity counter |
| `0x77B1F+0x177` | — | Entity behavior enable flag |
| `0x77B1F+0x17Bh` | — | Countdown shift register |
| `0x77B1F+0x179h` | — | Shift count for countdown |
| `0x506+N` | `entity_timers` | Per-entity countdown timers (1B each) |
| `0xFDE8` | — | Channel 6 audio level word A (sbi_level_write_6) |
| `0xFDEA` | — | Channel 6 audio level word B |

---

## 0x54AF Farobj / Entity Area

| Offset | Name | Description |
|---|---|---|
| `0x1734` | `farobj_scan_list` | 16 × 4B far pointers to active FarObj instances |
| `0x4ED` | `entity_accum_table` | 40 × 14B EntityAccumEntry motion records |
| `0x386F` | `entity_slot_records` | 16 × 92B entity slot records (farobj_slot_update_driver) |

---

## Overlay Segment Map (Post-finding 120, 47 R05 object segments)

| Overlay | Contents | Key functions |
|---|---|---|
| Resident (seg000-seg020) | Core: IRQ, mouse, farobj API, 3D math, viewport | op_dispatch, farptr_table_get, view_projection, timer_tick_isr |
| R05_1E10 | FarObj entity management, sweep, field ops | farobj_entity_accum_sweep, farobj_slot_sweep, entity_slot_create |
| R05_1EFE | 3D projection utilities, angle math | pos_diff_norm, viewobj_project_if_moved |
| R05_1EA1 | Entity creation | entity_slot_create, entity_slot_pair_create, entity_record_table_build |
| R05_1F40 | View mode 3 vectors | viewmode3_vector_project |
| R05_1F59 | View list projection | viewlist_project_flagged |
| R05_1F64 | Main game loop, rendering pipeline | main_frame_update_loop, game_frame_pipeline_step, game_frame_update_chain, mode_frame_step_core |
| R05_2ACF | Position step engine | pos_step_chain_engine |
| R05_2B83 | Terrain sampling, sprite projection, farobj update | farobj_slot_update_driver, farobj_record_ops_exec |
| R05_3xxx | Flight physics, state machines | mode_session_state_reset, steerpoint chain |
| R05_33AE | Entity attribute setup | farobj_entity_attr_setup (entity class type table) |
| R05_393C | Aircraft slot cycling | aircraft_slot_cycle_step |
| R05_3BDD | FarObj type gate | farobj_type_gate_test |
| R05_3DAD | Terrain object projection | sub_4DC97, sub_4DDB4 (LOD 3-tier) |
| R05_3D81 | Entity spawning | farobj_slot_step_spawn |
| R05_3C0D | Entity motion accumulation | farobj_move_accumulate_step |
| R06_xxx | Menu/UI | UI event loop |
| R07 (seg006-007) | Sound system | opl_reg_write, channel_*, sbi_* |
| R12_xxx | State record entries | r12_state_record |
| R14_5E0B | Stream read, farptr gate | r14_stream_read |
| R15_5E8F | Flag/sequence dispatch | r15_flag_107762 |
| R17_5E8F | UI event loop | r17_event_main_loop |
| R30_569F | Loadout menu | ui_loadout_menu_enter, r30_record_link |
| VGRAPH (0x85AE0) | Graphics driver | 40-slot entry table, pixel ops |

---

## What We Don't Know Yet

1. **Entity class codes** (0x12/0x14/0x33/0x38): type table B at R05_33AE DS:0x16F4 not
   correctly read yet due to segment base calculation complexity.

2. **Full FarObj struct** (fields 0x2E–0x73 and 0x7C–0xD0): ~100 bytes unmapped.
   `farobj_record_ops_exec` accesses something at [+0xC0/0xC1] = 0x1E (30, possibly HP/fuel).

3. **13-word flight state block** (DS:[0x32]): exact layout not decoded (heading, speed,
   altitude, roll, pitch, XYZ deltas — order and encoding unknown).

4. **Aircraft aerodynamics**: lift/drag/gravity equations inside `pos_step_chain_engine`
   not yet decoded (1762B of self-modifying code).

5. **event_state_machine** (0x1AB34, 2266B): 17-case switch not fully decoded.

6. **HUD rendering path**: how does `record_queue_push` output get displayed?
   `far_cb_3`/`far_cb_7` in `draw_from_struct` are the likely endpoints.

7. **Tile command stream format**: `farobj_batch_build_project` command byte format
   (bit 7 meaning, top-2-bit skip condition) needs more analysis.

8. **Campaign/mission state** (above Level-18): `main_frame_update_loop` → what calls it?
   The game's campaign structure, mission load/save, and debrief systems.

9. **15 view mode functions** (fn_table_dispatch table sub_23235..sub_235BB):
   what does each of the 15 view modes implement?

10. **Asset format**: PKWARE DCL compression — never confirmed in use.
