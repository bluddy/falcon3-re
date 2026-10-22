"""Docs for Finding 98 (orphan batch 4, 66 named). Idempotent."""
import io

# ---------- findings_log.md (LF) ----------
FL = "docs/findings_log.md"
raw = io.open(FL, encoding="utf-8", newline="").read()
if "## 2026-10-22 98" not in raw:
    foot2 = "\n\n(append new findings below)"
    assert raw.rstrip("\n").endswith(foot2), repr(raw[-60:])
    i = raw.rindex(foot2)
    assert raw[:i].rstrip("\n").endswith("---"), "footer must be preceded by ---"
    entry = (
        "\n\n## 2026-10-22 98 - Orphan batch 4 complete: 66 named\n"
        "(`named` 1,830 -> **1,896**; orphans 198 -> **132**)\n"
        "\n"
        "Batch 4 of the 397-orphan sweep named 66 (46 medium / 20 low\n"
        "conf). Headlines:\n"
        "\n"
        "**`r48_op_dispatch_batch_entry`** (r48_e191, 1470B, 4 callees):\n"
        "the largest batch-4 function - ~30x op_dispatch_far_entry\n"
        "state-init emissions (opcode 0Ah with 2/6/1 variants) over\n"
        "7894h/602Eh/7A32h/639Eh, clamps + farobj_field_scale_check.\n"
        "\n"
        "**`r39_ring_slot_render_entry`** (r39_e145, 686B C): 8 angular\n"
        "draws with x = base + {180,0,90,180,270,240,120,240} mod 360,\n"
        "height by 63955, closes r39_farptr_call_gate; sister\n"
        "**`r39_column_bar_render_entry`** (r39_e129, 306B C).\n"
        "\n"
        "**`r24_pane_toggle_menu_loop`** (r24_e60, 569B C): 6E45h\n"
        "DGROUP modal loop - word_6E8CC pane flips, 10-way key scan\n"
        "cs:239h jmp table, r17_menu_event_loop.\n"
        "\n"
        "**`view_wrap_projection_entry`** (sub_4DC16, 551B, 6 callees -\n"
        "camera wrap probe vs cs:2E108/2E10A, early retn leaves 474B\n"
        "tail undumped), **`record_span_mask_rebuild`** (sub_299D5),\n"
        "**`op_emit_far_state_step`** (sub_69ACB, 402B),\n"
        "**`r36_slot_type_priority_scan`**, **`r31_score_max_update`**,\n"
        "**`menu_mod_patch_row_set`** (self-modifying cs:6E146/6E148),\n"
        "**`key_action_101_range_gate`**, SBI pair\n"
        "(**`sbi_channel_flags_init`** / **`sbi_channel_release_gate`**),\n"
        "and the r12 record family (FD08h/FD05h/ah=0Ch variants).\n"
        "\n"
        "Low-conf tail: 13 `overlay_undecoded_body_*` markers + 7\n"
        "fragments (r35/r36/r38/r54 x2/r64/r67); 14 medium-conf\n"
        "`tail_bridge_to_*` 8-byte stubs (incl. loadout_enter d/e/f,\n"
        "state_init_all h/i, farobj_proc_c, panel_init_c).\n"
        "\n"
        "### Gates (all green)\n"
        "\n"
        "`naming.py check` **1,898** . `verify_rebuild` **faithful (2,237\n"
        "== 2,237)** . `verify_idb` **INTACT** . `name_readback`\n"
        "**1,896/1,896 function + 2/2 global**.\n"
    )
    new = raw[:i] + entry + "\n---" + foot2
    io.open(FL, "w", encoding="utf-8", newline="").write(new)
    print("findings_log: inserted Finding 98 entry")
else:
    print("findings_log: Finding 98 already present")

