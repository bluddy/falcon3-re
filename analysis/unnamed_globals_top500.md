# Unnamed Globals from Top 500 Analysis

This document lists all `word_XXXXX`, `byte_XXXXX`, and `dword_XXXXX` references found in our Top 500 analysis that need proper names.

## Menu/UI System Globals (Segment 7894h)

### Discovered in Top 400/500 Analysis

| Address | Current Name | Context | Proposed Name | Confidence |
|---------|-------------|---------|---------------|------------|
| 7894h:79B62 | word_79B62 | Current flight number (0-based) | `menu_current_flight_index` | HIGH |
| 7894h:79B6E | dword_79B6E | Flight data pointer | `menu_flight_data_ptr` | HIGH |
| 7894h:79B72 | word_79B72 | Total pilot/flight count | `menu_pilot_count_total` | HIGH |
| 7894h:79BDA | word_79BDA | Selected pilot index | `menu_pilot_selected_index` | HIGH |
| 7894h:79BEC | dword_79BEC | Flight record table (130B stride) | `menu_flight_records_ptr` | HIGH |
| 7894h:79BD8 | word_79BD8 | Campaign menu mode (0-7) | `menu_campaign_selected_mode` | HIGH |
| 7894h:79E64 | word_79E64 | UI state/mode | `menu_ui_state_flags` | MEDIUM |
| 7894h:79E70 | word_79E70 | Unknown word | `menu_unknown_79e70` | LOW |
| 7894h:79E72 | word_79E72 | Unknown word | `menu_unknown_79e72` | LOW |
| 7894h:79E80 | word_79E80 | VGA resolution check (300 threshold) | `ui_screen_width_pixels` | HIGH |
| 7894h:79E9C | word_79E9C | UI state | `menu_ui_state_79e9c` | MEDIUM |
| 7894h:79EA4 | word_79EA4 | Loadout mode flag | `menu_loadout_mode_flag` | HIGH |
| 7894h:79EEC | word_79EEC | Total flights count | `menu_total_flights_count` | HIGH |
| 7894h:79E60 | dword_79E60 | Loadout data pointer | `menu_loadout_data_ptr` | HIGH |
| 7894h:79E6C | dword_79E6C | Display record table | `menu_display_records_ptr` | MEDIUM |
| 7894h:79E28 | dword_79E28 | Unknown dword | `menu_unknown_79e28` | LOW |
| 7894h:79D1A | dword_79D1A | Unknown dword | `menu_unknown_79d1a` | LOW |
| 7894h:1938 | array | UI state array (word indexed) | `ui_state_word_array` | HIGH |
| 7894h:79976 | byte_79976 | UI palette/color data | `ui_palette_data_base` | MEDIUM |
| 7894h:79D6C | dword_79D6C | Aircraft array (18B stride) | `entity_aircraft_array_ptr` | HIGH |

### From apply_known_names.py (Already in Code)

| Address | Current Name | Status |
|---------|-------------|--------|
| 4FC2h:4FD5E | menu_current_id | ✓ Known |
| 4FC2h:4FD60 | menu_previous_id | ✓ Known |
| 4FC2h:4FD74 | menu_state_1 | ✓ Known |
| 4FC2h:4FD72 | menu_state_2 | ✓ Known |
| 7894h:79E60 | menu_loadout_data | ✓ Known (conflict with dword_79E60?) |
| 7894h:79B66 | menu_selection_state | ✓ Known |

## Input System Globals

| Address | Current Name | Context | Proposed Name | Confidence |
|---------|-------------|---------|---------------|------------|
| 1110h:11175 | byte_11175 | Input device calibration flag | `input_device_calibration_flag` | HIGH |
| CS:2F6B6 | byte_2F6B6 | Key event gate flag (0x0C) | `keyboard_event_gate_flag` | HIGH |
| CS:427B0 | byte range | Input state bytes (427B0-427B8) | `input_state_context_bytes` | HIGH |
| CS:427B2 | byte_427B2 | Previous state byte | `input_state_prev_byte1` | MEDIUM |
| CS:427B3 | byte_427B3 | Saved state byte | `input_state_saved_byte1` | MEDIUM |
| CS:427B6 | word_427B6 | Previous state word | `input_state_prev_word` | MEDIUM |
| CS:427B8 | word_427B8 | Saved state word | `input_state_saved_word` | MEDIUM |
| DS:15B4h | word | State flags register | `state_flags_register` | MEDIUM |

## Graphics/Rendering Globals

| Address | Current Name | Context | Proposed Name | Confidence |
|---------|-------------|---------|---------------|------------|
| DS:0EF5h | word | Rotation matrix element | `matrix_rotation_element_0ef5` | MEDIUM |
| DS:0EF7h | word | Rotation matrix element | `matrix_rotation_element_0ef7` | MEDIUM |
| CS:byte_1f72f | byte_1f72f | Rendering flag | `render_state_flag_1f72f` | MEDIUM |
| CS:byte_1f73a | byte_1f73a | Rendering flag | `render_state_flag_1f73a` | MEDIUM |
| 7894h:word_79B56 | word_79B56 | Graphics state | `graphics_state_79b56` | LOW |

## Text/Font Globals

