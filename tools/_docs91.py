"""Docs for Finding 91 (L19 Batch 5 of 6, 34 named). Idempotent per doc."""
import io

# ---------- findings_log.md (LF) ----------
FL = "docs/findings_log.md"
raw = io.open(FL, encoding="utf-8", newline="").read()
if "## 2026-10-19 91" not in raw:
    foot2 = "\n\n(append new findings below)"
    assert raw.rstrip("\n").endswith(foot2), repr(raw[-60:])
    i = raw.rindex(foot2)
    assert raw[:i].rstrip("\n").endswith("---"), "footer must be preceded by ---"
    entry = (
        "\n\n## 2026-10-19 91 - L19 Batch 5 of 6: 34 named, L19 queue 68 -> 34\n"
        "(`named` 1,536 -> **1,570**)\n"
        "\n"
        "Fifth slice of the giant Level-19 SCC. 34 of 68 named from\n"
        "`level19_batch5.txt` (6,023 ln). Highlights:\n"
        "\n"
        "**`farobj_record_bulk_copy`** (sub_30CB8, 518B, **in=25 - the most\n"
        "called helper in the batch**): bulk lodsb/lodsw field copy through\n"
        "the 500Ch:38h (74h) and 500Ch:4E8h (28h) record-pointer tables;\n"
        "callers span far_mode_event_dispatch, farobj_project_transform_write,\n"
        "and every farobj hub. **`mode_session_state_reset`** (sub_32C62,\n"
        "1204B, in=9): key_input_state_reset + op_bitmap_sweep_clear +\n"
        "ems_seg_free_21_49 + farobj_slot_create_ems + ems_gate_10218_run +\n"
        "hw_config_copy_22e_3e8, with the far request bodies at\n"
        "loc_32FE8/3303A/330B6. **`farobj_slot_project_step`** (sub_3C4F2,\n"
        "1983B, in=5): 16-slot 54AF:386Fh walk with selection compare vs\n"
        "word_55E50/word_2E104 feeding viewobj_project_select.\n"
        "\n"
        "**`tile_sample_script_dispatch`** (sub_386F2, in=13): rotates\n"
        "ds:816h/818h into ds:804h..80Ah then dispatch_220a4_stub ->\n"
        "record_script_exec_main. **`game_config_apply_init`** (sub_2F6D0,\n"
        "1123B, **in=16**): global config apply - overlay_seg_word_read,\n"
        "int15_joystick_detect, entity_setup_step, terrain_matrix_advance_11d04.\n"
        "**`hud_readout_timer_render`** (sub_46999): 0x40-row 63FD:10Eh\n"
        "countdown at word_2E112 rate -> hud_readout_render +\n"
        "hud_field0c/14_value_draw. **`ui_slot_filter_predicate`** (sub_4289E,\n"
        "in=2, ui_menu_panel_init + ui_loadout_menu_enter): the boolean slot\n"
        "filters used by menu init.\n"
        "\n"
        "**Also named:** ems_stream_pointer_step, event_table_name_fill,\n"
        "terrain_state_reinit, farobj_entity_attr_setup, farobj_class16_record_ops\n"
        "+ farobj_flag_dispatch_step (the entity_record_table_ops pair),\n"
        "hud_entity_search_select, hud_panel_rect_compute, farobj_slot_table_copy,\n"
        "matrix_constants_setup, viewport_rect_state_store, viewport_strip_row_draw,\n"
        "mode_request_code_dispatch, mode_quadrant_accum_step, mode_strip_frame_step,\n"
        "farobj_fuel_burn_step (one-shot [si+5Ah] bit2 fuel burn), and the two\n"
        "phase trampolines mode_phase_apply_state/event.\n"
        "\n"
        "### Gates (all green)\n"
        "\n"
        "`naming.py check` **1,572** . `verify_rebuild` **faithful (2,237 ==\n"
        "2,237)** . `verify_idb` **INTACT** . `name_readback` **1,570/1,570\n"
        "function + 2/2 global**.\n"
    )
    new = raw[:i] + entry + "\n---" + foot2
    io.open(FL, "w", encoding="utf-8", newline="").write(new)
    print("findings_log: inserted Finding 91 entry")