# ---------- time_log.yaml (CRLF) ----------
TL = "docs/time_log.yaml"
raw = io.open(TL, encoding="utf-8", newline="").read()
if "Finding 98:" not in raw:
    j = raw.index("Finding 97")
    eol = raw.index("\n", j) + 1
    row = (
        "| 2026-10-22 (session 50) | ~1 h | **Finding 98: orphan batch 4 "
        "complete -- 66 named, `named` 1,830 -> **1,896**, orphans 198 -> "
        "**132** (queue still 0).** Headlines: r48_op_dispatch_batch_entry "
        "(r48_e191 1470B 4-callee), r39_ring_slot_render_entry (686B C) + "
        "r39_column_bar_render_entry, r24_pane_toggle_menu_loop (569B C), "
        "view_wrap_projection_entry (551B), record_span_mask_rebuild, "
        "op_emit_far_state_step (402B), r36_slot_type_priority_scan, "
        "r31_score_max_update, menu_mod_patch_row_set, SBI pair, r12 "
        "record family; 46 medium / 20 low (13 overlay_undecoded_* + 7 "
        "fragments); 14 tail_bridge_to_* stubs. **Gates green:** check "
        "1,898, verify_rebuild faithful, verify_idb INTACT, read-back "
        "1896/1896+2/2. |\r\n"
    )
    new = raw[:eol] + row + raw[eol:]
    io.open(TL, "w", encoding="utf-8", newline="").write(new)
    print("time_log: inserted Finding 98 row")
else:
    print("time_log: Finding 98 row already present")

# ---------- status.md ----------
ST = "status.md"
raw = io.open(ST, encoding="utf-8", newline="").read()
if "ORPHAN BATCH 4 (finding 98)" not in raw:
    marker = "**Still outstanding:**"
    i = raw.index(marker)
    para = (
        "**ORPHAN BATCH 4 (finding 98):** the next 66 of 397 orphans "
        "named (`named` 1,830 → **1,896 / 2,237**; orphans 198 → **132**). "
        "Headlines: **r48_op_dispatch_batch_entry** (r48_e191, 1470B, 4 "
        "callees — ~30x op_dispatch_far_entry emissions); "
        "**r39_ring_slot_render_entry** (686B C) + **r39_column_bar_"
        "render_entry**; **r24_pane_toggle_menu_loop** (569B C modal "
        "loop); **view_wrap_projection_entry** (551B camera wrap); "
        "**record_span_mask_rebuild**; **op_emit_far_state_step** (402B); "
        "**menu_mod_patch_row_set** (self-modifying); SBI pair + r12 "
        "record family. 46 medium / 20 low (13 "
        "`overlay_undecoded_body_*` + 7 fragments) + 14 "
        "`tail_bridge_to_*` stubs. **Gates green:** check **1,898**, "
        "verify_rebuild **faithful**, verify_idb **INTACT**, read-back "
        "**1,896/1,896 + 2/2**.\n\n"
    )
    new = raw[:i] + para + raw[i:]
    io.open(ST, "w", encoding="utf-8", newline="").write(new)
    print("status: inserted ORPHAN BATCH 4 paragraph")
else:
    print("status: ORPHAN BATCH 4 paragraph already present")

# ---------- open_items.md (CRLF, update orphan bullet) ----------
OI = "docs/open_items.md"
raw = io.open(OI, encoding="utf-8", newline="").read()
old = "- Orphan batches 4-6 (198 orphans remaining of the 397; "
if old in raw:
    line_end = raw.index("\r\n", raw.index(old)) + 2
    line_start = raw.rindex("\n", 0, raw.index(old)) + 1
    new_line = (
        "- Orphan batches 5-6 (132 orphans remaining of the 397; "
        "orphan_batches.json has 6 batches) -- continue one finding per "
        "batch; 2 batches x ~66 fns each.\r\n"
    )
    raw = raw[:line_start] + new_line + raw[line_end:]
    io.open(OI, "w", encoding="utf-8", newline="").write(raw)
    print("open_items: updated orphan-batches bullet (4-6 -> 5-6)")
else:
    print("open_items: orphan bullet already at batch 5-6")
print("docs98 done")
