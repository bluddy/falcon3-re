"""Docs for Finding 99 (orphan batch 5, 66 named). Idempotent."""
import io

# ---------- findings_log.md (LF) ----------
FL = "docs/findings_log.md"
raw = io.open(FL, encoding="utf-8", newline="").read()
if "## 2026-10-22 99" not in raw:
    foot2 = "\n\n(append new findings below)"
    assert raw.rstrip("\n").endswith(foot2), repr(raw[-60:])
    i = raw.rindex(foot2)
    assert raw[:i].rstrip("\n").endswith("---"), "footer must be preceded by ---"
    entry = (
        "\n\n## 2026-10-22 99 - Orphan batch 5 complete: 66 named\n"
        "(`named` 1,896 -> **1,962**; orphans 132 -> **66**)\n"
        "\n"
        "Batch 5 of the 397-orphan sweep named 66 (47 medium / 19 low\n"
        "conf). Headlines:\n"
        "\n"
        "**`r33_op_vec3_init_batch`** (r33_e105, 1415B): the largest\n"
        "batch-5 function - vec3 op-batch state init across the overlay\n"
        "dispatch family.\n"
        "\n"
        "**`r40_progress_list_render_entry`** (r40_e130, 599B C) and\n"
        "**`r46_rowtable_remap_area`** (r46_e155, 534B C) - the two\n"
        "class-C render/remap entries of the batch.\n"
        "\n"
        "**`r48_time_threshold_table_init`** (r48_e76, 326B, no TERM),\n"
        "**`r38_mode_phase_select_entry`** (219B),\n"
        "**`r33_record_pair_status_resolve`** (201B C),\n"
        "**`view_scroll_quad_update`** (183B),\n"
        "**`menu_state_snapshot_load`** (161B), and\n"
        "**`mscdex_drive_string_setup`** (144B - MSCDEX drive-letter\n"
        "buffer setup).\n"
        "\n"
        "Also: `r33_slot_flag_scan_resolve`, `r35_mode9_menu_select_step`\n"
        "/ `r35_op_dispatch_f32_step`, `r08_angle_xy_quad_resolve`, the\n"
        "r12 record trio (FD0Ah/FD05h/tag 0Ah), KB pair\n"
        "(**`kb_field24_action_gate`** / **`kb_record_load_seg_wrapper`**),\n"
        "**`fixed_axis_sign_crosscheck`**, **`mem_free_probe_flags`**,\n"
        "string helpers (**`near_string_pair_split`** /\n"
        "**`near_table_slot_copy_advance`**), **`sbi_channel_release_"
        "state_get`**, **`table_iterate_far_wrapper`**, and the\n"
        "interrupt/flag gates (**`interrupt_enable_gate`** cli/sti,\n"
        "**`frame_preserve_true_gate`**, **`trig_bsearch_8364_far_"
        "wrapper`**).\n"
        "\n"
        "Low-conf tail: 10 `overlay_undecoded_body_*` markers + 7\n"
        "fragments (r15/r32/r53/r54/r56/r64/r67) + `r15_flag_body_far_"
        "wrapper` partial + `es_word_79f34_load` data fragment;\n"
        "15 medium-conf `tail_bridge_to_*` 8-byte stubs (incl.\n"
        "state_init_all j/k/l, loadout_enter g, entry_partial b/c,\n"
        "mode_set_637fc).\n"
        "\n"
        "### Gates (all green)\n"
        "\n"
        "`naming.py check` **1,964** . `verify_rebuild` **faithful (2,237\n"
        "== 2,237)** . `verify_idb` **INTACT** . `name_readback`\n"
        "**1,962/1,962 function + 2/2 global**.\n"
    )
    new = raw[:i] + entry + "\n---" + foot2
    io.open(FL, "w", encoding="utf-8", newline="").write(new)
    print("findings_log: inserted Finding 99 entry")
else:
    print("findings_log: Finding 99 already present")