else:
    print("findings_log: Finding 91 already present")

# ---------- time_log.yaml (CRLF) ----------
TL = "docs/time_log.yaml"
raw = io.open(TL, encoding="utf-8", newline="").read()
if "Finding 91:" not in raw:
    j = raw.index("Finding 90")
    eol = raw.index("\n", j) + 1
    row = (
        "| 2026-10-19 (session 46) | ~2 h | **Finding 91: L19 Batch 5 of 6 -- "
        "34 named, `named` 1,536 -> **1,570**, L19 queue 68 -> 34**. "
        "Headlines: **farobj_record_bulk_copy** (in=25, most-called helper in "
        "the batch), **mode_session_state_reset** (in=9 session reset hub), "
        "**farobj_slot_project_step** (1983B 16-slot selection walk), "
        "**tile_sample_script_dispatch** (in=13), **game_config_apply_init** "
        "(in=16), **hud_readout_timer_render**, **ui_slot_filter_predicate**. "
        "Queue 95 -> 61. **Gates green:** check 1,572, verify_rebuild faithful, "
        "verify_idb INTACT, read-back 1570/1570+2/2. |\r\n"
    )
    new = raw[:eol] + row + raw[eol:]
    io.open(TL, "w", encoding="utf-8", newline="").write(new)
    print("time_log: inserted Finding 91 row")
else:
    print("time_log: Finding 91 row already present")

# ---------- status.md ----------
ST = "status.md"
raw = io.open(ST, encoding="utf-8", newline="").read()
if "L19 Batch 5/6 (finding 91)" not in raw:
    marker = "**Still outstanding:**"
    i = raw.index(marker)
    para = (
        "**L19 Batch 5/6 (finding 91):** 34 functions named "
        "(`named` 1,536 → **1,570**), **L19 `naming_queue` 68 → 34**. "
        "Headlines: **farobj_record_bulk_copy** (sub_30CB8, in=25 — bulk "
        "lodsb/lodsw copy through the 500Ch:38h/4E8h record-pointer tables, "
        "the batch's most-called helper); **mode_session_state_reset** "
        "(sub_32C62, in=9 — key/op/EMS reset hub with the far request "
        "bodies); **farobj_slot_project_step** (sub_3C4F2, in=5 — 16-slot "
        "54AF:386Fh selection walk → viewobj_project_select); "
        "**tile_sample_script_dispatch** (sub_386F2, in=13); "
        "**game_config_apply_init** (sub_2F6D0, in=16); "
        "**hud_readout_timer_render** (0x40-row countdown render); "
        "**ui_slot_filter_predicate** (menu-init boolean filters). "
        "**Gates green:** check **1,572**, verify_rebuild **faithful**, "
        "verify_idb **INTACT**, read-back **1,570/1,570 + 2/2**. "
        "Remaining: L19 batch 6 (34), then L20 (25), L21 (2).\n\n"
    )
    new = raw[:i] + para + raw[i:]
    io.open(ST, "w", encoding="utf-8", newline="").write(new)
    print("status: inserted L19 Batch 5/6 paragraph")
else:
    print("status: Batch 5/6 paragraph already present")

# ---------- open_items.md (CRLF, plain bullet) ----------
OI = "docs/open_items.md"
raw = io.open(OI, encoding="utf-8", newline="").read()
key = "L19 batch 6 (34"
if key not in raw:
    line = (
        "- L19 batch 6 (34 fns remaining of the giant SCC; "
        "`level19_batch6.txt` ready) \u2014 one final finding for the SCC; "
        "then L20 (25) + L21 (2) to hit queue 0.\r\n"
    )
    if not raw.endswith("\r\n"):
        raw += "\r\n"
    io.open(OI, "w", encoding="utf-8", newline="").write(raw + line)
    print("open_items: appended batch 6 bullet")
else:
    print("open_items: batch 6 bullet already present")
print("docs91 done")