| Address | Current Name | Context | Proposed Name | Confidence |
|---------|-------------|---------|---------------|------------|
| DS:2615h | word | Text buffer offset | `text_buffer_offset_2615` | MEDIUM |
| 0xD829h | word | HUD display buffer | `hud_display_buffer_base` | MEDIUM |
| CS:43509 | word_43509 | HUD text counter | `hud_text_line_counter` | MEDIUM |
| 14E964 | byte_14E964 | Screen transition counter (0-3) | `ui_transition_frame_counter` | HIGH |
| 151ABC | word_151ABC | Transition coordinate X | `ui_transition_coord_x` | HIGH |
| 151ABE | word_151ABE | Transition coordinate Y | `ui_transition_coord_y` | HIGH |

## Data Management Globals

| Address | Current Name | Context | Proposed Name | Confidence |
|---------|-------------|---------|---------------|------------|
| 709Fh:70A4D | word_70A4D | Data buffer cursor/offset | `data_buffer_cursor_709f` | HIGH |
| 709Fh:70A4F | word_70A4F | Data buffer related | `data_buffer_offset_70a4f` | MEDIUM |
| 788Dh | segment | 5-param structure base | `data_segment_788d_base` | MEDIUM |
| DS:word_709F0 | word_709F0 | Mode flag | `state_mode_flag_709f0` | MEDIUM |

## String/Resource Globals

| Address | Current Name | Context | Proposed Name | Confidence |
|---------|-------------|---------|---------------|------------|
| 602Eh:15155C | byte_15155C | String: "CAMPAIGN STATUS" | `str_campaign_status` | HIGH |
| 602Eh:151881 | byte_151881 | String: " OF " | `str_of` | HIGH |
| 602Eh:151749 | byte_151749 | String: "FLIGHT #" | `str_flight_number` | HIGH |
| 602Eh:151894 | byte_15183A | String: "PILOT INFORMATION" | `str_pilot_information` | HIGH |
| 602Eh:1515BB | byte_1515BB | String: "COMMS." | `str_comms` | HIGH |
| 602Eh:1516AE | byte_1516AE | String: "DONE" | `str_done` | HIGH |
| 602Eh:151A36 | byte_151A36 | String: "WAR ROOM" | `str_war_room` | HIGH |
| 602Eh:15196E | byte_15196E | String: "SET WAYPOINTS" | `str_set_waypoints` | HIGH |

## Campaign System Globals

| Address | Current Name | Context | Proposed Name | Confidence |
|---------|-------------|---------|---------------|------------|
| ES:dword_79BEC | dword_79BEC | Campaign entry table (130B stride) | `campaign_entries_table_ptr` | HIGH |
| DS:2224a | flag | Campaign file operation gate | `campaign_file_operation_flag` | HIGH |

## Hardware/Network Globals

| Address | Current Name | Context | Proposed Name | Confidence |
|---------|-------------|---------|---------------|------------|
| DS:word_78910 | word_78910 | Selection criteria filter | `filter_selection_criteria` | MEDIUM |

## Timer/Timing Globals

| Address | Current Name | Context | Proposed Name | Confidence |
|---------|-------------|---------|---------------|------------|
| CS:word_107759 | word_107759 | Frame tick rate | `timing_frame_tick_rate` | HIGH |
| CS:word_10788C | word_10788C | Callback iteration count | `timing_callback_iteration_count` | HIGH |
| CS:byte_107762 | byte_107762 | Timer related | `timing_byte_107762` | MEDIUM |
| CS:byte_10788B | byte_10788B | Timer related | `timing_byte_10788b` | MEDIUM |

## State Management Globals

| Address | Current Name | Context | Proposed Name | Confidence |
|---------|-------------|---------|---------------|------------|
| DS:word_10219 | word_10219 | State word | `state_word_10219` | MEDIUM |

## Unknown/Low Confidence

| Address | Current Name | Context | Proposed Name | Confidence |
|---------|-------------|---------|---------------|------------|
| 14F8C0 | word_14F8C0 | Unknown | TBD | LOW |
| 14F98C | word_14F98C | Unknown | TBD | LOW |
| 151C15 | word_151C15 | Unknown | TBD | LOW |
| 14E5A0 | byte_14E5A0 | Unknown | TBD | LOW |
| 14EC29 | byte_14EC29 | Unknown | TBD | LOW |
| 151337 | byte_151337 | Unknown | TBD | LOW |
| 7A302 | byte_7A302 | Unknown | TBD | LOW |
| 7A304 | byte_7A304 | Unknown | TBD | LOW |
| 7A305 | byte_7A305 | Unknown | TBD | LOW |
| 7A30E | byte_7A30E | Unknown | TBD | LOW |

---

## Summary

- **Total unnamed globals found**: ~80
- **High confidence names**: ~35
- **Medium confidence names**: ~25
- **Low confidence**: ~20

## Next Steps

1. Add high-confidence names to `registry/globals.yaml`
2. Update IDA database with proper global names
3. Replace word_/byte_ references in analysis documents
4. Update function descriptions in registry to use proper global names
5. Re-run apply_known_names.py to sync everything

## Priority for Loadout Menu Deep Dive

**Critical globals for loadout menu**:
1. `menu_current_flight_index` (word_79B62)
2. `menu_total_flights_count` (word_79EEC)
3. `menu_loadout_mode_flag` (word_79EA4)
4. `menu_loadout_data_ptr` (dword_79E60)
5. `menu_flight_records_ptr` (dword_79BEC)
6. `menu_pilot_selected_index` (word_79BDA)
7. `menu_pilot_count_total` (word_79B72)
8. `ui_screen_width_pixels` (word_79E80)

These 8 globals are referenced extensively in the R57 loadout menu functions.