# ---------- time_log.yaml (CRLF) ----------
TL = "docs/time_log.yaml"
raw = io.open(TL, encoding="utf-8", newline="").read()
if "Finding 99:" not in raw:
    j = raw.index("Finding 98")
    eol = raw.index("\n", j) + 1
    row = (
        "| 2026-10-22 (session 50) | ~1 h | **Finding 99: orphan batch 5 "
        "complete -- 66 named, `named` 1,896 -> **1,962**, orphans 132 -> "
        "**66** (queue still 0).** Headlines: r33_op_vec3_init_batch "
        "(r33_e105 1415B), r40_progress_list_render_entry (599B C) + "
        "r46_rowtable_remap_area (534B C), r48_time_threshold_table_init "
        "(326B no-TERM), r38_mode_phase_select_entry (219B), "
        "view_scroll_quad_update (183B), menu_state_snapshot_load (161B), "
        "mscdex_drive_string_setup (144B), r12 record trio, KB pair, "
        "interrupt/flag gates; 47 medium / 19 low (10 overlay_undecoded_* "
        "+ 8 fragments/partials + es data fragment); 15 tail_bridge_to_* "
        "stubs. **Gates green:** check 1,964, verify_rebuild faithful, "
        "verify_idb INTACT, read-back 1962/1962+2/2. |\r\n"
    )
    new = raw[:eol] + row + raw[eol:]
    io.open(TL, "w", encoding="utf-8", newline="").write(new)
    print("time_log: inserted Finding 99 row")
else:
    print("time_log: Finding 99 row already present")

# ---------- status.md ----------
ST = "status.md"
raw = io.open(ST, encoding="utf-8", newline="").read()
if "ORPHAN BATCH 5 (finding 99)" not in raw:
    marker = "**Still outstanding:**"
    i = raw.index(marker)
    para = (
        "**ORPHAN BATCH 5 (finding 99):** the next 66 of 397 orphans "
        "named (`named` 1,896 → **1,962 / 2,237**; orphans 132 → **66**). "
        "Headlines: **r33_op_vec3_init_batch** (r33_e105, 1415B); "
        "**r40_progress_list_render_entry** (599B C) + **r46_rowtable_"
        "remap_area** (534B C); **r48_time_threshold_table_init** (326B, "
        "no TERM); **r38_mode_phase_select_entry**; "
        "**view_scroll_quad_update**; **menu_state_snapshot_load**; "
        "**mscdex_drive_string_setup**; r12 record trio + KB pair + "
        "interrupt/flag gates. 47 medium / 19 low (10 "
        "`overlay_undecoded_body_*` + fragments) + 15 "
        "`tail_bridge_to_*` stubs. **Gates green:** check **1,964**, "
        "verify_rebuild **faithful**, verify_idb **INTACT**, read-back "
        "**1,962/1,962 + 2/2**.\n\n"
    )
    new = raw[:i] + para + raw[i:]
    io.open(ST, "w", encoding="utf-8", newline="").write(new)
    print("status: inserted ORPHAN BATCH 5 paragraph")
else:
    print("status: ORPHAN BATCH 5 paragraph already present")

# ---------- open_items.md (CRLF, update orphan bullet) ----------
OI = "docs/open_items.md"
raw = io.open(OI, encoding="utf-8", newline="").read()
old = "- Orphan batches 5-6 (132 orphans remaining of the 397; "
if old in raw:
    line_end = raw.index("\r\n", raw.index(old)) + 2
    line_start = raw.rindex("\n", 0, raw.index(old)) + 1
    new_line = (
        "- Orphan batch 6 (66 orphans remaining of the 397; "
        "orphan_batches.json has 6 batches) -- final batch of the "
        "orphan sweep (Finding 100, 1 batch x 66 fns).\r\n"
    )
    raw = raw[:line_start] + new_line + raw[line_end:]
    io.open(OI, "w", encoding="utf-8", newline="").write(raw)
    print("open_items: updated orphan-batches bullet (5-6 -> batch 6)")
else:
    print("open_items: orphan bullet already at batch 6")
print("docs99 done")
